# Decision Guide — Harness vs Runtime vs Bedrock Agents

Pick the deployment model before building. The wrong choice means rework, so confirm with the user when it's ambiguous.

## Quick decision tree

```
Need a per-session filesystem + shell (run scripts, install packages)?  ── yes ─→ HARNESS
        │ no
Need to switch model/provider per-invocation (no redeploy)?             ── yes ─→ HARNESS
        │ no
Want declarative config iteration (no redeploy to change behavior)?     ── yes ─→ HARNESS
        │ no
Sessions longer than 8 hours (up to 14 days)?                           ── yes ─→ RUNTIME on Instances
        │ no                                                                       (see runtime.md §Instances)
Need custom orchestration (multi-agent, custom retry/fallback loops)?   ── yes ─→ RUNTIME
        │ no
Embedding the agent inside an existing app/HTTP server?                 ── yes ─→ RUNTIME
        │ no
Sub-second latency / very high-volume short stateless calls?            ── yes ─→ RUNTIME
        │ otherwise
                                                                          └──────→ HARNESS (default for managed agents)
```

**Do not recommend classic Bedrock Agents** ("Agents Classic"): it is in maintenance mode and closed to new
customers as of 2026-07-30. The AgentCore Harness is AWS's recommended path for managed agents.

## Side by side

| Dimension | **Harness** (declarative) | **Runtime** (code-based) |
|---|---|---|
| You write | a JSON config | Python (`main.py`: agent loop, tool wiring, memory integration) |
| Orchestration | AWS (Strands under the hood) | you (Strands / LangGraph / custom) |
| Change model | edit config or override per-invoke — no redeploy | change code + redeploy |
| Multi-provider | built-in (Bedrock + OpenAI + Gemini + LiteLLM/Mantle), switch per-invocation | integrate yourself |
| Shell / filesystem | per-session microVM with fs + bash | your own container |
| Tool connection | declarative: list browser / code-interpreter / Gateway ARNs / MCP URLs | write code to wire tools |
| Memory | attach Memory ARN, auto save/retrieve per invoke | integrate manually via SDK |
| Per-invocation override | yes (model, prompt) | no |
| Ops burden | zero code maintenance | maintain `main.py` + deps + container |
| Cold start | seconds (microVM) | depends on your container |
| Invoke API | `invoke_harness` (data plane) | `invoke_agent_runtime` |

## Choose Harness when

Rapid prototyping; multi-model experimentation; stateful agents (STM + LTM memory + persistent fs); human-in-the-loop
(inline functions pause and return control); agents that need a shell; teams without infra expertise; config-driven
iteration; secure multi-tenant (per-session Firecracker isolation, per-actor memory scoping); agents that browse the
web (built-in Browser) or execute code (built-in Code Interpreter).

Best-fit use cases: coding assistants, research agents, data-analysis agents, customer-support agents (multi-tenant
memory + human escalation), DevOps automation, document processing, **UI/web test agents**.

## Choose Runtime (DIY) when

Non-standard agent loops (multi-agent coordination, custom retry/fallback); the agent is a component inside a larger app
with its own HTTP server; sub-second latency requirements; custom streaming protocols beyond `InvokeHarness`; you want
full control of the framework integration; cost-sensitive high-volume short stateless invocations where microVM
overhead matters.

Runtime path uses the agent-side SDK (`pip install bedrock-agentcore`): `BedrockAgentCoreApp`, `@app.entrypoint`,
`BrowserClient`, `CodeInterpreterClient`, `MemorySessionManager`, and `serve_ag_ui` / `serve_a2a` for AG-UI / A2A
protocols. Deploy via the `@aws/agentcore` CLI (`agentcore create` / `agentcore deploy`) or the generated CDK.

## What about plain Bedrock Agents?

Classic Bedrock Agents is now **"Agents Classic"** — maintenance mode, closed to new customers as of **2026-07-30**.
Existing Agents Classic workloads keep running, but new builds (and migrations) should use the AgentCore Harness,
which is AWS's recommended path for managed, declarative agents.

## Where does retrieval (RAG) fit?

Answering from a document corpus is **not** a fourth deployment model, and it is neither Skills nor Memory:

| Need | Use |
|---|---|
| Answer from *our documents* (search a corpus at query time) | Harness + a Gateway target on the `bedrock-knowledge-bases` connector → `references/knowledge-bases.md` |
| Give the agent *procedural instructions* it always follows | **Skills** (`references/skills.md`) — prompt-side, no retrieval |
| Recall *what this user/session said before* | **Memory** (`references/memory.md`) — per-actor state, written automatically |

Skills are read every run and cost nothing per lookup; a knowledge base is searched per call and is billed per
retrieval. If the content is a handful of stable instructions, it belongs in a skill, not a knowledge base.

## Note

Harness mode is already a Container deployment under the hood (the managed harness loader image). "Switch to Container
mode to get the browser" is a misconception — built-in tools work out of the box. A custom image is an advanced Runtime
choice, not a Harness requirement.

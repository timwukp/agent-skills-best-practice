# Decision Guide — Harness vs Runtime vs Bedrock Agents

Pick the deployment model before building. The wrong choice means rework, so confirm with the user when it's ambiguous.

## Quick decision tree

```
Need a per-session filesystem + shell (run scripts, install packages)?  ── yes ─→ HARNESS
        │ no
Need to switch model/provider per-invocation or mid-session?            ── yes ─→ HARNESS
        │ no
Want declarative config iteration (no redeploy to change behavior)?     ── yes ─→ HARNESS
        │ no
Need custom orchestration (multi-agent, custom retry/fallback loops)?   ── yes ─→ RUNTIME
        │ no
Embedding the agent inside an existing app/HTTP server?                 ── yes ─→ RUNTIME
        │ no
Sub-second latency / very high-volume short stateless calls?            ── yes ─→ RUNTIME
        │ no
Want fully no-code, console-only tool calling, no fs/shell?             ── yes ─→ BEDROCK AGENTS
        │ otherwise
                                                                          └──────→ HARNESS (default for managed agents)
```

## Side by side

| Dimension | **Harness** (declarative) | **Runtime** (code-based) |
|---|---|---|
| You write | a JSON config | Python (`main.py`: agent loop, tool wiring, memory integration) |
| Orchestration | AWS (Strands under the hood) | you (Strands / LangGraph / custom) |
| Change model | edit config or override per-invoke — no redeploy | change code + redeploy |
| Multi-provider | built-in (Bedrock + OpenAI + Gemini), switch mid-session | integrate yourself |
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

## Choose neither (plain Bedrock Agents) when

Fully no-code console configuration is enough; only simple tool calling, no filesystem/shell; no multi-model or
mid-session switching needed.

## Note

Harness mode is already a Container deployment under the hood (the managed harness loader image). "Switch to Container
mode to get the browser" is a misconception — built-in tools work out of the box. A custom image is an advanced Runtime
choice, not a Harness requirement.

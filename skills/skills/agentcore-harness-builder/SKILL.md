---
name: agentcore-harness-builder
description: Build production-ready AWS Bedrock AgentCore Harness agents end to end — declarative model + system prompt, Memory (semantic/episodic/summarization/user-preference), built-in Browser and Code Interpreter, Gateway/MCP tools, inline functions, Skills, advanced config (truncation, limits, lifecycle, network, inbound auth), Observability (log delivery + tracing), Evaluations, Optimizations, Identity (outbound auth, Token Vault, credential providers), Policy guardrails, Payments, and the Agent Registry. Use whenever the user wants to create, configure, deploy, wire, harden, invoke, or troubleshoot an AgentCore Harness — or asks about AgentCore best practices, harness.json, CreateHarness/UpdateHarness/InvokeHarness, attaching Memory, wiring browser/code-interpreter, adding skills, observability/log delivery, or A/B-testing prompts. Trigger even when the user describes a managed, declarative Bedrock agent with tools/memory/skills without saying "harness".
license: Complete terms in LICENSE.txt
---

# AWS Bedrock AgentCore Harness Builder

## Overview

A **Harness** is AWS Bedrock AgentCore's declarative, fully-managed way to run an agent. You hand AWS a JSON
configuration — model, system prompt, tools, memory, skills, limits — and AWS runs the agent loop (Strands under the
hood) inside a per-session Firecracker microVM with its own filesystem and shell. No container to build, no agent loop
to write. You change behavior by changing config, not redeploying code, and you can override model/prompt per
invocation.

This skill builds a **complete, best-practice Harness use case** that exercises every AgentCore capability the user
needs, wired correctly the first time. AgentCore is a fast-moving **preview** service whose real API shapes often
differ from the published docs — this skill encodes the hard-won facts so you don't rediscover them through validation
errors.

### The two-plane mental model (internalize this first)

AgentCore has two distinct API surfaces. Confusing them is the #1 source of wasted time.

| Plane | What it is | How you call it |
|---|---|---|
| **Control plane** | Create/configure/inspect resources (harness, memory, runtimes) | `boto3.client("bedrock-agentcore-control")` — `create_harness`, `update_harness`, `create_memory`, … |
| **Data plane** | Invoke a running harness | `boto3.client("bedrock-agentcore")` — `invoke_harness` |

The agent-side SDK (`pip install bedrock-agentcore`) is a *third* thing: it's the library that runs **inside** a custom
Runtime container (`BedrockAgentCoreApp`, `BrowserClient`, `MemorySessionManager`). **A Harness does not need it** — the
managed harness loader image already wires the tools. You only touch the agent-side SDK if you drop down to Runtime
mode. See `references/decision-guide.md`.

---

## Before you build: confirm Harness is the right tool

Don't assume. If the user needs custom orchestration, sub-second latency, or to embed the agent inside an existing HTTP
service, **Runtime** (code-based) is the better fit; for a no-code console-configured assistant, plain **Bedrock
Agents** may be enough. Read `references/decision-guide.md` and confirm with the user when it's ambiguous. If Harness is
clearly right (filesystem/shell needed, multi-model switching, declarative iteration, built-in browser/code-interpreter,
stateful memory), proceed.

If Runtime is the right fit instead (you need control of the loop, AG-UI / A2A protocols, embedding in an existing app),
this skill still helps: `references/runtime.md` covers the code-first path end to end (`BedrockAgentCoreApp`,
`@app.entrypoint`, the `/invocations`/`/ping` HTTP contract incl. the `time_of_last_update` gotcha, AG-UI / A2A, and
`CreateAgentRuntime` shapes). Memory, Identity, Observability wire the same way as for a Harness — pass the Runtime's
`roleArn` to `wire_memory.py` and `setup_observability.py`.

---

## The build workflow

Work through these phases in order. Each phase points to a reference file — **read the reference before writing the
config or running the script for that phase.** Don't try to hold every field shape in your head; the references exist
because the exact shapes are non-obvious and the cost of guessing wrong is a failed `update_harness` or a broken
session start.

### Phase 0 — Preflight (always do this first)

The harness control-plane operations simply **do not exist** in older SDKs. Before anything else, run:

```bash
python scripts/preflight.py --region us-east-1
```

This verifies `boto3 >= 1.43.18` and AWS CLI v2 `>= 2.34.57` (older versions return **zero** harness operations),
confirms credentials and region (preview lives in `us-east-1`, `us-west-2`, `eu-central-1`, `ap-southeast-2`), and
prints the live `CreateHarness`/`UpdateHarness` input shapes via schema introspection so you build against *this*
account's actual API, not stale docs. If it reports a version gap, fix that before continuing — nothing downstream will
work otherwise. Details: `references/gotchas.md` §versions and §schema-introspection.

### Phase 1 — Design the use case

Decide which capabilities this agent needs. Walk the user through the **feature checklist** below and record choices.
Anchor the design on a known-good shape: `assets/harness.json.template` mirrors a real, working production harness
(the UITestAgent) and is the safest starting point. Copy it and strip what the use case doesn't need rather than
building from an empty file.

### Phase 2 — Author the configuration

Fill in the config section by section. Read the matching reference as you go:

| Section | Reference | Key best practice |
|---|---|---|
| Model + system prompt + inference config | `references/model-and-prompt.md` | Pick an inference-profile model id (`global.*`/`us.*`); use Converse API; keep the prompt declarative and rule-based |
| Tools: Browser, Code Interpreter, Gateway/MCP, inline functions | `references/tools.md` | `tools[].config` is *practically required* to actually wire a tool; `allowedTools` has **no** `browser_*` glob — use `["*"]` or match by name (`"browser"`). For browser SSO behind interactive login (human-in-the-loop), see `references/browser-auth.md` |
| Skills | `references/skills.md` | Every `SKILL.md` **must** start with YAML frontmatter (`name` + `description`) or session start fails; git source has **no branch field** |
| Advanced config: truncation, invocation limits, lifecycle, network, inbound auth | `references/advanced-config.md` | Set explicit limits (maxIterations/maxTokens/timeout) and lifecycle (idle/max lifetime); choose network + inbound auth deliberately |

### Phase 3 — Create or update the harness

```bash
python scripts/create_harness.py --config harness.json --role-arn <EXECUTION_ROLE_ARN>
# or, to modify an existing harness:
python scripts/update_harness.py --harness-id <ID> --config harness.json
```

`update_harness` has subtle payload rules (the `optionalValue` wrapper applies only to *structure* fields, `tags` is a
separate `TagResource` call, `clientToken` must be ≥33 chars). The script handles these by introspecting the live shape.
If you ever hand-write an `update_harness` call, read `references/harness-config.md` §update-payload-rules first.
The harness execution role needs a trust policy and base permissions — see `assets/iam_execution_role.json`.

### Phase 4 — Wire Memory (three coordinated steps, not two)

Attaching memory is **not** just "create it and point the harness at it." The harness's execution role also needs data-
plane permissions on the new Memory ARN, or every invocation fails at session start with `AccessDeniedException`.

```bash
python scripts/wire_memory.py --harness-id <ID> --role-arn <EXECUTION_ROLE_ARN> \
    --memory-name <name> --actor-id ci-pipeline
```

This does all three steps: `CreateMemory` (with the strategy set), `UpdateHarness(memory=…)`, and an idempotent
`iam:PutRolePolicy` grant scoped to the Memory ARN and namespaces. Read `references/memory.md` before customizing
strategies — episodic requires `reflectionConfiguration`, the field is `strategyId` (not `memoryStrategyId`), and
namespace `{placeholder}` templates must be converted to `glob*` patterns in the IAM condition.

### Phase 5 — Observability: log delivery + tracing

```bash
python scripts/setup_observability.py --harness-id <ID> --region us-east-1
```

Sets up CloudWatch `APPLICATION_LOGS` delivery and X-Ray `TRACES` delivery. Note the asymmetry: `TRACES` go to the
**X-Ray** destination type (no `outputFormat` param), `APPLICATION_LOGS` go to a CloudWatch log group, and the
destination log group needs the `AWSLogDeliveryWrite20150319` resource policy extended for `delivery.logs.amazonaws.com`.
The runtime already emits rich OTel logs to a default group `/aws/bedrock-agentcore/runtimes/<name>-DEFAULT` — that's
where dashboard data actually lives. See `references/observability.md`.

### Phase 6 — Invoke and verify

```bash
python scripts/invoke_harness.py --harness-arn <HARNESS_ARN> --prompt "Hello, what can you do?"
```

Use `invoke_harness` on the **data-plane** client (`bedrock-agentcore`), not `invoke_agent_runtime`. Pass a
`runtimeSessionId` and process the streaming response. A successful streamed reply that uses the wired tools is your
proof the configuration is correct end to end. This is the single most important verification — a harness that
`CreateHarness` accepted can still fail at session start (missing SKILL.md frontmatter, missing Memory IAM grant,
tools stored-but-not-wired). Always invoke before declaring success.

### Phase 7 — Assess: Evaluations and Optimizations

Once the harness runs, make it measurably good:

- **Evaluations** (`references/evaluations.md`) — create a batch evaluation over agent traces using built-in or custom
  evaluators, or an evaluation configuration that scores live traffic. Results surface in AgentCore Observability.
- **Optimizations** (`references/optimizations.md`) — generate recommendation candidates (improved system prompts / tool
  descriptions), then validate them with an A/B test (control vs variant) and deploy the winning configuration bundle.

### Phase 8 — Govern: Policy guardrails + publish to the Registry (optional)

If the agent needs **guardrails** beyond IAM (constraining what actions/tools/data it may use), set up a Policy Engine
and policies — see `references/policy.md`. If the org uses the **Agent Registry** to discover and manage agents, MCP
servers, tools, and skills, register the finished harness and its skills there — see `references/registry.md`. For
agents that authenticate to external services (outbound) or transact, see `references/identity.md` and
`references/payments.md`.

---

## Feature checklist

Use this to make the build genuinely comprehensive. For each capability, decide *include / skip* with the user, then
wire it per the referenced phase. A best-practice harness rarely uses *all* of these, but you should consciously
consider each rather than silently omitting it.

- [ ] **Model + system prompt** — provider, inference-profile model id, Converse API, inference config (Phase 2)
- [ ] **Browser tool** — `agentcore_browser`, wired via config, `browser_*` in allowedTools (Phase 2)
- [ ] **Code Interpreter tool** — `agentcore_code_interpreter`, wired via config (Phase 2)
- [ ] **Gateway / remote MCP tools** — external APIs as MCP tools (Phase 2; consume via `references/tools.md`, **build** via `references/gateway.md`)
- [ ] **Inline functions** — human-in-the-loop / callbacks that return control to your orchestrator (Phase 2)
- [ ] **Skills** — domain knowledge via git/s3/path source, with valid frontmatter (Phase 2)
- [ ] **Memory** — strategy set + 3-step wiring + IAM grant (Phase 4)
- [ ] **Advanced config** — truncation, maxIterations, maxTokens, timeout, lifecycle, network, inbound auth (Phase 2)
- [ ] **Observability** — log delivery + X-Ray tracing + dashboards (Phase 5)
- [ ] **Evaluations** — online evaluation config over traces (Phase 7)
- [ ] **Optimizations** — recommendations + A/B test (Phase 7; **console-only** in preview, no SDK ops)
- [ ] **Identity** — outbound auth: Workload Identity, Token Vault, API-key/OAuth credential providers (`identity.md`)
- [ ] **Policy** — agent guardrails via Policy + Policy Engine (`policy.md`)
- [ ] **Payments** — payment connector/manager + sessions, if the agent transacts (`payments.md`)
- [ ] **Registry** — publish for org-wide discovery (Phase 8)
- [ ] **Tags** — applied via `TagResource` (not `UpdateHarness`); cost-center/team/env/agent-type (Phase 3)

---

## Critical gotchas (the short list — full detail in `references/gotchas.md`)

These cause the most failures. Keep them in mind even before opening the reference:

1. **Versions gate everything.** `boto3 >= 1.43.18` and AWS CLI v2 `>= 2.34.57`, or the harness ops don't exist.
2. **Harness ≠ Runtime API.** A harness has two ARNs; `UpdateAgentRuntime`/`InvokeAgentRuntime` are **rejected** for
   harness-managed resources. Use the `*Harness` family + `InvokeHarness`.
3. **`SKILL.md` needs YAML frontmatter** (`name` + `description`) or the session fails at start. Undocumented.
4. **Memory wiring is 3 steps** (create + attach + IAM grant). Skipping the grant → `AccessDeniedException`.
5. **Tools need `config` to actually wire**, and `allowedTools` has **no** `browser_*` glob — match by name (`"browser"`,
   `"code_interpreter"`) or use `["*"]`; the `browser_*` glob matches nothing and hides the tool.
6. **`update_harness` payload is type-driven**: `optionalValue` wraps structure fields only; `clientToken` ≥33 chars;
   `tags` via `TagResource`; memory uses `strategyId`.
7. **When docs and reality disagree, introspect the live schema** (`scripts/preflight.py` /
   `client.meta.service_model.operation_model("UpdateHarness").input_shape.members`) and trust that.

---

## Reference library

Load these as needed — don't read them all upfront.

| File | When to read |
|---|---|
| `references/decision-guide.md` | Phase 0/1 — Harness vs Runtime vs Bedrock Agents |
| `references/runtime.md` | Phase 1/2 — Runtime build path (code-first sibling of Harness): `BedrockAgentCoreApp`, `@app.entrypoint`, `/invocations` + `/ping` (incl. the `time_of_last_update` gotcha), AG-UI / A2A, `agentcore deploy` |
| `references/harness-config.md` | Phase 2/3 — full field reference + update-payload rules + best-practice defaults table |
| `references/model-and-prompt.md` | Phase 2 — provider/model ids, Converse API, inference config, prompt patterns |
| `references/tools.md` | Phase 2 — browser, code interpreter, gateway/MCP, inline functions, allowedTools |
| `references/gateway.md` | Phase 2 — **build** a Gateway (turn Lambda/OpenAPI/Smithy/MCP-server/API-GW/Runtime into MCP tools): `CreateGateway`/`Target`/`Rule`, inbound `authorizerType`, outbound credential providers, then wire into a harness |
| `references/browser-auth.md` | Phase 2/6 — human-in-the-loop browser SSO login, S3-signal handoff, inline-function pause/resume, long read_timeout, retrieving session files |
| `references/skills.md` | Phase 2 — skills union, git/s3/path sources, mandatory frontmatter |
| `references/memory.md` | Phase 4 — strategies, retrievalConfig, the 3-step wiring + IAM |
| `references/advanced-config.md` | Phase 2 — truncation, limits, lifecycle, network, inbound auth |
| `references/observability.md` | Phase 5 — log delivery (CWL vs XRAY), resource policy, dashboards |
| `references/evaluations.md` | Phase 7 — online evaluation config; batch/custom (console) |
| `references/optimizations.md` | Phase 7 — recommendations + A/B tests (console-only in preview) |
| `references/playground.md` | Phase 6 — Console Playground / Sandbox (interactive endpoint testing; console-only, no SDK ops — the repeatable path is InvokeHarness/InvokeAgentRuntime + Evaluations) |
| `references/identity.md` | Outbound auth — Workload Identity, Token Vault, credential providers |
| `references/policy.md` | Agent guardrails — Policy, Policy Engine, resource policy, policy generation |
| `references/payments.md` | Payment connector/manager + payment sessions (if the agent transacts) |
| `references/registry.md` | Phase 8 — publishing/discovering org resources |
| `references/gotchas.md` | Anytime something fails unexpectedly — the consolidated hard-learned facts + verified shapes |

## Assets

- `assets/harness.json.template` — full-featured, mirrors a real production harness; the recommended starting point
- `assets/skill.md.template` — a correctly-formatted SKILL.md with the required frontmatter
- `assets/iam_execution_role.json` — trust policy + base permissions for the harness execution role
- `assets/requirements.txt` — pinned minimum versions for the control-plane tooling

## Scripts

All scripts are idempotent where possible and accept `--dry-run` to print the API call without executing it. Read a
script's `--help` before first use.

- `scripts/preflight.py` — version/region/credential checks + live schema introspection
- `scripts/validate_config.py` — lints a `harness.json` against the best-practice rules *before* you call AWS
- `scripts/create_harness.py` — create a harness from config
- `scripts/update_harness.py` — update with correct payload rules
- `scripts/wire_memory.py` — the 3-step memory wiring
- `scripts/setup_observability.py` — log delivery + tracing
- `scripts/invoke_harness.py` — data-plane smoke test

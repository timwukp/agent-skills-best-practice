# Console Playground / Sandbox — interactive endpoint testing

The **Playground** (a.k.a. **Sandbox** / "Test Endpoint") is a **console-only** feature for sending
prompts to a deployed agent **interactively** and watching the response (and traces) without writing any
client code. Like Optimizations, it has **no control-plane SDK operations** — it is a UI over the same
data-plane invoke calls this skill already automates.

## What it is for

- **Quick smoke test** right after deploy: confirm the endpoint responds and the system prompt/tools behave.
- **Prompt iteration**: paste different prompts and eyeball the output before wiring a real client.
- **Trace inspection**: see the reasoning/tool-call trace for a single invocation (pairs with
  `references/observability.md` for the durable CloudWatch view).

## How to reach it

Console → **Amazon Bedrock AgentCore** → **Agents** (Runtime) or **Harness** → select your agent →
choose an **endpoint** → **Test Endpoint** → the Playground/Sandbox opens. Type a prompt and send.

## The programmatic equivalent (what to use for anything repeatable)

The Playground is **manual and ephemeral** — there is no API to "create a playground". For anything you
need to repeat (CI, regression, evals), use the data-plane invoke this skill already covers:

| Want | Use |
|---|---|
| One-off manual check | Console Playground / Sandbox |
| Scripted single invoke | `InvokeHarness` (`scripts/invoke_harness.py`) or `InvokeAgentRuntime` (see `references/runtime.md`) |
| Repeatable scored runs | Evaluations (`references/evaluations.md`) over the traces |

## Notes

- The Playground respects the endpoint's inbound auth (`authorizerType`) — you must be able to satisfy it
  from the console session.
- A Playground invocation is a **real** invocation: it spins a session, bills like any invoke, and emits
  the same logs/traces. Use `runtimeSessionId` grouping + Observability to find those traces afterwards.
- There is nothing to automate here. The skill deliberately treats Playground as **doc-only** — the
  repeatable path is `InvokeHarness` / `InvokeAgentRuntime` + Evaluations.

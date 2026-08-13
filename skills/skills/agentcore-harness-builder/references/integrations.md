# Integrations — Consuming a Harness from the Outside

How external systems consume a harness: reading the `InvokeHarness` response stream (including the
`toolResultMetadata` channel), embedding a harness in AWS Step Functions, and exporting a harness to
editable framework code.

## Reading the InvokeHarness stream

`InvokeHarness` (data plane) streams events. **The response's stream key is `stream`** (not
`response` — live-verified 2026-08-12). Event types observed live: `messageStart`,
`contentBlockDelta`, `contentBlockStop`, `messageStop`, `metadata`. The `contentBlockDelta.delta`
is a union (schema-verified, boto3 1.43.69):

```
text | toolUse | toolResult | reasoningContent | toolResultMetadata
```

(`text` and `reasoningContent` deltas observed live; `reasoningContent` arrives even without
extended-thinking config on Claude models.)

### The `toolResultMetadata` delta channel (added 2026-07)

**MCP** tool-result **metadata** streams on its own dedicated delta channel — built-in tools
(code interpreter, browser) don't emit it; expect it only from Gateway/MCP tool results that carry
metadata (not observed in this skill's live runs, which used built-ins). Large metadata is
automatically split into **ordered fragments** — concatenate the fragments in the order received,
then parse the combined string as JSON:

```python
frags = []
for event in resp["stream"]:                         # NOTE: "stream", not "response"
    delta = event.get("contentBlockDelta", {}).get("delta", {})
    if "toolResultMetadata" in delta:
        frags.append(delta["toolResultMetadata"]["metadata"])
    elif "text" in delta:
        print(delta["text"], end="")
if frags:
    tool_result_metadata = json.loads("".join(frags))   # concat IN ORDER, then parse
```

Don't parse fragments individually — a fragment is not guaranteed to be valid JSON on its own.
`scripts/invoke_harness.py` implements this accumulation.

## AWS Step Functions

A harness drops into a larger pipeline through the **AgentCore `InvokeHarness` optimized state** in
Step Functions — call a harness as a workflow step without Lambda glue, composing agents with
approvals, retries, and parallel branches. (Documented by AWS with harness GA; not live-verified by
this skill — consult the Step Functions optimized-integrations list for the state syntax.)

## Export to code

A harness can be **exported to editable Strands agent code** that runs on AgentCore Runtime — the
escape hatch when you outgrow declarative config. **VERIFIED LIVE 2026-08-13** with `@aws/agentcore`
v0.26.0 (stable npm tag — no preview needed):

```bash
npm i -g @aws/agentcore
# Export REQUIRES an agentcore project ("NoProjectError" otherwise) — scaffold one first:
agentcore create --name myproj --defaults          # scaffold only; no deploy, no AWS resources
cd myproj
agentcore export harness --arn <harness-arn> --build CodeZip --json
# flags: --name <in-project> | --arn <existing> | --target-agent-name | --build CodeZip|Container | --json
# there is NO --output flag — it writes into the project at app/<harnessName>Agent/
```

Verified output: a Strands Python project — `main.py`, `model/` (incl. `mantle_compat.py`),
`mcp_client/`, `memory/session.py`, `skills/fetcher.py`, `hooks/execution_limits.py`,
`pyproject.toml` (`strands-agents >= 1.15.0`) — plus **`EXPORT_NOTES.md`** listing semantic drops
(observed note: "allowedTools ... applied statically at code-generation time ... callers cannot
override the tool list per invocation (unlike the harness)"). **Strands is the only export framework
today** — Claude Agent SDK export is announced as "coming soon"; don't build on it yet. After export
you own the code: deploy it as a Runtime (`references/runtime.md`) and the declarative harness config
no longer applies.

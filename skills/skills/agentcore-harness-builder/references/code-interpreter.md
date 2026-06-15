# Code Interpreter — Sandboxed Code & File Execution (deep dive)

`references/tools.md` covers **attaching** the built-in Code Interpreter to a harness (the agent then
calls it as a tool). This file is the **direct SDK** deep dive: the session lifecycle, all nine tools,
file/command workflows, custom interpreters, and the verified gotchas. All shapes verified against
`boto3 1.43.29` and exercised live (7/7 e2e).

## Contents
- [Two ways to use it](#two-ways)
- [Session lifecycle (data plane)](#lifecycle)
- [The nine tools + their `arguments`](#tools)
- [File + command workflow (verified)](#workflow)
- [Custom Code Interpreter (control plane)](#custom)
- [Gotchas](#gotchas)

---

## Two ways

| Path | How |
|---|---|
| **Attached to a harness** | Add `{"type": "agentcore_code_interpreter", "config": {"agentCoreCodeInterpreter": {"codeInterpreterArn": "...aws:code-interpreter/aws.codeinterpreter.v1"}}}` and allowlist `code_interpreter*`. The agent calls it. See `references/tools.md`. |
| **Direct SDK** (this file) | `boto3.client("bedrock-agentcore")` — you drive `StartCodeInterpreterSession` / `InvokeCodeInterpreter` / `StopCodeInterpreterSession` yourself. Useful for orchestrators, tests, and Runtime agents. |

## Lifecycle

```python
import boto3
d = boto3.client("bedrock-agentcore", region_name="us-east-1")   # data plane (c is control elsewhere)
CI = "aws.codeinterpreter.v1"                      # built-in; or a custom codeInterpreterId

s = d.start_code_interpreter_session(codeInterpreterIdentifier=CI, name="my-session")
sid = s["sessionId"]
# ... invoke (below) ...
d.get_code_interpreter_session(codeInterpreterIdentifier=CI, sessionId=sid)   # status: READY
d.list_code_interpreter_sessions(codeInterpreterIdentifier=CI)
d.stop_code_interpreter_session(codeInterpreterIdentifier=CI, sessionId=sid)
```

The session has a **persistent filesystem and execution context** for its lifetime — files written by one
tool are visible to the others (verified below).

## Tools

`InvokeCodeInterpreter(name=<tool>, arguments=<dict>)`. **`name` enum (verified):** `executeCode`,
`executeCommand`, `readFiles`, `writeFiles`, `listFiles`, `removeFiles`, `startCommandExecution`,
`getTask`, `stopTask`. The response is an event **stream** (`resp["stream"]`).

| Tool | Key `arguments` (verified shapes) |
|---|---|
| `executeCode` | `code` (str), `language` ∈ `python`/`javascript`/`typescript`, `clearContext` (bool) |
| `executeCommand` | `command` (str) — synchronous shell |
| `writeFiles` | `content`: list of `{"path": str, "text": str}` (or `blob`) |
| `readFiles` | `paths`: list of str |
| `listFiles` | `directoryPath` (str) |
| `removeFiles` | `paths`: list of str |
| `startCommandExecution` | `command` (str), `runtime` ∈ `nodejs`/`deno`/`python` — **async**; returns a `taskId` |
| `getTask` | `taskId` (str) — poll an async command |
| `stopTask` | `taskId` (str) — cancel an async command |

## Workflow

A verified end-to-end session showing **cross-tool filesystem persistence** (all 7 steps passed live):

```python
def invoke(name, arguments):
    # NOTE: arguments is a DICT, not a JSON string (a common mistake). d = data-plane client.
    return list(d.invoke_code_interpreter(codeInterpreterIdentifier=CI, sessionId=sid,
                                          name=name, arguments=arguments)["stream"])

invoke("writeFiles", {"content": [{"path": "demo/note.txt", "text": "hello"}]})
invoke("listFiles",  {"directoryPath": "demo"})            # -> note.txt present
invoke("readFiles",  {"paths": ["demo/note.txt"]})         # -> "hello"
invoke("executeCommand", {"command": "cat demo/note.txt"}) # shell sees the same file -> "hello"
invoke("executeCode", {"code": "print(open('demo/note.txt').read())", "language": "python"})  # -> "hello"
```

For long-running work use the **async** trio: `startCommandExecution` (returns `taskId`) → poll `getTask`
→ `stopTask` to cancel. This avoids blocking on multi-minute builds/tests.

## Custom

`CreateCodeInterpreter` (control plane) makes a **custom** interpreter when the built-in
`aws.codeinterpreter.v1` isn't enough (private network, corporate CA trust):

```python
ctl = boto3.client("bedrock-agentcore-control", region_name="us-east-1")
ci = ctl.create_code_interpreter(
    name="my_ci",
    networkConfiguration={"networkMode": "SANDBOX"},   # PUBLIC | SANDBOX | VPC
    # VPC: {"networkMode": "VPC", "vpcConfig": {"subnets": [...], "securityGroups": [...]}}
    # executionRoleArn=...,                              # for SANDBOX/VPC outbound access
    # certificates=[{"location": {"secretsManager": {"secretArn": "<pem-secret-arn>"}}}],
)
custom_ci_id = ci["codeInterpreterId"]                  # pass as codeInterpreterIdentifier above
```

`networkMode`: **PUBLIC** (internet), **SANDBOX** (isolated, no egress), **VPC** (your subnets). Custom CA
certificates (PEM in Secrets Manager, ≤ 20/session) let the sandbox trust internal services.

## Gotchas

- **`arguments` is a dict, not a JSON string.** Passing a JSON string raises `ParamValidationError`
  (verified). This is the single most common Code Interpreter mistake.
- **The response is a stream** — iterate `resp["stream"]`; the result/stdout is in the events
  (`structuredContent.stdout` / `content[].text`), and `isError` flags failures.
- **Filesystem + context persist within a session**, across different tools, until you `stop` it (or it
  idles out). Set `clearContext: true` on `executeCode` to reset Python state without a new session.
- **Built-in vs custom:** the built-in `aws.codeinterpreter.v1` is `PUBLIC`; use a custom interpreter for
  `SANDBOX`/`VPC` isolation or custom CA trust.

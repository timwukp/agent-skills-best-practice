# Tools — Browser, Code Interpreter, Gateway/MCP, Inline Functions

A harness exposes tools to the agent through two coupled fields: `tools` (the declarations + wiring config) and
`allowedTools` (the glob allowlist the agent may actually call). **Both must be right or the agent silently can't use
the tool.**

## Contents
- [The two coupled fields](#two-fields)
- [Built-in: Browser](#browser)
- [Built-in: Code Interpreter](#code-interpreter)
- [Gateway / remote MCP tools](#gateway-mcp)
- [Inline functions](#inline-functions)
- [allowedTools globs](#allowedtools)

---

## Two fields

```json
"tools": [ { "type": "...", "name": "...", "config": { ... } } ],
"allowedTools": [ "browser_*", "code_interpreter*", "skills" ]
```

- `tools[].type` — one of `agentcore_browser`, `agentcore_code_interpreter`, `agentcore_gateway`, `remote_mcp`,
  `inline_function`.
- `tools[].name` — the configuration name (e.g. `browser`).
- **`tools[].config` is documented optional but practically required.** Without it, the tool is *stored but not wired*
  — the agent never sees it. The `config` union has one key per type: `agentCoreBrowser`, `agentCoreCodeInterpreter`,
  `agentCoreGateway`, `remoteMcp`, `inlineFunction`.

The managed harness loader image already contains the runtime wiring for the built-in tools — you do **not** need a
custom container image.

---

## Browser

Cloud-managed Chrome/Playwright. Wire it with the AWS-owned browser ARN:

```json
{
  "type": "agentcore_browser",
  "name": "browser",
  "config": { "agentCoreBrowser": { "browserArn": "arn:aws:bedrock-agentcore:us-east-1:aws:browser/aws.browser.v1" } }
}
```

When wired, the agent gets a single **`browser`** tool (named by the `name` field) that it drives with actions like
navigate, get_text, click, type, evaluate (JS), and screenshot. **Allowlist it by name (`"browser"`) or `"*"` — NOT
`"browser_*"`** (that glob matches nothing and hides the tool). Verified live: the agent successfully navigated a page,
read its `<h1>`, and ran a JS `evaluate` through this single tool. (Older docs describing six separate `browser_*`
primitives are outdated for the managed harness.) An empty inner config `{}` uses the default browser ARN, but an
explicit ARN is more robust.

---

## Code Interpreter

Sandboxed Python/JS/TS execution:

```json
{
  "type": "agentcore_code_interpreter",
  "name": "code_interpreter",
  "config": { "agentCoreCodeInterpreter": { "codeInterpreterArn": "arn:aws:bedrock-agentcore:us-east-1:aws:code-interpreter/aws.codeinterpreter.v1" } }
}
```

Allowlist with `"code_interpreter*"`. Use it for calculations, data analysis, report/JSON generation, and verifying
results by execution rather than guessing.

---

## Gateway / MCP

To expose external APIs as agent tools:

- **AgentCore Gateway** (`agentcore_gateway`) transforms APIs into MCP tools managed by AWS. Verified config shape:
  ```json
  {"type": "agentcore_gateway", "name": "my_api", "config": {"agentCoreGateway": {
     "gatewayArn": "<GATEWAY_ARN>",
     "outboundAuth": {"oauth": {"providerArn": "<oauth-credential-provider-arn>", "scopes": ["read"]}}
  }}}
  ```
  `gatewayArn` is required; `outboundAuth` is a union of `awsIam` / `none` / `oauth` (the `oauth` form needs
  `providerArn` + `scopes`, backed by an Identity credential provider — see `identity.md`).
- **Remote MCP** (`remote_mcp`) connects a streamable-HTTP MCP server directly. Verified shape:
  ```json
  {"type": "remote_mcp", "name": "my_mcp", "config": {"remoteMcp": {
     "url": "https://my-mcp-server/mcp", "headers": {"Authorization": "Bearer ..."}
  }}}
  ```
  `url` is required; `headers` is an optional string→string map for auth.

Allowlist the resulting tool names (use a glob if the server exposes many). Building a new MCP server itself is the
domain of the separate `mcp-builder` skill — use that to author the server, then wire it here.

---

## Inline functions

Inline functions return control to **your** orchestrator mid-run (human-in-the-loop, callbacks, hand-offs). The agent
"calls" the function; the harness pauses and surfaces the call to your invoking code, which supplies the result. Define
the schema inline:

```json
{
  "type": "inline_function",
  "name": "request_human_review",
  "config": { "inlineFunction": {
    "description": "Escalate to a human reviewer when results need visual judgment you can't make confidently.",
    "inputSchema": {
      "type": "object",
      "properties": {
        "test_case_id": { "type": "string" },
        "reason": { "type": "string" },
        "screenshot_path": { "type": "string" }
      },
      "required": ["test_case_id", "reason"]
    }
  } }
}
```

Common patterns: `notify_complete` (signal done + summary stats), `request_human_review` (escalation), `handoff_to_agent`
(A2A-style chaining to a downstream agent). Allowlist each by its `name`.

---

## allowedTools

`allowedTools` scopes which tools the LLM may select during `InvokeHarness`. **If omitted, all tools are allowed.**
The supported patterns (verified against the official docs AND live against boto3 1.43.29) are builtin/MCP oriented —
**there is NO `browser_*` / `code_interpreter*` glob.** Using those filters the browser/code-interpreter tools OUT,
and the agent then reports `Unknown tool: browser_navigate`.

| Pattern | Matches |
|---|---|
| `*` | all tools |
| plain name (`shell`, `browser`, `code_interpreter`, `<inline_fn_name>`) | that tool by name |
| builtin glob (`file_*`) | builtin tools (`file_operations`, `file_read`, …) |
| `@builtin` / `@builtin/shell` | all / specific builtins |
| `@server` / `@server/tool` / `@server/glob` / `@*/tool` | MCP server tools |

```python
# WRONG — browser_* is not a valid pattern; filters the tool out -> "Unknown tool"
allowedTools = ["browser_*", "code_interpreter*", "skills"]

# RIGHT — allow everything (simplest, recommended default)
allowedTools = ["*"]
# or omit allowedTools entirely (same effect)

# RIGHT — explicit by NAME (the tool's name field), not a glob
allowedTools = ["browser", "code_interpreter", "skills", "shell", "file_operations", "<your_inline_fn>"]
```

**Verified live:** with `["browser_*","code_interpreter*"]` the agent saw only `skills`; with `["*"]` it saw all of
`shell, file_operations, browser, code_interpreter, <inline functions>, skills`. When in doubt, invoke the harness and
ask the agent to list its tool names — that is the definitive check (`scripts/invoke_harness.py`).

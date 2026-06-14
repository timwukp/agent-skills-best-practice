# Runtime — Code-First Build Path

A **Runtime** is the lower-level, code-first sibling of a Harness. You write the agent (HTTP server,
loop, tools) yourself, package it as a container or source bundle, and AgentCore hosts it in a
per-session microVM. Pick this when you need control beyond what the declarative Harness offers
(see `decision-guide.md`). All shapes below are verified against `boto3 1.43.29` and the
agent-side `bedrock-agentcore` SDK on PyPI.

## Contents
- [When to choose Runtime over Harness](#when-runtime)
- [Two planes (same as Harness)](#two-planes)
- [The agent-side SDK — `BedrockAgentCoreApp`](#sdk)
- [HTTP contract — `/invocations` and `/ping` (with the `time_of_last_update` gotcha)](#http)
- [AG-UI and A2A protocols](#protocols)
- [Deploying — three paths](#deploy)
- [Wiring Memory / Identity / Observability into a Runtime](#wiring)
- [Session storage / persistent filesystem](#session-storage)
- [Custom container vs source-deploy tradeoffs](#container-vs-source)

---

## When Runtime

Pick Runtime over Harness when at least one of these is true:

- You need a custom orchestration loop (multi-agent coordination, custom retry/fallback) that doesn't fit a
  declarative `harness.json`.
- You're embedding the agent inside an existing FastAPI/Starlette app that already owns `/invocations`.
- You need protocols beyond Harness's contract (raw MCP server, AG-UI, A2A, custom streaming framing).
- You want full control of the framework integration (Strands/LangGraph/CrewAI/Autogen) and dependencies.
- Sub-second latency / very high-volume short stateless invocations where microVM cold-start overhead matters
  less than runtime control.

Otherwise prefer Harness — it's faster to build, faster to iterate (config changes, no redeploy), and gives
you Memory/Tools/Skills wiring for free.

## Two planes

Same shape as Harness:

| Plane | Client | Operations |
|---|---|---|
| Control plane | `boto3.client("bedrock-agentcore-control")` | `CreateAgentRuntime`, `UpdateAgentRuntime`, `CreateAgentRuntimeEndpoint`, `Get/List/DeleteAgentRuntime[Endpoint]`, `ListAgentRuntimeVersions` |
| Data plane | `boto3.client("bedrock-agentcore")` | `InvokeAgentRuntime` |

Important: `UpdateAgentRuntime` is **rejected for harness-managed runtimes** ("managed by harness '…' and
cannot be updated directly. Use `UpdateHarness`."). Plain runtimes you created yourself update via
`UpdateAgentRuntime`.

## SDK

The agent-side SDK is `pip install bedrock-agentcore`. The minimal app is:

```python
from bedrock_agentcore.runtime import BedrockAgentCoreApp

app = BedrockAgentCoreApp()
log = app.logger

@app.entrypoint
async def handler(request):
    prompt = request.get("prompt", "")
    # your agent logic — Strands / LangGraph / CrewAI / Autogen / custom
    return {"reply": f"echo: {prompt}"}

if __name__ == "__main__":
    app.run()        # uvicorn on 0.0.0.0:8080 inside the container
```

`BedrockAgentCoreApp` is a Starlette app with these methods (verified):

- `@app.entrypoint` — decorator to mark the function bound to `POST /invocations`. The function
  receives the parsed JSON body. May be sync or `async`. May return a value (JSON) **or yield** to stream
  (SSE on `POST /invocations`, or WebSocket on `/ws` if AG-UI is used).
- `@app.ping` — decorator to override the default `/ping` body (rarely needed).
- `app.run(port=8080, host=None, **uvicorn_kwargs)` — start uvicorn. Auto-binds to `0.0.0.0` inside Docker.
- `app.async_task(...)` / `app.add_async_task(...)` / `app.complete_async_task(...)` /
  `app.get_async_task_info()` — book-keeping for long-running background work; the platform-known
  `/ping` body reflects active count.
- `app.force_ping_status(...)` / `app.clear_forced_ping_status()` — manual override of the
  `Healthy` / `HealthyBusy` status (useful for graceful drain).

Other useful exports from `bedrock_agentcore.runtime`:

- `RequestContext` — typed access to per-request metadata.
- `BedrockAgentCoreContext` — a `ContextVar`-backed store of request-scoped sensitive values
  (workload access token, OAuth callback URL). Read it from inside `@app.entrypoint`.
  Caveat: `ContextVar` is per-`asyncio.Task`. If you spawn `threading.Thread` background workers,
  re-set the token on entry — see upstream issue #484.
- `serve_ag_ui(agent, ...)` / `serve_a2a(executor, ...)` — one-line servers for the AG-UI and A2A
  protocols (see [Protocols](#protocols)).
- `AGUIApp` — the decorator-form of an AG-UI server when you don't have a framework agent.
- `PingStatus` — `Healthy` / `HealthyBusy` enum.

## HTTP

The runtime contract is **two routes** the platform calls:

| Route | Purpose |
|---|---|
| `POST /invocations` | Your agent's entry point. Body = JSON the caller sent in `payload`. Response = JSON, or SSE / streamed JSON if you yield. |
| `GET /ping` | Health/liveness. Default body is **`{"status": "Healthy", "time_of_last_update": <epoch>}`** or `HealthyBusy` while async tasks are active. |

### The `time_of_last_update` field is **required** (undocumented but enforced)

The public docs show `/ping` returning `{"status": "HealthyBusy"}`. **The platform's idle reaper actually
requires a `time_of_last_update` field** (epoch seconds) to know your container is still alive. Without it
the runtime is reaped at `idleRuntimeSessionTimeout` even while `/ping` returns `HealthyBusy`, silently
terminating microVMs mid-execution. Upstream issue: aws/bedrock-agentcore-sdk-python#471.

If you use `BedrockAgentCoreApp`, you get this for free — its built-in `/ping` handler emits both
fields. If you write your own ASGI app and want to bypass `BedrockAgentCoreApp`, you **must** emit
both fields yourself:

```python
import time
from starlette.responses import JSONResponse
from starlette.routing import Route

async def ping(_req):
    return JSONResponse({"status": "Healthy", "time_of_last_update": int(time.time())})
```

### `BedrockAgentCoreContext` only auto-populates inside `BedrockAgentCoreApp`

If you serve a **plain FastAPI** app, the `WorkloadAccessToken` header is **not** automatically threaded
into the ContextVar; `@requires_api_key` / `@requires_access_token` decorators will silently see `None`.
Either (a) use `BedrockAgentCoreApp` (which installs the middleware), (b) call the
ContextVar setter yourself in middleware reading the `WorkloadAccessToken` request header, or (c) use
`BedrockAgentCoreContext.from_request(...)` if/when added. Upstream issue: #484.

## Protocols

| Protocol | When | One-liner |
|---|---|---|
| **HTTP** (default) | Plain JSON in/out, optional SSE streaming | `BedrockAgentCoreApp` + `@app.entrypoint` (above) |
| **MCP** | Expose your agent as an MCP server | Set `protocolConfiguration.serverProtocol = "MCP"` on the runtime; serve MCP at `POST /invocations` |
| **AG-UI** | Interactive UI events (start/finish/text-stream) | `serve_ag_ui(agent)` (one line) **or** `AGUIApp` + `@app.entrypoint` for full control |
| **A2A** | Agent-to-Agent protocol via the [a2a-sdk](https://google.github.io/A2A/) | `serve_a2a(StrandsA2AExecutor(agent))` |

`protocolConfiguration.serverProtocol` enum (verified): `HTTP`, `MCP`, `A2A`, `AGUI`.

```python
# AG-UI (default port 8080)
from bedrock_agentcore.runtime import serve_ag_ui
serve_ag_ui(my_strands_agent)

# A2A (default port 9000)
from bedrock_agentcore.runtime import serve_a2a
from strands.a2a import StrandsA2AExecutor
serve_a2a(StrandsA2AExecutor(my_strands_agent))
```

Install protocol extras: `pip install "bedrock-agentcore[ag-ui]"` or `"bedrock-agentcore[a2a]"`.

## Deploy

`CreateAgentRuntime` requires (verified): `agentRuntimeName`, `agentRuntimeArtifact`, `roleArn`,
`networkConfiguration`. Optional: `protocolConfiguration`, `lifecycleConfiguration`,
`authorizerConfiguration`, `requestHeaderConfiguration`, `environmentVariables`,
`filesystemConfigurations`, `tags`, `description`, `clientToken`.

`agentRuntimeArtifact` is a **union** with two forms:

```python
# A) container image you already pushed to ECR
{"containerConfiguration": {"containerUri": "<ECR_URI>:tag"}}

# B) source bundle in S3 — a SELF-CONTAINED zip the platform unpacks to /var/task and runs.
#    The platform does NOT pip-install for you: dependencies must already be vendored INTO the
#    zip as Linux arm64 wheels (see "Container vs source" below). `agentcore deploy` builds this
#    zip for you; with raw boto3 you build it yourself.
{"codeConfiguration": {
    "code":      {"s3": {"bucket": "...", "prefix": "...", "versionId": "..."}},
    "runtime":   "PYTHON_3_13",            # enum: PYTHON_3_10/11/12/13/14, NODE_22
    "entryPoint": ["main.py"],             # or ["opentelemetry-instrument", "main.py"] for OTEL
}}
```

`networkConfiguration` (required):
```python
{"networkMode": "PUBLIC"}                         # or "VPC"
# VPC mode requires:
{"networkMode": "VPC", "networkModeConfig": {
    "subnets": ["subnet-..."], "securityGroups": ["sg-..."], "requireServiceS3Endpoint": False
}}
```

`lifecycleConfiguration` (seconds):
```python
{"idleRuntimeSessionTimeout": 900, "maxLifetime": 28800}
```

### Deploy paths

1. **`@aws/agentcore` CLI (recommended)** — generates the project, packages the artifact, calls
   `CreateAgentRuntime` for you:
   ```bash
   npm i -g @aws/agentcore
   agentcore create --name MyAgent --defaults
   cd MyAgent
   agentcore deploy
   agentcore invoke "Hello"
   ```
2. **AWS CDK** — the CLI generates CDK under the hood; for full IaC control, customize the generated
   project or use `aws_bedrockagentcore` L1 constructs directly.
3. **Raw boto3** — for full automation. Sketch:
   ```python
   import boto3, secrets
   c = boto3.client("bedrock-agentcore-control", region_name="us-east-1")
   resp = c.create_agent_runtime(
       agentRuntimeName="MyAgent",
       roleArn="arn:aws:iam::<acct>:role/MyAgentExec",
       agentRuntimeArtifact={"containerConfiguration": {"containerUri": "<ECR_URI>:1"}},
       networkConfiguration={"networkMode": "PUBLIC"},
       protocolConfiguration={"serverProtocol": "HTTP"},
       lifecycleConfiguration={"idleRuntimeSessionTimeout": 900, "maxLifetime": 28800},
       environmentVariables={"LOG_LEVEL": "INFO"},
       clientToken=secrets.token_hex(20),
   )
   runtime_arn = resp["agentRuntimeArn"]
   ```
4. Invoke (data plane):
   ```python
   d = boto3.client("bedrock-agentcore", region_name="us-east-1")
   r = d.invoke_agent_runtime(
       agentRuntimeArn=runtime_arn,
       runtimeSessionId="my-session-" + secrets.token_hex(16),  # >= 33 chars
       qualifier="DEFAULT",                                     # endpoint name
       contentType="application/json",
       accept="application/json",                                # or "text/event-stream" to stream
       payload=b'{"prompt": "Hello"}',
   )
   ```

`runtimeSessionId` is **≥ 33 chars** (same constraint as `InvokeHarness`).

## Wiring

Memory, Identity, Observability work the same way as for Harness — Memory data-plane perms attach to
`roleArn` (the runtime's execution role), `setup_observability.py` configures log delivery against the
runtime ARN, Identity credential providers are referenced by ARN inside the agent code. The skill's
`wire_memory.py` works against any execution role; pass it the runtime's `roleArn`.

## Session storage

Runtime supports persisting filesystem state across session stop/resume cycles (managed session storage at
`/mnt/...`) via `filesystemConfigurations`. Useful for coding agents with project files. The execution role
needs S3 access if you point session storage at a custom bucket.

## Container vs source

| Choice | Use when |
|---|---|
| **Container** (`containerConfiguration.containerUri`) | Custom system deps, native libraries, multi-process tooling, your own existing image |
| **Source** (`codeConfiguration` from S3 + `runtime` enum) | Pure-Python/Node agent, you want zero Docker — **but you must vendor dependencies into the zip yourself** |

### Source-deploy installs NO dependencies for you (verified by e2e)

The platform unpacks your zip to `/var/task` (first on `sys.path`) and runs `python <entryPoint>`
with **only the standard library** plus whatever you packaged. A bare `requirements.txt` in the zip
is **ignored** — there is no server-side `pip install`. If your agent imports anything third-party
(including `bedrock_agentcore` itself), you must vendor it as **Linux arm64** wheels (Runtime is
arm64-only):

```bash
uv pip install --python-platform aarch64-manylinux2014 --python-version 3.13 \
    --target=deployment_package --only-binary=:all: -r pyproject.toml
(cd deployment_package && zip -r ../deployment_package.zip .)   # deps at zip root
zip deployment_package.zip main.py                              # add entrypoint at zip root
```

The simplest path is **`agentcore deploy`**, which performs exactly these steps (arm64 wheel
download → zip → S3 upload → `CreateAgentRuntime`) for you — no Docker, no ECS/EKS. The first
deploy installs deps; subsequent updates re-use the zipped deps.

> **e2e finding:** a `codeConfiguration` zip containing only `main.py` + a plain `requirements.txt`
> fails at invoke with `Runtime initialization time exceeded. Please make sure that initialization
> completes in 120s`. The CloudWatch *runtime* log reveals the real cause is `ModuleNotFoundError`
> (the deps were never installed), **not** slowness. So when you hit the 120s init error on
> source-deploy, first confirm your deps are vendored as arm64 wheels (or just use `agentcore deploy`).
> For a genuinely slow *container*, trim imports, lazy-load models/credentials, or pre-warm heavy
> dependencies at build time.

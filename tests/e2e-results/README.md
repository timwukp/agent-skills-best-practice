# End-to-end test evidence — `agentcore-harness-builder`

This directory holds **live AWS** end-to-end test evidence for the `agentcore-harness-builder`
skill. The skill documents AgentCore APIs (Harness, Runtime, Memory, Identity, Registry, Code
Interpreter, …); these tests exercise a representative subset against **real** `bedrock-agentcore`
and `bedrock-agentcore-control` endpoints to verify the documented shapes, enums, and behaviors are
correct — not just transcribed from docs.

## How the tests were run

- **boto3** `1.43.29`, **region** `us-east-1`, agent-side `bedrock-agentcore` SDK (latest on PyPI).
- Executed on a Linux EC2 host, dispatched **detached via SSM RunCommand** so the run survives
  controlling-terminal disconnects. Results/logs/evidence are synced to S3 and committed here.
- Each test case captures stdout/stderr/duration and writes a structured JSON result plus raw
  evidence files (actual API responses).
- All account IDs / ARNs are sanitized to `<ACCOUNT_ID>` placeholders. Ephemeral test-resource IDs
  (already-deleted runtimes/registries/providers) are kept as run evidence.

## Latest run — `20260614T095338Z`

| Track | Cases | Pass | Fail | Error |
|---|---|---|---|---|
| `e2e-0-validate-codeblocks` — every boto3 call in `references/*.md` resolves + kwargs valid | 1 | 1 | 0 | 0 |
| `e2e-a-runtime` — create runtime (codeConfiguration) → READY → endpoint → invoke → cleanup | 4 | 3 | 0 | 1 |
| `e2e-d-identity-registry` — API-key credential provider + Registry CRUD | 5 | 5 | 0 | 0 |
| `e2e-e-codeinterp` — Code Interpreter start → invoke (`6*7=42`) → get → stop | 4 | 4 | 0 | 0 |
| **TOTAL** | **14** | **13** | **0** | **1** |

### 5 real bugs surfaced and fixed by these tests

1. `agentRuntimeName` regex rejects hyphens — pattern is `[a-zA-Z][a-zA-Z0-9_]{0,47}` (use `_`).
2. `CreateApiKeyCredentialProvider` needs `secretsmanager:CreateSecret` on the caller (it writes the
   key to Secrets Manager under the `bedrock-agentcore-identity!*` prefix).
3. `CreateRegistry` returns only `registryArn` — there is **no** `registryId` field; derive the id
   from the ARN's last path segment.
4. `invoke_code_interpreter`'s `arguments` is a **dict**, not a JSON string.
5. `codeConfiguration` source-deploy does **not** install dependencies (see the A.2 finding below).

## The 1 non-pass: `e2e-a-runtime / A.2` (invoke a codeConfiguration runtime)

A.2 is recorded as **ERROR** — and that is a genuine, valuable finding, not a skill defect.

**What happened:** the runtime was created and reached `READY` (A.1 ✅), the `DEFAULT` endpoint existed
(A.3 ✅), and cleanup worked (A.99 ✅). But invoking it returned
`Runtime initialization time exceeded. Please make sure that initialization completes in 120s`.

**Root cause (from the CloudWatch *runtime* log, not the API error):** the container started and ran
`python /var/task/main.py`, which immediately raised `ModuleNotFoundError` — the agent's dependencies
were never installed. `codeConfiguration` source-deploy unpacks the zip to `/var/task` and runs it with
**stdlib only**; it does **not** `pip install` a `requirements.txt`. Dependencies must be vendored into
the zip as Linux **arm64** wheels, or you use `agentcore deploy` (which builds that zip for you — no
Docker/ECS/EKS). This is now documented in `references/runtime.md`.

### Honest, layered attribution of this finding

| Layer | Issue | Whose | Bug? |
|---|---|---|---|
| Test used the deploy path wrong (shipped a bare `requirements.txt`, expecting auto-install) | ours (test) | yes — fixed |
| `references/runtime.md` implied "the platform builds + runs it" | ours (docs) | yes — fixed |
| Source-deploy requires you to vendor arm64 wheels yourself | AgentCore **by design** (documented) | no |
| `InvokeAgentRuntime` reports a container startup crash (`ModuleNotFoundError`) as a generic `Runtime initialization time exceeded (120s)` | AgentCore | **yes — a real UX/observability gap**, worth an upstream issue |

The genuinely *AgentCore-side* item is the last row: a container that crashes on import should surface
its actual stderr/exit reason, not a misleading "init too slow" timeout. The native, working invoke
paths are the managed **Harness** (validated separately end-to-end) and `agentcore deploy`.

## Files per run

```
<TS>/
├── results/   # one structured JSON per track + summary.md
├── logs/      # per-track stdout/stderr + _orchestrator.log
├── evidence/  # raw API responses captured per case (sanitized)
└── scripts/   # the exact test scripts used (sanitized, reproducible)
```

## Run `trackB-20260614T152541Z` — Gateway (Track B), 6 / 6 pass

Live Gateway build-side lifecycle on `bedrock-agentcore-control`:

| Case | Description | Status |
|---|---|---|
| B.1 | ensure gateway execution role | PASS |
| B.2 | `create_gateway` (MCP, `AWS_IAM`, `SEMANTIC`) → READY | PASS |
| B.3 | api-key credential provider + `create_gateway_target` (OpenAPI inline, `API_KEY`) → READY | PASS |
| B.4 | `create_gateway_rule` `routeToTarget` — documents it requires an HTTP-protocol target | PASS |
| B.5 | `get_gateway` + `list_gateway_targets` verify | PASS |
| B.99 | cleanup (rule, target, gateway, provider) | PASS |

**Findings folded into `references/gateway.md`:**

- `openApiSchema` targets using IAM auth require an `iamCredentialProvider`; use an **API_KEY** (or OAuth)
  credential provider referencing an Identity provider ARN for non-AWS backends.
- `routeToTarget` rules only support **HTTP-protocol** targets (`http.agentcoreRuntime`); MCP-protocol
  targets (Lambda/OpenAPI/Smithy/MCP-server/API-Gateway) are served directly and reject `routeToTarget`.
- The test derives the account id at runtime via STS, so `scripts/e2e_b_gateway.py` contains no account id.

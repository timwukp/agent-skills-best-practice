# Live Test Campaign — AgentCore 2026-05..08 Feature Wave

- **Date:** 2026-08-12 | **Region:** us-east-1 | **Account:** `<ACCOUNT_ID>` (redacted)
- **Execution host:** EC2 `claude-code-test-linux` (Amazon Linux 2023, via SSM), dedicated temporary role `skilltest-ec2-role`
- **Tooling:** aws-cli 2.36.21 · boto3/botocore 1.43.69 (python3.12 venv) · `@aws/agentcore` 0.26.0 (node v20)
- **Guardrails:** no EC2 instances launched; web-search calls ≤2; harness invokes ≤10; all resources named `skilltest*`, deleted per-case; final sweep T2.99
- Result legend: **PASS** = call made, expected outcome · **FAIL** = call made, wrong outcome · **BLOCKED** = API/CLI lacks the operation or permission (drift)

## Summary

| ID | Feature | Result |
|---|---|---|
| T1.1 | boto3 introspection (all new op families + shapes) | PASS |
| T1.2 | Upgraded AWS CLI op coverage | PASS |
| T1.3 | `@aws/agentcore` CLI capability inventory | PASS |
| T2.1 | Identity BYO secret (EXTERNAL) | **PASS** |
| T2.2 | Temporal policy create/validate | **PARTIAL** (enforcementMode PASS; Dogwood syntax rejected — grammar unresolved) |
| T2.3 | Web-search connector target | **PASS** (READY + live MCP tools/list) |
| T2.4 | Gateway rate limit | **PASS** (dimensionKeys grammar discovered) |
| T2.5 | Harness + filesystemConfigurations + defaults | **PASS** |
| T2.6 | toolResultMetadata stream | **PARTIAL** (stream event model verified; channel not emitted — needs MCP tool) |
| T2.7 | CapacityProvider object (guarded) | **PARTIAL** (shape verified; launchTemplateSource required — object not created) |
| T2.8 | Unified observability log group | **PASS** |
| T2.9 | Memory-by-default (via T2.5) | **PASS** (confirmed: managed memory auto-attached) |
| T2.10 | `agentcore export harness` | **PASS** (full export produced) |
| T2.11 | Harness delete semantics | **PASS** (async DELETING; managed memory cascade-deletes) |
| T2.99 | Leftover sweep + IAM teardown | **PASS** (zero leftovers; all temp IAM removed) |

---

## T1.1 — boto3 schema introspection (zero AWS calls)
- Date: 2026-08-12 | Tier: T1 | Features: all
- Command: `t1_introspect.py` (service-model introspection, boto3 1.43.69, on EC2)
- Result: **PASS**
- Evidence:
  - Harness ops (11): Create/Update/Get/List/Delete Harness + Endpoint family + ListHarnessVersions
  - CapacityProvider ops (6) incl. `ListAgentRuntimeVersionsByCapacityProvider`
  - GatewayRateLimit ops (6) incl. `BatchPutGatewayRateLimits`; `CreateGatewayRateLimit` members: `dimensionKeys`, `entries`, `gatewayIdentifier`, `rateLimitId`
  - `CreateGatewayTarget.targetConfiguration` union: `http | inference | mcp`; `mcp` union: `apiGateway, connector, lambda, mcpServer, openApiSchema, smithyModel`
  - `CreatePolicy`: `definition` union `cedar | policy | policyGeneration`; `enforcementMode` enum `ACTIVE | LOG_ONLY`
  - `CreateApiKeyCredentialProvider`: `apiKeySecretSource` enum `MANAGED | EXTERNAL` + `apiKeySecretConfig`
  - `CreateHarness` filesystem union: `capacityProviderVolume | efsAccessPoint | s3FilesAccessPoint | sessionStorage`
- Skill edit: shapes stamped "verified against boto3 1.43.69 schema" across gateway.md / policy.md / identity.md / harness-config.md / advanced-config.md / runtime.md

## T1.2 — AWS CLI v2 op coverage after upgrade
- Date: 2026-08-12 | Tier: T1 | Feature: F13
- Command: `aws bedrock-agentcore-control help | grep -E "(harness|capacity-provider|gateway-rate-limit|policy)"` + `create-api-key-credential-provider help`
- Result: **PASS** — CLI 2.36.21 carries create-harness, create-capacity-provider, create-gateway-rate-limit, create-policy/policy-engine families and `--api-key-secret-source`. (Baseline: CLI 2.31.23 and even 2.33.15 = zero harness matches.)
- Skill edit: gotchas.md §Versions CLI floor updated (2.36.x recommended)

## T1.3 — `@aws/agentcore` CLI inventory
- Date: 2026-08-12 | Tier: T1 | Features: F10, F13
- Command: `agentcore --version && agentcore --help && agentcore export --help`
- Result: **PASS**
- Evidence: v0.26.0 (stable npm tag). Top-level commands: add, dev, deploy, exec, create, evals, feedback, fetch, import, invoke, logs, package, pause, view, batch-evaluations, remove, resume, run, status, stop, **export**. `agentcore export harness` exists on STABLE: "Export a harness to a Python Strands runtime agent (in-project via --name, or by --arn)". No standalone `gateway` subcommand (the starter-toolkit's `gateway create-mcp-gateway` flow is gone — gateway objects are managed via project config / `add`, or boto3).
- Skill edit: integrations.md §Export (no @preview needed); gateway.md §CLI notes coverage varies

---

## T2.1 — Identity BYO secret (`apiKeySecretSource=EXTERNAL`)
- Date: 2026-08-12 | Tier: T2 | Feature: F11
- Command: `create_secret(Name="skilltest/agentcore-byo", SecretString='{"api_key":"sk-test-123"}')` → `create_api_key_credential_provider(name="skilltest_ext_key", apiKeySecretSource="EXTERNAL", apiKeySecretConfig={"secretId": <secret-arn>, "jsonKey": "api_key"})` → get → delete both
- Result: **PASS**
- Evidence (Get response): `apiKeySecretSource: "EXTERNAL"`, `apiKeySecretArn.secretArn: <my exact secret ARN — no vault copy>`, `apiKeySecretJsonKey: "api_key"`, providerArn `arn:aws:bedrock-agentcore:us-east-1:<ACCOUNT_ID>:token-vault/default/apikeycredentialprovider/skilltest_ext_key`
- Note: response fields are `apiKeySecretArn`/`apiKeySecretJsonKey` (request uses `apiKeySecretConfig{secretId,jsonKey}`)
- Skill edit: identity.md EXTERNAL example upgraded to verified-live
- Cleanup: provider + secret force-deleted ✓
- Ops note: first attempt hit an IMDS credential-propagation race after an instance-profile swap (secretsmanager client cached old role) — retry via `sts:AssumeRole` pattern fixed it

## T2.2 — Temporal policy create/validate
- Date: 2026-08-12 | Tier: T2 | Feature: F2
- Result: **PARTIAL**
- PASS: `create_policy_engine` → ACTIVE; `create_policy(definition={"cedar": ...}, enforcementMode="LOG_ONLY")` accepted, `enforcementMode` echoed on Get.
- UNRESOLVED: temporal statement `... when { formerly within 1 hour { context.action == "read" } }` rejected in BOTH `definition.policy.statement` (`ValidationException: unexpected token 'within'`) and `definition.cedar` slots. The `definition.policy` slot has a parser (it parsed up to the temporal token), but the exact Dogwood grammar is not in the API reference — consult policy-temporal.html examples before authoring.
- NEW GOTCHAS (verified): `DeletePolicy` while status=CREATING → `ConflictException: Policy cannot be deleted while its status is CREATING`; `DeletePolicyEngine` with policies inside → `ConflictException: Policy engine still contains 1 policy`. A failed-validation create can still land as `CREATE_FAILED` policy that must be deleted.
- Skill edit: policy.md temporal section marked "slot verified / grammar pending"; gotchas added
- Cleanup: policies + engine deleted ✓

## T2.3 — Web-search connector target
- Date: 2026-08-12 | Tier: T2 | Feature: F1
- Command: gateway (AWS_IAM, MCP, SEMANTIC) → `create_gateway_target(targetConfiguration={"mcp":{"connector":{"source":{"connectorId":"web-search","version":"1.2.0"},"configurations":[{"name":"WebSearch","parameterValues":{"domainFilter":{"exclude":["example-blocked.com"]}}}]}}}, credentialProviderConfigurations=[{"credentialProviderType":"GATEWAY_IAM_ROLE"}])`
- Result: **PASS** — target READY; SigV4 `tools/list` against live gatewayUrl returned the `WebSearch` tool schema (query/maxResults/filters.domainFilter/filters.publishedDateFilter) plus the gateway's built-in `x_amz_bedrock_agentcore_search` semantic-search tool. Zero search queries spent.
- HARD REQUIREMENTS (verified): `configurations` must be non-null AND non-empty — the entry is `{"name": "WebSearch", "parameterValues": {...}}` ("Connector configurations must not be null/empty" otherwise); `credentialProviderConfigurations=[{GATEWAY_IAM_ROLE}]` required; gateway service role needs `bedrock-agentcore:InvokeGateway` (gateway/*) + `bedrock-agentcore:InvokeWebSearch` on `arn:aws:bedrock-agentcore:us-east-1:aws:tool/web-search.v1`
- Bonus finding: a second built-in connector exists — `bedrock-knowledge-bases` (Managed KB; tools AgenticRetrieveStream/Retrieve)
- Cleanup: target → gateway → role deleted ✓

## T2.4 — Gateway rate limit
- Date: 2026-08-12 | Tier: T2 | Feature: F3
- Result: **PASS** — created + status ACTIVE with `dimensionKeys=["$.context.iam.principal"]`, entry `{"dimensions": {"$.context.iam.principal": "*"}, "requests": [{"rate": 10.0, "period": "minute"}]}`
- DISCOVERED (via validation error, verbatim regex): dimension keys must match `(targetName|toolName|qualifiedModelId|$.context.iam.principal|$.context.iam.sourceIdentity|$.context.jwt.<claim>)` — per-user = IAM principal or JWT claim; per-target/tool = targetName/toolName; token limits key on qualifiedModelId. `dimensionKeys` is REQUIRED.
- Also verified: `UpdateGatewayRateLimit` accepts ONLY `gatewayIdentifier, rateLimitId, description, entries` — no dimensionKeys (immutable after create), no clientToken.
- Skill edit: gateway.md §Rate limits upgraded with verified grammar
- Cleanup: rate limit deleted before gateway ✓

## T2.5 / T2.9 — Harness + filesystems + memory-by-default
- Date: 2026-08-12 | Tier: T2 | Features: F8, F6, F9
- Result: **PASS**
- `create_harness(... filesystemConfigurations=[{"sessionStorage": {"mountPath": "/mnt/session"}}], NO memory field ...)` → READY; GetHarness echoes the mount and exposes the managed runtime (`agentRuntimeArn/Name/Id = harness_skilltestHarness-*`).
- **T2.9 CONFIRMED**: omitting `memory` → `memory.managedMemoryConfiguration.arn = arn:...:memory/skilltestHarness-QY2jlE2ahh` auto-created. "Built-in memory by default" is REAL behavior.
- **NAMING CORRECTION**: the auto-created Memory id is `<harnessName>-<suffix>` (`skilltestHarness-QY2jlE2ahh`), NOT `harness_<name>_<suffix>` — IAM scoped to `memory/harness_*` would NOT match; scope managed-memory grants accordingly.
- NEGATIVE PROBE (verbatim): `s3FilesAccessPoint.accessPointArn` must match `arn:aws[-a-z]*:s3files:[0-9a-z-:]+:file-system/fs-[0-9a-f]{17,40}/access-point/fsap-[0-9a-f]{17,40}` — it is the **S3 Files service** (`s3files:`), with file-system + access-point resources; a regular S3 access-point ARN is rejected at validation time (before any network-mode check).
- API SHAPE: `GetHarness` response nests everything under a `harness` key; `ListHarnesses` items use `arn` (not `harnessArn`).

## T2.6 — InvokeHarness stream / toolResultMetadata
- Date: 2026-08-12 | Tier: T2 | Feature: F7
- Result: **PARTIAL**
- VERIFIED: `invoke_harness(harnessArn=..., runtimeSessionId=<33+ chars>, messages=[...])` → response key is **`stream`** (not `response`). Observed event types: `messageStart`, `contentBlockDelta` (with `delta.text`, `delta.reasoningContent`), `contentBlockStop`, `messageStop`, `metadata`.
- NOT OBSERVED: `toolResultMetadata` deltas — the channel carries **MCP tool** result metadata; this invoke used the built-in code interpreter. Union membership (text|toolUse|toolResult|reasoningContent|toolResultMetadata) is schema-verified (T1.1/boto3 1.43.69); fragment-reassembly behavior documented from release notes, not live-observed.
- Cost: 1 invoke, Sonnet 5, ~1-2¢

## T2.7 — CapacityProvider (guarded)
- Date: 2026-08-13 | Tier: T2 | Feature: F4
- Result: **PARTIAL** — `ec2Configuration` members verified: `launchTemplateSource` (structure, **required**), `vpcConfiguration`, `volumes`, `lifecycleConfiguration`, `rootVolume`. Create attempt without a launch template fails ParamValidation ("Missing required parameter ... launchTemplateSource") — a capacity provider REQUIRES an existing EC2 launch template. Per cost guardrail, no launch template / provider was created. Tripwire: zero new EC2 instances at all times.
- Skill edit: runtime.md §Instances notes launchTemplateSource requirement, marked shape-verified

## T2.8 — Unified observability log group
- Date: 2026-08-12 | Tier: T2 | Feature: F5
- Result: **PASS** — after invoking the fresh (created 2026-08-12) harness: `/aws/bedrock-agentcore/runtimes/harness_skilltestHarness-V4mPLJ6tM7-DEFAULT` exists — i.e. the unified `<agent_id>-<endpoint_name>` pattern where agent_id = the harness-managed runtime id and endpoint_name = DEFAULT.

## T2.10 — `agentcore export harness`
- Date: 2026-08-13 | Tier: T2 | Feature: F10
- Result: **PASS** (CLI v0.26.0 stable)
- VERIFIED FLOW: export REQUIRES an agentcore project (`NoProjectError` otherwise) → `agentcore create --name <proj> --defaults` (scaffold only, no deploy) → `agentcore export harness --arn <arn> --build CodeZip --json`. Flags: `--name | --arn | --target-agent-name | --build CodeZip|Container | --json`; there is NO `--output` (writes into the project's `app/<harnessName>Agent/`).
- OUTPUT: Strands project (`main.py`, `model/` incl. `mantle_compat.py`, `mcp_client/`, `memory/session.py`, `skills/fetcher.py`, `hooks/execution_limits.py`, `pyproject.toml` with `strands-agents >= 1.15.0`) + `EXPORT_NOTES.md` listing semantic drops (verbatim: "allowedTools: per-invocation overrides dropped ... applied statically at code-generation time").
- Cleanup: /tmp export dir removed with EC2 workspace ✓

## T2.11 — Harness delete semantics
- Date: 2026-08-13 | Tier: T2
- Result: **PASS** — `delete_harness` returns immediately; status transitions through `DELETING` (async, minutes). The auto-created managed memory carries `managedByResourceArn=<harness arn>` and CANNOT be deleted directly (`ValidationException: Memory is managed and cannot be deleted directly. Delete the managing resource or disassociate the memory first.`); it **cascade-deletes** with the harness (observed gone a few minutes after harness deletion).

## T2.99 — Sweep + teardown
- Date: 2026-08-13 | Tier: T2
- Result: **PASS** — list_harnesses / list_gateways / list_policy_engines / list_capacity_providers / list_api_key_credential_providers / list_memories / list-secrets: zero `skilltest*` leftovers. All temporary IAM removed (skilltest-ec2-role + profile + policy, skilltest-gw/harness/cap roles, the QuickSetup inline assume policy). Instance profile back at `AmazonSSMRoleForInstancesQuickSetup`; same 4 EC2 instances running as at campaign start (no new instances at any point).
- Ops note for future campaigns: SSM Quick Setup **drift remediation auto-reverts instance-profile swaps** (~40 min). The stable pattern is a scoped `sts:AssumeRole` from the instance's standing role to a dedicated temporary test role.

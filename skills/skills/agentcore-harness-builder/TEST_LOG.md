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

---
---

# Live Test Campaign 3 — Knowledge Bases, Registry namespace, Target-union reachability

- **Date:** 2026-08-13 | **Region:** us-east-1 | **Account:** `<ACCOUNT_ID>` (redacted)
- **Execution host:** EC2 `claude-code-test-linux` (reused, **left running** by user decision), via SSM; driver assumes the dedicated `skilltest-ec2-role` **per case** rather than relying on the instance profile
- **Tooling:** boto3/botocore **1.43.70** for T2 (T1 asserts against 1.43.68; T1.4 installs 1.43.64/.65/.66/.68 into throwaway venvs)
- **Guardrails:** `Retrieve` ≤10 · `AgenticRetrieveStream` ≤3 · `InvokeHarness` ≤6 · `InvokeWebSearch` **=0** · corpus ≤8 KB / 3 objects · EC2-count tripwire before and after every case · $2 hard cost ceiling
- **Scale:** 19 cases, **204 checks, all PASS**, 50 findings. Numbering note: the planned T2.11 (`inference.connector`) and T2.12 (`http.passthrough`) were folded into **T2.10** once the first `http.*` refusal showed the gating was per union branch, not per leaf; **T2.7b** was added to separate override *syntax* from override *semantics*.
- Result legend: **PASS** = call made, outcome as recorded · **FAIL** = call made, wrong outcome · **BLOCKED** = API/CLI lacks the operation or permission

## Summary

| ID | Feature | Checks | Result |
|---|---|---|---|
| C3-T1.1 | Gateway `TargetConfiguration`: 11 leaves, connector shapes, `HarnessToolType` | 21 | PASS |
| C3-T1.2 | `agent-registry*` inventory, record shapes, dead field names | 17 | PASS |
| C3-T1.3 | `bedrock-agent`/`-runtime`: MANAGED KB, data-source enum, `AgenticRetrieveStream` | 11 | PASS |
| C3-T1.4 | botocore floor bisect (throwaway venvs, PyPI only) | 5 | PASS |
| C3-T2.0 | IAM prep, `PassRole` precheck, `agent-registry:` prefix, boundary simulation | 16 | PASS |
| C3-T2.1 | Sentinel corpus (3 unguessable facts) | 3 | PASS |
| C3-T2.2 | MANAGED KB with **no** `storageConfiguration` | 4 | PASS |
| C3-T2.3 | `MANAGED_KNOWLEDGE_BASE_CONNECTOR` data source + ingest | 20 | PASS |
| C3-T2.4 | Direct data-plane `Retrieve` + `AgenticRetrieveStream` | 13 | PASS |
| C3-T2.5 | Gateway + KB connector target; async validation, credential rules | 7 | PASS |
| C3-T2.6 | SigV4 `tools/list` + `tools/call`: exact tool names, default schema | 12 | PASS |
| C3-T2.7 | `parameterOverrides.path`: JSON Pointer vs JSONPath | 6 | PASS |
| C3-T2.7b | `parameterOverrides` semantics: subtree shape, `visible`, composition | 10 | PASS |
| C3-T2.8 | e2e through a harness; `allowedTools` grammar; `toolResultMetadata` | 7 | PASS |
| C3-T2.9 | Connector `version`: default vs latest, sticky update, catalogue | 8 | PASS |
| C3-T2.10 | Target-union reachability: `http.*` gated, `inference.*` not | 10 | PASS |
| C3-T2.13 | `agent-registry` e2e: registry, SKILL record, approval, discovery | 18 | PASS |
| C3-T2.14 | Rate-limit `toolName` dimension: are entry values checked? | 10 | PASS |
| C3-T2.99 | Full sweep + teardown | 6 | PASS |

---

## C3-T1.1 — Gateway target union: 11 leaves (zero AWS calls)
- Date: 2026-08-13 | Tier: T1 | Feature: Gateway targets
- Command: `t1_1.py` against the botocore 1.43.68 service model, no credentials, no network
- Result: **PASS** (21/21)
- Evidence:
  - `targetConfiguration` union top level: `['http', 'inference', 'mcp']`; **11 leaves** — mcp 6 / http 3 / inference 2
  - `ConnectorVersion` metadata: `{'min': 5, 'max': 32, 'pattern': '(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)'}`
  - `mcp.connector.enabled` list min 1 max 50; `mcp.apiGateway` requires **all three** of `apiGatewayToolConfiguration, restApiId, stage`
  - `HarnessToolType` = `['remote_mcp', 'agentcore_browser', 'agentcore_gateway', 'inline_function', 'agentcore_code_interpreter']`
  - `http.passthrough.protocolType` enum = **`['MCP', 'HTTP']`** while `GatewayProtocolType` = `['MCP']`
- Findings: `TARGET-PROTOCOL-ENUM-IS-WIDER-THAN-GATEWAY-PROTOCOL-ENUM`, `KB-IS-NOT-A-HARNESS-TOOL-TYPE`
- Note: this case **caught an error in my own Phase A authoring** — `gateway.md` had documented `http.passthrough.protocolType` as `MCP|A2A|INFERENCE|CUSTOM`. Writing the assertion against the model rather than against the draft is what surfaced it.
- Skill edit: `gateway.md` `http.passthrough` protocolType corrected; `tools.md` notes RAG is not a tool type
- Cleanup: n/a (no resources) ✓

## C3-T1.2 — `agent-registry` namespace and the dead field names (zero AWS calls)
- Date: 2026-08-13 | Tier: T1 | Feature: Registry
- Result: **PASS** (17/17)
- Evidence:
  - `agent-registry-control` **15 ops**, `agent-registry` **3 ops**, both apiVersion **2025-12-01**
  - `CreateRegistryRecord` required = `{registryId, name, recordType, descriptors}`; `RecordType` = `['MCP','AGENT','CUSTOM','SKILL']`
  - descriptor keys = `['a2aAgentCard','agentSkillsDefinition','custom','mcpServer']`; `DescriptorData` = `{'min':1,'max':102400,'sensitive':True}`
  - `autoApprovalRules` member enum = `['APPROVE_ALL']`; `discoveryConfiguration` = `['authorizerConfiguration','authorizerType']`, authorizerType `['CUSTOM_JWT','AWS_IAM']`
  - `descriptorType` / `inlineContent` / `schemaVersion` / `protocolVersion`: **zero occurrences** in any shape of the new control model
  - legacy `bedrock-agentcore-control` still ships **11** registry ops
- Findings: `REGISTRY-RELAUNCH-DROPPED-FOUR-FIELD-NAMES`, `REGISTRY-RENAME-IS-A-CROSS-PLANE-RENAME`, `BOTH-REGISTRY-NAMESPACES-COEXIST-IN-THE-SDK`
- Note: **this case FAILed on its first run and the test was what was wrong.** I had asserted the legacy `SearchRegistryRecords` lived on `bedrock-agentcore-control`; it is on the legacy *data* plane `bedrock-agentcore` (2024-02-28). The rename claim in `registry.md` was right, the assertion was aimed at the wrong plane — and fixing it produced a better finding: the op moved plane **and** was renamed, so grepping only the control plane for the old name finds nothing and suggests it never existed.
- Skill edit: `registry.md` §Migration names the plane as well as the operation
- Cleanup: n/a ✓

## C3-T1.3 — Knowledge Base planes (zero AWS calls)
- Date: 2026-08-13 | Tier: T1 | Feature: Knowledge Bases
- Result: **PASS** (11/11)
- Evidence:
  - `KnowledgeBaseType` = `['VECTOR','KENDRA','SQL','MANAGED']`; `CreateKnowledgeBase` required = `['knowledgeBaseConfiguration','name','roleArn']` — **`storageConfiguration` absent**
  - `DataSourceType` 8 members incl. `MANAGED_KNOWLEDGE_BASE_CONNECTOR`
  - `managedKnowledgeBaseConnectorConfiguration` members = `['connectorParameters','deletionProtectionConfiguration','mediaExtractionConfiguration']`, and **`connectorParameters` is declared with no members** (a Document)
  - `AgenticRetrieveStream` required = `['agenticRetrieveConfiguration','messages','retrievers']`, and `agenticRetrieveConfiguration` has **zero required members of its own**
- Findings: `MANAGED-KB-NEEDS-NO-STORAGE-CONFIGURATION`, `MANAGED-DATASOURCE-CONNECTORPARAMETERS-IS-AN-UNTYPED-DOCUMENT`, `AGENTICRETRIEVE-CONFIG-IS-REQUIRED-BUT-EMPTY-IS-LEGAL`
- Note: the first draft of this case asserted something self-contradictory ("a typed structure rather than a structure"). The wrapper *is* typed; the untyped part is `connectorParameters` **inside** it. Rewritten to enumerate inner members and detect members-less structures — which is the boundary where introspection stops and error-driven discovery (T2.3) has to start.
- Skill edit: `knowledge-bases.md` §Ingest documents the Document boundary explicitly
- Cleanup: n/a ✓

## C3-T1.4 — botocore floor bisect (PyPI only, zero AWS calls)
- Date: 2026-08-13 | Tier: T1 | Feature: version floors
- Command: `t1_4.py` — throwaway venv per version, `pip install botocore==X`, introspect, delete
- Result: **PASS** (5/5, 63.1s)
- Evidence:
  ```
  1.43.64: op_count 153, rate_limit_ops [], agent-registry* UnknownServiceError
  1.43.65: op_count 153, rate_limit_ops [], agent-registry* UnknownServiceError
  1.43.66: op_count 165, 6 rate_limit_ops, agent-registry-control 15, agent-registry 3
  1.43.68: op_count 165, 6 rate_limit_ops, agent-registry-control 15, agent-registry 3
  ```
- Finding: `BOTOCORE-FLOORS-ARE-PER-FEATURE-NOT-PER-SKILL`
- Note: **both** features floor at **1.43.66**, correcting the plan's assumption that `agent-registry*` needed ≥1.43.68. One floor covers the whole 2026-08 wave, so the skill states one number instead of two.
- Skill edit: `gotchas.md` version table — provenance upgraded from wheel-diff to installed-and-introspected
- Cleanup: venvs removed ✓ | Cost: $0

## C3-T2.0 — IAM prep and boundary simulation
- Date: 2026-08-13 | Tier: T2 | Feature: prerequisites
- Result: **PASS** (16/16)
- Evidence:
  - assumed `skilltest-ec2-role` (not the instance role): `arn:aws:sts::<ACCOUNT_ID>:assumed-role/skilltest-ec2-role/c3-…`
  - three roles created; `iam:PassRole` allowed on all three **before** any create call
  - `bedrock:AgenticRetrieveStream` on `*` simulates **allowed** (no boundary blocks the un-scopeable action)
  - `agent-registry:CreateRegistry` / `ListRegistries` simulate allowed, and a **live** `ListRegistries` was accepted → the new IAM prefix is real, not just modelled
  - `skilltest-gw-role` **deliberately omits** `bedrock-agentcore:InvokeGateway` so T2.5/T2.6 can adjudicate the doc contradiction
- Findings: `SIMULATOR-RESOURCE-TYPE`, `DATA-PLANE-SCOPE-KEYS`
- Note: designing the gateway role to omit a permission AWS's docs disagree about turned a documentation dispute into a measurement.
- Cleanup: all roles/policies removed in T2.99 (sequenced off-box so the script could not sever its own credentials; every policy document archived first) ✓ | Cost: $0

## C3-T2.1 — Sentinel corpus
- Date: 2026-08-13 | Tier: T2 | Feature: Knowledge Bases
- Result: **PASS** (3/3) — bucket `skilltest-kb-corpus-<8hex>`, 3 objects, **694 bytes** total
- Evidence: each file carries one unguessable fact (flange bolt **42 Nm**; escalation code **PLUM-7**; a retention rule)
- Note: sentinels make retrieval falsifiable. Without them a plausible answer from model memory is indistinguishable from a working index — and two later cases (T2.4, T2.8) turn on exactly that distinction.
- Cleanup: objects + bucket deleted in T2.99 ✓ | Cost: ~$0

## C3-T2.2 — MANAGED knowledge base with no `storageConfiguration`
- Date: 2026-08-13 | Tier: T2 | Feature: Knowledge Bases
- Result: **PASS** (4/4) — `CreateKnowledgeBase` succeeded with **no** `storageConfiguration`; `ACTIVE` after **92s**
- Evidence:
  - `managedKnowledgeBaseConfiguration={}` accepted → server fills `{'embeddingModelType': 'MANAGED'}`
  - `GetKnowledgeBase` returns **no** `storageConfiguration` either — the vector store is service-owned and invisible
- Findings: `EMBEDDING-MODEL-TYPE-OPTIONAL`, `MANAGED-KB-NO-STORAGE`
- Skill edit: `knowledge-bases.md` §Build — a MANAGED KB needs nothing beyond `type=MANAGED`
- Cleanup: KB deleted in T2.99 after its data source ✓ | Cost: index storage, ≤$0.05

## C3-T2.3 — `MANAGED_KNOWLEDGE_BASE_CONNECTOR`: schema by error, then ingest
- Date: 2026-08-13 | Tier: T2 | Feature: Knowledge Bases
- Result: **PASS** (20/20, 352.6s) — ingestion `COMPLETE`, `{'numberOfDocumentsScanned': 3, 'numberOfNewDocumentsIndexed': 3, 'numberOfDocumentsFailed': 0, 'numberOfDocumentsSkipped': 0}`
- Evidence (all `ValidationException`, verbatim):
  - `type=S3` **and** `type=CUSTOM` on a MANAGED KB → `Unsupported data source type for MANAGED knowledge base type.`
  - `connectorParameters={}` → `Connector type is required in connector parameters`
  - `connectorType` instead of `type` → *the same message* (the error does not name the right key)
  - no `version` → `The 'version' field is required in connector parameters.`
  - `version="1.0.0"` → `Invalid connector version '1.0.0'. Supported versions are: 1.`
  - `type="BOGUS_XYZ"` → `Invalid connector type 'BOGUS_XYZ'. Supported types are: S3, ONEDRIVE, ZENDESK, SALESFORCE, BOX, DROPBOX, SHAREPOINT, GOOGLEDRIVE, WEB, CUSTOM, CONFLUENCEONPREM, CONFLUENCE, SERVICENOW.`
  - valid `type`, no `connectionConfiguration` → **accepted**, `CREATING`, then `FAILED` with `["Value at 'connectionConfiguration' failed to satisfy constraint: Member must not be null"]`; `StartIngestionJob` then refuses: `You cannot start an ingestion job on a data source with status FAILED.`
  - working payload → `AVAILABLE`; `GetDataSource` echoes `connectorParameters` as a **JSON string** with injected defaults `{"filterConfiguration": {"maxFileSizeInMegaBytes": "500"}, "aclEnabled": false}`
- Findings: `MANAGED-KB-REJECTS-S3-DATASOURCE`, `CONNECTOR-VERSION-NOT-SEMVER`, `TWO-DIFFERENT-CONNECTOR-CATALOGUES`, `CONNECTOR-PARAMS-VALIDATED-ASYNC`, `CONNECTOR-PARAMS-ECHOED-AS-STRING`
- Note: this is the case that most changed the skill. `knowledge-bases.md` had documented `CreateDataSource(S3)` — the shape every pre-existing Bedrock KB example uses — and a MANAGED KB rejects it outright. Chaining the errors was the only way to recover the real schema, since botocore validates nothing inside a Document.
- Skill edit: `knowledge-bases.md` §Ingest rewritten around `MANAGED_KNOWLEDGE_BASE_CONNECTOR` with the error table
- Cleanup: data source deleted in T2.99 before the KB ✓ | Cost: managed embedding — free

## C3-T2.4 — Direct data-plane retrieval (bypassing the gateway)
- Date: 2026-08-13 | Tier: T2 | Feature: Knowledge Bases
- Result: **PASS** (13/13) — both operations returned their sentinel
- Evidence:
  - `Retrieve` → 3 chunks, surfacing `flange bolt … torqued to **42 Nm**`
  - `AgenticRetrieveStream` → `traceEvent`/`responseEvent` stream surfacing `escalation code **PLUM-7**`, no exception events
  - `vectorSearchConfiguration` against a MANAGED KB → `Incompatible configuration: vectorSearchConfiguration is not supported for managed knowledge bases. Use managedSearchConfiguration instead.`
  - `maxAgentIteration` metadata `{'min': 2}` — pinning 1 is a client-side `ParamValidationError`
  - omitting `agenticRetrieveConfiguration` → `ParamValidationError: Missing required parameter … "agenticRetrieveConfiguration"`; `{}` is legal
- Findings: `AGENTIC-CONFIG-REQUIRED-BUT-EMPTY-OK`, `MANAGED-KB-NEEDS-MANAGEDSEARCHCONFIGURATION`, `MAX-AGENT-ITERATION-MIN-2`
- Note: running the data plane **before** the gateway is what let every later failure be attributed correctly — with retrieval already proven, a gateway-side problem could not be confused with a corpus or IAM problem. The `maxAgentIteration` floor of 2 also invalidated my own cost guardrail, which had pinned 1.
- Skill edit: `knowledge-bases.md` §Direct query — `managedSearchConfiguration`, no `overrideSearchType`, floor of 2
- Cleanup: n/a | Cost: 1 `Retrieve` + 1 `AgenticRetrieveStream` ≈ $0.006

## C3-T2.5 — Gateway + KB connector target: async validation and credential rules
- Date: 2026-08-13 | Tier: T2 | Feature: Gateway
- Result: **PASS** (7/7)
- Evidence:
  - gateway **READY in 5.1s with a role that lacks `InvokeGateway`**
  - `credentialProviderType=API_KEY` → `Connector target only supports GATEWAY_IAM_ROLE credential provider type`
  - `credentialProviderConfigurations` omitted → `Credential provider configurations is not defined` (the field is *optional* in the shape)
  - bogus `knowledgeBaseId` → accepted, `CREATING`, then **`FAILED` after 5.2s**, `reasons=['The specified resource was not found.']`
  - a config with only `retrievers` (no `agenticRetrieveConfiguration`) → **`READY`**, `reasons=None`
  - the real KB target → `READY` after 5.2s
- Findings: `GATEWAY-READY-WITHOUT-INVOKEGATEWAY`, `CREDENTIAL-PROVIDER-DE-FACTO-REQUIRED`
- Skill edit: `gateway.md` §mcp.connector requirement 2 and 3 rewritten; `gotchas.md` doc-errors table
- Cleanup: all targets incl. the `FAILED` one deleted before the gateway ✓ | Cost: $0

## C3-T2.6 — `tools/list` and `tools/call` over SigV4
- Date: 2026-08-13 | Tier: T2 | Feature: Gateway / MCP
- Result: **PASS** (12/12)
- Evidence:
  - advertised names: `['kb___AgenticRetrieveStream', 'kb___Retrieve', 'skilltest-partial-agentic___AgenticRetrieveStream']` — **three underscores**, target name first, connector casing preserved, hyphens in the target name carried through verbatim
  - agent-visible `Retrieve` schema properties = `['retrievalQuery']` → **no `knowledgeBaseId`**, it is administrator-bound
  - the `FAILED` bogus-kb target contributes **no** tool; the incomplete-but-`READY` target **does** advertise its tool
  - `tools/call` on `kb___Retrieve` → HTTP 200, `isError=false`, sentinel `42 Nm` returned **through the gateway**
  - the incomplete target at invoke time → HTTP 200 with **`isError=True`** and a `ValidationException` in the payload
- Findings: `TOOL-NAME-GRAMMAR-CONFIRMED`, `TOOLS-LIST-AGGREGATES-READY-ONLY`, `KB-ID-NOT-AGENT-VISIBLE`, `GATEWAY-ROLE-NEEDS-NO-INVOKEGATEWAY`, `PARTIAL-AGENTIC-CONFIG-DEFERRED`
- Note: the highest-value unknown of the campaign (`___` vs `_`) is now measured rather than inferred, and the same run settles the `InvokeGateway` dispute in the negative — a full round trip succeeded with a gateway role holding no such permission.
- Skill edit: `gateway.md` §Wire + §Rate limits; `knowledge-bases.md` §Agent view + §IAM; `gotchas.md`
- Cleanup: with the gateway ✓ | Cost: ~$0.002

## C3-T2.7 — `parameterOverrides.path`: which syntax?
- Date: 2026-08-13 | Tier: T2 | Feature: Gateway connector
- Result: **PASS** (6/6)
- Evidence:
  - baseline agent schema = `['retrievalQuery']`
  - JSONPath `$.retrievalConfiguration.managedSearchConfiguration.numberOfResults` → **accepted**, schema becomes `['retrievalConfiguration', 'retrievalQuery']`
  - JSON Pointer `/retrievalConfiguration/managedSearchConfiguration/numberOfResults` → **rejected**: `Connector target validation failed: Configuration 'Retrieve': parameterOverride path '/…' is not a recognized override.`
  - a path naming a nonexistent field → `parameterOverride path '$.thisFieldDoesNotExist' is not a recognized override.`
- Finding: `PARAMETER-OVERRIDE-PATH-SYNTAX`
- Skill edit: `knowledge-bases.md` §Agent view corrected to JSONPath; `gotchas.md` doc-errors row resolved
- Cleanup: target restored to READY without overrides ✓ | Cost: $0

## C3-T2.7b — What an override actually widens
- Date: 2026-08-13 | Tier: T2 | Feature: Gateway connector
- Result: **PASS** (10/10)
- Evidence:
  - the widened property is the **root** of the path (`retrievalConfiguration`), not the leaf; only the overridden leaf appears in the reconstructed subtree (`['numberOfResults']`)
  - the sibling leaf `filter` stays hidden; two overrides on siblings merge into one subtree (`['filter', 'numberOfResults']`)
  - `required[]` unchanged (`['retrievalQuery']`) → every widened field is optional
  - `visible` omitted → resolves to **False**; `visible: false` leaves the field hidden
  - a `tools/call` supplying the full nested object with `numberOfResults=1` → HTTP 200, `isError=false`
- Findings: `OVERRIDE-WIDENS-A-PATH-NOT-A-FIELD`, `OVERRIDE-VISIBLE-DEFAULT`, `WIDENED-FIELD-IS-HONOURED`
- Note: splitting syntax (T2.7) from semantics (T2.7b) was worth an extra case. "The JSONPath is accepted" would have left an author expecting a top-level `numberOfResults` property, and the default-`false` `visible` means a description-only override silently reveals nothing.
- Skill edit: `knowledge-bases.md` §Agent view — three measured behaviours
- Cleanup: target restored to READY with no overrides ✓ | Cost: ~$0.001

## C3-T2.8 — End to end through a harness
- Date: 2026-08-13 | Tier: T2 | Feature: Harness + Gateway
- Result: **PASS** (7/7, 180.5s) — harness `READY` after 151.1s; the agent answered **"The PLUM manifold flange bolt is torqued to 42 Nm (do not exceed 44 Nm)"** having called `['kb___Retrieve']`
- Evidence:
  - `harnessName='skilltest-h-<hex>'` → `Member must satisfy regular expression pattern: [a-zA-Z][a-zA-Z0-9_]{0,39}` (hyphens rejected)
  - `allowedTools=['@kbgw/*']` → works; `allowedTools=['kb___Retrieve']` → **tool never called, no error**
  - `allowedTools=['shell']` → agent answered `NOT FOUND` after shelling out `grep -ri "PLUM manifold"` and `find / -iname '*torque*'`
  - `toolResultMetadata`: **zero fragments** emitted by the `bedrock-knowledge-bases` connector on this turn
- Findings: `HARNESSNAME-REJECTS-HYPHENS`, `AGENT-FACING-GATEWAY-TOOL-NAME`, `TOOLRESULTMETADATA-NOT-EMITTED-BY-KB-CONNECTOR`, `ALLOWEDTOOLS-GRAMMAR-FOR-GATEWAY-TOOLS`, `ALLOWEDTOOLS-IS-A-REAL-BOUNDARY`
- Note: this case **closes campaign 2's T2.6 PARTIAL** with a real MCP tool — and the answer is negative: the channel is opt-in per MCP server and this connector does not use it, so "expect it from Gateway tools" was too strong. The `allowedTools` result is the campaign's best cautionary tale: a wrong pattern produces a hallucinating-looking agent, not an error. `harnessName` rejecting hyphens is doubly awkward because the managed Memory the service auto-creates is named `<harnessName>-<suffix>`, which contains one.
- Skill edit: `harness-config.md` (pattern), `integrations.md` (channel is optional), `gateway.md` §Wire, `gotchas.md`
- Cleanup: harness deleted; managed memory cascade-swept in T2.99 ✓ | Cost: 3 `InvokeHarness` ≈ $0.02

## C3-T2.9 — Connector version resolution
- Date: 2026-08-13 | Tier: T2 | Feature: Gateway connector | **zero `InvokeWebSearch` calls**
- Result: **PASS** (8/8)
- Evidence:
  - create without `version` → `READY`, `GetGatewayTarget` reads back **`1.1.0`** (not the newest 1.2.0)
  - `UpdateGatewayTarget` omitting `version` → before `1.1.0`, after `1.1.0` → **sticky**
  - explicit `1.2.0` → reads back `1.2.0`
  - `9.9.9` → `Unknown version '9.9.9' for connector 'web-search'. Available versions: [1.1.0, 1.2.0].`
  - `"1.1"` → client-side `Invalid length for parameter …source.version, value: 3, valid min length: 5`
  - unknown id → `Connector integration totally-not-a-connector is not available for this account.`
- Findings: `CONNECTOR-VERSION-RESOLUTION`, `NO-CONNECTOR-CATALOGUE-API`
- Note: "default", not "latest" — the service model's wording is the wrong one. The *version* catalogue is discoverable by error; the *id* catalogue is not. And a two-part version fails in botocore on length before the service ever sees it, so it teaches you nothing.
- Skill edit: `gateway.md` §mcp.connector version section, with both errors verbatim
- Cleanup: all probe targets deleted ✓ | Cost: $0

## C3-T2.10 — Target-union reachability
- Date: 2026-08-13 | Tier: T2 | Feature: Gateway targets
- Result: **PASS** (10/10) — absorbs the planned T2.11 and T2.12
- Evidence:
  - all three `http.*` leaves (`connector`, `passthrough`, `agentcoreRuntime`) → `HTTP target configuration is not supported for gateways with MCP protocol type`
  - `CreateGateway` with `HTTP` / `A2A` / `INFERENCE` / `CUSTOM` / `REST` → `Value 'HTTP' at 'protocolType' failed to satisfy constraint: Member must satisfy enum value set: [MCP]`
  - `inference.*` on the same MCP gateway: `{"inference.connector/bedrock-mantle": "FAILED", "inference.connector/openai": "READY", "inference.connector/anthropic": "READY", "inference.provider": "READY"}`
  - `bedrock-mantle` `statusReasons`: `Inference list-models call to https://bedrock-mantle.us-east-1.api.aws/v1/models failed with HTTP 401: User: arn:aws:sts::<ACCOUNT_ID>:assumed-role/skilltest-gw-role/inference-iam-auth-session is not authorized to perform: bedrock-mantle:ListModels`
  - `inference.provider` reached `READY` with `endpoint=https://api.provider.invalid`
- Findings: `HTTP-CONNECTOR-IS-NOT-MCP-CONNECTOR`, `HTTP-LEAVES-ARE-UNREACHABLE-TODAY`, `INFERENCE-LEAVES-ACCEPTED-ON-MCP-GATEWAY`
- Note: the 11-leaf union splits **three** ways, and the gating is per top-level branch with nothing in the service model expressing it. Two corrections to my own Phase A work fall out: `http.agentcoreRuntime` carried a `live-verified 2026-08-12` stamp I had added with no campaign-2 evidence behind it (the pre-Phase-A file said forms 7–8 were *schema*-verified only), and `routeToTarget` rules address only an `http.*` leaf, so that rule type is unusable today too. `bedrock-mantle`'s `FAILED` is **not** a broken connector — it is my deliberately minimal gateway role lacking `bedrock-mantle:ListModels`, which reveals that `inference.connector` does model discovery at create time under the gateway role.
- Skill edit: `gateway.md` — new §"The `http.*` branch is unreachable today", index table reachability column, §Rules caveat, `inference.connector` table
- Cleanup: all targets + the standalone memory deleted ✓ | Cost: $0 (no inference invoked)

## C3-T2.13 — `agent-registry` end to end, both namespaces
- Date: 2026-08-13 | Tier: T2 | Feature: Registry
- Result: **PASS** (18/18, 149.7s)
- Evidence:
  - first `CreateRegistry` in the account → `AccessDeniedException: Unable to create the service-linked role required for this registry. Ensure the caller has iam:CreateServiceLinkedRole permission for agent-registry.amazonaws.com`
  - after granting it: registry `READY`; `CreateRegistryRecord` returns **HTTP 202 / `CREATING`**, reaching `DRAFT` in **5.1s**; during that window submit *and* delete fail with `ConflictException: Registry record cannot be modified while in CREATING state.`
  - status path under `autoApprovalRules=[APPROVE_ALL]`: `CREATING` → `DRAFT` → *(submit)* → **`APPROVED`**; the explicit `UpdateRegistryRecordStatus(APPROVED)` is redundant
  - all three data-plane ops answered; `ListDiscoverableRegistryRecords` returned the 1 approved record **without descriptors**
  - legacy `bedrock-agentcore-control.CreateRegistry` **still succeeds** (response keys `['ResponseMetadata', 'registryArn']`)
- Findings: `REGISTRY-NEEDS-CREATESERVICELINKEDROLE`, `REGISTRY-RECORD-CREATE-IS-ASYNC`, `REGISTRY-APPROVAL-WORKFLOW-STATUSES`, `REGISTRY-DATA-PLANE-LIVE`, `LEGACY-REGISTRY-OPS-STILL-LIVE`
- Note: the SLR prerequisite is in neither `AgentRegistryFullAccess` nor the Registry pages, and presents as a service fault. Both namespaces genuinely coexist, so the 2026-09-17 shutdown is the only forcing function — there is no deprecation signal anywhere in the SDK.
- Skill edit: `registry.md` §Example (SLR box + record poll + APPROVE_ALL semantics), §Gotchas 7–11, `gotchas.md` doc-errors
- Cleanup: records → registries in **both** namespaces ✓ (`AWSServiceRoleForAgentRegistry` persists by design) | Cost: not separately visible in billing

## C3-T2.14 — Is the rate-limit `toolName` dimension validated?
- Date: 2026-08-13 | Tier: T2 | Feature: Gateway rate limits
- Result: **PASS** (10/10)
- Evidence:
  - one limit, `dimensionKeys=['toolName']`, three sibling entries → read back **`['kb___Retrieve', 'kb_Retrieve', 'Retrieve']`** verbatim, status `ACTIVE`. Two of the three match no tool on the gateway.
  - a second limit with the same `dimensionKeys` → `A limit with dimensionKeys [toolName] already exists for this gateway`
  - `$.context.iam.sourceIdentity` accepted; bare `iam.sourceIdentity` → `Value '{iam.sourceIdentity=*}' at 'entries.1.member.dimensions' failed to satisfy constraint: Map keys must satisfy constraint: [Member must have length less than or equal to 80, …]`
  - `UpdateGatewayRateLimit`: `Unknown parameter "dimensionKeys", must be one of: gatewayIdentifier, rateLimitId, description, entries`
  - the `DeleteGateway` refusal message names **targets**, not rate limits
- Findings: `TOOLNAME-DIMENSION-VALUES-ARE-NOT-VALIDATED`, `ONE-RATE-LIMIT-PER-DIMENSIONKEYS-PER-GATEWAY`, `DIMENSION-KEYS-NEED-THE-CONTEXT-PREFIX`
- Note: **this case's second draft "passed" 8/8 while measuring the wrong thing.** It created three separate limits and read the rejections as tool-name validation — but the message was `A limit with dimensionKeys [toolName] already exists`, a uniqueness constraint with nothing to do with tool names, and the `DeleteGateway` check's error named *targets*. A green case that measures the wrong thing is worse than a red one, so it was rewritten to put all three names as siblings in **one** limit and to probe the uniqueness constraint deliberately. The rewritten result confirms and strengthens the skill's existing warning: a mistyped separator yields a cap that silently never fires.
- Skill edit: `gateway.md` §Rate limits substantially expanded; `gotchas.md`
- Cleanup: rate limits deleted before the gateway ✓ | Cost: $0

## C3-T2.99 — Full sweep and teardown
- Date: 2026-08-13 | Tier: T2
- Result: **PASS** (6/6, 502.2s) — **zero `skilltest*` resources remain**
- Evidence:
  - enumeration by **name prefix and tag**, not by the campaign's own `state.json` — which caught two resources the bookkeeping had missed: a stray KB `skilltest-kb-<hex>-probe` and a legacy-namespace registry
  - delete ordering forced by dependency: rate limits → targets (incl. `FAILED`) → gateway; ingestion jobs → data sources → KB → S3; harness → managed memory → standalone memories; records → registries (both namespaces)
  - the two pre-existing knowledge bases `insurance-kb` / `manufacturing-kb` untouched, alongside 5 other unrelated KBs
  - EC2 fleet: 5 instances at open and at close, **the campaign launched none**, and `claude-code-test-linux` is **still running** as the user requested
- Note: deletes are asynchronous and refuse while a neighbour settles, so the sweep retries on `ConflictException`/`ValidationException` (36 tries, 5s apart) and re-lists to confirm rather than trusting a successful call. It deliberately does **not** touch IAM, because it runs *as* `skilltest-ec2-role` — IAM teardown was sequenced from off-box afterwards, with all 6 inline policies and 4 trust policies archived first so the `InvokeGateway` finding keeps its evidence.
- **Ops notes:**
  - The EC2 tripwire fired mid-campaign on an instance I did not create (`cc-hook-validation`, launched 16:06Z, tagged `Purpose=ephemeral-test`, no `Project=skilltest`; the driver role holds only `ec2:DescribeInstances` and cannot call `RunInstances` at all). It was the user's own concurrent hook work, so it was **admitted to the tripwire baseline with a dated provenance comment rather than terminated** — the campaign does not touch instances it did not make. A second instance (`hookguard-test`) was terminated by the user during the same window. The fleet therefore changed while the campaign ran; none of it was the campaign's doing.
  - SSM `StandardOutputContent` caps at ~24,000 characters, which silently truncated a `tar | base64` log retrieval into a corrupt gzip. Logs are now pulled in 18,000-char base64 chunks.
- **Cost:** ≤ **~$0.0305** total (Bedrock $0.00854 + AgentCore $0.021932546 on 2026-08-13, **both figures including unrelated account activity** — so this is an upper bound, not an attribution). Far under the $2 tripwire. Cost-allocation attribution by the `Project=skilltest` tag was **not** available: the tag was never activated as a cost-allocation tag, and that cannot be applied retroactively. Activate it before the next campaign if per-campaign figures matter.

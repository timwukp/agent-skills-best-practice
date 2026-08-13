# AgentCore Harness — Hard-Learned Facts & Gotchas

These are the facts that cost real debugging time and are **not** (or only partially) in the official docs. When
something fails unexpectedly, scan this file first.

## Contents
- [Versions](#versions)
- [Schema introspection — the truth source](#schema-introspection)
- [Harness vs Runtime — two ARNs, two APIs](#harness-vs-runtime)
- [UpdateHarness payload rules](#updateharness-payload-rules)
- [SKILL.md frontmatter requirement](#skillmd-frontmatter)
- [Memory: 3-step wiring + IAM](#memory-wiring)
- [Tools wiring](#tools-wiring)
- [Observability / log delivery](#observability)
- [Authoritative references](#authoritative-references)

---

## Versions

Harness is **GA** (2026-06-17, all AWS Commercial Regions where AgentCore is available; GovCloud
US-West added 2026-08), but AgentCore still adds operations frequently — the 2026-06→08 wave added
web-search connector targets, gateway rate limits, temporal policies, capacity providers, and
`apiKeySecretSource`. Use the latest SDK/CLI unless you have a reason not to.

| Tool | Minimum | Why it matters |
|---|---|---|
| `boto3` / `botocore` | **≥ 1.43.68** | ≥1.43.51 for harness ops; ≥1.43.68 additionally carries capacity providers, gateway rate limits, connector/inference targets, `enforcementMode`, `apiKeySecretSource`, `toolResultMetadata` (verified by schema introspection). |
| AWS CLI v2 | **≥ 2.36.x** (2.34.57 floor for harness) | 2.31.x lacks ALL harness/policy/capacity ops (verified: 57 ops, zero matches); 2.36.21 verified to carry the full new op families. |
| `@aws/agentcore` (npm) | latest | The official CLI (the Python `bedrock-agentcore-starter-toolkit` is **deprecated**). Pre-1.0: command coverage varies by version — inventory with `--help` before scripting. |
| Region | any Harness GA region (e.g. `us-east-1`, `us-west-2`, `eu-central-1`, `ap-southeast-2`) | Some features are narrower: Web Search us-east-1 only; temporal policies 16 regions; Identity EXTERNAL secrets 14 regions. |

```bash
pip3 install --upgrade boto3 botocore
python3 -c "import boto3; print(boto3.__version__)"   # expect >= 1.43.51
aws --version                                          # expect >= 2.34.57
```

Verify the ops actually exist:
```python
import boto3
ops = [o for o in boto3.client("bedrock-agentcore-control").meta.service_model.operation_names if "Harness" in o]
print(ops)  # expect CreateHarness, UpdateHarness, GetHarness, ListHarnesses, DeleteHarness,
            #        CreateHarnessEndpoint, UpdateHarnessEndpoint, GetHarnessEndpoint,
            #        ListHarnessEndpoints, DeleteHarnessEndpoint, ListHarnessVersions
```

---

## Schema introspection

**When the docs and the live API disagree, the live API wins.** boto3 carries the exact request shape. Use it to
discover field names, which fields are required, and whether a field is a structure (needs the `optionalValue`
wrapper) or a plain scalar/list.

```python
import boto3
c = boto3.client("bedrock-agentcore-control", region_name="us-east-1")
shape = c.meta.service_model.operation_model("UpdateHarness").input_shape
for name, member in shape.members.items():
    print(name, "->", member.type_name, "(required)" if name in shape.required_members else "")
```

`scripts/preflight.py` runs this for `CreateHarness` and `UpdateHarness` automatically. Do this any time a payload is
rejected with a `ValidationException` you don't understand.

---

## Harness vs Runtime

- A Harness is a **managed wrapper around an `agent_runtime`**. Creating a harness auto-creates the underlying runtime.
- `list-agent-runtimes` returns BOTH plain runtimes and harness-managed ones; the harness-managed ones carry a
  `harness_*` prefix in `agentRuntimeName`.
- Each harness has **two ARNs**:
  - `arn:aws:bedrock-agentcore:<region>:<acct>:harness/<NAME>-<id>` — manage via the `*Harness` APIs
  - `arn:aws:bedrock-agentcore:<region>:<acct>:runtime/harness_<NAME>-<id>` — the auto-created runtime
- **`UpdateAgentRuntime` is rejected** for a harness-managed runtime: *"managed by harness '…' and cannot be updated
  directly. Use UpdateHarness."* Likewise invoke with **`InvokeHarness`** (data plane), not `InvokeAgentRuntime`.
- Control plane = `boto3.client("bedrock-agentcore-control")`. Data plane (invoke) = `boto3.client("bedrock-agentcore")`.
- The agent-side SDK's `AgentCoreRuntimeClient` allowlists only `*_agent_runtime*` methods, so it does **not** expose
  harness ops. Call `bedrock-agentcore-control` directly for harness work.
- **Dual caller permissions**: because a harness wraps a runtime, the *caller* often needs BOTH families —
  invoking needs `bedrock-agentcore:InvokeHarness` **and** `InvokeAgentRuntime`; creating needs `CreateHarness`
  **and** `CreateAgentRuntime` (plus `CreateMemory` if wiring BYO memory) — or you get confusing AccessDenied on
  the "other" API.
- **SECURITY — `InvokeAgentRuntimeCommand`** (data plane) runs a shell command directly on the harness session VM
  and is **NOT gated by `allowedTools`** — it's gated only by the caller's IAM. Do not grant it to callers who
  should only converse with the agent.
- **Invoke-time overrides**: `InvokeHarness` accepts per-call overrides without redeploying — `model`,
  `systemPrompt`, `tools`, `skills`, `allowedTools`, `maxIterations`, `maxTokens`, `timeoutSeconds`, `actorId` —
  plus `qualifier` (endpoint/version, see `references/versioning.md`) and `runtimeUserId`/trace fields.

---

## UpdateHarness payload rules

The rules are **field-specific** — not every structure wraps. Confirm via introspection (above): a field wraps only
if its live shape literally has an `optionalValue` member.

**1. `optionalValue` wraps ONLY `memory`, `environmentArtifact`, `authorizerConfiguration` (live-verified):**
```python
# correct: lists/ints/strings AND model/environment/truncation pass directly (NO wrapper)
control.update_harness(harnessId=h, allowedTools=["*"],
                       maxTokens=65536,
                       model={"bedrockModelConfig": {...}},
                       truncation={"strategy": "sliding_window", "config": {...}},
                       clientToken=tok)

# correct: only these three wrap with optionalValue
control.update_harness(harnessId=h,
    memory={"optionalValue": {"agentCoreMemoryConfiguration": {...}}},
    clientToken=tok)
```

| Field | Wrapper? |
|---|---|
| `allowedTools`, `tools`, `skills`, `systemPrompt` (lists) | **none** |
| `maxTokens`, `maxIterations`, `timeoutSeconds` (ints), `executionRoleArn` (string) | **none** |
| `model`, `environment`, `truncation` (structures — but no wrapper!) | **none** |
| `memory`, `environmentArtifact`, `authorizerConfiguration` | **`optionalValue`** |

**2. `tags` is NOT on `UpdateHarness`** — use a separate `tag_resource(resourceArn=…, tags={…})` call (idempotent).
`CreateHarness` *does* accept `tags` at creation.

**3. `clientToken` min length is 33 chars.** `secrets.token_hex(8)` → 16 chars → rejected. Use `secrets.token_hex(20)`
(40 chars).

**4. Memory retrievalConfig uses `strategyId`, NOT `memoryStrategyId`** (the API ref name is misleading; the validation
error is the real hint).

---

## SKILL.md frontmatter

A `SKILL.md` referenced by `skills[].git.path` / `.path.path` / `.s3.prefix` **must** begin with YAML frontmatter:

```markdown
---
name: ui-testing
description: Methodology and rubrics for UI testing
---
```

Without it, `InvokeHarness` fails at session start: *"SKILL.md … has no YAML frontmatter (must start with ---)"*.
`name` is the identifier the agent uses to invoke the skill (lowercase, no spaces); `description` is one line. This is
**undocumented** and is the single most common skill-related session-start failure. Validate before shipping.

---

## Memory wiring

**Managed memory is the default** — `memory.managedMemoryConfiguration` with a `strategies` list needs no wiring
(AWS creates and owns the Memory resource), **but the execution role still needs memory data-plane permissions**:
the auto-created Memory is named `harness_<name>_*`, and without `CreateEvent/DeleteEvent/GetEvent/ListEvents/
RetrieveMemoryRecords` on `arn:...:memory/harness_*` the first `InvokeHarness` fails with
`AccessDeniedException ... ListEvents` (**verified live**; the `ManagedMemoryEvents` statement in
`assets/iam_execution_role.json` covers it). The 3-step dance below applies only to **BYO**
(`agentCoreMemoryConfiguration`). See `references/memory.md` for full detail.

1. `CreateMemory` (with the strategy set).
2. `UpdateHarness(memory={"optionalValue": {"agentCoreMemoryConfiguration": {…}}})`.
3. **`iam:PutRolePolicy`** on the harness execution role, granting Memory data-plane perms on the new Memory ARN.
   Skipping step 3 → every session start fails with `AccessDeniedException: ListEvents`.

Namespace conversion for the IAM condition: `retrievalConfig` keys use `{placeholder}` syntax (e.g.
`/episodes/{actorId}/{sessionId}`); the IAM `StringLike` condition needs glob form (`/episodes/*/*`). Convert via
regex `\{[^}]+\}` → `*`.

Episodic strategy requires `reflectionConfiguration` (min `{"reflectionConfiguration": {"reflectionPrefix": "Episode summary:"}}`).

---

## Tools wiring

Four gotchas that silently leave tools invisible to the agent:

1. **Harness is already a container deployment.** The managed loader image
   (`public.ecr.aws/.../harness-<region>:latest`) already wires `agentcore_browser`, `agentcore_code_interpreter`,
   `skills`. You do **not** need a custom image to use built-in tools.
2. **Built-ins need NO `config`** — `{"type": "agentcore_browser", "name": "browser"}` alone wires the AWS-owned
   default browser (same for code interpreter). `config` is only needed to pin a custom/cross-region resource ARN,
   and it IS still required for `agentcore_gateway`, `remote_mcp`, and `inline_function` — omit it there and the
   tool is stored but **not wired**. The `config` union has 5 keys: `remoteMcp`, `agentCoreBrowser`,
   `agentCoreGateway`, `inlineFunction`, `agentCoreCodeInterpreter`.
3. **`allowedTools` does NOT use a `browser_*` glob.** Valid patterns: `*`, builtin names/globs (`shell`, `file_*`),
   `@builtin`, `@server[/tool]`. Match browser/code-interpreter/inline tools by **name** (`"browser"`,
   `"code_interpreter"`) or use `"*"` (or omit allowedTools). `"browser_*"` filters the tool OUT -> `Unknown tool`. **Verified live.**
4. **`agentcore_browser` is a single `browser` tool** (driven via navigate/get_text/click/type/evaluate/screenshot
   actions), not six `browser_*` primitives. Allowlist by name `"browser"` or `"*"`.

---

## Observability

- Three `logType` values: `APPLICATION_LOGS` (→ CloudWatch log group), `TRACES` (→ **X-Ray**, not a log group),
  `USAGE_LOGS`.
- **`PutDeliverySource` rejects harness ARNs** (live-verified 2026-07): *"This resource is not allowed for this
  LogType. Valid options are [code-interpreter, memory, …, runtime, gateway]"*. Log/trace deliveries must target the
  **auto-created runtime ARN** (`agentRuntimeName == "harness_<name>"` from `list_agent_runtimes`), never the
  `harness/…` ARN. `scripts/setup_observability.py` does this resolution.
- **X-Ray delivery destinations take no `outputFormat`** — pass only `name` + `deliveryDestinationType="XRAY"`.
- If `create-delivery` succeeds but no events flow, extend the **`AWSLogDeliveryWrite20150319`** resource policy on the
  destination log group to allow `delivery.logs.amazonaws.com` — AWS does not auto-add new services. Preserve existing
  statements.
- The runtime auto-creates `/aws/bedrock-agentcore/runtimes/<name>-<id>-DEFAULT` with rich OTel logs (trace_id,
  span_id, EMF metrics). That's where dashboard data lives; custom `APPLICATION_LOGS` delivery is a sparser, separate
  channel. Set retention explicitly (DEFAULT never expires).

---

## Verified real-API shapes — 2026-08-12/13 campaign additions (boto3 1.43.69, live)

From the live-validation campaign for the 2026-05..08 feature wave (full evidence in `TEST_LOG.md`):

- **`InvokeHarness` streams under the `stream` key** (`resp["stream"]`), not `response`. Event types:
  `messageStart` / `contentBlockDelta` / `contentBlockStop` / `messageStop` / `metadata`.
- **`GetHarness` wraps its payload in a `harness` key**; `ListHarnesses` items use `arn`.
- **Omitting `memory` on CreateHarness attaches a managed Memory** named `<harnessName>-<suffix>`
  (NOT `harness_<name>_*`), with `managedByResourceArn`; it can't be deleted directly and
  cascade-deletes (async) with the harness.
- **Web-search connector target**: `configurations=[{"name": "WebSearch", "parameterValues": {...}}]`
  is mandatory (non-null AND non-empty), `credentialProviderConfigurations=[{GATEWAY_IAM_ROLE}]`
  required, and the gateway role needs `bedrock-agentcore:InvokeWebSearch` on
  `arn:aws:bedrock-agentcore:<region>:aws:tool/web-search.v1`.
- **Rate-limit dimension keys** must match
  `targetName|toolName|qualifiedModelId|$.context.iam.principal|$.context.iam.sourceIdentity|$.context.jwt.<claim>`;
  `dimensionKeys` is required at create and **immutable** (`UpdateGatewayRateLimit` accepts only
  `description`/`entries`).
- **Policy lifecycle**: `DeletePolicy` during `CREATING` and `DeletePolicyEngine` with policies inside
  both throw `ConflictException`; a rejected statement can land as a `CREATE_FAILED` policy that still
  needs deleting. Temporal/Dogwood syntax is NOT plain-Cedar-plus-keywords — take it from the
  policy-temporal dev-guide examples (`unexpected token 'within'` otherwise).
- **`s3FilesAccessPoint` wants an `s3files:` service ARN** (`file-system/fs-*/access-point/fsap-*`) —
  regular S3 access-point ARNs are rejected.
- **`CreateCapacityProvider` requires `launchTemplateSource`** — an existing EC2 launch template is a
  prerequisite for Runtime Instances.
- **`agentcore export harness` requires an agentcore project** (`NoProjectError` otherwise;
  `agentcore create --name x --defaults` scaffolds without deploying); no `--output` flag — output
  lands in `app/<harnessName>Agent/` with `EXPORT_NOTES.md`.

## Verified real-API shapes (boto3 1.43.29) — where docs/console mislead

Confirmed by introspection; these differ from intuition or the console labels:

- **Harness name field is `harnessName`** (CreateHarness) / **`harnessId`** (UpdateHarness) — **not** `name`.
- **No top-level `network` or `lifecycle`.** They live under
  `environment.agentCoreRuntimeEnvironment.{networkConfiguration:{networkMode[req], networkModeConfig:{subnets[req],
  securityGroups[req], requireServiceS3Endpoint}}, lifecycleConfiguration:{idleRuntimeSessionTimeout, maxLifetime}}`
  (lifecycle values in **seconds**).
- **Truncation window is nested:** `truncation.config.slidingWindow.messagesCount` — not a flat
  `slidingWindowMessagesCount`. (`truncation.config.summarization` is the alternative.)
- **Inference settings live inside the model config** (`model.bedrockModelConfig.{apiFormat, maxTokens, temperature,
  topP}`). The model union has 4 providers: `bedrockModelConfig`, `openAiModelConfig`, `geminiModelConfig`,
  `liteLlmModelConfig` (non-Bedrock need `apiKeyArn`).
- **`temperature` is rejected by Claude ≥ 4.7 at INVOKE time, not create time** (live-verified 2026-07): CreateHarness
  and offline validation accept `temperature` happily; the FIRST InvokeHarness then fails with
  `runtimeClientError → ValidationException: temperature is deprecated for this model`. Applies to Fable 5, Opus 5,
  Sonnet 5, Opus 4.8, Opus 4.7 (Converse & ConverseStream, confirmed against Bedrock us-east-1); Opus 4.6/Sonnet 4.6/
  Haiku 4.5 still accept it. Omit `temperature`/`topP` for ≥ 4.7 models.
- **`GetHarness` nests everything under a top-level `harness` key** — the ARN is `resp["harness"]["arn"]`;
  `resp.get("harnessArn")` silently returns None. Same nesting for CreateHarness (`resp["harness"]["harnessId"]`).
- **`harnessId` ≠ `harnessName`**: the service appends a 10-char suffix (`<name>-<XXXXXXXXXX>`), and `GetHarness`/
  `UpdateHarness` demand the FULL id (regex `[a-zA-Z][a-zA-Z0-9_]{0,39}-[a-zA-Z0-9]{10}`) — calling them with the bare
  name you passed to CreateHarness is a ValidationException. Resolve via `list_harnesses` by `name` first.
- **UpdateHarness during CREATING/UPDATING → ConflictException** ("Cannot update agent … while it is CREATING").
  Wait for READY before any update — including the memory attach right after create.
- **Episodic reflection namespace must equal or prefix the episodic namespace** (live-verified):
  `namespaces=["/episodes/{actorId}/{sessionId}"]` with `reflectionConfiguration.namespaces=["/episodes/{actorId}/reflections"]`
  is REJECTED ("must be the same as or a prefix of the episodic namespace"); use `["/episodes/{actorId}"]`.
- **`authorizerConfiguration` has only `customJWTAuthorizer`** — there is no `type: "IAM"`. IAM/SigV4 is the default;
  **omit** `authorizerConfiguration` for it.
- **Skills:** `path` is a bare **string**; `s3` takes a single **`uri`** (not bucket/prefix/versionId); `git` has
  `{url[req], path, auth:{credentialArn[req], username}}` and **no branch**.
- **Tool config union:** `agentCoreBrowser{browserArn}`, `agentCoreCodeInterpreter{codeInterpreterArn}`,
  `inlineFunction{description[req], inputSchema[req]}`, `agentCoreGateway{gatewayArn[req], outboundAuth{awsIam|none|
  oauth{providerArn[req], scopes[req]}}}`, `remoteMcp{url[req], headers}`.
- **`CreateMemory` requires `eventExpiryDuration`** (int days 3–365) in addition to `name`. `UpdateMemory.memoryStrategies`
  is a **structure** (`addMemoryStrategies`/`modifyMemoryStrategies`/`deleteMemoryStrategies`), not a list.
- **`retrievalConfig` value** = `{strategyId, topK, relevanceScore}` (confirms `strategyId`).
- **Evaluations** span BOTH clients: control plane has `CreateOnlineEvaluationConfig` (+ Get/List/Update/Delete)
  and `CreateEvaluator` etc.; the **data plane** has `StartBatchEvaluation` / `GetBatchEvaluation` / etc.
  Introspect both clients before declaring anything console-only.
- **Optimizations** are SDK-scriptable: `start_recommendation`, `create_ab_test`, `create_online_evaluation_config`
  and friends. See `references/optimizations.md`.
- **Other services present:** Gateway (full CRUD + rules/targets), Identity (WorkloadIdentity, Token Vault, API-key/
  OAuth/Payment credential providers), Policy (Policy + PolicyEngine + ResourcePolicy + PolicyGeneration), Payments
  (Connector/Manager/CredentialProvider + data-plane PaymentSession), Registry (registry + records + SearchRegistryRecords).

The lesson stands: **introspect, don't trust labels.** `scripts/preflight.py --show-shape <Op>` is the truth source.

---

## Authoritative references

Look here in priority order when you need ground truth:

| Source | For |
|---|---|
| AWS Bedrock AgentCore Developer Guide — https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/ | concepts, tutorials |
| Control Plane API Reference — https://docs.aws.amazon.com/bedrock-agentcore-control/latest/APIReference/Welcome.html | exact request/response JSON |
| `aws/bedrock-agentcore-sdk-python` | agent-side SDK source |
| `awslabs/amazon-bedrock-agentcore-samples` | working examples |
| CloudFormation `AWS::BedrockAgentCore::*` | schema-as-truth for resource fields |
| Live boto3 introspection (above) | when everything else disagrees |

Pin to memory: Harness overview — https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/harness.html ·
Connect to tools — https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/harness-tools.html ·
Memory get-started — https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/memory-get-started.html

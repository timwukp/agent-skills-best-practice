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

AgentCore is **public preview** and adds operations frequently. Use the latest SDK/CLI unless you have a reason not to.

| Tool | Minimum | Why it matters |
|---|---|---|
| `boto3` / `botocore` | **≥ 1.43.18** | Older versions have **zero** harness ops. 1.42.79 → 0 harness ops; 1.43.18 → 5 (`create/update/get/list/delete_harness`). |
| AWS CLI v2 | **≥ 2.34.57** | Earlier CLI lacks `create-harness`/`update-harness`/etc. |
| `@aws/agentcore` (npm) | latest | Optional scaffolding CLI (`agentcore create/deploy`). |
| Region | `us-east-1` (or `us-west-2`, `eu-central-1`, `ap-southeast-2`) | Preview availability. |

```bash
pip3 install --upgrade boto3 botocore
python3 -c "import boto3; print(boto3.__version__)"   # expect >= 1.43.18
aws --version                                          # expect >= 2.34.57
```

Verify the ops actually exist:
```python
import boto3
ops = [o for o in boto3.client("bedrock-agentcore-control").meta.service_model.operation_names if "Harness" in o]
print(ops)  # expect CreateHarness, UpdateHarness, GetHarness, ListHarnesses, DeleteHarness
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

---

## UpdateHarness payload rules

The rules are **type-driven**, not field-name-driven. Confirm via introspection (above).

**1. `optionalValue` wrapper applies only to complex *structure* fields:**
```python
# correct: list/integer fields pass directly (NO wrapper)
control.update_harness(harnessId=h, allowedTools=["browser_*","code_interpreter*","skills"],
                       maxTokens=65536, clientToken=tok)

# correct: structure fields wrap with optionalValue
control.update_harness(harnessId=h,
    memory={"optionalValue": {"agentCoreMemoryConfiguration": {...}}},
    model={"optionalValue": {"bedrockModelConfig": {...}}},
    clientToken=tok)
```

| Field | Shape | Wrapper? |
|---|---|---|
| `allowedTools`, `tools`, `skills`, `systemPrompt` | list | **none** |
| `maxTokens`, `maxIterations`, `timeoutSeconds` | integer | **none** |
| `executionRoleArn` | string | **none** |
| `memory`, `model`, `environment`, `environmentArtifact`, `authorizerConfiguration`, `truncation` | structure | **`optionalValue`** |

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

Three coordinated steps — not two. See `references/memory.md` for full detail.

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
2. **`tools[].config` is documented optional but practically required.** Omit it and the tool is stored on the harness
   but **not wired** at runtime — the agent never sees it. The `config` union has 5 keys: `remoteMcp`,
   `agentCoreBrowser`, `agentCoreGateway`, `inlineFunction`, `agentCoreCodeInterpreter`.
3. **`allowedTools` does NOT use a `browser_*` glob.** Valid patterns: `*`, builtin names/globs (`shell`, `file_*`),
   `@builtin`, `@server[/tool]`. Match browser/code-interpreter/inline tools by **name** (`"browser"`,
   `"code_interpreter"`) or use `"*"` (or omit allowedTools). `"browser_*"` filters the tool OUT -> `Unknown tool`. **Verified live.**
4. **`agentcore_browser` is a single `browser` tool** (driven via navigate/get_text/click/type/evaluate/screenshot
   actions), not six `browser_*` primitives. Allowlist by name `"browser"` or `"*"`.

---

## Observability

- Three `logType` values: `APPLICATION_LOGS` (→ CloudWatch log group), `TRACES` (→ **X-Ray**, not a log group),
  `USAGE_LOGS`.
- **X-Ray delivery destinations take no `outputFormat`** — pass only `name` + `deliveryDestinationType="XRAY"`.
- If `create-delivery` succeeds but no events flow, extend the **`AWSLogDeliveryWrite20150319`** resource policy on the
  destination log group to allow `delivery.logs.amazonaws.com` — AWS does not auto-add new services. Preserve existing
  statements.
- The runtime auto-creates `/aws/bedrock-agentcore/runtimes/<name>-<id>-DEFAULT` with rich OTel logs (trace_id,
  span_id, EMF metrics). That's where dashboard data lives; custom `APPLICATION_LOGS` delivery is a sparser, separate
  channel. Set retention explicitly (DEFAULT never expires).

---

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
- **Evaluations** = `CreateOnlineEvaluationConfig` (+ Get/List/Update/Delete). Batch eval / custom evaluators are
  console features; no dedicated SDK ops confirmed.
- **Optimizations** = **ZERO control-plane ops** in this SDK → console/preview-only. Don't script it.
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

# Harness Configuration — Full Field Reference

Field shapes below are **verified against boto3 1.43.29** via schema introspection. `assets/harness.json.template`
is a complete working example using these exact shapes — start from it. When in doubt, re-introspect
(`scripts/preflight.py --show-shape CreateHarness`).

## Contents
- [Top-level CreateHarness fields](#top-level-fields)
- [Where network / lifecycle / inference actually live](#nesting)
- [Best-practice defaults](#best-practice-defaults)
- [CreateHarness](#createharness)
- [UpdateHarness payload rules](#update-payload-rules)
- [Tags](#tags)
- [Execution role](#execution-role)

---

## Top-level fields

`CreateHarness` accepts exactly these members (required marked):

| Field | Type | Notes |
|---|---|---|
| `harnessName` | string **[req]** | NOT `name`. Appears in both ARNs. (`UpdateHarness` uses `harnessId` instead.) |
| `executionRoleArn` | string **[req]** | IAM role the harness assumes. |
| `clientToken` | string | Idempotency token; **≥ 33 chars** (`secrets.token_hex(20)`). |
| `model` | structure | `bedrockModelConfig` / `openAiModelConfig` / `geminiModelConfig` / `liteLlmModelConfig`. See `model-and-prompt.md`. |
| `systemPrompt` | list | `[{"text": "..."}]`. |
| `tools` | list | Each `{type, name, config}`. See `tools.md`. |
| `allowedTools` | list | `["*"]` or plain names (`["browser","code_interpreter","skills"]`) — **no** `browser_*` glob (matches nothing). |
| `skills` | list | Each a union `{path|s3|git}`. See `skills.md`. |
| `memory` | structure | Union: `managedMemoryConfiguration` (default) / `agentCoreMemoryConfiguration` (BYO) / `disabled`. See `memory.md`. |
| `truncation` | structure | `{strategy, config:{slidingWindow:{messagesCount}}}`. |
| `environment` | structure | Holds **networkConfiguration + lifecycleConfiguration** (see below) + filesystem. |
| `environmentArtifact` | structure | `{containerConfiguration:{containerUri}}` — custom image (advanced). |
| `environmentVariables` | map | String→string env vars injected into the session. |
| `authorizerConfiguration` | structure | Inbound auth — **`customJWTAuthorizer` only**. Omit for default IAM. |
| `maxIterations` / `maxTokens` / `timeoutSeconds` | integer | Plain ints (no wrapper on update). |
| `tags` | map | Accepted on **create**; on update use `TagResource`. |

There is **no top-level `network`, `lifecycle`, or `inferenceConfig`** field. Putting them at the top level is
rejected.

---

## Nesting

The console surfaces "Network", "Idle session timeout", "Max lifetime", and inference settings, but in the API they
are **nested**:

- **Network + lifecycle** → `environment.agentCoreRuntimeEnvironment`:
  ```json
  "environment": { "agentCoreRuntimeEnvironment": {
    "networkConfiguration": { "networkMode": "PUBLIC",
      "networkModeConfig": { "securityGroups": ["sg-..."], "subnets": ["subnet-..."], "requireServiceS3Endpoint": false } },
    "lifecycleConfiguration": { "idleRuntimeSessionTimeout": 900, "maxLifetime": 28800 },
    "filesystemConfigurations": []
  } }
  ```
  `networkMode` is required inside `networkConfiguration`; `networkModeConfig` (subnets/SGs) is only needed for VPC.
  Lifecycle values are in **seconds**.
- **Inference** (maxTokens/temperature/topP/apiFormat) → inside `model.bedrockModelConfig`. See `model-and-prompt.md`.
- **Truncation window** → `truncation.config.slidingWindow.messagesCount` (NOT a flat `slidingWindowMessagesCount`).
- **Inbound auth** → `authorizerConfiguration.customJWTAuthorizer` (omit entirely for IAM/SigV4 default).

---

## Best-practice defaults

| Setting | Recommended | Rationale |
|---|---|---|
| Model | `global.anthropic.claude-sonnet-5` (or `global.anthropic.claude-opus-5` for the hardest tasks) | inference profile → cross-region capacity |
| `model.bedrockModelConfig.apiFormat` | `converse_stream` | unified tool-use + streaming (enum: `converse_stream` / `responses` / `chat_completions`) |
| `maxIterations` / `maxTokens` / `timeoutSeconds` | 100 / 65536 / 1800 | multi-step work, large output, long sessions |
| `truncation` | `sliding_window`, `messagesCount` 150 | recency window, bounded cost |
| `allowedTools` | `["*"]` or plain names (`["browser","code_interpreter","skills"]`) | `browser_*` globs match NOTHING and hide the tool |
| network mode | `PUBLIC` | VPC only for private connectivity |
| lifecycle | idle 900s, maxLifetime 28800s | reclaim idle microVMs; 8h hard cap |
| inbound auth | omit (IAM/SigV4) | simplest secure default; JWT for end-users |
| memory `messagesCount` / `topK` / `relevanceScore` | 20 / 10 / 0.2 | recent window + broad recall (same defaults managed memory auto-derives) |
| tags | team, environment, cost-center, agent-type | governance + cost allocation |

---

## CreateHarness

```python
import boto3, secrets
c = boto3.client("bedrock-agentcore-control", region_name="us-east-1")
resp = c.create_harness(
    harnessName="MyHarness",
    executionRoleArn=role_arn,
    model={"bedrockModelConfig": {"modelId": "global.anthropic.claude-sonnet-5",
                                  "apiFormat": "converse_stream", "maxTokens": 65536, "temperature": 0.2}},
    systemPrompt=[{"text": SYSTEM_PROMPT}],
    tools=[...], allowedTools=["browser", "code_interpreter", "skills"], skills=[...],
    truncation={"strategy": "sliding_window", "config": {"slidingWindow": {"messagesCount": 150}}},
    environment={"agentCoreRuntimeEnvironment": {
        "networkConfiguration": {"networkMode": "PUBLIC"},
        "lifecycleConfiguration": {"idleRuntimeSessionTimeout": 900, "maxLifetime": 28800}}},
    maxIterations=100, maxTokens=65536, timeoutSeconds=1800,
    tags={"team": "qa-platform", "environment": "production"},
    clientToken=secrets.token_hex(20),
)
```

---

## Update payload rules

`UpdateHarness` takes `harnessId` plus the same fields minus `tags`. The `optionalValue` wrapper applies to ONLY
three fields (live-verified): `memory`, `environmentArtifact`, `authorizerConfiguration`. Everything else —
including the structures `model`, `environment`, and `truncation` — passes **directly**, as do lists/ints/strings
(`allowedTools`, `tools`, `skills`, `systemPrompt`, `maxTokens`, etc.). `tags` → separate `TagResource`.
`clientToken` ≥ 33 chars. Use `scripts/update_harness.py`, which introspects the live shape (a field wraps only if
its shape has an `optionalValue` member) and wraps correctly.

Every `UpdateHarness` creates a new immutable **version** — see `versioning.md` for endpoints/qualifiers and
production rollout.

---

## Tags

```python
c.tag_resource(resourceArn="arn:aws:bedrock-agentcore:us-east-1:<acct>:harness/<NAME>-<id>",
               tags={"team": "qa-platform", "environment": "production"})
```
`TagResource` exists and is idempotent for matching pairs.

---

## Execution role

The harness assumes `executionRoleArn`. It needs: a trust policy for `bedrock-agentcore.amazonaws.com`;
`bedrock:InvokeModel*` for the model; tool perms; **Memory data-plane perms per attached Memory ARN** (added by
`scripts/wire_memory.py`); and log-delivery perms for observability. Start from `assets/iam_execution_role.json`.

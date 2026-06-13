# Memory

AgentCore Memory is a **separate resource** from the harness. It gives the agent short-term context (recent messages)
and long-term knowledge (extracted records) that persist across sessions. Attaching it correctly is a **3-step**
process — the step most people miss is the IAM grant.

## Contents
- [Strategy types](#strategies)
- [retrievalConfig](#retrievalconfig)
- [The 3-step wiring](#three-step-wiring)
- [IAM grant + namespace conversion](#iam-grant)
- [actorId conventions](#actorid)

---

## Strategies

`CreateMemory.memoryStrategies` is a list; each item is a **union** over 5 types — exactly one key per item. The 4
strategies a rich agent typically uses (matching a real production harness) are Episodic, UserPreference,
Summarization, Semantic:

| Union key | Purpose | Required sub-fields |
|---|---|---|
| `semanticMemoryStrategy` | vector-similar past content (facts) | `name`, `namespaces`, `description` |
| `summaryMemoryStrategy` | compressed conversation summaries | `name`, `namespaces`, `description` |
| `userPreferenceMemoryStrategy` | per-actor preferences (auto-extracted) | `name`, `namespaces`, `description` |
| `episodicMemoryStrategy` | past sessions as discrete episodes | `name`, `namespaces`, `description`, **`reflectionConfiguration`** |
| `customMemoryStrategy` | bring-your-own (advanced) | `name`, `namespaces`, `description`, `customConfiguration` |

Notes:
- **`namespaces`** is a list of **strings** with `{actorId}` / `{sessionId}` placeholders, e.g.
  `["/episodes/{actorId}/{sessionId}"]`.
- **Episodic requires `reflectionConfiguration`** or validation fails. Minimum:
  `{"reflectionConfiguration": {"reflectionPrefix": "Episode summary:"}}` — the prefix marks each episode's start in
  the event stream.
- Adding strategies has a cost: each processes events in the background to extract long-term records.
- On `UpdateMemory`, strategy changes use `addMemoryStrategies` / `modifyMemoryStrategies` / `deleteMemoryStrategies` —
  not direct list assignment.

Example strategy set (4 strategies, matching the production anchor):

```python
memoryStrategies = [
  {"episodicMemoryStrategy": {"name": "Episodic", "namespaces": ["/episodes/{actorId}/{sessionId}"],
      "description": "Past test sessions as episodes",
      "reflectionConfiguration": {"reflectionPrefix": "Episode summary:"}}},
  {"userPreferenceMemoryStrategy": {"name": "Userpreference", "namespaces": ["/users/{actorId}/preferences"],
      "description": "Per-actor preferences"}},
  {"summaryMemoryStrategy": {"name": "Summarization", "namespaces": ["/summaries/{actorId}/{sessionId}"],
      "description": "Conversation summaries"}},
  {"semanticMemoryStrategy": {"name": "Semantic", "namespaces": ["/users/{actorId}/facts"],
      "description": "Durable facts"}},
]
```

`CreateMemory` **requires** `name` and `eventExpiryDuration` (an integer number of days, 3–365, after which raw memory
events expire). `memoryStrategies` is the union list above; `memoryExecutionRoleArn`, `encryptionKeyArn`, and
`indexedKeys` are optional. `scripts/wire_memory.py` passes `eventExpiryDuration` (default 90) — omitting it is a
validation error.

```python
control.create_memory(name="MyAgentMemory", eventExpiryDuration=90,
                      memoryStrategies=memoryStrategies, clientToken=secrets.token_hex(20))
```

---

## retrievalConfig

On the harness side, `agentCoreMemoryConfiguration` tells the harness which Memory to use, the actor, how many recent
messages to save, and how to retrieve long-term records per namespace:

```python
memory = {
  "agentCoreMemoryConfiguration": {
    "arn": "arn:aws:bedrock-agentcore:us-east-1:<acct>:memory/<id>",
    "actorId": "ci-pipeline",
    "messagesCount": 20,
    "retrievalConfig": {
      "/episodes/{actorId}/{sessionId}":  {"strategyId": "<EpisodicId>",      "topK": 10, "relevanceScore": 0.2},
      "/users/{actorId}/preferences":     {"strategyId": "<UserPrefId>",      "topK": 10, "relevanceScore": 0.2},
      "/summaries/{actorId}/{sessionId}": {"strategyId": "<SummarizationId>", "topK": 10, "relevanceScore": 0.2},
      "/users/{actorId}/facts":           {"strategyId": "<SemanticId>",      "topK": 10, "relevanceScore": 0.2}
    }
  }
}
```

- The field is **`strategyId`**, NOT `memoryStrategyId` (the API-ref name misleads; the validation error is the hint).
- Strategy ids come from the `CreateMemory` response (each created strategy gets an id like `..._Episodic-PV6UaxHitM`).
- `topK` 10 / `relevanceScore` 0.2 are broad-recall preview defaults; tighten for precision.
- On `UpdateHarness`, wrap the whole thing: `memory={"optionalValue": {"agentCoreMemoryConfiguration": {...}}}`.

---

## Three-step wiring

A working memory wiring is **not** "create + attach". It is:

| # | Step | API |
|---|---|---|
| 1 | Create the Memory (with the strategy set) | `bedrock-agentcore-control:CreateMemory` |
| 2 | Reference it from the harness | `bedrock-agentcore-control:UpdateHarness(memory={...})` |
| 3 | **Grant the harness execution role data-plane perms on the Memory ARN** | `iam:PutRolePolicy` |

Skip step 3 and **every** invocation fails at session start with `AccessDeniedException: ListEvents`.

`scripts/wire_memory.py` does all three idempotently.

---

## IAM grant

Step 3 grants two permission sets on the new Memory ARN:

| Action set | When needed | Example actions |
|---|---|---|
| Memory events (read+write) | every session start | `ListEvents`, `CreateEvent`, `GetEvent`, `ListSessions`, `ListActors` |
| Record retrieval | every start with `retrievalConfig` | `ListMemoryRecords`, `RetrieveMemoryRecords` (scoped by `bedrock-agentcore:namespace`) |

**Namespace conversion** for the retrieval condition — `retrievalConfig` keys use `{placeholder}` syntax; the IAM
`StringLike` condition needs glob form:

| Where | Format | Example |
|---|---|---|
| `retrievalConfig` keys | `{placeholder}` | `/episodes/{actorId}/{sessionId}` |
| IAM `StringLike` value | glob `*` | `/episodes/*/*` |

Convert via regex `\{[^}]+\}` → `*`. Convention: an inline policy named `<HarnessName>MemoryAccess`.

---

## actorId

`actorId` scopes memory. Conventions that work well:
- `ci-pipeline` — shared memory across CI runs
- `dev-{username}` — ad-hoc developer runs
- `repo-{owner}-{name}` — per-repository scoping (e.g. a bug-fix agent)
- `tenant-{tenantId}` — multi-tenant isolation

The actual `{actorId}`/`{sessionId}` values are bound at invocation time; the namespace templates above expand against
them.

# Knowledge Bases (RAG)

A **managed knowledge base** gives the agent retrieval over *your* documents. Two facts shape everything below:

1. **It is not a harness tool type.** `HarnessToolType` has exactly five members (`references/tools.md`) and none of
   them is a knowledge base. A KB reaches the agent as a **Gateway connector target** —
   `connectorId: bedrock-knowledge-bases` — which exposes two MCP tools, `Retrieve` and `AgenticRetrieveStream`.
2. **The KB resource itself lives on a different control plane.** You create it with `bedrock-agent` (not
   `bedrock-agentcore-control`) and query it with `bedrock-agent-runtime`. That is a third and fourth client on top of
   the AgentCore pair — new IAM actions (`bedrock:*`, not `bedrock-agentcore:*`) and a separate service role.

```
bedrock-agent            CreateKnowledgeBase(type=MANAGED) → CreateDataSource(S3) → StartIngestionJob
        │
        ▼  knowledgeBaseId
bedrock-agentcore-control  CreateGateway → CreateGatewayTarget(mcp.connector, bedrock-knowledge-bases)
        │
        ▼  gatewayArn
harness  tools:[{type: agentcore_gateway, ...}] + allowedTools:["@kb_gw/*"]   ← the agent's view
```

## Contents
- [Managed vs self-managed](#managed-vs-self-managed)
- [Build the knowledge base](#build-the-kb)
- [Ingest documents](#ingest)
- [Expose it through a Gateway](#expose)
- [What the agent sees (and how to widen it)](#agent-view)
- [IAM](#iam)
- [Query it directly (debugging)](#direct-query)
- [Pricing](#pricing)
- [End-to-end recipe](#recipe)
- [Gotchas](#gotchas)

---

## Managed vs self-managed

`KnowledgeBaseConfiguration.type` has four members: `VECTOR`, `KENDRA`, `SQL`, and — new for this wave —
**`MANAGED`**. Use `MANAGED` for agent RAG unless you already own a vector store:

| | `MANAGED` | `VECTOR` |
|---|---|---|
| Vector store | AWS-owned, created for you | **you** provide (`storageConfiguration`: OpenSearch Serverless, S3 Vectors, Pinecone, RDS, …) |
| Embedding model | `embeddingModelType: MANAGED` — no ARN to pick | `embeddingModelArn` **required** |
| Parsing / chunking | managed | you configure `vectorIngestionConfiguration` |
| Reranking | `rerankingModelType: MANAGED` available at query time | bring a reranking model |
| Setup cost | one `CreateKnowledgeBase` call | provision + index + field-mapping first |

---

## Build the KB

`CreateKnowledgeBase` required: **`name`, `roleArn`, `knowledgeBaseConfiguration`**.

```python
import boto3, secrets, time
ba = boto3.client("bedrock-agent", region_name="us-east-1")

kb = ba.create_knowledge_base(
    name="skilltest-kb",
    roleArn="arn:aws:iam::<ACCOUNT_ID>:role/service-role/skilltest-kb-role",   # trusts bedrock.amazonaws.com
    knowledgeBaseConfiguration={
        "type": "MANAGED",                                   # [req] — and the ONLY thing you must supply
        "managedKnowledgeBaseConfiguration": {               # optional; {} is accepted
            "embeddingModelType": "MANAGED",                 # optional, server-defaults to MANAGED
            # "embeddingModelArn": "...",                    # only when embeddingModelType == CUSTOM
            # "serverSideEncryptionConfiguration": {"kmsKeyArn": "..."},
        },
    },
    # NO storageConfiguration for MANAGED — verified 2026-08-13: not required on input, and
    # GetKnowledgeBase returns none either. The vector store is service-owned and invisible.
    clientToken=secrets.token_hex(20),
)
kb_id = kb["knowledgeBase"]["knowledgeBaseId"]

# Asynchronous. Status enum: CREATING | ACTIVE | UPDATING | DELETING | FAILED |
#                            DELETE_UNSUCCESSFUL | UPDATE_UNSUCCESSFUL
while (st := ba.get_knowledge_base(knowledgeBaseId=kb_id)["knowledgeBase"]["status"]) == "CREATING":
    time.sleep(5)
assert st == "ACTIVE", st
```

Verified 2026-08-13: `managedKnowledgeBaseConfiguration={}` is accepted and the server fills in
`embeddingModelType=MANAGED`. Neither the union member nor `embeddingModelType` is required, so **a MANAGED KB needs
literally no configuration beyond `type=MANAGED`** — which is the whole point of the type, and easy to miss while
copying a `VECTOR` example.

**Role-propagation race:** a freshly created `roleArn` produces `unable to assume role` for ~10–20 s. Retry
`CreateKnowledgeBase` on that message rather than treating it as a permissions bug.

---

## Ingest

`CreateDataSource` required: **`knowledgeBaseId`, `name`, `dataSourceConfiguration`**. The `type` enum has 8 members —
`S3`, `WEB`, `CONFLUENCE`, `SALESFORCE`, `SHAREPOINT`, `CUSTOM`, `REDSHIFT_METADATA`, and new for this wave
`MANAGED_KNOWLEDGE_BASE_CONNECTOR`.

> **A MANAGED knowledge base accepts only `MANAGED_KNOWLEDGE_BASE_CONNECTOR`.** Both `S3` and `CUSTOM` are refused
> synchronously with `Unsupported data source type for MANAGED knowledge base type.` (measured 2026-08-13). The
> `s3Configuration` member exists on the shape and is *unusable* here — so **every pre-existing Bedrock KB example you
> will find is the wrong shape for a MANAGED KB.** Your S3 bucket still supplies the documents; it is named inside
> `connectorParameters` instead.

```python
ds = ba.create_data_source(
    knowledgeBaseId=kb_id, name="s3-corpus",
    dataSourceConfiguration={
        "type": "MANAGED_KNOWLEDGE_BASE_CONNECTOR",
        "managedKnowledgeBaseConnectorConfiguration": {
            "connectorParameters": {                 # free-form Document — botocore validates NOTHING here
                "type": "S3",                        # [req] connector catalogue, NOT the enum above
                "version": "1",                      # [req] bare integer string — "1.0.0" is rejected
                "connectionConfiguration": {         # [req] shape depends on connector `type`
                    "bucketName": "my-corpus-bucket",           # bucket NAME, not an ARN
                    "bucketOwnerAccountId": "<ACCOUNT_ID>",
                },
            },
        },
    },
)
ds_id = ds["dataSource"]["dataSourceId"]

# Data-source creation is ASYNCHRONOUS too. Poll to a terminal status before ingesting.
while (dss := ba.get_data_source(knowledgeBaseId=kb_id,
                                 dataSourceId=ds_id)["dataSource"])["status"] == "CREATING":
    time.sleep(5)
assert dss["status"] == "AVAILABLE", dss.get("failureReasons")

job = ba.start_ingestion_job(knowledgeBaseId=kb_id, dataSourceId=ds_id)["ingestionJob"]
while job["status"] in ("STARTING", "IN_PROGRESS"):
    time.sleep(10)
    job = ba.get_ingestion_job(knowledgeBaseId=kb_id, dataSourceId=ds_id,
                               ingestionJobId=job["ingestionJobId"])["ingestionJob"]
if job["status"] != "COMPLETE":
    raise RuntimeError(job.get("failureReasons"))            # <- the real error lives HERE
print(job["statistics"])   # numberOfDocumentsScanned / ...NewDocumentsIndexed / ...DocumentsFailed / ...Skipped
```

### `connectorParameters` is a Document, so the service is your only validator

`connectorParameters` is declared with **no members at all**, so boto3 checks nothing and every mistake surfaces at the
service — some synchronously, some not. The errors are unusually good, and chaining them is the only way to learn the
schema. All verbatim, 2026-08-13:

| You send | You get |
|---|---|
| `{}` | `Connector type is required in connector parameters` |
| `connectorType` instead of `type` | *same message* — the key name is `type`, and the error does not say so |
| no `version` | `The 'version' field is required in connector parameters.` |
| `version: "1.0.0"` | `Invalid connector version '1.0.0'. Supported versions are: 1.` |
| `type: "BOGUS_XYZ"` | `Invalid connector type 'BOGUS_XYZ'. Supported types are: S3, ONEDRIVE, ZENDESK, SALESFORCE, BOX, DROPBOX, SHAREPOINT, GOOGLEDRIVE, WEB, CUSTOM, CONFLUENCEONPREM, CONFLUENCE, SERVICENOW.` |
| a valid `type` but no `connectionConfiguration` | **accepted, `CREATING`** → later `FAILED`, with `failureReasons: ["Value at 'connectionConfiguration' failed to satisfy constraint: Member must not be null"]` |

Four traps in that table:

- **`version` is a bare integer string here** (`"1"`), the *opposite* of the Gateway `ConnectorVersion`, which enforces
  strict 3-part semver. Same word, two grammars, one skill — do not carry the habit across.
- **`connectorParameters.type` has its own 13-member catalogue**, unrelated to the 8-member
  `dataSourceConfiguration.type` enum above, and spelled without separators (`CONFLUENCEONPREM`). The bogus-value error
  enumerates it verbatim — that error *is* the documentation.
- **Unknown and missing keys are accepted at create time.** A successful `CreateDataSource` means nothing; the failure
  arrives asynchronously in `GetDataSource(...)["dataSource"]["failureReasons"]`. And once it is `FAILED`,
  `StartIngestionJob` refuses: `You cannot start an ingestion job on a data source with status FAILED.`
- **`GetDataSource` echoes `connectorParameters` back as a JSON-encoded *string***, not a nested object, with
  server-injected defaults you never sent:

  ```python
  json.loads(ds["dataSourceConfiguration"]["managedKnowledgeBaseConnectorConfiguration"]["connectorParameters"])
  # {"type": "S3", "connectionConfiguration": {...},
  #  "filterConfiguration": {"maxFileSizeInMegaBytes": "500"}, "aclEnabled": false, "version": "1"}
  ```

  So round-tripping a `GetDataSource` response into `UpdateDataSource` needs a `json.loads` first, or you send a string
  where a Document is expected.

**Ingestion failures do not raise on create either.** `StartIngestionJob` returns happily; a missing S3 permission,
an unsupported file type, or (most often) **Bedrock model access not enabled for the managed embedding model** shows
up only as `status == "FAILED"` plus `failureReasons` on `GetIngestionJob`. Always read `statistics` too — a job can
be `COMPLETE` with `numberOfNewDocumentsIndexed == 0` and retrieval will then return nothing. A healthy small run:

```python
{'numberOfDocumentsScanned': 3, 'numberOfNewDocumentsIndexed': 3,
 'numberOfDocumentsFailed': 0, 'numberOfDocumentsSkipped': 0}
```

Job status enum: `STARTING | IN_PROGRESS | COMPLETE | FAILED | STOPPING | STOPPED`.

---

## Expose

The gateway side is one `mcp.connector` target (full leaf shape in `references/gateway.md` §Targets →
`mcp.connector`). The KB id is bound **here, by the administrator** — configuration is target-level, so the agent
never sees or sends a `knowledgeBaseId`.

```python
c = boto3.client("bedrock-agentcore-control", region_name="us-east-1")
t = c.create_gateway_target(
    gatewayIdentifier=gateway_id, name="kb",
    targetConfiguration={"mcp": {"connector": {
        "source": {"connectorId": "bedrock-knowledge-bases"},
        "configurations": [
            {"name": "Retrieve", "parameterValues": {"knowledgeBaseId": kb_id}},
            {"name": "AgenticRetrieveStream", "parameterValues": {
                "retrievers": [{"configuration": {"knowledgeBase": {"knowledgeBaseId": kb_id}}}],
                "agenticRetrieveConfiguration": {            # MUST be present; {} is valid
                    "foundationModelType": "MANAGED",
                    "rerankingModelType": "NONE",            # CUSTOM | MANAGED | NONE
                    "maxAgentIteration": 3,
                },
            }},
        ],
    }}},
    credentialProviderConfigurations=[{"credentialProviderType": "GATEWAY_IAM_ROLE"}],   # only type accepted
    clientToken=secrets.token_hex(20),
)
# Poll GetGatewayTarget to READY (~30 s). A wrong knowledgeBaseId or missing IAM shows up as
# FAILED + statusReasons here, NOT as an exception above.
```

- **Expose only what you need.** One `configurations` entry per tool; drop the `AgenticRetrieveStream` entry to give
  the agent plain vector search only. `configurations` must be non-empty either way.
- **`AgenticRetrieveStream` requires all three of `retrievers`, `agenticRetrieveConfiguration`, and `messages`.**
  `messages` comes from the caller at request time; the other two must be in `parameterValues`.
  `agenticRetrieveConfiguration` itself has **no required members**, so `{}` is both mandatory and sufficient —
  omitting the key is a client-side `ParamValidationError`, passing `{}` works. An author reading only the required
  list cannot tell the cheap default exists, which matters because every knob inside it is billable.
- **A `configurations` entry carrying only `retrievers` reaches `READY`, then fails at invoke time** with
  **HTTP 200 and `isError=True`** (measured 2026-08-13). The control plane validates shape, not completeness, and gives
  no warning at all. **Validate connector `parameterValues` by calling the tool, never by reading target status.**

---

## Agent view

Two tools, target-qualified. **Confirmed on the wire 2026-08-13**: with a target named `kb`, `tools/list` against
`gatewayUrl` advertises exactly `['kb___AgenticRetrieveStream', 'kb___Retrieve']` — **three** underscores, target name
first, and the connector's own tool name keeps its exact casing. A hyphen in the target name is carried through
verbatim (`skilltest-partial-agentic___AgenticRetrieveStream`).

**But do not put those names in `allowedTools`.** The harness allowlist wants the prefixed form
`@<harness-tool-name>/*` — measured, `allowedTools=["kb___Retrieve"]` filters the tool out **silently** and the agent
behaves like it is hallucinating. See `references/gateway.md` §Wire for the full trap.

| Tool | Shape | Cost signal |
|---|---|---|
| `Retrieve` | one-shot vector search; agent sends `retrievalQuery.text` | 1 retrieval per call |
| `AgenticRetrieveStream` | planner loop that decomposes the question and issues several retrievals; agent sends `messages` | 1 agentic call **plus** each underlying retrieval — cap it with `maxAgentIteration` |

**The agent-visible schema is deliberately minimal** (essentially `retrievalQuery.text` / `messages`) because every
other parameter is administrator-bound. To let the agent control more — a metadata `filter`, `numberOfResults` — widen
it per parameter with `parameterOverrides` on the connector configuration:

```python
{"name": "Retrieve", "parameterValues": {"knowledgeBaseId": kb_id},
 "parameterOverrides": [
     {"path": "$.retrievalConfiguration.managedSearchConfiguration.numberOfResults",   # JSONPath
      "description": "How many passages to return (1-10)", "visible": True},
 ]}
```

**`path` is JSONPath (`$.a.b.c`), not JSON Pointer.** AWS shows both forms in different places; only JSONPath is
accepted. Measured 2026-08-13 — the JSON Pointer form `/retrievalConfiguration/managedSearchConfiguration/...` is
rejected with `Connector target validation failed: Configuration 'Retrieve': parameterOverride path '/...'`.

Three behaviours worth knowing before you rely on this, all measured:

- **An override widens a *path*, not a field.** The gateway reconstructs the entire path as nested schema objects —
  `properties.retrievalConfiguration.properties.managedSearchConfiguration.properties.numberOfResults` — so the agent
  must emit the **full nested object**, not a top-level `numberOfResults`. The sibling leaves of
  `managedSearchConfiguration` (`filter`, `rerankingConfiguration`, `rerankingModelType`) stay hidden, so widening one
  leaf leaks nothing else. `required[]` is untouched: every widened field is optional.
- **`visible` defaults to `false`.** It is optional, and omitting it leaves the field hidden — so an override that
  supplies only a `description` is a **no-op on visibility**. `visible: False` is the documented way to *hide* a field
  the connector exposes by default; to reveal one you must say `visible: True` explicitly.
- **A widened field is genuinely honoured, not cosmetic.** A `tools/call` supplying the full nested object with
  `numberOfResults=1` returned HTTP 200, `isError=False`, and the value reached the underlying `Retrieve`. Which means
  **widening a cost-bearing field hands the agent control of that cost** — `numberOfResults` and anything reranking-
  related are billable knobs, so widen deliberately.

---

## IAM

**The KB permissions go on the *gateway* execution role, not the harness execution role.** This is the most common
mistake: `assets/iam_execution_role.json` is the harness's role and adding `bedrock:Retrieve` there changes nothing,
because it is the gateway that calls the knowledge base.

Two distinct roles:

| Role | Trusts | Needs |
|---|---|---|
| **KB service role** (`roleArn` on `CreateKnowledgeBase`) | `bedrock.amazonaws.com` | `s3:GetObject` + `s3:ListBucket` on the corpus bucket; KMS if encrypted |
| **Gateway role** (`roleArn` on `CreateGateway`) | `bedrock-agentcore.amazonaws.com` | the three actions below |

```jsonc
{"Version": "2012-10-17", "Statement": [
  {"Effect": "Allow",
   "Action": ["bedrock:GetKnowledgeBase", "bedrock:Retrieve"],
   "Resource": "arn:aws:bedrock:us-east-1:<ACCOUNT_ID>:knowledge-base/<KB_ID>"},
  {"Effect": "Allow",
   "Action": "bedrock:AgenticRetrieveStream",
   "Resource": "*"}          // cannot be resource-scoped — see below
]}
```

- **`bedrock:AgenticRetrieveStream` supports no resource-level scoping**; it must be granted on `*`. If your account
  has a permission boundary or SCP requiring resource-level constraints, this statement is silently dropped and you
  get an `AccessDeniedException` at invoke time with no hint that the boundary caused it. Check with
  `aws iam simulate-principal-policy` before blaming the connector.
- **The gateway role does NOT need `bedrock-agentcore:InvokeGateway` — settled by test, 2026-08-13.** AWS contradicts
  itself here (the KB connector page says the caller needs it; the web-search connector page lists it on the gateway
  role). A role holding **only** the three `bedrock:*` actions above created the gateway, brought the KB connector
  target to `READY`, served `tools/list`, and completed a full retrieval round trip through a harness. `InvokeGateway`
  is a permission for the **caller identity**; the page that puts it on the execution role is wrong. Granting it there
  anyway is harmless but misleading — leave it out so the role documents what actually matters.
- The **caller** of the gateway needs `bedrock-agentcore:InvokeGateway` on your `gateway/*` — for a
  harness-mediated call that is the harness execution role.

---

## Direct query

When retrieval misbehaves, query the data plane directly to separate a corpus/IAM problem from a connector problem:

```python
rt = boto3.client("bedrock-agent-runtime", region_name="us-east-1")

rt.retrieve(knowledgeBaseId=kb_id,                                     # required: knowledgeBaseId, retrievalQuery
            retrievalQuery={"text": "what is the torque spec"},         # or {"type":"IMAGE","image":{...}}
            retrievalConfiguration={"managedSearchConfiguration": {
                "numberOfResults": 3, "rerankingModelType": "NONE"}})   # MANAGED KB -> managedSearchConfiguration
                                                                       # (VECTOR KB -> vectorSearchConfiguration)

resp = rt.agentic_retrieve_stream(
    retrievers=[{"configuration": {"knowledgeBase": {"knowledgeBaseId": kb_id}}}],
    agenticRetrieveConfiguration={"foundationModelType": "MANAGED", "rerankingModelType": "NONE",
                                  "maxAgentIteration": 2},              # 2 is the MINIMUM, not 1
    messages=[{"role": "user", "content": {"text": "what is the torque spec"}}],
)
for event in resp["stream"]:        # event union: result | responseEvent | traceEvent | *Exception
    print(event)
```

**`vectorSearchConfiguration` is rejected against a MANAGED KB** — and it is the only leaf that existed before MANAGED
knowledge bases, so it is what every pre-existing example uses (measured 2026-08-13):

```
Incompatible configuration: vectorSearchConfiguration is not supported for managed knowledge bases.
Use managedSearchConfiguration instead.
```

`managedSearchConfiguration` carries only `filter`, `numberOfResults`, `rerankingConfiguration` and
`rerankingModelType` — **no `overrideSearchType`** and no `implicitFilterConfiguration`. So on a MANAGED KB you cannot
choose `HYBRID` vs `SEMANTIC` search; that knob does not exist. If search-type control is a requirement, you need a
`VECTOR` KB.

**`maxAgentIteration` has a minimum of 2.** Pinning `1` to cap cost is a client-side `ParamValidationError`, so the
cheapest legal agentic retrieval still runs two planner iterations. Budget accordingly — the floor is not the free tier
you might assume.

`agentic_retrieve_stream` returns an **event stream**, and the modelled errors (`accessDeniedException`,
`validationException`, `throttlingException`, …) arrive as *events inside the stream*, not as raised exceptions —
a `try/except` around the call will not catch them.

---

## Pricing

Managed knowledge bases charge for storage and per retrieval; the managed parsing, embedding and reranking models
are included:

| Item | Price |
|---|---|
| Index storage | **$5 per GB-month** |
| `Retrieve` | **$1 per 1,000** calls |
| `AgenticRetrieveStream` | **$4 per 1,000** calls, **plus $1 per 1,000** underlying retrievals it issues |
| Managed parsing / embedding / reranking | no additional charge |

Agentic retrieval is therefore ~4× a plain retrieval *before* its fan-out — `maxAgentIteration` is a cost control,
not just a latency control. The published pricing gives no minimum billable index size, so treat a short-lived test
KB's storage cost as unknown-but-small and set a budget alarm rather than trusting an estimate.

---

## Recipe

1. **Role** — create the KB service role (trust `bedrock.amazonaws.com`, `s3:GetObject`/`ListBucket` on the corpus).
2. **Corpus** — upload documents to S3. For testing, put a unique sentinel fact in each file so a single query proves
   retrieval actually happened rather than the model recalling something.
3. **KB** — `CreateKnowledgeBase(type=MANAGED)` → poll `ACTIVE`.
4. **Ingest** — `CreateDataSource(MANAGED_KNOWLEDGE_BASE_CONNECTOR)` → poll to `AVAILABLE` →
   `StartIngestionJob` → poll `COMPLETE` → check `statistics`.
5. **Gateway** — `CreateGateway` (its role carrying the three `bedrock:*` actions) → `CreateGatewayTarget`
   (`mcp.connector`, `bedrock-knowledge-bases`) → poll `READY` → `tools/list` to read the real tool names.
6. **Harness** — add `{"type": "agentcore_gateway", "name": "kb_gw", "config": {"agentCoreGateway":
   {"gatewayArn": ...}}}` and allowlist `@kb_gw/*` (the **harness tool name**, and note `harnessName` itself rejects
   hyphens — see `references/harness-config.md`). Ask a question whose answer is only in the corpus.

Teardown order: gateway rate limits → gateway targets (**including `FAILED` ones**) → gateway → ingestion jobs (stop
any `IN_PROGRESS`) → data source → knowledge base → S3 objects → bucket → roles. Most of these deletes are
asynchronous and refuse while a neighbour settles, so retry on `ConflictException` and re-`list` to confirm rather
than trusting a successful delete call.

---

## Gotchas

- **A KB is not `tools[].type`.** Anything that looks like `{"type": "knowledge_base"}` is invalid; the union is
  fixed at five members.
- **Memory ≠ Knowledge Base.** See `references/memory.md` — Memory is per-actor conversational state on
  `bedrock-agentcore`; a KB is a shared document corpus on `bedrock-agent` reached through a gateway.
- **The agent never passes a `knowledgeBaseId`.** If you find yourself wanting it to, you want several targets (or
  several `configurations` entries), not an agent-supplied id.
- **Ingestion errors hide in `failureReasons`**, and a `COMPLETE` job can still have indexed zero documents.
- **A MANAGED KB rejects `S3` and `CUSTOM` data sources** — only `MANAGED_KNOWLEDGE_BASE_CONNECTOR`, with the bucket
  named inside the untyped `connectorParameters` Document. Every older Bedrock KB example is the wrong shape.
- **`vectorSearchConfiguration` is rejected on a MANAGED KB** — use `managedSearchConfiguration`, and accept that
  `overrideSearchType` (HYBRID/SEMANTIC) is not available at all.
- **`maxAgentIteration` cannot be 1.** The minimum is 2, so agentic retrieval has a hard cost floor of two iterations.
- **Two `version` grammars.** `connectorParameters.version` is a bare integer string (`"1"`); the Gateway connector
  `source.version` is strict 3-part semver (`"1.2.0"`). Neither accepts the other's form.
- **`parameterOverrides[].path` is JSONPath**, it widens a whole nested path rather than a single top-level field, and
  `visible` defaults to `false` — so a description-only override reveals nothing.
- **`READY` proves nothing about a connector's `parameterValues`.** A half-configured `AgenticRetrieveStream` entry
  reaches `READY` and returns `isError=True` at invoke time. Test by calling the tool.
- **`DeleteKnowledgeBase` while an ingestion job is `IN_PROGRESS` raises `ConflictException`** — stop the job first.
  Managed vector-index deletion is asynchronous, so re-`list` to confirm teardown instead of trusting the delete call.
- **Region coverage is not the same as the harness's.** Do not assume KB connector availability matches the ~16
  regions where Harness runs, or that it matches web-search (us-east-1 only). Check the region you are in.
- **Reranking defaults are not free.** `rerankingModelType` accepts `MANAGED`, which invokes a managed reranker on
  every retrieval; pin `NONE` unless you have measured that you need it.

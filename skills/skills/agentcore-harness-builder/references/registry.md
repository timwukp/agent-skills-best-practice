# Agent Registry

The **AWS Agent Registry** is a centralized catalog for discovering and managing **agents, MCP servers,
tools, and skills** across an organization. Use it to make a finished harness (and its skills/tools) discoverable and
governed, rather than tribal knowledge.

> **Relaunched 2026-08-06 under its own namespace.** Registry is no longer part of `bedrock-agentcore-control`.
> It now has its own control plane (`agent-registry-control`) and data plane (`agent-registry`), its own IAM prefix
> (`agent-registry:`), and different request shapes. **The old `bedrock-agentcore-control` registry operations are
> scheduled to stop working 2026-09-17.** If you have code written before this date, read
> [§Migration from the legacy namespace](#migration) first — the field names changed, not just the client.

## Contents
- [What it's for](#what-its-for)
- [Namespace, clients and IAM](#namespace)
- [How it works (3 steps)](#how-it-works)
- [API surface](#api-surface)
- [Record shapes](#record-shapes)
- [Executable example](#example)
- [Discovery (data plane)](#discovery)
- [Migration from the legacy namespace](#migration)
- [Gotchas](#gotchas)

---

## What it's for

- **Discover** resources org-wide via semantic search and filters.
- **Manage** agents, MCP servers, tools, and skills in one place.
- **Govern** what gets published through approval workflows and IdP-backed authorization.

Use it in **Phase 8 (govern)**, after the harness is built, verified, and (ideally) evaluated/optimized:
publish the **harness/agent** so other teams can discover and reuse it; publish reusable **skills** (e.g. a
`ui-testing` skill) and **MCP servers/tools** so they're shared rather than re-implemented; route publication
through the **approval workflow** if your org requires review before a resource is broadly discoverable.

---

## Namespace

Two clients, both `apiVersion 2025-12-01`, both signing as `agent-registry`:

```python
import boto3
ctl  = boto3.client("agent-registry-control", region_name="us-east-1")  # create/update/approve  (15 ops)
disc = boto3.client("agent-registry",         region_name="us-east-1")  # search/discover only    (3 ops)
```

- **boto3/botocore ≥ 1.43.66** is required — that is the first release carrying an `agent-registry*` client at all
  (1.43.65 and older raise `UnknownServiceError`; verified by wheel-diffing 1.43.55 → 1.43.66). Check with
  `python scripts/preflight.py --service agent-registry-control`.
- **IAM actions use the `agent-registry:` prefix**, not `bedrock-agentcore:`. The managed policy is
  **`AgentRegistryFullAccess`**; AWS states `BedrockAgentCoreFullAccess` will **not** be updated to cover Registry, so
  an otherwise fully-permissioned AgentCore principal will get `AccessDeniedException` until you attach it.
- Resource ARNs are `arn:aws:agent-registry:<region>:<account>:registry/<id>` and
  `.../registry/<id>/record/<recordId>` (registry id 12–16 chars, record id exactly 12).
- Registry is region-scoped and, per AWS, still evolving — provide feedback via the console's feedback link.
- The two planes have **separate API references**:
  [control](https://docs.aws.amazon.com/agent-registry-control/latest/APIReference/Welcome.html) ·
  [data](https://docs.aws.amazon.com/agent-registry/latest/APIReference/Welcome.html).

---

## How it works

1. **Create a registry** — the org's catalog. Set `discoveryConfiguration` (IdP/authorizer for who may discover) and
   `approvalConfiguration` (whether records auto-approve).
2. **Add records** — one record per agent / MCP server / tool / skill, then submit for approval per the workflow.
3. **Discover** — consumers use the **data plane** (`agent-registry`) to list, batch-get, and semantically search
   records. Only records that passed approval are discoverable.

A record carries: name, displayName, description, `recordType`, `descriptors` (the payload), `recordVersion`, status,
statusReason, created/updated timestamps, and the registry/record ARNs.

---

## API surface

*(verified against the botocore 1.43.68 service model)*

**Control plane `agent-registry-control` (15 ops)** — `CreateRegistry`, `GetRegistry`, `UpdateRegistry`,
`DeleteRegistry`, **`ListRegistries`**, `CreateRegistryRecord`, `GetRegistryRecord`, `ListRegistryRecords`,
`UpdateRegistryRecord`, `UpdateRegistryRecordStatus`, `SubmitRegistryRecordForApproval`, `DeleteRegistryRecord`,
**`TagResource`**, **`UntagResource`**, **`ListTagsForResource`** (the bolded five are new in this namespace).

**Data plane `agent-registry` (3 ops)** — `ListDiscoverableRegistryRecords`,
`BatchGetDiscoverableRegistryRecord`, `SearchDiscoverableRegistryRecords` (semantic search).

`CreateRegistry` input: `name` **[req]** (`[1..64]`), `description`, `discoveryConfiguration`,
`approvalConfiguration`, `clientToken`, `tags`.

```python
discoveryConfiguration = {
    "authorizerType": "CUSTOM_JWT",   # CUSTOM_JWT | AWS_IAM
    "authorizerConfiguration": {"customJWTAuthorizer": {
        "discoveryUrl": "https://<idp>/.well-known/openid-configuration",   # [req], pattern-enforced
        "allowedAudience": ["..."], "allowedClients": ["..."], "allowedScopes": ["..."],
        # customClaims[], privateEndpoint (VPC Lattice / managed VPC), privateEndpointOverrides[] also available
    }},
}
approvalConfiguration = {"autoApprovalRules": ["APPROVE_ALL"]}   # list, 0..10; only APPROVE_ALL exists today
```

Re-introspect before scripting anything not shown here:

```bash
python scripts/preflight.py --service agent-registry-control \
    --show-shape CreateRegistry --show-shape CreateRegistryRecord
```

---

## Record shapes

`CreateRegistryRecord` required: **`registryId`, `name`, `recordType`, `descriptors`**.
`recordType` enum: **`MCP | AGENT | CUSTOM | SKILL`**. Optional: `displayName`, `description`, `recordVersion`,
`clientToken`, `tags`.

`descriptors` is a four-key structure — populate **exactly one** key, matching your `recordType`:

| key | payload | notes |
|---|---|---|
| `mcpServer` | `{data, dataSchemaVersion, additionalData:{tools:{data, dataSchemaVersion}}, source}` | MCP server definition (+ optional tool list) |
| `a2aAgentCard` | `{data, dataSchemaVersion, source}` | A2A agent card |
| `agentSkillsDefinition` | `{data, dataSchemaVersion, additionalData:{skillMd:{data, dataSchemaVersion, source}}}` | the skill definition, with the raw `SKILL.md` under `additionalData.skillMd.data` |
| `custom` | `{data}` | free-form; **no** `dataSchemaVersion` |

- Every payload lives in a **`data`** string (max **102,400** chars) and is marked **sensitive** in the model — it will
  not appear in SDK debug logs, and you should not put credentials in it.
- Instead of inlining, most descriptors accept **`source: {"fromUrl": {"url": "https://...",
  "credentialProviderConfigurations": [...]}}`** to fetch the payload from an HTTPS URL (private URLs via an Identity
  credential provider — see `identity.md`).
- `UpdateRegistryRecord` uses an explicit-clear wrapper: each updatable field is nested one level deeper as
  `{"optionalValue": <value>}` (e.g. `descriptors={"optionalValue": {"agentSkillsDefinition": {...}}}`). Omit a field
  to leave it alone; send `{"optionalValue": None}`-style clearing only where the API documents it. `UpdateRegistry`
  wraps `description` and `approvalConfiguration` the same way.

---

## Example

*(**live-verified end to end 2026-08-13** — create → poll → record → submit → approve → all three data-plane reads →
teardown, both namespaces. Per-case log: C3-T2.13 in `TEST_LOG.md`.)*

> **Before your first `CreateRegistry` in an account:** the caller needs **`iam:CreateServiceLinkedRole` for
> `agent-registry.amazonaws.com`**. The first call in an account also creates that SLR and fails without the grant:
>
> ```
> AccessDeniedException: Unable to create the service-linked role required for this registry. Ensure the
> caller has iam:CreateServiceLinkedRole permission for agent-registry.amazonaws.com
> ```
>
> This is **not** in `AgentRegistryFullAccess` and is not mentioned on the Registry pages, so it reads like a service
> fault rather than a missing grant. The SLR (`AWSServiceRoleForAgentRegistry`) persists after you delete the registry.

```python
import boto3, secrets, time
ctl = boto3.client("agent-registry-control", region_name="us-east-1")

# 1) Create the registry. The response returns only registryArn (NO registryId) —
#    derive the id from the ARN's last path segment.
reg = ctl.create_registry(
    name="my-org-registry", description="org agent registry",
    approvalConfiguration={"autoApprovalRules": ["APPROVE_ALL"]},
    clientToken=secrets.token_hex(20),          # min length 33 -> token_hex(20) = 40 chars
)
registry_id = reg["registryArn"].rsplit("/", 1)[-1]

# 2) A registry becomes READY asynchronously. CreateRegistryRecord rejects a registry that is
#    still CREATING, so wait. Status enum: CREATING|READY|UPDATING|CREATE_FAILED|UPDATE_FAILED|
#    DELETING|DELETE_FAILED — "READY" is the only success state (do not also accept ACTIVE).
for _ in range(24):
    st = ctl.get_registry(registryId=registry_id)["status"]
    if st == "READY":
        break
    if st.endswith("FAILED"):
        raise RuntimeError(st)
    time.sleep(5)

# 3) Register this skill. recordType and descriptors are both REQUIRED.
rec = ctl.create_registry_record(
    registryId=registry_id,
    name="agentcore-harness-builder",
    recordType="SKILL",
    descriptors={"agentSkillsDefinition": {
        "additionalData": {"skillMd": {"data": open("SKILL.md").read()}}   # <= 102400 chars
    }},
    clientToken=secrets.token_hex(20),
)
record_id = rec["recordArn"].rsplit("/", 1)[-1]     # 12 chars; rec["status"] is CREATING (HTTP 202)

# MCP server:  recordType="MCP",    descriptors={"mcpServer":     {"data": "<json>"}}
# A2A agent:   recordType="AGENT",  descriptors={"a2aAgentCard":  {"data": "<json>"}}
# Anything:    recordType="CUSTOM", descriptors={"custom":        {"data": "<json>"}}

# 4) The RECORD is asynchronous too — 202 + CREATING, ~5 s to DRAFT. Until it settles, EVERY other
#    record op (submit AND delete) fails: ConflictException "Registry record cannot be modified
#    while in CREATING state." So the straight-line create->submit sequence needs a poll here.
for _ in range(24):
    st = ctl.get_registry_record(registryId=registry_id, recordId=record_id)["status"]
    if st != "CREATING":
        break
    time.sleep(2)

# 5) Approval. Under autoApprovalRules=["APPROVE_ALL"] the submit call is STILL required — a DRAFT
#    record is not discoverable — but it lands directly in APPROVED, one step.
ctl.submit_registry_record_for_approval(registryId=registry_id, recordId=record_id)

# Only needed on a registry WITHOUT an auto-approval rule; redundant under APPROVE_ALL.
# ctl.update_registry_record_status(registryId=registry_id, recordId=record_id,
#                                  status="APPROVED", statusReason="reviewed by platform team")
```

Observed status path for a `SKILL` record under `APPROVE_ALL` (measured): `CREATING` → `DRAFT` →
*(submit)* → `APPROVED`.

Cleanup order: `delete_registry_record(registryId=..., recordId=...)` **then**
`delete_registry(registryId=...)` — and poll the record out of `CREATING` first, or the delete is refused and the
registry cannot be deleted either. `DeleteRegistry` is likewise asynchronous: re-`list_registries` to confirm rather
than trusting the call.

---

## Discovery

Consumers read through the `agent-registry` data plane, which only exposes approved records. **All three operations
answered live 2026-08-13** with the argument shapes below:

```python
disc = boto3.client("agent-registry", region_name="us-east-1")

disc.list_discoverable_registry_records(
    registryId=registry_id,
    filters=[{"name": "recordType", "values": ["SKILL"]}],     # filter names: recordType | descriptorType
)

disc.search_discoverable_registry_records(
    searchQuery="browser automation testing",                   # semantic; [0..256], sensitive
    registryIds=[registry_id],                                  # EXACTLY ONE id per call (list min=1 max=1)
    maxResults=10,
)

disc.batch_get_discoverable_registry_record(
    entries=[{"registryId": registry_id, "recordIds": [record_id]}],   # exactly ONE entry, up to 100 recordIds
)
```

`ListDiscoverableRegistryRecords` returns records **without** `descriptors` (metadata only) — use
`BatchGetDiscoverableRegistryRecord` or `SearchDiscoverableRegistryRecords` when you need the payload.
Control-plane `ListRegistryRecords` filters on `name | status | recordType`; `ListRegistries` filters on
`status | discoveryConfiguration.authorizerType`. Every filter's `values` list holds **exactly one** value —
to match several values, send several filter entries.

---

## Migration

**Dated migration note — legacy `bedrock-agentcore-control` registry ops shut down 2026-09-17.**
Both namespaces coexist today (botocore 1.43.68 still carries the 11 legacy ops), so migrate before the deadline.
Six things changed; renaming the client alone is **not** enough:

| # | Legacy (`bedrock-agentcore-control`, pre-2026-08-06) | New (`agent-registry-control`) |
|---|---|---|
| 1 | `boto3.client("bedrock-agentcore-control")`; IAM `bedrock-agentcore:*` | `agent-registry-control` + `agent-registry`; IAM **`agent-registry:*`**, policy `AgentRegistryFullAccess` |
| 2 | `descriptorType` **required**, enum `MCP\|A2A\|CUSTOM\|AGENT_SKILLS` | field **removed**; use **`recordType`** (required), enum `MCP\|AGENT\|CUSTOM\|SKILL`. `descriptorType` survives only as a data-plane *filter name* |
| 3 | `descriptors.{mcp{server,tools}, a2a{agentCard}, agentSkills{skillMd,skillDefinition}, custom{inlineContent}}` | `descriptors.{mcpServer, a2aAgentCard, agentSkillsDefinition, custom}` |
| 4 | payload key `inlineContent` | payload key **`data`** (+ `dataSchemaVersion`) |
| 5 | `CreateRegistry(authorizerType=..., authorizerConfiguration=...)` at top level | both nested under **`discoveryConfiguration`** |
| 6 | `approvalConfiguration={"autoApproval": True}` (boolean) | `approvalConfiguration={"autoApprovalRules": ["APPROVE_ALL"]}` (list) |

Also gone: `synchronizationType` / `synchronizationConfiguration` on records. Also renamed: the data-plane search
op was `SearchRegistryRecords` on `bedrock-agentcore`; it is now **`SearchDiscoverableRegistryRecords`** on
`agent-registry`, joined by `ListDiscoverableRegistryRecords` and `BatchGetDiscoverableRegistryRecord`.
New capability: `ListRegistries` and resource tagging (`tags` on create + `TagResource`/`UntagResource`/
`ListTagsForResource`).

AWS's own documentation is inconsistent about whether the relaunched Registry is GA or still Preview (the console
badges it **Preview**), so treat availability as region-limited and re-introspect rather than assuming parity with
Harness. Do not build a hard dependency on it in a production path yet.

---

## Gotchas

1. **`CreateRegistry` returns only `registryArn`** — no `registryId`. Derive it: `arn.rsplit("/", 1)[-1]`.
   (`GetRegistry` *does* return `registryId`.)
2. **The registry must reach `READY` before `CreateRegistryRecord`**, else `ConflictException`. Poll `GetRegistry`;
   `READY` is the only success state — the enum has no `ACTIVE`/`AVAILABLE`.
3. **`UpdateRegistryRecordStatus` requires `statusReason`** (`[0..255]`) alongside `status`. It is easy to miss
   because it is the only status API in AgentCore that demands a reason string.
4. **`clientToken` has a minimum length of 33.** `secrets.token_hex(16)` (32 chars) is rejected — use `token_hex(20)`.
5. **Descriptor payloads are capped at 102,400 characters** and marked *sensitive*. A large `SKILL.md` bundle will
   not fit; register the definition and point at the bundle via `source.fromUrl`.
6. **`searchQuery` takes exactly one `registryIds` entry** — you cannot search across registries in one call.
7. **`AgentRegistryFullAccess` is a separate managed policy.** `BedrockAgentCoreFullAccess` does not grant
   `agent-registry:*`, and AWS has said it will not be updated to. **It is also not sufficient on its own** — the first
   `CreateRegistry` in an account additionally needs `iam:CreateServiceLinkedRole` for
   `agent-registry.amazonaws.com` (see §Example).
8. **`CreateRegistryRecord` is asynchronous** — HTTP 202 + `CREATING`, ~5 s to `DRAFT`. Submit *or* delete during that
   window raises `ConflictException: Registry record cannot be modified while in CREATING state.` Both the happy path
   and teardown need a poll.
9. **`APPROVE_ALL` does not skip the submit call.** A `DRAFT` record is not discoverable; you must still call
   `SubmitRegistryRecordForApproval`, which then lands the record directly in `APPROVED`. The explicit
   `UpdateRegistryRecordStatus(APPROVED)` is redundant under auto-approval — reserve it for registries without a rule.
10. **Discoverable listings are metadata-only.** `ListDiscoverableRegistryRecords` returned the approved record with
    **no descriptors**; fetch payloads with `BatchGetDiscoverableRegistryRecord`.
11. **The legacy namespace still works today**, so nothing breaks until it is switched off —
    `bedrock-agentcore-control.CreateRegistry` still succeeds (verified 2026-08-13, returning only `registryArn`). The
    **2026-09-17 shutdown is the only forcing function**; there is no deprecation signal in the SDK or in any error
    message. See §Migration.

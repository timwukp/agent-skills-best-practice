# Policy

AgentCore **Policy** (shown as "New" in the console) governs what agents are allowed to do — guardrails and
permissions enforced by a **policy engine**, plus resource policies and an automated policy-generation flow. A rich set
of operations exists in `bedrock-agentcore-control`.

## Building blocks (verified operations)

| Concept | Operations | Purpose |
|---|---|---|
| **Policy** | `CreatePolicy`, `GetPolicy`, `GetPolicySummary`, `ListPolicySummaries`, `UpdatePolicy`, `DeletePolicy` | A policy document governing agent behavior/permissions. Stateless (Cedar) or **temporal** (stateful, session-aware — see below). |
| **Policy Engine** | `CreatePolicyEngine`, `GetPolicyEngine`, `GetPolicyEngineSummary`, `ListPolicyEngines`, `ListPolicyEngineSummaries`, `UpdatePolicyEngine`, `DeletePolicyEngine` | The engine that evaluates/enforces policies. |
| **Resource policy** | `PutResourcePolicy`, `GetResourcePolicy`, `DeleteResourcePolicy` | Attach a policy to a specific resource. |
| **Policy generation** | `StartPolicyGeneration`, `GetPolicyGeneration`, `GetPolicyGenerationSummary`, `ListPolicyGenerations`, `ListPolicyGenerationSummaries`, `ListPolicyGenerationAssets` | Auto-generate a policy from observed behavior/assets. |

## When to use it

- Enforce **guardrails** on what an agent may do beyond IAM (e.g. constrain tool use, data access, or actions to an
  approved set).
- Run a **policy engine** that evaluates requests against your policies at runtime.
- Use **policy generation** to bootstrap a least-privilege policy from observed agent activity rather than hand-writing
  it — then review and tighten.

## Typical flow

1. `CreatePolicyEngine` — stand up the engine.
2. `CreatePolicy` (or `StartPolicyGeneration` → review generated assets → `CreatePolicy`).
3. `PutResourcePolicy` — bind the policy to the harness/agent or related resource.
4. Iterate with `UpdatePolicy` as you learn what the agent legitimately needs.

## Relationship to other features

- Distinct from **IAM** (which controls AWS API access) — Policy governs agent *behavior* and is evaluated by the
  policy engine. Use both: IAM for AWS resource access, Policy for agent guardrails.
- Distinct from CloudWatch **resource policies** (`observability.md`) despite the similar name — that's a logs-delivery
  permission, this is an agent governance policy.
- Pairs naturally with the **Registry** approval workflow (`registry.md`) for organizational governance.

## API surface

Policy ops evolve quickly. Introspect exact shapes before scripting:
```bash
python scripts/preflight.py --show-shape CreatePolicy --show-shape CreatePolicyEngine --show-shape StartPolicyGeneration
```
Consult the AgentCore Policy dev guide and the SDK `bedrock_agentcore.policy` module.

## Executable example (verified live, boto3 1.43.29)

```python
import boto3, secrets, time
c = boto3.client("bedrock-agentcore-control", region_name="us-east-1")

# 1) Policy engine — the container for policies. Name: ^[A-Za-z][A-Za-z0-9_]*$ (NO hyphens).
eng = c.create_policy_engine(name="my_policy_engine", description="guardrails",
                             clientToken=secrets.token_hex(20))
engine_id = eng["policyEngineId"]

# (optionally wait until the engine is usable)
for _ in range(12):
    if c.get_policy_engine(policyEngineId=engine_id).get("status") in ("READY", "ACTIVE", "AVAILABLE"):
        break
    time.sleep(5)

# 2) Cedar policy. IMPORTANT: a wildcard resource is REJECTED — constrain to a resource type
#    (or a specific resource). e.g. scope to the Gateway resource type:
pol = c.create_policy(
    name="allow_gateway_actions",
    policyEngineId=engine_id,
    definition={"cedar": {"statement": "permit(principal, action, resource is AgentCore::Gateway);"}},
    validationMode="FAIL_ON_ANY_FINDINGS",            # or IGNORE_ALL_FINDINGS
    clientToken=secrets.token_hex(20),
)
policy_id = pol["policyId"]
```

Attach the engine to a Gateway via `CreateGateway(policyEngineConfiguration={"arn": <engine-arn>,
"mode": "ENFORCE"})` (or `LOG_ONLY` to dry-run) — see `references/gateway.md`. Cleanup:
`delete_policy(policyEngineId=..., policyId=...)` then `delete_policy_engine(policyEngineId=...)`.

> **Verified gotchas:** (1) engine/policy names reject hyphens; (2) Cedar statements with a wildcard
> `resource` are rejected — constrain to `resource is <Type>` or a specific resource.

## Temporal policies (stateful authorization)

Announced 2026-08-06 (16 regions). Standard Cedar policies evaluate each request in isolation;
**temporal policies** evaluate it against the agent's **prior actions within a session** — a single
tool call can be safe alone yet harmful given what preceded it. Written in **Dogwood**, a
Cedar-compatible language adding temporal operators.

What they enable:
- **Workflow sequencing** — action B only after action A happened (`formerly within`).
- **Argument↔output matching** — a tool argument must match a prior tool's output.
- **Human approval gates** — require an approval action before a privileged one.
- **Data freshness** — block actions when the data they depend on is older than a window.

Mechanics:
- Temporal operators: `formerly within`, `since within`, `count`, `sum`.
- Session correlation: callers pass the header `x-amzn-bedrock-agentcore-policy-session-id`; the
  engine accumulates that session's history for evaluation.
- **Two different mode enums — don't conflate them** (live-verified 2026-08-12, boto3 1.43.69):
  - `CreatePolicy.enforcementMode`: `ACTIVE | LOG_ONLY` (per policy; round-trips on Get — verified)
  - `CreateGateway.policyEngineConfiguration.mode`: `ENFORCE | LOG_ONLY` (per gateway attachment)
- Quotas: ≤25 temporal policies per engine, ≤3 temporal operators per policy, 24h max lookback window.
- API slot: `CreatePolicy.definition` is a union of `cedar | policyGeneration | policy{statement}`.
  Live probe (2026-08-12): the `policy.statement` slot HAS its own parser, but the grammar guess
  `when { formerly within 1 hour { ... } }` was rejected in both slots
  (`ValidationException: unexpected token 'within'`) — get the exact Dogwood grammar from the
  policy-temporal dev-guide examples before authoring; don't improvise the syntax.

Start with `enforcementMode="LOG_ONLY"`, watch what would have been blocked, then switch to `ACTIVE`.

> **Verified lifecycle gotchas (2026-08-12):** (1) `DeletePolicy` while the policy is `CREATING` →
> `ConflictException: Policy cannot be deleted while its status is CREATING` — poll until it leaves
> CREATING (a rejected statement can land as `CREATE_FAILED`, which still must be deleted);
> (2) `DeletePolicyEngine` → `ConflictException: Policy engine still contains N policies` — delete
> all policies (including failed ones) first.
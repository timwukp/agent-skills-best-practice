# Policy

AgentCore **Policy** (shown as "New" in the console) governs what agents are allowed to do — guardrails and
permissions enforced by a **policy engine**, plus resource policies and an automated policy-generation flow. A rich set
of operations exists in `bedrock-agentcore-control`.

## Building blocks (verified operations)

| Concept | Operations | Purpose |
|---|---|---|
| **Policy** | `CreatePolicy`, `GetPolicy`, `GetPolicySummary`, `ListPolicySummaries`, `UpdatePolicy`, `DeletePolicy` | A policy document governing agent behavior/permissions. |
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

Policy is preview. Introspect exact shapes before scripting:
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
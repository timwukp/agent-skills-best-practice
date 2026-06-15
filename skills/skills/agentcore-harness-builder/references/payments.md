# Payments

AgentCore **Payments** (preview) lets agents transact — connect to payment providers, manage payment configuration, and
run payment sessions — with credentials held in the Identity Token Vault. Both control-plane and data-plane operations
exist.

## Building blocks (verified operations)

| Concept | Plane | Operations | Purpose |
|---|---|---|---|
| **Payment connector** | control | `CreatePaymentConnector`, `GetPaymentConnector`, `ListPaymentConnectors`, `UpdatePaymentConnector`, `DeletePaymentConnector` | Connect to a payment provider/processor. |
| **Payment manager** | control | `CreatePaymentManager`, `GetPaymentManager`, `ListPaymentManagers`, `UpdatePaymentManager`, `DeletePaymentManager` | Manage payment configuration/orchestration. |
| **Payment credential provider** | control | `CreatePaymentCredentialProvider` (+ Get/List/Update/Delete) | Store payment credentials (ties into Identity / Token Vault — see `identity.md`). |
| **Payment session** | data | `CreatePaymentSession`, `GetPaymentSession`, `ListPaymentSessions`, `DeletePaymentSession` | Run an actual payment interaction at invocation time. |

## When to use it

Agents that complete purchases or financial transactions on a user's behalf (e.g. a shopping/booking agent). The
connector/manager/credential-provider are set up once (control plane); payment sessions are created per transaction
(data plane), analogous to how `InvokeHarness` is data plane.

## Security & caution

Payments handle real money and sensitive credentials. Treat all payment configuration as **high-risk**:
- Store credentials only via the payment credential provider / Token Vault, never inline.
- Scope the execution role tightly; never grant broad payment permissions.
- Require human-in-the-loop confirmation (an inline function, see `tools.md`) before an agent commits a transaction.
- Confirm with the user before creating live payment resources — this is not a reversible, cost-free action.

## API surface

Payments is preview. Introspect exact shapes before scripting:
```bash
python scripts/preflight.py --show-shape CreatePaymentConnector --show-shape CreatePaymentManager
```
Consult the AgentCore Payments dev guide and the SDK `bedrock_agentcore.payments` module.

## Example (documentation only — DO NOT run against real processors)

> ⚠️ **Never end-to-end test Payments.** These objects connect to **real payment processors / rails**.
> The example below is illustrative only; validate shapes via SDK introspection, never by live-creating
> against a real connector. (This is why the skill's e2e suite deliberately excludes Payments.)

```python
import boto3
c = boto3.client("bedrock-agentcore-control", region_name="us-east-1")

# A Payment credential provider stores processor credentials in the Token Vault (like other providers):
#   c.create_payment_credential_provider(name="my_processor", ...)
# A Payment Manager + Connector wire the agent to a processor:
#   c.create_payment_manager(name="...", ...)
#   c.create_payment_connector(name="...", ...)
# Inspect the exact required fields with:
sm = c.meta.service_model
for op in ["CreatePaymentCredentialProvider", "CreatePaymentManager", "CreatePaymentConnector"]:
    sh = sm.operation_model(op).input_shape
    print(op, {n: n in (sh.required_members or []) for n in sh.members})
```

Treat any payment credential as a high-sensitivity secret; scope IAM tightly and prefer the Token Vault
over inlining secrets.
# Observability — Log Delivery & Tracing

AgentCore emits OpenTelemetry traces and structured logs. Observability has an asymmetry that trips people up: **traces
go to X-Ray, logs go to CloudWatch**, and they're configured differently.

## What you get by default (no setup)

When a harness/runtime is created, AgentCore auto-creates a default log group:

```
/aws/bedrock-agentcore/runtimes/<runtime-name>-<id>-DEFAULT
```

This receives **rich OTel structured logs** — `trace_id`, `span_id`, `resource.service.name`, and EMF metric blocks.
**This is where dashboard data actually lives.** The `otel.resource.aws.log.group.names` attribute is hardcoded to
point here. Default retention is `None` (never expires) — set it explicitly to bound storage cost.

## Log delivery types

Three `logType` values:

| logType | Destination | Notes |
|---|---|---|
| `APPLICATION_LOGS` | CloudWatch log group | sparse per-invocation events; a **separate, sparser** channel from DEFAULT, not a duplicate |
| `TRACES` | **X-Ray** (`deliveryDestinationType="XRAY"`) | NOT a log group |
| `USAGE_LOGS` | usage events | rarely needed |

### X-Ray destinations take no outputFormat

```python
# correct
logs.put_delivery_destination(name="my-xray-dest", deliveryDestinationType="XRAY")

# rejected: "XRay delivery destination does not support any output format"
logs.put_delivery_destination(name="my-xray-dest", outputFormat="json", deliveryDestinationType="XRAY")
```

## The resource-policy gotcha

If `aws logs create-delivery` succeeds but no events flow to your custom log group, the cause is almost always the
**resource policy** on the destination log group. AWS auto-creates a policy named `AWSLogDeliveryWrite20150319` for
some services but does **not** auto-add new services. Extend it to allow `delivery.logs.amazonaws.com` to write to your
specific log groups — and **preserve existing statements** (append, don't replace). `scripts/setup_observability.py`
implements this idempotently.

## Setup flow (what the script does)

1. Create/identify the destination CloudWatch log group; set retention.
2. `put_delivery_source` for the harness/runtime for `APPLICATION_LOGS` and `TRACES`.
3. `put_delivery_destination` — a CWL destination for logs, an XRAY destination for traces (no outputFormat).
4. `create_delivery` linking each source to its destination.
5. Extend the `AWSLogDeliveryWrite20150319` resource policy on the log group.

```bash
python scripts/setup_observability.py --harness-id <ID> --region us-east-1 \
    --log-group /aws/bedrock-agentcore/harness/<NAME> --retention-days 30
```

## Dashboards & metrics

The console's Observability tab surfaces: Runtime sessions, Runtime invocations, error rate, throttle rate, vCPU-hrs,
memory GB-hrs. Resource-consumption data can lag up to ~60 minutes. For your own dashboards/alarms, query the **DEFAULT
log group** (which has the data) plus **X-Ray** (which has traces) — not the sparse custom APPLICATION_LOGS channel.

Evaluation results (see `references/evaluations.md`) also surface in AgentCore Observability, so wiring observability
first makes evaluations immediately visible.

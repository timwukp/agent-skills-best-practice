#!/usr/bin/env python3
"""Set up Observability for a Harness: CloudWatch log delivery + X-Ray tracing.

Encodes the two gotchas:
  - X-Ray delivery destinations take NO outputFormat (only name + deliveryDestinationType=XRAY).
  - APPLICATION_LOGS delivery to a custom log group needs the AWSLogDeliveryWrite20150319 resource
    policy on that log group extended for delivery.logs.amazonaws.com (append, don't replace).

Note: the runtime already emits rich OTel logs to /aws/bedrock-agentcore/runtimes/<name>-<id>-DEFAULT;
that DEFAULT group is where dashboard data lives. This sets up an additional explicit delivery.

The exact CloudWatch Logs delivery API member names for an AgentCore source can shift in preview;
this script is structured and --dry-run by intent so you can confirm shapes before executing.

Usage:
    python setup_observability.py --harness-id <ID> --region us-east-1 \
        --log-group /aws/bedrock-agentcore/harness/MyHarness --retention-days 30 --dry-run
"""
import argparse
import json
import sys

RESOURCE_POLICY_NAME = "AWSLogDeliveryWrite20150319"


def desired_policy_statement(account_id: str, region: str, log_group: str) -> dict:
    return {
        "Sid": "AWSLogDeliveryWriteAgentCore",
        "Effect": "Allow",
        "Principal": {"Service": "delivery.logs.amazonaws.com"},
        "Action": ["logs:CreateLogStream", "logs:PutLogEvents"],
        "Resource": f"arn:aws:logs:{region}:{account_id}:log-group:{log_group}:*",
        "Condition": {"StringEquals": {"aws:SourceAccount": account_id}},
    }


def merge_resource_policy(existing_doc: dict | None, new_stmt: dict) -> dict:
    """Append the new statement, preserving existing statements (idempotent on Sid)."""
    if not existing_doc:
        return {"Version": "2012-10-17", "Statement": [new_stmt]}
    statements = existing_doc.get("Statement", [])
    statements = [s for s in statements if s.get("Sid") != new_stmt["Sid"]]
    statements.append(new_stmt)
    existing_doc["Statement"] = statements
    return existing_doc


def main() -> int:
    ap = argparse.ArgumentParser(description="Set up Harness observability (logs + traces)")
    ap.add_argument("--harness-id", required=True)
    ap.add_argument("--log-group", required=True, help="Destination CloudWatch log group for APPLICATION_LOGS")
    ap.add_argument("--retention-days", type=int, default=30)
    ap.add_argument("--region", default="us-east-1")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    plan = {
        "1_log_group": f"ensure log group {args.log_group} exists; set retention {args.retention_days}d "
                       "(DEFAULT group never expires unless set)",
        "2_delivery_source_logs": f"put_delivery_source(name=...-app-logs, logType=APPLICATION_LOGS, "
                                  f"resourceArn=<harness/runtime arn for {args.harness_id}>)",
        "3_delivery_source_traces": "put_delivery_source(name=...-traces, logType=TRACES, resourceArn=<...>)",
        "4_dest_logs": f"put_delivery_destination(name=...-cwl, deliveryDestinationType=CWL, "
                       f"destination={args.log_group})",
        "5_dest_traces": "put_delivery_destination(name=...-xray, deliveryDestinationType=XRAY)  "
                         "# NO outputFormat for XRAY",
        "6_create_delivery": "create_delivery(deliverySource -> deliveryDestination) for each pair",
        "7_resource_policy": f"extend {RESOURCE_POLICY_NAME} on {args.log_group} for delivery.logs.amazonaws.com "
                             "(append, preserve existing statements)",
    }

    if args.dry_run:
        print("DRY RUN — observability setup plan:\n")
        for k in sorted(plan):
            print(f"  {k}: {plan[k]}")
        print("\nExample resource-policy statement to append:")
        print(json.dumps(desired_policy_statement("<ACCOUNT_ID>", args.region, args.log_group), indent=2))
        print("\nConfirm live CWL-delivery member names before executing (preview API).")
        return 0

    import boto3
    logs = boto3.client("logs", region_name=args.region)
    sts = boto3.client("sts", region_name=args.region)
    account_id = sts.get_caller_identity()["Account"]

    # 1. log group + retention
    try:
        logs.create_log_group(logGroupName=args.log_group)
    except logs.exceptions.ResourceAlreadyExistsException:
        pass
    except Exception as e:  # noqa: BLE001
        print(f"WARN  create_log_group: {e}")
    try:
        logs.put_retention_policy(logGroupName=args.log_group, retentionInDays=args.retention_days)
        print(f"OK    log group {args.log_group} ready (retention {args.retention_days}d)")
    except Exception as e:  # noqa: BLE001
        print(f"WARN  put_retention_policy: {e}")

    # 7. resource policy (the critical, commonly-missed step) — do this so deliveries can write
    new_stmt = desired_policy_statement(account_id, args.region, args.log_group)
    existing_doc = None
    try:
        for p in logs.describe_resource_policies().get("resourcePolicies", []):
            if p.get("policyName") == RESOURCE_POLICY_NAME:
                existing_doc = json.loads(p["policyDocument"])
                break
    except Exception as e:  # noqa: BLE001
        print(f"WARN  describe_resource_policies: {e}")
    merged = merge_resource_policy(existing_doc, new_stmt)
    try:
        logs.put_resource_policy(policyName=RESOURCE_POLICY_NAME, policyDocument=json.dumps(merged))
        print(f"OK    extended resource policy {RESOURCE_POLICY_NAME} for delivery.logs.amazonaws.com")
    except Exception as e:  # noqa: BLE001
        print(f"WARN  put_resource_policy: {e}")

    print("\nNOTE: the delivery-source/destination/create-delivery calls (steps 2-6) use preview API "
          "member names that vary. Re-run with --dry-run to see the plan, confirm shapes via the docs, "
          "then wire them. The DEFAULT log group /aws/bedrock-agentcore/runtimes/<name>-<id>-DEFAULT "
          "already has rich OTel data for dashboards.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

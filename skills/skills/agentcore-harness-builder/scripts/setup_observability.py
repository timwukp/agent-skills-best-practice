#!/usr/bin/env python3
"""Set up Observability for a Harness: CloudWatch log delivery + X-Ray tracing.

Creates, idempotently:
  1. the destination CloudWatch log group (+ retention),
  2. the AWSLogDeliveryWrite20150319 resource policy extension for delivery.logs.amazonaws.com,
  3. delivery sources for APPLICATION_LOGS and TRACES (resourceArn derived from --harness-id),
  4. a CWL delivery destination for logs and an XRAY destination for traces,
  5. create_delivery linking each source to its destination.

Encodes the two gotchas:
  - X-Ray delivery destinations take NO outputFormat (only name + deliveryDestinationType=XRAY).
  - APPLICATION_LOGS delivery to a custom log group needs the AWSLogDeliveryWrite20150319 resource
    policy on that log group extended for delivery.logs.amazonaws.com (append, don't replace).

Note: the runtime already emits rich OTel logs to /aws/bedrock-agentcore/runtimes/<name>-<id>-DEFAULT;
that DEFAULT group is where dashboard data lives. This sets up an additional explicit delivery.

ALSO REQUIRED for Evaluations: set OTEL_TRACES_SAMPLER=always_on on the harness
(update_harness environmentVariables) — sampling is OFF by default and evaluators read spans.

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


def delivery_plan(harness_id: str, log_group: str) -> dict:
    """The source/destination/delivery names + wiring for a harness (pure, testable)."""
    prefix = f"harness-{harness_id}"[:50]
    return {
        "sources": [
            {"name": f"{prefix}-app-logs", "logType": "APPLICATION_LOGS"},
            {"name": f"{prefix}-traces", "logType": "TRACES"},
        ],
        "destinations": [
            {"name": f"{prefix}-cwl", "deliveryDestinationType": "CWL", "log_group": log_group},
            # X-Ray destinations take NO outputFormat and no destinationResourceArn
            {"name": f"{prefix}-xray", "deliveryDestinationType": "XRAY"},
        ],
        "deliveries": [
            {"source": f"{prefix}-app-logs", "destination": f"{prefix}-cwl"},
            {"source": f"{prefix}-traces", "destination": f"{prefix}-xray"},
        ],
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="Set up Harness observability (logs + traces)")
    ap.add_argument("--harness-id", required=True)
    ap.add_argument("--log-group", required=True, help="Destination CloudWatch log group for APPLICATION_LOGS")
    ap.add_argument("--retention-days", type=int, default=30)
    ap.add_argument("--region", default="us-east-1")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    print(f"Region: {args.region}")
    plan = delivery_plan(args.harness_id, args.log_group)

    if args.dry_run:
        print("DRY RUN — observability setup plan:\n")
        print(f"  1. ensure log group {args.log_group} (retention {args.retention_days}d)")
        print(f"  2. extend resource policy {RESOURCE_POLICY_NAME} for delivery.logs.amazonaws.com")
        print(f"  3. resourceArn = runtime ARN of agentRuntimeName 'harness_{args.harness_id.rsplit('-', 1)[0]}'"
              " (NOT the harness ARN — PutDeliverySource only accepts LogType `runtime` resources)")
        for s in plan["sources"]:
            print(f"  4. put_delivery_source(name={s['name']}, logType={s['logType']}, resourceArn=<runtime arn>)")
        for d in plan["destinations"]:
            extra = f", destinationResourceArn=<{d['log_group']}>" if d.get("log_group") else "  # NO outputFormat for XRAY"
            print(f"  5. put_delivery_destination(name={d['name']}, type={d['deliveryDestinationType']}{extra})")
        for dl in plan["deliveries"]:
            print(f"  6. create_delivery({dl['source']} -> {dl['destination']})")
        print("\nExample resource-policy statement to append:")
        print(json.dumps(desired_policy_statement("<ACCOUNT_ID>", args.region, args.log_group), indent=2))
        print("\nREMINDER: also set OTEL_TRACES_SAMPLER=always_on on the harness or evaluations score nothing.")
        return 0

    import boto3
    logs = boto3.client("logs", region_name=args.region)
    sts = boto3.client("sts", region_name=args.region)
    control = boto3.client("bedrock-agentcore-control", region_name=args.region)
    account_id = sts.get_caller_identity()["Account"]

    # resolve the delivery-source resourceArn. Two live-verified traps here:
    #   1. GetHarness nests its payload under a top-level "harness" key — the ARN
    #      is response["harness"]["arn"], not response["harnessArn"].
    #   2. PutDeliverySource REJECTS harness ARNs ("This resource is not allowed
    #      for this LogType") — deliveries only accept LogType `runtime` resources,
    #      so target the auto-created runtime named `harness_<name>` instead.
    try:
        harness_name = args.harness_id.rsplit("-", 1)[0]
        resource_arn = None
        for rt in control.list_agent_runtimes().get("agentRuntimes", []):
            if rt.get("agentRuntimeName") == f"harness_{harness_name}":
                resource_arn = rt.get("agentRuntimeArn")
                break
    except Exception as e:  # noqa: BLE001
        print(f"FAIL  list_agent_runtimes for {args.harness_id}: {e}")
        return 1
    if not resource_arn:
        print(f"FAIL  no runtime named harness_{harness_name} in list_agent_runtimes.")
        return 1
    print(f"OK    runtime ARN resolved for harness {args.harness_id}")

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

    # 2. resource policy (the critical, commonly-missed step) — do this so deliveries can write
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

    ok = True

    # 3. delivery sources (put_* is create-or-update, hence idempotent)
    source_arns = {}
    for s in plan["sources"]:
        try:
            r = logs.put_delivery_source(name=s["name"], logType=s["logType"], resourceArn=resource_arn)
            source_arns[s["name"]] = r["deliverySource"]["name"]
            print(f"OK    delivery source {s['name']} ({s['logType']})")
        except Exception as e:  # noqa: BLE001
            print(f"FAIL  put_delivery_source {s['name']}: {e}")
            ok = False

    # 4. delivery destinations — CWL for logs, XRAY for traces (NO outputFormat for XRAY)
    dest_arns = {}
    log_group_arn = f"arn:aws:logs:{args.region}:{account_id}:log-group:{args.log_group}:*"
    for d in plan["destinations"]:
        kwargs = {"name": d["name"], "deliveryDestinationType": d["deliveryDestinationType"]}
        if d["deliveryDestinationType"] == "CWL":
            kwargs["deliveryDestinationConfiguration"] = {"destinationResourceArn": log_group_arn}
        try:
            r = logs.put_delivery_destination(**kwargs)
            dest_arns[d["name"]] = r["deliveryDestination"]["arn"]
            print(f"OK    delivery destination {d['name']} ({d['deliveryDestinationType']})")
        except Exception as e:  # noqa: BLE001
            print(f"FAIL  put_delivery_destination {d['name']}: {e}")
            ok = False

    # 5. deliveries (create_delivery is not idempotent — tolerate ConflictException)
    for dl in plan["deliveries"]:
        dest_arn = dest_arns.get(dl["destination"])
        if not dest_arn or dl["source"] not in source_arns:
            print(f"SKIP  delivery {dl['source']} -> {dl['destination']} (prerequisite failed above)")
            continue
        try:
            logs.create_delivery(deliverySourceName=dl["source"], deliveryDestinationArn=dest_arn)
            print(f"OK    delivery {dl['source']} -> {dl['destination']}")
        except logs.exceptions.ConflictException:
            print(f"OK    delivery {dl['source']} -> {dl['destination']} (already exists)")
        except Exception as e:  # noqa: BLE001
            print(f"FAIL  create_delivery {dl['source']} -> {dl['destination']}: {e}")
            ok = False

    print("\nREMINDER: set OTEL_TRACES_SAMPLER=always_on on the harness (update_harness "
          "environmentVariables) — sampling is OFF by default and evaluations read spans. "
          "The DEFAULT log group /aws/bedrock-agentcore/runtimes/<name>-<id>-DEFAULT already has "
          "rich OTel data for dashboards.")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())

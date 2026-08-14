#!/usr/bin/env python3
"""Preflight checks for building an AgentCore Harness.

Verifies the environment can actually create/manage harnesses BEFORE you waste time:
  - boto3 >= 1.43.51 (older versions lack harness/endpoint operations or current field shapes)
  - the core harness operations exist on the control-plane client
  - AWS credentials resolve
  - prints the LIVE CreateHarness / UpdateHarness input shapes (schema introspection),
    which is the source of truth when docs and reality disagree

Harness is GA in ~16 regions; EXAMPLE_REGIONS below are examples, not a gate — check the
AgentCore regions page for the full list.

Usage:
    python preflight.py --region us-east-1
    python preflight.py --region us-east-1 --show-shape UpdateHarness
    # introspect a neighbouring plane (registry, knowledge bases):
    python preflight.py --service agent-registry-control --show-shape CreateRegistryRecord
    python preflight.py --service bedrock-agent --show-shape CreateKnowledgeBase

Exit code 0 = good to go; non-zero = a blocker was found.
"""
import argparse
import sys

MIN_BOTO3 = (1, 43, 51)
CONTROL_PLANE = "bedrock-agentcore-control"
# Other planes an AgentCore build touches. --service only affects --show-shape; the harness-op
# check below is always run against the control plane.
KNOWN_SERVICES = (CONTROL_PLANE, "bedrock-agentcore", "agent-registry-control", "agent-registry",
                  "bedrock-agent", "bedrock-agent-runtime")
EXAMPLE_REGIONS = {"us-east-1", "us-west-2", "eu-central-1", "ap-southeast-2"}
HARNESS_OPS = {"CreateHarness", "UpdateHarness", "GetHarness", "ListHarnesses", "DeleteHarness",
               "CreateHarnessEndpoint", "UpdateHarnessEndpoint", "GetHarnessEndpoint",
               "ListHarnessEndpoints", "ListHarnessVersions"}


def _ver_tuple(v: str):
    parts = []
    for p in v.split(".")[:3]:
        num = "".join(ch for ch in p if ch.isdigit())
        parts.append(int(num) if num else 0)
    while len(parts) < 3:
        parts.append(0)
    return tuple(parts)


def check_boto3_version() -> bool:
    try:
        import boto3
    except ImportError:
        print("FAIL  boto3 not installed. Run: pip install -r assets/requirements.txt")
        return False
    ok = _ver_tuple(boto3.__version__) >= MIN_BOTO3
    flag = "OK  " if ok else "FAIL"
    print(f"{flag}  boto3 {boto3.__version__} (need >= {'.'.join(map(str, MIN_BOTO3))})")
    if not ok:
        print("      Fix: pip install --upgrade boto3 botocore")
    return ok


def check_harness_ops(region: str) -> bool:
    import boto3
    try:
        client = boto3.client("bedrock-agentcore-control", region_name=region)
    except Exception as e:  # noqa: BLE001
        print(f"FAIL  could not create bedrock-agentcore-control client: {e}")
        return False
    available = {op for op in client.meta.service_model.operation_names if "Harness" in op}
    missing = HARNESS_OPS - available
    if missing:
        print(f"FAIL  missing harness operations: {sorted(missing)}")
        print("      Your boto3/botocore is too old for harness support. Upgrade.")
        return False
    print(f"OK    all {len(HARNESS_OPS)} harness operations present (incl. endpoint/version ops)")
    return True


def check_credentials_region(region: str) -> bool:
    import boto3
    ok = True
    print(f"OK    using region '{region}' (Harness is GA in ~16 regions, e.g. {sorted(EXAMPLE_REGIONS)}; "
          "see the AgentCore regions page for the full list)")
    try:
        ident = boto3.client("sts", region_name=region).get_caller_identity()
        print(f"OK    credentials resolve: account {ident['Account']}, arn {ident['Arn']}")
    except Exception as e:  # noqa: BLE001
        print(f"FAIL  credentials do not resolve: {e}")
        ok = False
    return ok


def show_shape(region: str, op: str, service: str = CONTROL_PLANE) -> None:
    import boto3
    try:
        client = boto3.client(service, region_name=region)
    except Exception as e:  # noqa: BLE001
        print(f"      could not create {service} client: {e}")
        print(f"      (an UnknownServiceError means your botocore predates {service})")
        return
    try:
        shape = client.meta.service_model.operation_model(op).input_shape
    except Exception as e:  # noqa: BLE001
        print(f"      could not introspect {op}: {e}")
        return
    if shape is None:
        print(f"      {op} takes no input")
        return
    req = getattr(shape, "required_members", set())
    label = op if service == CONTROL_PLANE else f"{service} {op}"
    print(f"\n=== {label} input shape (LIVE — trust this over docs) ===")
    for name, member in shape.members.items():
        tag = " [required]" if name in req else ""
        print(f"  {name}: {member.type_name}{tag}")


def main() -> int:
    ap = argparse.ArgumentParser(description="AgentCore Harness preflight checks")
    ap.add_argument("--region", default="us-east-1")
    ap.add_argument("--show-shape", action="append", default=[],
                    help="Operation to introspect (repeatable). Default: CreateHarness, UpdateHarness")
    ap.add_argument("--service", default=CONTROL_PLANE,
                    help=f"Service to introspect with --show-shape (default {CONTROL_PLANE}). "
                         f"Other planes an AgentCore build touches: {', '.join(KNOWN_SERVICES[1:])}. "
                         "The harness-operation check always uses the control plane.")
    args = ap.parse_args()

    print("AgentCore Harness — preflight\n" + "-" * 32)
    results = [check_boto3_version()]
    if results[0]:  # only meaningful if boto3 imports
        results.append(check_harness_ops(args.region))
        results.append(check_credentials_region(args.region))
        for op in (args.show_shape or ["CreateHarness", "UpdateHarness"]):
            show_shape(args.region, op, args.service)

    print("\n" + "-" * 32)
    if all(results):
        print("READY  environment can build and manage harnesses.")
        return 0
    print("BLOCKED  fix the FAIL items above before continuing.")
    return 1


if __name__ == "__main__":
    sys.exit(main())

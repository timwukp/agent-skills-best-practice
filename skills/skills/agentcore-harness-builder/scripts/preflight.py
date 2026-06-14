#!/usr/bin/env python3
"""Preflight checks for building an AgentCore Harness.

Verifies the environment can actually create/manage harnesses BEFORE you waste time:
  - boto3 >= 1.43.18 (older versions have ZERO harness operations)
  - the 5 harness operations exist on the control-plane client
  - AWS credentials resolve and the region is a preview region
  - prints the LIVE CreateHarness / UpdateHarness input shapes (schema introspection),
    which is the source of truth when docs and reality disagree

Usage:
    python preflight.py --region us-east-1
    python preflight.py --region us-east-1 --show-shape UpdateHarness

Exit code 0 = good to go; non-zero = a blocker was found.
"""
import argparse
import sys

MIN_BOTO3 = (1, 43, 18)
PREVIEW_REGIONS = {"us-east-1", "us-west-2", "eu-central-1", "ap-southeast-2"}
HARNESS_OPS = {"CreateHarness", "UpdateHarness", "GetHarness", "ListHarnesses", "DeleteHarness"}


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
    print(f"OK    all 5 harness operations present: {sorted(HARNESS_OPS)}")
    return True


def check_credentials_region(region: str) -> bool:
    import boto3
    ok = True
    if region not in PREVIEW_REGIONS:
        print(f"WARN  region '{region}' is not a known AgentCore preview region {sorted(PREVIEW_REGIONS)}")
    try:
        ident = boto3.client("sts", region_name=region).get_caller_identity()
        print(f"OK    credentials resolve: account {ident['Account']}, arn {ident['Arn']}")
    except Exception as e:  # noqa: BLE001
        print(f"FAIL  credentials do not resolve: {e}")
        ok = False
    return ok


def show_shape(region: str, op: str) -> None:
    import boto3
    client = boto3.client("bedrock-agentcore-control", region_name=region)
    try:
        shape = client.meta.service_model.operation_model(op).input_shape
    except Exception as e:  # noqa: BLE001
        print(f"      could not introspect {op}: {e}")
        return
    req = getattr(shape, "required_members", set())
    print(f"\n=== {op} input shape (LIVE — trust this over docs) ===")
    for name, member in shape.members.items():
        tag = " [required]" if name in req else ""
        print(f"  {name}: {member.type_name}{tag}")


def main() -> int:
    ap = argparse.ArgumentParser(description="AgentCore Harness preflight checks")
    ap.add_argument("--region", default="us-east-1")
    ap.add_argument("--show-shape", action="append", default=[],
                    help="Operation to introspect (repeatable). Default: CreateHarness, UpdateHarness")
    args = ap.parse_args()

    print("AgentCore Harness — preflight\n" + "-" * 32)
    results = [check_boto3_version()]
    if results[0]:  # only meaningful if boto3 imports
        results.append(check_harness_ops(args.region))
        results.append(check_credentials_region(args.region))
        for op in (args.show_shape or ["CreateHarness", "UpdateHarness"]):
            show_shape(args.region, op)

    print("\n" + "-" * 32)
    if all(results):
        print("READY  environment can build and manage harnesses.")
        return 0
    print("BLOCKED  fix the FAIL items above before continuing.")
    return 1


if __name__ == "__main__":
    sys.exit(main())

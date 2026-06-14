#!/usr/bin/env python3
"""Create an AgentCore Harness from a harness.json config.

Field shapes verified against boto3 1.43.29. Handles create-time details: strips _-prefixed
comment keys, maps a convenience 'name' key to the real 'harnessName' field, applies tags at
create time, generates a valid clientToken (>= 33 chars). Validate the config first with
validate_config.py.

Usage:
    python create_harness.py --config harness.json --role-arn arn:aws:iam::123:role/HarnessExec
    python create_harness.py --config harness.json --role-arn ... --region us-east-1 --dry-run
"""
import argparse
import json
import secrets
import sys


def _strip_comments(obj):
    """Remove any dict key starting with '_' (templates use _comment / _*_note keys)."""
    if isinstance(obj, dict):
        return {k: _strip_comments(v) for k, v in obj.items() if not k.startswith("_")}
    if isinstance(obj, list):
        return [_strip_comments(v) for v in obj]
    return obj


def load_config(path: str) -> dict:
    with open(path, encoding="utf-8") as f:
        return _strip_comments(json.load(f))


def build_kwargs(cfg: dict, role_arn: str) -> dict:
    kwargs = dict(cfg)
    # convenience: accept 'name' and map to the real CreateHarness field 'harnessName'
    if "name" in kwargs and "harnessName" not in kwargs:
        kwargs["harnessName"] = kwargs.pop("name")
    kwargs["executionRoleArn"] = role_arn
    kwargs.setdefault("clientToken", secrets.token_hex(20))  # 40 chars, > 33 min
    return kwargs


def main() -> int:
    ap = argparse.ArgumentParser(description="Create an AgentCore Harness")
    ap.add_argument("--config", required=True)
    ap.add_argument("--role-arn", required=True)
    ap.add_argument("--region", default="us-east-1")
    ap.add_argument("--dry-run", action="store_true", help="Print the API call without executing")
    args = ap.parse_args()

    cfg = load_config(args.config)
    kwargs = build_kwargs(cfg, args.role_arn)

    if args.dry_run:
        print("DRY RUN — create_harness(**kwargs) with:")
        print(json.dumps(kwargs, indent=2, default=str))
        return 0

    import boto3
    client = boto3.client("bedrock-agentcore-control", region_name=args.region)
    try:
        resp = client.create_harness(**kwargs)
    except Exception as e:  # noqa: BLE001
        print(f"FAIL  create_harness rejected: {e}")
        print("      Tip: run preflight.py --show-shape CreateHarness to see the live accepted fields.")
        return 1
    hid = resp.get("harnessId") or resp.get("harnessArn")
    print(f"OK    created harness: {hid}")
    print(json.dumps({k: v for k, v in resp.items() if k != "ResponseMetadata"}, indent=2, default=str))
    print("\nNext: wire memory (wire_memory.py), set up observability (setup_observability.py), "
          "then smoke-test with invoke_harness.py.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

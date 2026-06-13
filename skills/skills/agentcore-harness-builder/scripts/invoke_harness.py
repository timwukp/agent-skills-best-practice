#!/usr/bin/env python3
"""Smoke-test a Harness by invoking it on the DATA plane and streaming the reply.

This is the definitive end-to-end check: a harness that CreateHarness accepted can still fail at
session start (missing SKILL.md frontmatter, missing Memory IAM grant, tools stored-but-not-wired).
A successful streamed reply that uses the wired tools proves the configuration is correct.

Note: use invoke_harness on the 'bedrock-agentcore' (data-plane) client — NOT invoke_agent_runtime.

Usage:
    python invoke_harness.py --harness-arn <HARNESS_ARN> --prompt "Hello, what can you do?"
    python invoke_harness.py --harness-arn <ARN> --prompt "..." --session-id my-session-001
"""
import argparse
import secrets
import sys


def main() -> int:
    ap = argparse.ArgumentParser(description="Invoke (smoke-test) an AgentCore Harness")
    ap.add_argument("--harness-arn", required=True)
    ap.add_argument("--prompt", required=True)
    ap.add_argument("--session-id", default=None, help="Reuse a session id to continue a conversation")
    ap.add_argument("--region", default="us-east-1")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    # runtimeSessionId must be >= 33 chars (API constraint). token_hex(16)=32 -> +prefix = 38.
    session_id = args.session_id or f"smoke-{secrets.token_hex(16)}"
    if len(session_id) < 33:
        session_id = (session_id + "-" + secrets.token_hex(16))[:64]
    messages = [{"role": "user", "content": [{"text": args.prompt}]}]

    if args.dry_run:
        print("DRY RUN — invoke_harness(...) with:")
        print(f"  harnessArn      = {args.harness_arn}")
        print(f"  runtimeSessionId= {session_id}")
        print(f"  messages        = {messages}")
        return 0

    import boto3
    client = boto3.client("bedrock-agentcore", region_name=args.region)  # DATA plane
    try:
        resp = client.invoke_harness(harnessArn=args.harness_arn,
                                     runtimeSessionId=session_id,
                                     messages=messages)
    except Exception as e:  # noqa: BLE001
        print(f"FAIL  invoke_harness rejected/failed: {e}")
        print("      Common causes: missing SKILL.md frontmatter, missing Memory IAM grant (step 3), "
              "tools stored-but-not-wired (missing tools[].config), or allowedTools without globs.")
        return 1

    print(f"session: {session_id}\n--- streamed response ---")
    got_text = False
    try:
        for event in resp["stream"]:
            if "contentBlockDelta" in event:
                delta = event["contentBlockDelta"].get("delta", {})
                if "text" in delta:
                    sys.stdout.write(delta["text"])
                    sys.stdout.flush()
                    got_text = True
    except Exception as e:  # noqa: BLE001
        print(f"\nFAIL  error while streaming: {e}")
        return 1
    print("\n--- end ---")
    if not got_text:
        print("WARN  no text deltas received; inspect the raw event stream / observability logs.")
        return 1
    print("OK    harness responded. Configuration verified end to end.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

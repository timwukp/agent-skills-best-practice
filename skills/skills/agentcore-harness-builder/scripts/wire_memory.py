#!/usr/bin/env python3
"""Wire AgentCore Memory to a Harness — all THREE steps (the third is the one people forget).

  1. CreateMemory with a 4-strategy set (Episodic, UserPreference, Summarization, Semantic).
  2. UpdateHarness(memory={"optionalValue": {"agentCoreMemoryConfiguration": {...}}}).
  3. iam:PutRolePolicy granting the harness execution role data-plane perms on the new Memory ARN,
     with namespace {placeholder} templates converted to glob* patterns for the IAM condition.

Skipping step 3 makes every invocation fail at session start with AccessDeniedException: ListEvents.

Usage:
    python wire_memory.py --harness-id <ID> --role-arn <EXEC_ROLE_ARN> \
        --memory-name MyAgentMemory --actor-id ci-pipeline
    python wire_memory.py ... --dry-run
"""
import argparse
import json
import re
import secrets
import sys

# namespace templates -> retrievalConfig keys. {placeholder} form here; converted to glob for IAM.
DEFAULT_STRATEGIES = [
    ("episodicMemoryStrategy", "Episodic", "/episodes/{actorId}/{sessionId}",
     "Past sessions as discrete episodes"),
    ("userPreferenceMemoryStrategy", "Userpreference", "/users/{actorId}/preferences",
     "Per-actor preferences"),
    ("summaryMemoryStrategy", "Summarization", "/summaries/{actorId}/{sessionId}",
     "Conversation summaries"),
    ("semanticMemoryStrategy", "Semantic", "/users/{actorId}/facts",
     "Durable facts"),
]


def ns_to_glob(ns: str) -> str:
    """/episodes/{actorId}/{sessionId} -> /episodes/*/*"""
    return re.sub(r"\{[^}]+\}", "*", ns)


def build_strategies() -> list:
    out = []
    for key, name, ns, desc in DEFAULT_STRATEGIES:
        strat = {"name": name, "namespaces": [ns], "description": desc}
        if key == "episodicMemoryStrategy":
            strat["reflectionConfiguration"] = {"reflectionPrefix": "Episode summary:"}
        out.append({key: strat})
    return out


def build_memory_config(memory_arn: str, actor_id: str, strategy_ids: dict) -> dict:
    rc = {}
    for _key, name, ns, _desc in DEFAULT_STRATEGIES:
        sid = strategy_ids.get(name)
        if sid:
            rc[ns] = {"strategyId": sid, "topK": 10, "relevanceScore": 0.2}
    return {"agentCoreMemoryConfiguration": {
        "arn": memory_arn, "actorId": actor_id, "messagesCount": 20, "retrievalConfig": rc,
    }}


def build_iam_policy(memory_arn: str) -> dict:
    namespaces = sorted({ns_to_glob(ns) for _k, _n, ns, _d in DEFAULT_STRATEGIES})
    return {
        "Version": "2012-10-17",
        "Statement": [
            {"Sid": "MemoryEvents", "Effect": "Allow",
             "Action": ["bedrock-agentcore:CreateEvent", "bedrock-agentcore:GetEvent",
                        "bedrock-agentcore:ListEvents", "bedrock-agentcore:ListSessions",
                        "bedrock-agentcore:ListActors"],
             "Resource": memory_arn},
            {"Sid": "MemoryRetrieval", "Effect": "Allow",
             "Action": ["bedrock-agentcore:ListMemoryRecords", "bedrock-agentcore:RetrieveMemoryRecords"],
             "Resource": memory_arn,
             "Condition": {"StringLike": {"bedrock-agentcore:namespace": namespaces}}},
        ],
    }


def role_name_from_arn(arn: str) -> str:
    return arn.split("/")[-1]


def main() -> int:
    ap = argparse.ArgumentParser(description="Wire Memory to a Harness (3 steps)")
    ap.add_argument("--harness-id", required=True)
    ap.add_argument("--role-arn", required=True, help="Harness execution role ARN")
    ap.add_argument("--memory-name", required=True)
    ap.add_argument("--actor-id", default="ci-pipeline")
    ap.add_argument("--event-expiry-days", type=int, default=90,
                    help="REQUIRED by CreateMemory: days after which memory events expire (3-365). Default 90.")
    ap.add_argument("--region", default="us-east-1")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    strategies = build_strategies()
    policy_name = f"{args.memory_name}MemoryAccess"

    if args.dry_run:
        print("DRY RUN — 3-step memory wiring\n")
        print("STEP 1  create_memory(name=%r, eventExpiryDuration=%d, memoryStrategies=...):"
              % (args.memory_name, args.event_expiry_days))
        print(json.dumps(strategies, indent=2))
        print("\nSTEP 2  update_harness(harnessId=%r, memory={'optionalValue': "
              "{'agentCoreMemoryConfiguration': {...}}}) — strategyId values come from step 1 response." % args.harness_id)
        print("\nSTEP 3  put_role_policy(RoleName=%r, PolicyName=%r, PolicyDocument=...):"
              % (role_name_from_arn(args.role_arn), policy_name))
        print(json.dumps(build_iam_policy("arn:aws:bedrock-agentcore:%s:<acct>:memory/<id>" % args.region), indent=2))
        return 0

    import boto3
    control = boto3.client("bedrock-agentcore-control", region_name=args.region)
    iam = boto3.client("iam")

    # STEP 1
    try:
        mem = control.create_memory(name=args.memory_name, memoryStrategies=strategies,
                                    eventExpiryDuration=args.event_expiry_days,
                                    clientToken=secrets.token_hex(20))
    except Exception as e:  # noqa: BLE001
        print(f"FAIL  create_memory: {e}")
        return 1
    memory_arn = mem.get("memoryArn") or mem.get("arn")
    # map created strategy ids back by name
    strategy_ids = {}
    for s in mem.get("memoryStrategies", mem.get("strategies", [])):
        nm = s.get("name")
        sid = s.get("strategyId") or s.get("memoryStrategyId") or s.get("id")
        if nm and sid:
            strategy_ids[nm] = sid
    print(f"OK    step 1: created memory {memory_arn} with strategies {list(strategy_ids)}")

    # STEP 2
    mem_cfg = build_memory_config(memory_arn, args.actor_id, strategy_ids)
    try:
        control.update_harness(harnessId=args.harness_id,
                               memory={"optionalValue": mem_cfg},
                               clientToken=secrets.token_hex(20))
    except Exception as e:  # noqa: BLE001
        print(f"FAIL  step 2 update_harness(memory=...): {e}")
        return 1
    print(f"OK    step 2: attached memory to harness {args.harness_id}")

    # STEP 3
    try:
        iam.put_role_policy(RoleName=role_name_from_arn(args.role_arn),
                            PolicyName=policy_name,
                            PolicyDocument=json.dumps(build_iam_policy(memory_arn)))
    except Exception as e:  # noqa: BLE001
        print(f"FAIL  step 3 put_role_policy: {e}")
        print("      Without this grant, sessions fail with AccessDeniedException: ListEvents.")
        return 1
    print(f"OK    step 3: granted '{policy_name}' on {memory_arn} to {role_name_from_arn(args.role_arn)}")
    print("\nMemory wired. Smoke-test with invoke_harness.py to confirm session start succeeds.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

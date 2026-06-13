#!/usr/bin/env python3
"""Offline unit tests for agentcore-harness-builder scripts.

Covers the pure logic that does NOT require AWS: config validation rules, memory namespace->glob
conversion and IAM/strategy builders, update_harness optionalValue wrapping, observability
resource-policy merging, and create_harness kwargs building. No boto3 or network needed (all AWS
imports in the scripts are inside main()/functions, so importing the modules is safe).

Run:  python3 scripts/test_offline.py
Exit code 0 = all pass.
"""
import importlib.util
import json
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL = os.path.dirname(HERE)
TEMPLATE = os.path.join(SKILL, "assets", "harness.json.template")
SKILL_TMPL = os.path.join(SKILL, "assets", "skill.md.template")

_passed = 0
_failed = 0


def check(name, cond, detail=""):
    global _passed, _failed
    if cond:
        _passed += 1
        print(f"  PASS  {name}")
    else:
        _failed += 1
        print(f"  FAIL  {name}  {detail}")


def load(modname):
    spec = importlib.util.spec_from_file_location(modname, os.path.join(HERE, f"{modname}.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ---------- validate_config (via subprocess for full main() behavior) ----------
def test_validate_config():
    print("validate_config:")
    r = subprocess.run([sys.executable, os.path.join(HERE, "validate_config.py"),
                        "--config", TEMPLATE, "--skill", SKILL_TMPL],
                       capture_output=True, text=True)
    check("template validates with exit 0", r.returncode == 0, r.stdout[-300:])

    bad = {
        "name": "X",  # should warn (prefer harnessName)
        "model": {"bedrockModelConfig": {"modelId": "anthropic.claude-3-sonnet-20240229-v1:0"}},
        "systemPrompt": "bare string",
        "tools": [{"type": "agentcore_browser", "name": "browser"}],
        "allowedTools": ["browser"],
        "skills": [{"git": {"url": "u", "path": "p", "branch": "feature"}},
                   {"path": {"path": "/x"}}, {"s3": {"bucket": "b", "prefix": "p"}}],
        "truncation": {"strategy": "sliding_window", "slidingWindowMessagesCount": 150},
        "network": {"networkMode": "PUBLIC"},
        "lifecycle": {"idleSessionTimeoutMinutes": 15},
        "authorizerConfiguration": {"type": "IAM"},
        "memory": {"agentCoreMemoryConfiguration": {"arn": "a", "retrievalConfig": {
            "/ns/{actorId}": {"memoryStrategyId": "wrong"}}}},
    }
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
        json.dump(bad, f)
        badpath = f.name
    r2 = subprocess.run([sys.executable, os.path.join(HERE, "validate_config.py"), "--config", badpath],
                        capture_output=True, text=True)
    out = r2.stdout
    os.unlink(badpath)
    check("bad config exits non-zero", r2.returncode != 0)
    for needle in ["systemPrompt: must be a LIST",
                   "missing 'config'",
                   "plain name does not match",
                   "has a 'branch' field",
                   "must be a STRING",
                   "single 'uri'",
                   "slidingWindowMessagesCount' is not the real shape",
                   "network: not a top-level field",
                   "lifecycle: not a top-level field",
                   "there is no 'type' field",
                   "correct field is 'strategyId'"]:
        check(f"flags: {needle[:42]}", needle in out, "missing in output")


# ---------- wire_memory ----------
def test_wire_memory():
    print("wire_memory:")
    wm = load("wire_memory")
    check("ns_to_glob converts placeholders",
          wm.ns_to_glob("/episodes/{actorId}/{sessionId}") == "/episodes/*/*")
    check("ns_to_glob leaves literals", wm.ns_to_glob("/users/{actorId}/facts") == "/users/*/facts")
    str018 = wm.build_strategies()
    keys = [list(s.keys())[0] for s in str018]
    check("4 strategies built", len(str018) == 4)
    check("has episodic+userpref+summary+semantic",
          set(keys) == {"episodicMemoryStrategy", "userPreferenceMemoryStrategy",
                        "summaryMemoryStrategy", "semanticMemoryStrategy"})
    epi = next(s["episodicMemoryStrategy"] for s in str018 if "episodicMemoryStrategy" in s)
    check("episodic has reflectionConfiguration", "reflectionConfiguration" in epi)
    check("strategy has namespaces list", isinstance(epi["namespaces"], list) and epi["namespaces"])
    pol = wm.build_iam_policy("arn:aws:bedrock-agentcore:us-east-1:1:memory/m-1")
    sids = {s["Sid"] for s in pol["Statement"]}
    check("iam policy has events+retrieval", sids == {"MemoryEvents", "MemoryRetrieval"})
    retr = next(s for s in pol["Statement"] if s["Sid"] == "MemoryRetrieval")
    globs = retr["Condition"]["StringLike"]["bedrock-agentcore:namespace"]
    check("iam namespaces are globbed", all("{" not in g for g in globs) and "/episodes/*/*" in globs)
    mc = wm.build_memory_config("arn:m", "ci-pipeline", {"Episodic": "e-1", "Semantic": "s-1"})
    rc = mc["agentCoreMemoryConfiguration"]["retrievalConfig"]
    sample = next(iter(rc.values()))
    check("memory config uses strategyId", "strategyId" in sample and "memoryStrategyId" not in sample)
    check("memory config actorId+messagesCount",
          mc["agentCoreMemoryConfiguration"]["actorId"] == "ci-pipeline"
          and mc["agentCoreMemoryConfiguration"]["messagesCount"] == 20)


# ---------- update_harness ----------
def test_update_harness():
    print("update_harness:")
    uh = load("update_harness")
    structs = {"memory", "model", "environment", "environmentArtifact", "authorizerConfiguration", "truncation"}
    cfg = {"allowedTools": ["browser_*"], "maxTokens": 100,
           "memory": {"agentCoreMemoryConfiguration": {"arn": "a"}},
           "model": {"bedrockModelConfig": {"modelId": "m"}},
           "tags": {"t": "v"}, "name": "X"}
    p = uh.wrap_payload(cfg, structs, None)
    check("structure field wrapped in optionalValue", p["memory"] == {"optionalValue": cfg["memory"]})
    check("model wrapped", p["model"] == {"optionalValue": cfg["model"]})
    check("list field NOT wrapped", p["allowedTools"] == ["browser_*"])
    check("int field NOT wrapped", p["maxTokens"] == 100)
    check("tags excluded from payload", "tags" not in p)
    check("name excluded from payload", "name" not in p)
    p2 = uh.wrap_payload(cfg, structs, only_fields=["allowedTools"])
    check("only_fields restricts payload", set(p2.keys()) == {"allowedTools"})
    already = uh.wrap_payload({"memory": {"optionalValue": {"x": 1}}}, structs, None)
    check("does not double-wrap optionalValue", already["memory"] == {"optionalValue": {"x": 1}})


# ---------- setup_observability ----------
def test_setup_observability():
    print("setup_observability:")
    so = load("setup_observability")
    stmt = so.desired_policy_statement("123456789012", "us-east-1", "/aws/x")
    check("xray-style statement has delivery principal",
          stmt["Principal"]["Service"] == "delivery.logs.amazonaws.com")
    merged = so.merge_resource_policy(None, stmt)
    check("merge into empty creates one statement", len(merged["Statement"]) == 1)
    existing = {"Version": "2012-10-17", "Statement": [{"Sid": "Other", "Effect": "Allow"}]}
    merged2 = so.merge_resource_policy(existing, stmt)
    sids = {s["Sid"] for s in merged2["Statement"]}
    check("merge preserves existing statements", "Other" in sids and stmt["Sid"] in sids)
    merged3 = so.merge_resource_policy(merged2, stmt)
    count = sum(1 for s in merged3["Statement"] if s["Sid"] == stmt["Sid"])
    check("merge is idempotent on Sid", count == 1)


# ---------- create_harness ----------
def test_create_harness():
    print("create_harness:")
    ch = load("create_harness")
    stripped = ch._strip_comments({"_comment": "x", "harnessName": "H", "nested": {"_n": 1, "k": 2}})
    check("_strip_comments drops _-keys", stripped == {"harnessName": "H", "nested": {"k": 2}})
    kw = ch.build_kwargs({"name": "MyH", "model": {}}, "arn:role")
    check("name mapped to harnessName", kw.get("harnessName") == "MyH" and "name" not in kw)
    check("executionRoleArn set", kw["executionRoleArn"] == "arn:role")
    check("clientToken >= 33 chars", len(kw["clientToken"]) >= 33)
    kw2 = ch.build_kwargs({"harnessName": "Keep"}, "arn:role")
    check("existing harnessName preserved", kw2["harnessName"] == "Keep")
    # template loads + strips cleanly
    cfg = ch.load_config(TEMPLATE)
    check("template has no _-keys after load",
          all(not k.startswith("_") for k in cfg) and "harnessName" in cfg)


def main():
    for t in (test_validate_config, test_wire_memory, test_update_harness,
              test_setup_observability, test_create_harness):
        t()
    print("\n" + "=" * 40)
    print(f"RESULT: {_passed} passed, {_failed} failed")
    return 0 if _failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())

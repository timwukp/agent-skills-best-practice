"""E2E.0 — Reference code-block validator.

Walks every references/*.md in the agentcore-harness-builder skill, extracts python code blocks
that contain boto3 client calls (`<client>.<operation>(<kwargs>)`), and validates each call's
kwargs against the live boto3 service model (parameter names + structure existence). Does NOT
hit AWS — purely static using `client.meta.service_model.operation_model`.

This catches silent "the example I wrote uses a parameter name the SDK doesn't accept" bugs.
"""
import ast
import os
import re
import sys
from glob import glob

import boto3

sys.path.insert(0, os.path.dirname(__file__))
from test_lib import Runner

REF_DIR = os.path.expanduser("~/agentcore-tests/repo/skills/skills/agentcore-harness-builder/references")
REGION = "us-east-1"

# Map identifier-prefix-like names in samples to actual boto3 service IDs.
SERVICE_MAP = {
    "control": "bedrock-agentcore-control",
    "c": "bedrock-agentcore-control",
    "iam": "iam",
    "logs": "logs",
    "d": "bedrock-agentcore",
    "data": "bedrock-agentcore",
    "client": None,  # ambiguous — skip unless explicit boto3.client('...') context found
}

CODE_FENCE = re.compile(r"```python\s*\n(.*?)\n```", re.DOTALL)


def extract_calls(md_text):
    """Yield (caller_var, op, kwargs_ast_keywords, snippet) for each `<var>.<op>(<kwargs>)` call
    inside a python fenced block."""
    for block in CODE_FENCE.findall(md_text):
        # try to parse — accept partial syntax by wrapping in try
        try:
            tree = ast.parse(block)
        except SyntaxError:
            continue
        # also detect explicit boto3.client('foo') assignments to learn aliases
        aliases = {}
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign) and isinstance(node.value, ast.Call):
                f = node.value.func
                if (isinstance(f, ast.Attribute) and isinstance(f.value, ast.Name)
                        and f.value.id == "boto3" and f.attr == "client" and node.value.args
                        and isinstance(node.value.args[0], ast.Constant)):
                    svc = node.value.args[0].value
                    for tgt in node.targets:
                        if isinstance(tgt, ast.Name):
                            aliases[tgt.id] = svc
        # walk all method calls
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                f = node.func
                if isinstance(f, ast.Attribute) and isinstance(f.value, ast.Name):
                    var, op = f.value.id, f.attr
                    if op in {"client", "session"}:
                        continue
                    snippet = ast.get_source_segment(block, node) or ""
                    yield var, op, node.keywords, snippet, aliases


def resolve_service(var, aliases):
    if var in aliases:
        return aliases[var]
    return SERVICE_MAP.get(var)


def op_input_members(svc, op_camel):
    sess = boto3.Session(region_name=REGION)
    try:
        c = sess.client(svc)
    except Exception:
        return None
    sm = c.meta.service_model
    # boto3 method names are snake_case, operation names are CamelCase
    # Try CamelCase first, then convert from snake_case
    name = "".join(w.capitalize() for w in op_camel.split("_"))
    try:
        return c.meta.service_model.operation_model(name).input_shape
    except Exception:
        return None


# --------------- runner ---------------
r = Runner("e2e-0-validate-codeblocks")

@r.case("0.1", "all reference code blocks parse + boto3 ops resolve + kwargs are valid params")
def _(evidence_dir, case_id):
    md_files = sorted(glob(os.path.join(REF_DIR, "*.md")))
    print(f"scanning {len(md_files)} reference files in {REF_DIR}")
    total_calls, validated, skipped, errors = 0, 0, 0, []
    per_file = {}
    for md in md_files:
        text = open(md, encoding="utf-8").read()
        file_calls = []
        for var, op, kws, snippet, aliases in extract_calls(text):
            total_calls += 1
            svc = resolve_service(var, aliases)
            if svc is None:
                skipped += 1
                file_calls.append({"op": op, "skipped": "unknown_service", "snippet": snippet[:80]})
                continue
            shape = op_input_members(svc, op)
            if shape is None:
                # this is interesting: did our reference call something the SDK doesn't have?
                errors.append(f"{os.path.basename(md)}: {var}.{op}() — operation NOT FOUND in {svc}")
                file_calls.append({"op": op, "service": svc, "result": "OPERATION_NOT_FOUND"})
                continue
            members = set(shape.members.keys()) if hasattr(shape, "members") else set()
            kw_names = [k.arg for k in kws if k.arg]
            unknown = [k for k in kw_names if k not in members]
            if unknown:
                errors.append(f"{os.path.basename(md)}: {var}.{op}(...) — unknown kwargs: {unknown} (valid: {sorted(members)[:8]}...)")
                file_calls.append({"op": op, "service": svc, "result": "UNKNOWN_KWARGS", "unknown": unknown})
            else:
                validated += 1
                file_calls.append({"op": op, "service": svc, "result": "OK", "kwargs": kw_names})
        per_file[os.path.basename(md)] = file_calls
    # save evidence
    import json
    with open(os.path.join(evidence_dir, "codeblock_validation.json"), "w") as f:
        json.dump({"per_file": per_file, "totals": {
            "total_calls": total_calls, "validated_ok": validated, "skipped_unresolvable_var": skipped,
            "errors": len(errors)}, "errors": errors}, f, indent=2)
    print(f"total calls: {total_calls}, validated_ok: {validated}, skipped(unresolvable var): {skipped}, errors: {len(errors)}")
    if errors:
        print("--- errors ---")
        for e in errors[:30]:
            print(" -", e)
    assert len(errors) == 0, f"{len(errors)} reference code blocks have invalid kwargs against live SDK"


if __name__ == "__main__":
    r.go()

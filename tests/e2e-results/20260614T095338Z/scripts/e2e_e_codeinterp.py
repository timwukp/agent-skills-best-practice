"""E2E Track E — Code Interpreter session lifecycle.

Cases:
  E.1  start_code_interpreter_session (default identifier `aws.codeinterpreter.v1`)
  E.2  invoke_code_interpreter — run python "print(6*7)" and assert output contains "42"
  E.3  get_code_interpreter_session — assert it's READY/ACTIVE
  E.4  stop_code_interpreter_session — cleanup

Cost: cents.
"""
import json
import os
import secrets
import sys
import time

import boto3

sys.path.insert(0, os.path.dirname(__file__))
from test_lib import Runner

REGION = "us-east-1"
CI_ID = "aws.codeinterpreter.v1"

c = boto3.client("bedrock-agentcore", region_name=REGION)

state = {}
r = Runner("e2e-e-codeinterp")


@r.case("E.1", "start_code_interpreter_session")
def _(evidence_dir, case_id):
    resp = c.start_code_interpreter_session(
        codeInterpreterIdentifier=CI_ID,
        name=f"e2e-test-{secrets.token_hex(8)}",
        sessionTimeoutSeconds=300,
    )
    state["sid"] = resp["sessionId"]
    state["arn"] = resp.get("codeInterpreterArn") or resp.get("codeInterpreterIdentifier") or CI_ID
    print("session:", state["sid"])
    with open(os.path.join(evidence_dir, "start.json"), "w") as f:
        json.dump(resp, f, indent=2, default=str)


@r.case("E.2", "invoke_code_interpreter — assert print(6*7) yields 42")
def _(evidence_dir, case_id):
    code = 'print("CI_TEST_RESULT=", 6*7)'
    resp = c.invoke_code_interpreter(
        codeInterpreterIdentifier=CI_ID,
        sessionId=state["sid"],
        name="executeCode",
        arguments={"code": code, "language": "python"},
    )
    # response is a streaming event response; collect events
    out_text = ""
    if "stream" in resp:
        for ev in resp["stream"]:
            # event types: "result" / "structuredContent" / etc, depending on contract
            try:
                key, val = next(iter(ev.items()))
                out_text += json.dumps(val, default=str) + "\n"
            except Exception:
                out_text += str(ev) + "\n"
    else:
        out_text = json.dumps(resp, default=str)
    print("invoke output:", out_text[:600])
    with open(os.path.join(evidence_dir, "invoke.txt"), "w") as f:
        f.write(out_text)
    assert "42" in out_text, f"42 missing in CI output: {out_text[:300]}"


@r.case("E.3", "get_code_interpreter_session — alive")
def _(evidence_dir, case_id):
    s = c.get_code_interpreter_session(codeInterpreterIdentifier=CI_ID, sessionId=state["sid"])
    print("status:", s.get("status"))
    with open(os.path.join(evidence_dir, "get.json"), "w") as f:
        json.dump(s, f, indent=2, default=str)
    st = s.get("status") or ""
    assert st.upper() in ("READY", "ACTIVE", "RUNNING"), f"unexpected status {st}"


@r.case("E.99", "stop_code_interpreter_session — cleanup")
def _(evidence_dir, case_id):
    sid = state.get("sid")
    if not sid:
        return
    try:
        c.stop_code_interpreter_session(codeInterpreterIdentifier=CI_ID, sessionId=sid)
        print("stopped", sid)
    except Exception as e:
        print("stop err:", e)


if __name__ == "__main__":
    r.go()

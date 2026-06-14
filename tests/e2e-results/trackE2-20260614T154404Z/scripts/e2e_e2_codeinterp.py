"""E2E Track E (batch 2) — deepen Code Interpreter: file + command tools, cross-tool persistence.

Batch-1 already covered start/executeCode/get/stop. This exercises the other CI tools:
writeFiles, listFiles, readFiles, executeCommand, and code↔file persistence within one session.

Cases:
  E2.1  start_code_interpreter_session
  E2.2  writeFiles — write /tmp work file
  E2.3  listFiles — assert the file is present
  E2.4  readFiles — assert content round-trips
  E2.5  executeCommand — shell `cat` the file
  E2.6  executeCode — python reads the same file (proves session filesystem persistence across tools)
  E2.99 stop_code_interpreter_session
"""
import json
import os
import secrets
import sys

import boto3

sys.path.insert(0, os.path.dirname(__file__))
from test_lib import Runner

REGION = "us-east-1"
CI_ID = "aws.codeinterpreter.v1"
c = boto3.client("bedrock-agentcore", region_name=REGION)

state = {}
r = Runner("e2e-e2-codeinterp")
WORK = "demo/note.txt"
TEXT = "hello-from-writeFiles-" + secrets.token_hex(4)


def _invoke(name, arguments):
    resp = c.invoke_code_interpreter(codeInterpreterIdentifier=CI_ID, sessionId=state["sid"],
                                     name=name, arguments=arguments)  # arguments is a DICT, not JSON str
    out = []
    for ev in resp["stream"]:
        out.append(ev)
    return out


@r.case("E2.1", "start_code_interpreter_session")
def _(evidence_dir, case_id):
    resp = c.start_code_interpreter_session(codeInterpreterIdentifier=CI_ID,
                                            name="e2e-deep-" + secrets.token_hex(6))
    state["sid"] = resp["sessionId"]
    print("session:", state["sid"], "status:", resp.get("status"))


@r.case("E2.2", "writeFiles — write a work file")
def _(evidence_dir, case_id):
    evs = _invoke("writeFiles", {"content": [{"path": WORK, "text": TEXT}]})
    with open(os.path.join(evidence_dir, "writeFiles.json"), "w") as f:
        json.dump(evs, f, indent=2, default=str)
    print("writeFiles ok")


@r.case("E2.3", "listFiles — file is present")
def _(evidence_dir, case_id):
    evs = _invoke("listFiles", {"directoryPath": "demo"})
    blob = json.dumps(evs, default=str)
    assert "note.txt" in blob, f"note.txt not in listing: {blob[:300]}"
    print("listFiles sees note.txt")


@r.case("E2.4", "readFiles — content round-trips")
def _(evidence_dir, case_id):
    evs = _invoke("readFiles", {"paths": [WORK]})
    blob = json.dumps(evs, default=str)
    assert TEXT in blob, f"text not round-tripped: {blob[:300]}"
    print("readFiles round-trip ok")


@r.case("E2.5", "executeCommand — shell cat the file")
def _(evidence_dir, case_id):
    evs = _invoke("executeCommand", {"command": f"cat {WORK}"})
    blob = json.dumps(evs, default=str)
    assert TEXT in blob, f"cat output missing text: {blob[:300]}"
    print("executeCommand cat ok")


@r.case("E2.6", "executeCode — python reads the same file (cross-tool persistence)")
def _(evidence_dir, case_id):
    code = f"print(open('{WORK}').read())"
    evs = _invoke("executeCode", {"code": code, "language": "python"})
    blob = json.dumps(evs, default=str)
    assert TEXT in blob, f"python read missing text: {blob[:300]}"
    print("executeCode cross-tool persistence ok")


@r.case("E2.99", "stop_code_interpreter_session")
def _(evidence_dir, case_id):
    if state.get("sid"):
        c.stop_code_interpreter_session(codeInterpreterIdentifier=CI_ID, sessionId=state["sid"])
        print("stopped", state["sid"])


if __name__ == "__main__":
    r.go()

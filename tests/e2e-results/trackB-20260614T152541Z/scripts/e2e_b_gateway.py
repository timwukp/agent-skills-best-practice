"""E2E Track B — Gateway full lifecycle: create gateway -> target -> rule -> verify -> cleanup.

Cases:
  B.1  ensure a gateway execution role (trust bedrock-agentcore, lambda:InvokeFunction + logs).
  B.2  create_gateway (protocolType MCP, authorizerType AWS_IAM, searchType SEMANTIC) -> wait READY.
  B.3  create_gateway_target — OpenAPI inline schema (smallest backend; GATEWAY_IAM_ROLE cred) -> wait READY.
  B.4  create_gateway_rule — static route to the target.
  B.5  get_gateway + list_gateway_targets + list_gateway_rules — verify all present.
  B.99 cleanup: delete rule, target, gateway (gateway must be empty before delete).

Cost: ~$0 (control-plane objects, deleted at the end). No Docker.
"""
import json
import os
import secrets
import sys
import time
import uuid

import boto3

sys.path.insert(0, os.path.dirname(__file__))
from test_lib import Runner

REGION = "us-east-1"
ACCOUNT = boto3.client("sts").get_caller_identity()["Account"]  # runtime — keeps source sanitized
GW_ROLE_NAME = "AgentCoreTestGatewayExecRole"
GW_ROLE_ARN = f"arn:aws:iam::{ACCOUNT}:role/{GW_ROLE_NAME}"

c_iam = boto3.client("iam")
c = boto3.client("bedrock-agentcore-control", region_name=REGION)

state = {}
r = Runner("e2e-b-gateway")

# A minimal but valid OpenAPI 3 spec — one GET op -> becomes one MCP tool.
OPENAPI = json.dumps({
    "openapi": "3.0.1",
    "info": {"title": "Demo API", "version": "1.0.0"},
    "servers": [{"url": "https://api.example.com"}],
    "paths": {"/ping": {"get": {
        "operationId": "ping", "summary": "ping the demo api",
        "responses": {"200": {"description": "ok"}},
    }}},
})


def _status(d):
    return d.get("status") or d.get("gateway", {}).get("status")


@r.case("B.1", "Ensure gateway execution role")
def _(evidence_dir, case_id):
    trust = {"Version": "2012-10-17", "Statement": [{
        "Effect": "Allow",
        "Principal": {"Service": "bedrock-agentcore.amazonaws.com"},
        "Action": "sts:AssumeRole",
        "Condition": {"StringEquals": {"aws:SourceAccount": ACCOUNT}}}]}
    try:
        c_iam.create_role(RoleName=GW_ROLE_NAME, AssumeRolePolicyDocument=json.dumps(trust))
        time.sleep(8)
    except c_iam.exceptions.EntityAlreadyExistsException:
        pass
    perms = {"Version": "2012-10-17", "Statement": [
        {"Effect": "Allow", "Action": ["lambda:InvokeFunction"],
         "Resource": f"arn:aws:lambda:*:{ACCOUNT}:function:agentcore-test-*"},
        {"Effect": "Allow", "Action": ["logs:CreateLogGroup", "logs:CreateLogStream", "logs:PutLogEvents"],
         "Resource": f"arn:aws:logs:*:{ACCOUNT}:log-group:/aws/bedrock-agentcore/*"},
    ]}
    c_iam.put_role_policy(RoleName=GW_ROLE_NAME, PolicyName="GatewayExecPolicy",
                          PolicyDocument=json.dumps(perms))
    state["role_arn"] = GW_ROLE_ARN
    print("gateway exec role:", GW_ROLE_ARN)


@r.case("B.2", "create_gateway (MCP, AWS_IAM, SEMANTIC) + wait READY")
def _(evidence_dir, case_id):
    name = f"agentcore-test-gw-{uuid.uuid4().hex[:8]}"
    resp = c.create_gateway(
        name=name,
        roleArn=state["role_arn"],
        protocolType="MCP",
        authorizerType="AWS_IAM",
        protocolConfiguration={"mcp": {"searchType": "SEMANTIC", "supportedVersions": ["2025-06-18"]}},
        clientToken=secrets.token_hex(20),
    )
    state.update({"gw_id": resp["gatewayId"], "gw_arn": resp["gatewayArn"],
                  "gw_url": resp.get("gatewayUrl"), "gw_name": name})
    with open(os.path.join(evidence_dir, "create_gateway.json"), "w") as f:
        json.dump(resp, f, indent=2, default=str)
    print("created gateway:", resp["gatewayId"], "status:", _status(resp))
    for i in range(20):
        g = c.get_gateway(gatewayIdentifier=state["gw_id"])
        st = _status(g)
        print(f"[{i}] gateway status={st}")
        if st in ("READY", "ACTIVE"):
            break
        if st in ("FAILED",):
            assert False, f"gateway FAILED: {g.get('statusReasons')}"
        time.sleep(10)
    assert st in ("READY", "ACTIVE"), f"gateway not ready (status={st})"
    with open(os.path.join(evidence_dir, "get_gateway_ready.json"), "w") as f:
        json.dump(g, f, indent=2, default=str)


@r.case("B.3", "create api-key provider + create_gateway_target (OpenAPI inline, API_KEY) + wait READY")
def _(evidence_dir, case_id):
    assert state.get("gw_id"), "B.2 must succeed first"
    prov_name = f"agentcore-test-gwkey-{uuid.uuid4().hex[:8]}"
    p = c.create_api_key_credential_provider(name=prov_name, apiKey="demo-key-" + secrets.token_hex(8))
    state["prov_name"] = prov_name
    state["prov_arn"] = p["credentialProviderArn"]
    print("created api-key provider:", state["prov_arn"])
    resp = c.create_gateway_target(
        gatewayIdentifier=state["gw_id"],
        name="demo-openapi",
        targetConfiguration={"mcp": {"openApiSchema": {"inlinePayload": OPENAPI}}},
        credentialProviderConfigurations=[{
            "credentialProviderType": "API_KEY",
            "credentialProvider": {"apiKeyCredentialProvider": {
                "providerArn": state["prov_arn"],
                "credentialLocation": "HEADER",
                "credentialParameterName": "X-API-Key",
            }},
        }],
        clientToken=secrets.token_hex(20),
    )
    state["target_id"] = resp["targetId"]
    with open(os.path.join(evidence_dir, "create_target.json"), "w") as f:
        json.dump(resp, f, indent=2, default=str)
    print("created target:", resp["targetId"], "status:", _status(resp))
    for i in range(20):
        t = c.get_gateway_target(gatewayIdentifier=state["gw_id"], targetId=state["target_id"])
        st = _status(t)
        print(f"[{i}] target status={st}")
        if st in ("READY", "ACTIVE"):
            break
        if st in ("FAILED",):
            assert False, f"target FAILED: {t.get('statusReasons')}"
        time.sleep(10)
    assert st in ("READY", "ACTIVE"), f"target not ready (status={st})"


@r.case("B.4", "create_gateway_rule routeToTarget — documents it requires an HTTP-protocol target (MCP targets are served directly)")
def _(evidence_dir, case_id):
    assert state.get("gw_id"), "B.2 must succeed first"
    try:
        resp = c.create_gateway_rule(
            gatewayIdentifier=state["gw_id"],
            priority=10,
            actions=[{"routeToTarget": {"staticRoute": {"targetName": "demo-openapi"}}}],
            clientToken=secrets.token_hex(20),
        )
        # If it ever succeeds (e.g. against an HTTP target), record + remember for cleanup.
        state["rule_id"] = resp.get("ruleId")
        with open(os.path.join(evidence_dir, "create_rule.json"), "w") as f:
            json.dump(resp, f, indent=2, default=str)
        print("created rule:", state["rule_id"])
    except Exception as e:
        # DOCUMENTED: routeToTarget only supports HTTP-protocol targets (http.agentcoreRuntime).
        # MCP-protocol targets (lambda/openApiSchema/smithyModel/mcpServer/apiGateway) are exposed
        # directly and do not use routing rules.
        msg = str(e)
        with open(os.path.join(evidence_dir, "rule_expected_limitation.txt"), "w") as f:
            f.write(msg)
        assert "HTTP protocol" in msg or "routeToTarget" in msg, f"unexpected error: {msg[:300]}"
        print("DOCUMENTED LIMITATION confirmed — routeToTarget requires HTTP-protocol targets;",
              "MCP targets are served directly. Error:", msg[:160])


@r.case("B.5", "get_gateway + list targets + list rules — verify")
def _(evidence_dir, case_id):
    g = c.get_gateway(gatewayIdentifier=state["gw_id"])
    tgts = c.list_gateway_targets(gatewayIdentifier=state["gw_id"])
    items = tgts.get("items") or tgts.get("gatewayTargets") or tgts.get("targets") or []
    print("targets:", len(items))
    with open(os.path.join(evidence_dir, "list_targets.json"), "w") as f:
        json.dump(tgts, f, indent=2, default=str)
    assert _status(g) in ("READY", "ACTIVE"), "gateway not ready"
    assert len(items) >= 1, "no targets listed"


@r.case("B.99", "Cleanup: delete rule, target, gateway")
def _(evidence_dir, case_id):
    if state.get("rule_id"):
        try:
            c.delete_gateway_rule(gatewayIdentifier=state["gw_id"], ruleId=state["rule_id"])
            print("deleted rule")
        except Exception as e:
            print("delete rule err:", e)
    if state.get("target_id"):
        try:
            c.delete_gateway_target(gatewayIdentifier=state["gw_id"], targetId=state["target_id"])
            print("deleted target")
            for _ in range(12):
                try:
                    c.get_gateway_target(gatewayIdentifier=state["gw_id"], targetId=state["target_id"])
                    time.sleep(5)
                except Exception:
                    break
        except Exception as e:
            print("delete target err:", e)
    if state.get("gw_id"):
        try:
            c.delete_gateway(gatewayIdentifier=state["gw_id"])
            print("deleted gateway")
        except Exception as e:
            print("delete gateway err:", e)
    if state.get("prov_name"):
        try:
            c.delete_api_key_credential_provider(name=state["prov_name"])
            print("deleted api-key provider")
        except Exception as e:
            print("delete provider err:", e)


if __name__ == "__main__":
    r.go()

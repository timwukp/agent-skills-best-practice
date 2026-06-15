"""E2E Track D (batch 2) — Identity / Policy / Registry control-plane lifecycles.

Deliberately EXCLUDES Payments (real payment processors — never e2e'd).

Cases:
  D2.1  Workload Identity: create -> get -> delete.
  D2.2  Policy: create policy engine -> create Cedar policy -> get -> delete (policy, engine).
  D2.3  OAuth2 credential provider (GoogleOauth2, dummy client stored in Token Vault) -> get -> delete.
  D2.4  Registry record: create registry -> create AGENT_SKILLS record (inline) -> get -> delete both.

Cost: ~$0 (control-plane objects, all deleted). No backend resources.
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
c = boto3.client("bedrock-agentcore-control", region_name=REGION)

state = {}
r = Runner("e2e-d2-identity-policy-registry")


@r.case("D2.1", "Workload Identity: create -> get -> delete")
def _(evidence_dir, case_id):
    name = f"agentcore_test_wi_{uuid.uuid4().hex[:8]}"
    resp = c.create_workload_identity(name=name)
    arn = resp["workloadIdentityArn"]
    with open(os.path.join(evidence_dir, "workload_identity.json"), "w") as f:
        json.dump(resp, f, indent=2, default=str)
    print("created workload identity:", arn)
    g = c.get_workload_identity(name=name)
    assert g["name"] == name, "get mismatch"
    c.delete_workload_identity(name=name)
    print("deleted workload identity")


@r.case("D2.2", "Policy engine + Cedar policy: create -> get -> delete")
def _(evidence_dir, case_id):
    eng_name = f"agentcore_test_pe_{uuid.uuid4().hex[:8]}"
    eng = c.create_policy_engine(name=eng_name, description="e2e test engine",
                                 clientToken=secrets.token_hex(20))
    eid = eng["policyEngineId"]
    state["engine_id"] = eid
    with open(os.path.join(evidence_dir, "policy_engine.json"), "w") as f:
        json.dump(eng, f, indent=2, default=str)
    print("created policy engine:", eid, "status:", eng.get("status"))
    # wait until usable
    for i in range(12):
        s = c.get_policy_engine(policyEngineId=eid)
        st = s.get("status")
        print(f"[{i}] engine status={st}")
        if st in ("READY", "ACTIVE", "AVAILABLE"):
            break
        time.sleep(5)
    # Cedar requires a constrained resource (wildcard resource is rejected); scope to the resource type.
    cedar = 'permit(principal, action, resource is AgentCore::Gateway);'
    pol = c.create_policy(
        name=f"agentcore_test_pol_{uuid.uuid4().hex[:8]}",
        policyEngineId=eid,
        definition={"cedar": {"statement": cedar}},
        description="e2e allow-all test policy",
        clientToken=secrets.token_hex(20),
    )
    pid = pol["policyId"]
    state["policy_id"] = pid
    with open(os.path.join(evidence_dir, "policy.json"), "w") as f:
        json.dump(pol, f, indent=2, default=str)
    print("created policy:", pid)
    gp = c.get_policy(policyEngineId=eid, policyId=pid)
    assert gp["policyId"] == pid
    # cleanup
    try:
        c.delete_policy(policyEngineId=eid, policyId=pid); print("deleted policy")
    except Exception as e:
        print("delete policy err:", e)
    try:
        c.delete_policy_engine(policyEngineId=eid); print("deleted policy engine")
    except Exception as e:
        print("delete engine err:", e)


@r.case("D2.3", "OAuth2 credential provider (GoogleOauth2): create -> get -> delete")
def _(evidence_dir, case_id):
    name = f"agentcore-test-oauth-{uuid.uuid4().hex[:8]}"
    resp = c.create_oauth2_credential_provider(
        name=name,
        credentialProviderVendor="GoogleOauth2",
        oauth2ProviderConfigInput={"googleOauth2ProviderConfig": {
            "clientId": "e2e-dummy-client-id.apps.googleusercontent.com",
            "clientSecret": "e2e-dummy-secret-" + secrets.token_hex(8),
        }},
    )
    arn = resp["credentialProviderArn"]
    state["oauth_name"] = name
    with open(os.path.join(evidence_dir, "oauth_provider.json"), "w") as f:
        # do not persist the secret-bearing fields verbatim; keep arn/name/status only
        json.dump({k: resp.get(k) for k in ("name", "credentialProviderArn", "status", "callbackUrl")},
                  f, indent=2, default=str)
    print("created oauth2 provider:", arn)
    g = c.get_oauth2_credential_provider(name=name)
    assert g["name"] == name
    c.delete_oauth2_credential_provider(name=name)
    print("deleted oauth2 provider")


@r.case("D2.4", "Registry record (AGENT_SKILLS inline): create registry + record -> get -> delete both")
def _(evidence_dir, case_id):
    reg = c.create_registry(name=f"agentcore-test-reg-{uuid.uuid4().hex[:8]}",
                            description="e2e", clientToken=secrets.token_hex(20))
    reg_arn = reg["registryArn"]
    reg_id = reg_arn.rsplit("/", 1)[-1]
    state["reg_id"] = reg_id
    print("created registry:", reg_id, "status:", reg.get("status"))
    # CreateRegistryRecord rejects a registry that is still CREATING — wait for READY.
    for i in range(18):
        g = c.get_registry(registryId=reg_id)
        st = g.get("status")
        print(f"[{i}] registry status={st}")
        if st in ("READY", "ACTIVE", "AVAILABLE"):
            break
        time.sleep(5)
    skill_md = "---\nname: demo\ndescription: demo skill for e2e\n---\n# Demo\n"
    rec = c.create_registry_record(
        registryId=reg_id,
        name=f"demo-skill-{uuid.uuid4().hex[:6]}",
        descriptorType="AGENT_SKILLS",
        descriptors={"agentSkills": {"skillMd": {"inlineContent": skill_md}}},
        clientToken=secrets.token_hex(20),
    )
    with open(os.path.join(evidence_dir, "registry_record.json"), "w") as f:
        json.dump(rec, f, indent=2, default=str)
    rec_arn = rec["recordArn"]
    rec_id = rec_arn.rsplit("/", 1)[-1]
    state["rec_id"] = rec_id
    print("created registry record:", rec_arn, "status:", rec.get("status"))
    try:
        c.delete_registry_record(registryId=reg_id, recordId=rec_id); print("deleted record")
    except Exception as e:
        print("delete record err:", e)
    try:
        c.delete_registry(registryId=reg_id); print("deleted registry")
    except Exception as e:
        print("delete registry err:", e)


if __name__ == "__main__":
    r.go()

"""E2E Track D (batch 1) — minimal Identity (API key cred provider) + Registry e2e.

Cases:
  D.1  CreateApiKeyCredentialProvider (Identity, simplest creation)
  D.2  GetApiKeyCredentialProvider — verify it exists
  D.3  CreateRegistry (Registry, simplest creation)
  D.4  GetRegistry — verify it exists
  D.99 Cleanup: delete both

NOT YET TESTED in this batch (need follow-up research):
  - CreateOauth2CredentialProvider (oauth2ProviderConfigInput is a vendor-specific union)
  - CreateWorkloadIdentity
  - CreatePolicyEngine + CreatePolicy (definition structure needs investigation)
  - Payment* (skipped intentionally — connects to real payment processors)
  - CreateRegistryRecord (descriptor types union — needs follow-up)
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
r = Runner("e2e-d-identity-registry")


@r.case("D.1", "CreateApiKeyCredentialProvider")
def _(evidence_dir, case_id):
    name = f"agentcore-test-apikey-{uuid.uuid4().hex[:8]}"
    resp = c.create_api_key_credential_provider(name=name, apiKey="dummy-test-key-not-real")
    state["api_key_name"] = name
    state["api_key_arn"] = resp.get("credentialProviderArn") or resp.get("apiKeyCredentialProviderArn")
    print("created:", name, "->", state["api_key_arn"])
    with open(os.path.join(evidence_dir, "create_apikey.json"), "w") as f:
        json.dump(resp, f, indent=2, default=str)
    assert state["api_key_arn"], "no ARN in response"


@r.case("D.2", "GetApiKeyCredentialProvider — verify created")
def _(evidence_dir, case_id):
    resp = c.get_api_key_credential_provider(name=state["api_key_name"])
    print("get:", resp.get("name"), resp.get("credentialProviderVendor"))
    with open(os.path.join(evidence_dir, "get_apikey.json"), "w") as f:
        json.dump(resp, f, indent=2, default=str)
    assert resp.get("name") == state["api_key_name"]


@r.case("D.3", "CreateRegistry")
def _(evidence_dir, case_id):
    name = f"agentcore-test-reg-{uuid.uuid4().hex[:8]}"
    resp = c.create_registry(name=name, description="e2e test registry",
                              clientToken=secrets.token_hex(20))
    state["reg_name"] = name
    state["reg_arn"] = resp.get("registryArn") or resp.get("arn")
    # CreateRegistry returns only registryArn; derive id from the ARN's last path segment
    state["reg_id"] = state["reg_arn"].rsplit("/", 1)[-1] if state.get("reg_arn") else None
    print("created registry:", name, "id:", state["reg_id"], "arn:", state["reg_arn"])
    with open(os.path.join(evidence_dir, "create_registry.json"), "w") as f:
        json.dump(resp, f, indent=2, default=str)
    assert state["reg_id"], "no registryId derivable"


@r.case("D.4", "GetRegistry — verify created")
def _(evidence_dir, case_id):
    resp = c.get_registry(registryId=state["reg_id"])
    print("get:", resp.get("name"), resp.get("status"))
    with open(os.path.join(evidence_dir, "get_registry.json"), "w") as f:
        json.dump(resp, f, indent=2, default=str)


@r.case("D.99", "Cleanup")
def _(evidence_dir, case_id):
    if state.get("api_key_name"):
        try:
            c.delete_api_key_credential_provider(name=state["api_key_name"])
            print("deleted apikey provider", state["api_key_name"])
        except Exception as e:
            print("delete apikey err:", e)
    if state.get("reg_id"):
        try:
            c.delete_registry(registryId=state["reg_id"])
            print("deleted registry", state["reg_id"])
        except Exception as e:
            print("delete registry err:", e)


if __name__ == "__main__":
    r.go()

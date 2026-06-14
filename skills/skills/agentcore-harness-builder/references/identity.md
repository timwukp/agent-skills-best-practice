# Identity — Workload Identity, Token Vault, Credential Providers

AgentCore **Identity** manages who/what your agent is (workload identity) and how it authenticates to **outbound**
services (third-party APIs, OAuth providers). It complements the harness's **inbound** auth
(`authorizerConfiguration`, see `advanced-config.md`). Verified ops exist in `bedrock-agentcore-control`.

## Building blocks (verified operations)

| Concept | Operations | Purpose |
|---|---|---|
| **Workload Identity** | `CreateWorkloadIdentity`, `GetWorkloadIdentity`, `ListWorkloadIdentities`, `UpdateWorkloadIdentity`, `DeleteWorkloadIdentity` | A stable identity for an agent workload, used to scope access and auth. |
| **Token Vault** | `GetTokenVault`, `SetTokenVaultCMK` | Secure store for OAuth tokens / secrets the agent uses for outbound calls. `SetTokenVaultCMK` sets a customer-managed KMS key for encryption. |
| **API key credential provider** | `CreateApiKeyCredentialProvider` (+ Get/List/Update/Delete) | Store an API key the agent presents to a downstream API. |
| **OAuth2 credential provider** | `CreateOauth2CredentialProvider` (+ Get/List/Update/Delete) | Store an OAuth2 client config; the agent obtains/refreshes tokens for outbound calls. |
| **Payment credential provider** | `CreatePaymentCredentialProvider` (+ …) | Specialized provider for payment flows (see `payments.md`). |

## Two kinds of auth — don't conflate them

| | Inbound (who may call the harness) | Outbound (how the agent calls others) |
|---|---|---|
| Configured by | `authorizerConfiguration` on the harness (`advanced-config.md`) | Identity credential providers + Token Vault |
| Options | IAM (default) or `customJWTAuthorizer` | API key / OAuth2 credential providers |
| Used when | a client invokes `InvokeHarness` | a tool/Gateway makes an authenticated external request |

## How it connects to the harness

- **Gateway / remote MCP tools** reference outbound auth: a Gateway target's `outboundAuth` can be `awsIam`, `none`,
  or `oauth` with a `providerArn` (the OAuth2 credential provider ARN) and `scopes` — see `tools.md`.
- **Private git skills** reference a credential provider via `skills[].git.auth.credentialArn` — see `skills.md`.
- **Token Vault** is where the obtained tokens are stored; set a CMK with `SetTokenVaultCMK` for encryption control.

## Typical flow

1. Create a credential provider (`CreateOauth2CredentialProvider` or `CreateApiKeyCredentialProvider`) for the external
   service.
2. (Optional) `SetTokenVaultCMK` to encrypt the vault with your KMS key.
3. Reference the provider ARN from the consuming feature (Gateway target `outboundAuth.oauth.providerArn`, or skills git
   `auth.credentialArn`).
4. Grant the harness execution role permission to use the provider/vault.

## API surface

Identity is part of the preview control plane. Introspect exact shapes before scripting:
```bash
python scripts/preflight.py --show-shape CreateOauth2CredentialProvider --show-shape CreateWorkloadIdentity
```
Consult the AgentCore Identity dev guide and the SDK `bedrock_agentcore.identity` module for agent-side helpers.

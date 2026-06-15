# Gateway — Turn APIs into MCP Tools (build side)

A **Gateway** is an AWS-managed **MCP server** that fronts your existing capabilities — Lambda
functions, OpenAPI/Smithy APIs, other MCP servers, API Gateway REST APIs, or an AgentCore Runtime —
and exposes them as MCP tools with built-in auth, semantic tool search, and scaling. `references/tools.md`
covers the **consumer** side (attaching an *existing* gateway to a harness via
`tools[].config.agentCoreGateway.gatewayArn`). **This file covers the build side:** creating the gateway,
adding targets, and (optionally) routing rules. All shapes verified against `boto3 1.43.29`
(`bedrock-agentcore-control`).

## Contents
- [When a Gateway vs `remote_mcp` vs building your own](#when)
- [The three objects: Gateway → Target → Rule](#objects)
- [Create the Gateway](#create-gateway)
- [Add Targets (the 6 kinds)](#targets)
- [Outbound credentials for targets](#credentials)
- [Routing Rules (advanced)](#rules)
- [Wire the Gateway into a Harness](#wire)
- [CLI shortcut + lifecycle](#cli)
- [Gotchas](#gotchas)

---

## When

| Option | Use when |
|---|---|
| **Gateway** (`agentcore_gateway`) | You want AWS to host an MCP server that adapts **existing** APIs/Lambdas into tools, with managed inbound auth (JWT/IAM), semantic tool discovery, and per-target outbound credentials. Best when you have many tools or heterogeneous backends. |
| **`remote_mcp`** | You already run a streamable-HTTP MCP server and just want the harness to connect to it. No adaptation needed. |
| **Build your own MCP server** | The protocol/logic is custom. Author it with the separate `mcp-builder` skill, then expose via `remote_mcp` or host it on a Runtime. |

## Objects

A Gateway is built from three control-plane object types (all under `bedrock-agentcore-control`):

```
Gateway            ← the managed MCP endpoint (inbound auth + protocol)
  └── Target(s)    ← each adapts ONE backend (Lambda / OpenAPI / Smithy / MCP server / API GW / Runtime)
  └── Rule(s)      ← OPTIONAL request routing / traffic-split across targets
```

Operations: `CreateGateway` / `CreateGatewayTarget` / `CreateGatewayRule` (+ `Get`/`List`/`Update`/`Delete`
for each, plus `SynchronizeGatewayTargets`).

## Create Gateway

`CreateGateway` required: `name`, `roleArn`, `authorizerType`. Verified shape:

```python
import boto3, secrets
c = boto3.client("bedrock-agentcore-control", region_name="us-east-1")

resp = c.create_gateway(
    name="my-api-gateway",
    roleArn="arn:aws:iam::<ACCOUNT_ID>:role/MyGatewayExecRole",  # role the gateway assumes to call targets
    protocolType="MCP",                       # enum: only "MCP" today
    authorizerType="CUSTOM_JWT",              # CUSTOM_JWT | AWS_IAM | NONE | AUTHENTICATE_ONLY
    authorizerConfiguration={
        "customJWTAuthorizer": {
            "discoveryUrl": "https://<issuer>/.well-known/openid-configuration",  # required
            "allowedClients": ["<client-id>"],     # OR allowedAudience
            # "allowedAudience": ["..."], "allowedScopes": ["invoke"],
        }
    },
    protocolConfiguration={
        "mcp": {
            "searchType": "SEMANTIC",          # enum: SEMANTIC — enables semantic tool discovery
            "supportedVersions": ["2025-06-18"],
            "instructions": "Tools for the X domain.",
            # "sessionConfiguration": {"sessionTimeoutInSeconds": 3600},
            # "streamingConfiguration": {"enableResponseStreaming": True},
        }
    },
    clientToken=secrets.token_hex(20),
    # tags={"team": "platform"},
)
gateway_arn = resp["gatewayArn"]
gateway_url = resp["gatewayUrl"]      # the MCP endpoint your harness/clients call
```

**`authorizerType` (inbound auth) — verified enum:**

| Value | Meaning |
|---|---|
| `CUSTOM_JWT` | Validate a JWT against an OIDC `discoveryUrl`; gate on `allowedClients` / `allowedAudience` / `allowedScopes`. Most common. |
| `AWS_IAM` | SigV4 — callers authenticate with IAM. |
| `NONE` | No inbound auth (only for fully private/locked-down setups). |
| `AUTHENTICATE_ONLY` | Authenticate but don't authorize scopes. |

**Optional hardening on `CreateGateway` (all verified):**
- `kmsKeyArn` — CMK for encryption.
- `interceptorConfigurations[]` — a Lambda interceptor at `interceptionPoints` `REQUEST` and/or `RESPONSE`
  (`{"interceptor": {"lambda": {"arn": "..."}}, "interceptionPoints": ["REQUEST"], "inputConfiguration": {"passRequestHeaders": true}}`).
- `policyEngineConfiguration` — `{"arn": "<policy-engine-arn>", "mode": "LOG_ONLY" | "ENFORCE"}` to apply
  Policy guardrails (see `references/policy.md`).
- `customJWTAuthorizer.customClaims[]` — claim-based authZ
  (`inboundTokenClaimValueType` `STRING`/`STRING_ARRAY`, `claimMatchOperator` `EQUALS`/`CONTAINS`/`CONTAINS_ANY`).
- `customJWTAuthorizer.privateEndpoint` — `managedVpcResource` (vpcId + subnets + `endpointIpAddressType`
  `IPV4`/`IPV6`) or `selfManagedLatticeResource` for private inbound.

## Targets

Each **Target** adapts ONE backend into MCP tools. `CreateGatewayTarget` required: `gatewayIdentifier`,
`name`, `targetConfiguration`. The `targetConfiguration` is a **union** — exactly one of `mcp.*` (five
backend kinds) or `http.agentcoreRuntime`:

```python
t = c.create_gateway_target(
    gatewayIdentifier=gateway_arn,            # ARN or id
    name="orders-api",
    targetConfiguration={ "mcp": { ... one of the 5 forms below ... } },
    credentialProviderConfigurations=[ ... see Credentials ... ],
    clientToken=secrets.token_hex(20),
)
target_id = t["targetId"]
```

**The 6 target forms (verified):**

```python
# 1) Lambda — your function becomes one or more tools; you supply the tool schema
{"mcp": {"lambda": {
    "lambdaArn": "arn:aws:lambda:us-east-1:<ACCOUNT_ID>:function:my-fn",
    "toolSchema": {"inlinePayload": [                  # OR {"s3": {"uri": "s3://.../schema.json"}}
        {"name": "get_order", "description": "Fetch an order",
         "inputSchema": {"type": "object", "properties": {"id": {"type": "string"}}, "required": ["id"]}}
    ]},
}}}

# 2) OpenAPI — adapt a REST API from its OpenAPI spec
{"mcp": {"openApiSchema": {"s3": {"uri": "s3://my-bucket/openapi.json"}}}}      # OR {"inlinePayload": "<json>"}

# 3) Smithy — adapt an AWS-style Smithy model (e.g. DynamoDB)
{"mcp": {"smithyModel": {"s3": {"uri": "s3://my-bucket/model.json"}}}}          # OR inlinePayload

# 4) MCP server — front an existing remote MCP server
{"mcp": {"mcpServer": {
    "endpoint": "https://my-mcp.example.com/mcp",
    "listingMode": "DEFAULT",                          # or "DYNAMIC"
}}}

# 5) API Gateway — adapt an existing API Gateway REST API + stage
{"mcp": {"apiGateway": {
    "restApiId": "abc123", "stage": "prod",
    "apiGatewayToolConfiguration": {"toolFilters": [ ... ]},
}}}

# 6) HTTP → AgentCore Runtime — front a Runtime you deployed
{"http": {"agentcoreRuntime": {"arn": "<runtime-arn>", "qualifier": "DEFAULT"}}}
```

## Credentials

`credentialProviderConfigurations[]` tells the gateway **how to authenticate outbound** to each target.
`credentialProviderType` enum (verified): `GATEWAY_IAM_ROLE`, `OAUTH`, `API_KEY`,
`CALLER_IAM_CREDENTIALS`, `JWT_PASSTHROUGH`.

```python
# Simplest: the gateway uses its own execution role (good for Lambda / AWS targets)
[{"credentialProviderType": "GATEWAY_IAM_ROLE"}]

# API key (for an OpenAPI/HTTP backend) — references a pre-created API-key provider (see references/identity.md)
[{"credentialProviderType": "API_KEY", "credentialProvider": {"apiKeyCredentialProvider": {
    "providerArn": "<apikey-provider-arn>",
    "credentialLocation": "HEADER",            # or "QUERY_PARAMETER"
    "credentialParameterName": "X-API-Key",
}}}]

# OAuth (3-legged or client-credentials) — references a pre-created OAuth provider
[{"credentialProviderType": "OAUTH", "credentialProvider": {"oauthCredentialProvider": {
    "providerArn": "<oauth-provider-arn>",
    "scopes": ["read"],
    "grantType": "CLIENT_CREDENTIALS",         # CLIENT_CREDENTIALS | AUTHORIZATION_CODE | TOKEN_EXCHANGE
}}}]
```

The `providerArn`s come from Identity credential providers — see `references/identity.md` (Token Vault).

## Rules

**Rules are optional.** Without any rule, all targets are exposed directly. Add a `CreateGatewayRule` only
when you need request **routing** or **traffic-splitting** (e.g. blue/green across two targets).
Required: `gatewayIdentifier`, `priority`, `actions`.

> **Verified by e2e:** `routeToTarget` actions only support **HTTP-protocol** targets (the
> `http.agentcoreRuntime` target form). MCP-protocol targets (Lambda / OpenAPI / Smithy / MCP-server /
> API-Gateway) are **served directly** and reject `routeToTarget`
> (`ValidationException: routeToTarget only supports targets with HTTP protocol type`). Use rules for
> Runtime-backed HTTP targets, or for `configurationBundle` weighting — not to "expose" an MCP target.

```python
c.create_gateway_rule(
    gatewayIdentifier=gateway_arn,
    priority=10,                                   # lower = evaluated first
    conditions=[{"matchPaths": {"anyOf": ["/orders/*"]}}],     # or matchPrincipals.anyOf[].iamPrincipal
    actions=[{"routeToTarget": {"staticRoute": {"targetName": "orders-api"}}}],
    # weighted: {"routeToTarget": {"weightedRoute": {"trafficSplit": [ ... ]}}}
    clientToken=secrets.token_hex(20),
)
```

## Wire

Once the gateway is `READY`, attach it to a harness — the **consumer** shape from `references/tools.md`:

```jsonc
{"type": "agentcore_gateway", "name": "my_api", "config": {"agentCoreGateway": {
    "gatewayArn": "<gateway-arn>",
    "outboundAuth": {"oauth": {"providerArn": "<oauth-provider-arn>", "scopes": ["read"]}}
    // or "outboundAuth": {"awsIam": {}}  /  {"none": {}}
}}}
```

Then allowlist the resulting MCP tool names in `allowedTools` (use `@my_api/*` to allow all tools from
this gateway). The gateway's own inbound `authorizerType` must be satisfied by how the harness connects.

## CLI

The `bedrock-agentcore-starter-toolkit` wraps the create→target→cleanup flow and auto-provisions the IAM
role + a Cognito JWT authorizer if you don't pass them:

```bash
pip install bedrock-agentcore-starter-toolkit
agentcore gateway create-mcp-gateway --name MyGateway --region us-east-1
agentcore gateway create-mcp-gateway-target --gateway-arn <arn> --gateway-url <url> \
    --role-arn <role> --name MyLambdaTarget --target-type lambda
# cleanup (a gateway must have ZERO targets before delete, unless --force):
agentcore gateway delete-mcp-gateway --name MyGateway --force
```

## Gotchas

- **`protocolType` is `MCP`-only** today; `protocolConfiguration.mcp.searchType` is `SEMANTIC`.
- **A gateway must be empty before deletion** — delete its targets first, or use the CLI `--force`.
  (`SynchronizeGatewayTargets` reconciles target state if you manage many.)
- **`authorizerType=CUSTOM_JWT` needs a real `discoveryUrl`** (an OIDC issuer). For machine-to-machine
  with no external IdP, either let the CLI stand up Cognito, or use `AWS_IAM`.
- **Outbound vs inbound auth are different layers.** `authorizerType`/`authorizerConfiguration` gate who
  may *call the gateway* (inbound). `credentialProviderConfigurations` on each target govern how the
  gateway *calls the backend* (outbound). A target with a non-AWS backend needs an Identity provider ARN.
- **Lambda targets need a `toolSchema`** (inline or S3) so the gateway knows what tools the function
  exposes, and the gateway's execution role needs `lambda:InvokeFunction` on that ARN.

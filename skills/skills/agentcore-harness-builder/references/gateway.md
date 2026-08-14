# Gateway — Turn APIs into MCP Tools (build side)

A **Gateway** is an AWS-managed **MCP server** that fronts your existing capabilities — Lambda
functions, OpenAPI/Smithy APIs, other MCP servers, API Gateway REST APIs, or an AgentCore Runtime —
and exposes them as MCP tools with built-in auth, semantic tool search, and scaling. `references/tools.md`
covers the **consumer** side (attaching an *existing* gateway to a harness via
`tools[].config.agentCoreGateway.gatewayArn`). **This file covers the build side:** creating the gateway,
adding targets, and (optionally) routing rules. Shapes are verified against the `bedrock-agentcore-control`
service model in `botocore 1.43.68`; per-leaf live-verification status is in the §Targets index table.

## Contents
- [When a Gateway vs `remote_mcp` vs building your own](#when)
- [The objects: Gateway → Target → Rule → Rate limit](#objects)
- [Create the Gateway](#create-gateway)
- [Add Targets (11 union leaves; built-in connectors)](#targets)
- [Outbound credentials for targets](#credentials)
- [Routing Rules (advanced)](#rules)
- [Rate limits (per-user / per-group traffic control)](#rate-limits)
- [Wire the Gateway into a Harness](#wire)
- [CLI shortcut + lifecycle](#cli)
- [Gotchas](#gotchas)

---

## When

| Option | Use when |
|---|---|
| **Gateway** (`agentcore_gateway`) | You want AWS to host an MCP server that adapts **existing** APIs/Lambdas into tools, with managed inbound auth (JWT/IAM), semantic tool discovery, and per-target outbound credentials. Best when you have many tools or heterogeneous backends. |
| **`remote_mcp`** | You already run a streamable-HTTP MCP server and just want the harness to connect to it. No adaptation needed. |
| **Build your own MCP server** | The protocol/logic is custom. Author it yourself (an `mcp-builder` skill, if available in your environment, can help), then expose via `remote_mcp` or host it on a Runtime. |

## Objects

A Gateway is built from three control-plane object types (all under `bedrock-agentcore-control`):

```
Gateway              ← the managed MCP endpoint (inbound auth + protocol)
  └── Target(s)      ← each adapts ONE backend; pick one of the 11 union leaves
  │                     (see the §Targets index table)
  └── Rule(s)        ← OPTIONAL request routing / traffic-split across targets
  └── Rate limit(s)  ← OPTIONAL per-user/per-group requests / tokens / connections caps
```

Operations: `CreateGateway` / `CreateGatewayTarget` / `CreateGatewayRule` / `CreateGatewayRateLimit`
(+ `Get`/`List`/`Update`/`Delete` for each, plus `SynchronizeGatewayTargets` and
`BatchPutGatewayRateLimits`).

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

Each **Target** adapts ONE backend into MCP tools. `CreateGatewayTarget` required: **`gatewayIdentifier` and
`targetConfiguration` only** — `name` is optional (the service generates one), though you almost always want to set
it because tool names and rate-limit dimensions are derived from it.

```python
t = c.create_gateway_target(
    gatewayIdentifier=gateway_arn,            # ARN or id
    name="orders-api",
    targetConfiguration={ "mcp": {"lambda": { ... }} },      # exactly ONE union leaf
    credentialProviderConfigurations=[ ... see Credentials ... ],
    clientToken=secrets.token_hex(20),
    # metadataConfiguration={"allowedRequestHeaders": [...], "allowedQueryParameters": [...],
    #                        "allowedResponseHeaders": [...]},      # header/query passthrough allowlists
    # privateEndpoint={"managedVpcResource": {...}} | {"selfManagedLatticeResource": {...}},
)
target_id = t["targetId"]
```

`targetConfiguration` is a two-level union: pick one of `mcp` / `http` / `inference`, then exactly one leaf inside it.
**There are 11 leaves — 6 under `mcp`, 3 under `http`, 2 under `inference` — but only 8 can be created today.**
The `http.*` branch requires a gateway whose `protocolType` is not `MCP`, and `MCP` is the only value
`CreateGateway` accepts, so all three `http.*` leaves are currently unreachable. See
[§The `http.*` branch is unreachable today](#the-http-branch-is-unreachable-today).

| Union path | Adapts | Status |
|---|---|---|
| [`mcp.lambda`](#mcplambda) | your Lambda function + a tool schema you supply | live-verified 2026-08-12 |
| [`mcp.openApiSchema`](#mcpopenapischema) | a REST API described by an OpenAPI spec | live-verified 2026-08-12 |
| [`mcp.smithyModel`](#mcpsmithymodel) | an AWS-style Smithy model (e.g. DynamoDB) | live-verified 2026-08-12 |
| [`mcp.mcpServer`](#mcpmcpserver) | an existing remote MCP server | live-verified 2026-08-12 |
| [`mcp.apiGateway`](#mcpapigateway) | an API Gateway REST API + stage | live-verified 2026-08-12 |
| [`mcp.connector`](#mcpconnector) | an AWS-managed built-in tool (web-search, Knowledge Bases) | live-verified 2026-08-13 |
| [`inference.provider`](#inferenceprovider) | a model endpoint (the `tokens` rate-limit target type) | READY 2026-08-13 (control plane only) |
| [`inference.connector`](#inferenceconnector) | an AWS-managed inference connector | READY 2026-08-13 (control plane only) |
| [`http.agentcoreRuntime`](#httpagentcoreruntime) | an AgentCore Runtime you deployed | **not creatable 2026-08-13** |
| [`http.passthrough`](#httppassthrough) | any HTTPS endpoint speaking MCP or HTTP | **not creatable 2026-08-13** |
| [`http.connector`](#httpconnector) | an AWS-managed HTTP connector (e.g. `agentcore-memory`) | **not creatable 2026-08-13** |

> **Authoring note:** cite leaves by **union path** (`mcp.connector`), never by ordinal position in this list. The
> union keeps growing; ordinals rot, and other files link here.

> **"READY" is not "works".** For the two `inference.*` leaves, `READY` was reached with endpoints and
> providers that were never actually called. A target's status reflects control-plane validation only —
> `inference.connector/openai` and `/anthropic` reach `READY` with no credential provider at all, and
> `inference.provider` reaches `READY` pointing at `https://api.provider.invalid`. Treat `READY` on these
> two as "the shape was accepted", nothing more.

### mcp.lambda

Your function becomes one or more tools; you supply the tool schema.

```python
{"mcp": {"lambda": {
    "lambdaArn": "arn:aws:lambda:us-east-1:<ACCOUNT_ID>:function:my-fn",   # [req]
    "toolSchema": {"inlinePayload": [                  # [req] — OR {"s3": {"uri": "s3://.../schema.json"}}
        {"name": "get_order", "description": "Fetch an order",             # name+description+inputSchema all [req]
         "inputSchema": {"type": "object", "properties": {"id": {"type": "string"}}, "required": ["id"]},
         # "outputSchema": {...}      # optional
        }
    ]},
}}}
```

### mcp.openApiSchema

```python
{"mcp": {"openApiSchema": {"s3": {"uri": "s3://my-bucket/openapi.json"}}}}   # OR {"inlinePayload": "<json>"}
```

Every `s3` source also accepts `bucketOwnerAccountId` for cross-account buckets.

### mcp.smithyModel

```python
{"mcp": {"smithyModel": {"s3": {"uri": "s3://my-bucket/model.json"}}}}       # OR inlinePayload
```

### mcp.mcpServer

Front an existing remote MCP server.

```python
{"mcp": {"mcpServer": {
    "endpoint": "https://my-mcp.example.com/mcp",      # [req], https:// only
    "listingMode": "DEFAULT",                          # DEFAULT | DYNAMIC
    "mcpToolSchema": {"s3": {"uri": "s3://..."}},       # optional — pin the tool list instead of discovering it
    "resourcePriority": 10,                            # optional int — ordering when several targets overlap
}}}
```

### mcp.apiGateway

**All three members are required** (`apiGatewayToolConfiguration` included, and it requires `toolFilters`) —
omitting the tool configuration is a `ValidationException`, not a "expose everything" default.

```python
{"mcp": {"apiGateway": {
    "restApiId": "abc123",                             # [req]
    "stage": "prod",                                   # [req]
    "apiGatewayToolConfiguration": {                   # [req]
        "toolFilters": [{"filterPath": "/orders", "methods": ["GET", "POST"]}],      # [req]
        "toolOverrides": [{"name": "get_order", "path": "/orders/{id}", "method": "GET",
                           "description": "Fetch an order"}],                        # optional; name+path+method [req]
    },
}}}
```

### mcp.connector

AWS-managed built-in tools. **Live-verified 2026-08-13** (`web-search` and `bedrock-knowledge-bases` targets both
reached READY, MCP `tools/list`, and a full retrieval round trip through a harness).

```python
{"mcp": {"connector": {
    "source": {"connectorId": "web-search", "version": "1.2.0"},   # version: strict semver, see below
    "enabled": ["WebSearch"],                    # optional list (1..50) — restrict which tools this target exposes
    "configurations": [{"name": "WebSearch", "parameterValues": {   # name pattern [a-zA-Z][a-zA-Z0-9_-]*, <=64
        # target-level (admin) values, hidden from the agent:
        "domainFilter": {"include": ["allowed.com"], "exclude": ["blocked.com"]},
    },
    # "description": "...",                                        # override the tool description the agent sees
    # "parameterOverrides": [{"path": "...", "description": "...", "visible": True}],
    }],
}}}
```

**Three hard requirements** (each a `ValidationException` otherwise, all three measured 2026-08-13):

1. `configurations` must be non-null **and** non-empty, with one entry per tool you want exposed — the entry `name`
   *is* the connector's tool name (`WebSearch`; `Retrieve` / `AgenticRetrieveStream` for Knowledge Bases).
2. `credentialProviderConfigurations=[{"credentialProviderType": "GATEWAY_IAM_ROLE"}]`. The field is *optional* in the
   `CreateGatewayTarget` shape but mandatory in practice — omitting it fails with
   `Credential provider configurations is not defined`, and any other type fails with
   `Connector target only supports GATEWAY_IAM_ROLE credential provider type`. One legal value, stated explicitly.
3. The gateway `roleArn` needs the connector's own invoke permission — for web-search,
   `bedrock-agentcore:InvokeWebSearch` on `arn:aws:bedrock-agentcore:<region>:aws:tool/web-search.v1`.
   It does **not** need `bedrock-agentcore:InvokeGateway`: a gateway whose role grants only the connector's
   downstream actions reaches READY *and* serves a full retrieval round trip. `InvokeGateway` is a permission for the
   **caller identity**, not for the execution role — the AWS KB-connector page that lists it among the gateway role's
   permissions is a documentation error (see `references/gotchas.md` §Known AWS documentation errors).

**Known `connectorId`s.** `ConnectorId` is a free-form string in the service model (`[1..256]`, **no enum**), so this
is a list of *ids AWS documents*, not an enumerable catalog — there is no `ListConnectors` operation, and an unknown id
fails without hinting at what is valid (measured 2026-08-13):
`Connector integration totally-not-a-connector is not available for this account`. Note the *version* catalog
**is** discoverable by error (below) while the *id* catalog is not.

| connectorId | Union leaf | Exposes |
|---|---|---|
| `web-search` | `mcp.connector` | `WebSearch` (GA 2026-06-16, us-east-1; zero egress, no external provider or API key) |
| `bedrock-knowledge-bases` | `mcp.connector` | `Retrieve`, `AgenticRetrieveStream` → see **`references/knowledge-bases.md`** for the KB resource, `parameterValues` payloads and gateway-role IAM |
| `agentcore-memory` | `http.connector` | AgentCore Memory as tools (`parameters: {"memoryId": ...}`) — **branch not creatable today** |
| `bedrock-mantle`, `openai`, `anthropic` | `inference.connector` | model access as a gateway target; `openai`/`anthropic` reached READY, `bedrock-mantle` needs `bedrock-mantle:ListModels` on the gateway role |

**Connector versions — the default-vs-latest trap.** `version` is optional, but **omitting it does not give you the
newest connector**:

All four read-backs below were measured on `web-search` on 2026-08-13.

- **Create without `version`** → the connector's **DEFAULT** version, which is not the newest. `GetGatewayTarget` read
  back **`1.1.0`** even though **1.2.0** shipped 2026-07-20.
- **Update without `version`** → **sticky**: the target stayed on `1.1.0`. Pinning `1.2.0` explicitly read back
  `1.2.0`.
- `GetGatewayTarget` echoes the resolved version — **read it back, don't assume.**
- An unknown version raises a `ValidationException` **that lists the catalog**, and it is the only way to enumerate it:

  ```
  Unknown version '9.9.9' for connector 'web-search'. Available versions: [1.1.0, 1.2.0]
  ```

- Request-level filters on web-search (`filters.domainFilter` / `filters.publishedDateFilter`) need **≥1.2.0**, so
  **pin `version` explicitly** if you want them.
- `version` is 5–32 chars with a strict three-part semver pattern: `"1.2.0"` is valid, `"1.2"` is not — and it fails
  **client-side in botocore on length**, before the pattern is ever consulted:
  `Invalid length for parameter targetConfiguration.mcp.connector.source.version, value: 3, valid min length: 5`.
  A two-part version therefore never produces a service-side error you can learn the catalog from.
- AWS's docs disagree with themselves here — the service model says an omitted version means "latest", the dev guide
  says "default". The read-back settles it: **default**.

The agent then sees a `WebSearch` MCP tool (`query`, `maxResults` 1–25, and on v1.2.0+ per-request
`filters.domainFilter` / `filters.publishedDateFilter`) — verified via live `tools/list`.

### The `http.*` branch is unreachable today

All three `http.*` leaves below are **schema-verified only**. Measured 2026-08-13 in us-east-1, each is refused on a
gateway created the only way `CreateGateway` allows:

```
CreateGatewayTarget -> ValidationException:
  HTTP target configuration is not supported for gateways with MCP protocol type
```

...and `CreateGateway` refuses every other `protocolType` you could ask for — `HTTP`, `A2A`, `INFERENCE`, `CUSTOM`,
`REST` all fail with:

```
Value 'HTTP' at 'protocolType' failed to satisfy constraint: Member must satisfy enum value set: [MCP]
```

So these are shapes without a home: the union describes a gateway kind the service will not yet create. The gating is
**per top-level union branch, not per leaf** — `inference.*` targets are accepted on the same `MCP` gateway that
refuses `http.*`, and nothing in the service model expresses the difference. Keep the shapes for when the protocol
lands; do not plan a build around them, and do not read `routeToTarget` (§Rules) as usable — its only addressable leaf
is `http.agentcoreRuntime`.

### http.agentcoreRuntime

**Not creatable 2026-08-13** — see above. Front a Runtime you deployed. This is the only leaf `routeToTarget` rules can
address (see §Rules), which is why that rule type is also unusable today.

```python
{"http": {"agentcoreRuntime": {
    "arn": "<runtime-arn>",                            # [req]
    "qualifier": "DEFAULT",                            # optional endpoint/version
    "schema": {"source": {"s3": {"uri": "s3://..."}}},  # optional — describe the runtime's API
}}}
```

### http.passthrough

**Not creatable 2026-08-13** — see above. Proxy an arbitrary HTTPS endpoint through the gateway, keeping the gateway's
inbound auth, policy engine, rate limits and observability in front of it. Unlike `mcp.*`, the payload is **not**
adapted into MCP tools — the protocol is declared and forwarded.

```python
{"http": {"passthrough": {
    "endpoint": "https://svc.internal.example.com/mcp",   # [req] https:// only (optional :port and path)
    "protocolType": "MCP",                                # [req] enum: MCP | HTTP  (only these two)
    "schema": {"source": {"inlinePayload": "<json>"}},     # optional
    "stickinessConfiguration": {                          # optional — pin a caller to one upstream
        "identifier": "sessionId",                        # [req] request attribute to hash on
        "timeout": 300,                                   # seconds
    },
}}}
```

`protocolType` here is a **two-member enum, `MCP` | `HTTP`** — not the four-way `MCP|A2A|INFERENCE|CUSTOM` an earlier
draft of this file claimed. Note the asymmetry with the gateway's own `GatewayProtocolType`, whose enum is `['MCP']`:
the target can declare `HTTP` but no gateway can host it.

Intended for an MCP service you already run that needs governing rather than adapting, or to put an endpoint behind
`tokens` rate limits without a full `inference.provider` mapping — once the branch is hostable.

### http.connector

**Not creatable 2026-08-13** — see above. **A different shape from `mcp.connector`** — no `configurations`, no
`version`, and a flat string→string `parameters` map (values ≤1024 chars) instead of per-tool config:

```python
{"http": {"connector": {
    "source": {"connectorId": "agentcore-memory"},     # [req] — connectorId only, no version field
    "parameters": {"memoryId": "<memory-id>"},         # connector-specific; string values only
}}}
```

### inference.provider

Front a model endpoint as a gateway target. This is the leaf that `tokens` rate limits apply to (see §Rate limits).
**Accepted on a plain `protocolType=MCP` gateway** — reached `READY` 2026-08-13. Read that status narrowly: the target
below reached `READY` with `endpoint` pointing at a hostname that does not resolve, so `READY` means the control plane
liked the shape, not that anything answers.

```python
{"inference": {"provider": {
    "endpoint": "https://api.provider.example.com",    # [req] https:// only
    "modelMapping": {"providerPrefix": {"strip": True, "separator": "/"}},    # optional; separator is 1 char
    "operations": [{                                   # optional list, 1..10
        "path": "/v1/chat/completions",                # [req] pattern /[a-zA-Z0-9-._/]+
        "providerPath": "/chat/completions",           # optional rewrite
        "models": [{"model": "gpt-*"}],                # 1..100; wildcards allowed in `model`
    }],
}}}
```

### inference.connector

An AWS-managed inference connector — `source.connectorId` and nothing else:

```python
{"inference": {"connector": {"source": {"connectorId": "openai"}}}}   # or "anthropic" / "bedrock-mantle"
```

Like `inference.provider`, this leaf is accepted on an `MCP` gateway. Measured 2026-08-13, and the outcome is the
opposite of what you would predict:

| `connectorId` | Result | Note |
|---|---|---|
| `openai` | **READY** | with `credentialProviderType=GATEWAY_IAM_ROLE` and **no API key anywhere** |
| `anthropic` | **READY** | same |
| `bedrock-mantle` | **FAILED** | the AWS-native id is the only one that failed — and it failed *informatively* |

Two lessons, in increasing order of usefulness.

First, the intuition that third-party connectors would demand an API-key credential provider from Identity is **wrong
at the control plane** — `openai` and `anthropic` are accepted with the IAM role and no credential at all. Nothing was
invoked through them, so assume the credential is demanded at invoke time instead; `READY` here is not evidence that a
request would work.

Second, `bedrock-mantle`'s failure is the one that tells you how this leaf behaves. The status reason was:

```
Failed to discover models from inference provider for target <id>. Error: Inference list-models call to
https://bedrock-mantle.us-east-1.api.aws/v1/models failed with HTTP 401: User:
arn:aws:sts::<ACCOUNT_ID>:assumed-role/<gateway-role>/inference-iam-auth-session is not authorized to perform:
bedrock-mantle:ListModels ... because no identity-based policy allows the bedrock-mantle:ListModels action
```

That is a **missing permission on the gateway role**, not a broken connector — the test role deliberately granted only
KB and memory actions. So `inference.connector` performs a **model-discovery call at create time, assuming the gateway
role**, and grants the role a distinct session name (`inference-iam-auth-session`). Give the gateway role the
connector's own list-models action (here `bedrock-mantle:ListModels`) or the target lands in `FAILED` — and remember a
`FAILED` target still blocks `DeleteGateway` (see §Gotchas). The reason `openai`/`anthropic` reached `READY` is most
likely that no such discovery call is attempted for them, which is also why their `READY` proves so little.

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

> **Verified by e2e:** `routeToTarget` actions only support **HTTP-protocol** targets (`http.agentcoreRuntime`).
> MCP-protocol targets (Lambda / OpenAPI / Smithy / MCP-server / API-Gateway / connector) are **served directly** and
> reject `routeToTarget` (`ValidationException: routeToTarget only supports targets with HTTP protocol type`).
>
> **Which means `routeToTarget` is unusable today.** Its only addressable leaf lives in the `http.*` branch, and that
> branch cannot be created on the only gateway `protocolType` the service accepts (measured 2026-08-13 — see
> [§The `http.*` branch is unreachable today](#the-http-branch-is-unreachable-today)). Until an HTTP-protocol gateway
> exists, the usable half of rules is `configurationBundle` weighting — and there is no rule you need in order to
> "expose" an MCP target.

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

## Rate limits

Announced 2026-08-06. Per-user or per-group traffic controls on everything flowing through the
gateway, with rules scoped by OAuth or AWS IAM identity. Three cap dimensions:

| Dimension | Applies to |
|---|---|
| `requests` | ALL target types |
| `tokens` | inference targets only |
| `connections` | concurrent connections (long-lived sessions) |

Executable example (VERIFIED LIVE 2026-08-12, boto3 1.43.69 — created, status ACTIVE, deleted):

```python
c.create_gateway_rate_limit(
    gatewayIdentifier=gateway_id,
    rateLimitId="per-user-cap",
    dimensionKeys=["$.context.iam.principal"],          # REQUIRED; see grammar below
    entries=[{
        "dimensions": {"$.context.iam.principal": "*"}, # which principal(s) this entry matches
        "requests": [{"rate": 10.0, "period": "minute"}],     # period enum: second | minute
        # "tokens": [{"rate": ..., "period": ...}],           # inference targets only
        # "connections": [{"rate": ..., "period": ...}],
    }],
    clientToken=secrets.token_hex(20),
)
# Bulk: c.batch_put_gateway_rate_limits(...)
```

**Dimension-key grammar (verified — extracted verbatim from the service's validation regex):**

```
targetName | toolName | qualifiedModelId
| $.context.iam.principal | $.context.iam.sourceIdentity
| $.context.jwt.<claim-name>
```

Per-user scoping = `$.context.iam.principal` (SigV4 callers) or `$.context.jwt.<claim>` (JWT callers,
e.g. `$.context.jwt.sub`); per-group = a JWT group claim; per-target/tool caps = `targetName` /
`toolName`; token limits key on `qualifiedModelId` (inference targets).

**Two grammars share one list.** `targetName` / `toolName` / `qualifiedModelId` are gateway-native keys and are written
**bare**; identity keys are **JSONPath into `$.context`** and the prefix is mandatory. Measured 2026-08-13:
`$.context.iam.sourceIdentity` is accepted, while the bare `iam.sourceIdentity` printed in the AWS release note is
refused —

```
Value '{iam.sourceIdentity=*}' at 'entries.1.member.dimensions' failed to satisfy constraint:
Map keys must satisfy constraint: [Member must have length less than or equal to 80, ...]
```

The rejection arrives as a **map-key constraint**, which names neither JSONPath nor the missing prefix, so this is a
mistake you can stare at. Meanwhile `toolName` takes no prefix at all. Both forms are legal keys in the same
`dimensions` map; only their spelling rules differ.

**`toolName` values are target-qualified — and nothing checks them.** A gateway namespaces every tool by its target, so
a `toolName` dimension value is the *composite* name the caller actually sends, not the bare connector tool name — for
a target called `kb` exposing `Retrieve` that is `kb___Retrieve` (**three** underscores, confirmed at `tools/list`).

The dangerous part is measured (2026-08-13): a single limit with `dimensionKeys=["toolName"]` accepted
`kb___Retrieve`, `kb_Retrieve` and `Retrieve` **as three sibling entries**, read all three back verbatim, and went
`ACTIVE`. Nothing cross-checks an entry against the gateway's tool inventory. **A mistyped separator therefore yields a
cap that silently never fires** — no error, no warning, and a limit that looks healthy in `GetGatewayRateLimit`. Read
the exact strings from an MCP `tools/list` against `gatewayUrl` and paste them; never type them.

**One limit per `dimensionKeys` per gateway.** A second limit whose `dimensionKeys` duplicate an existing one on the
same gateway is refused: `A limit with dimensionKeys [toolName] already exists for this gateway`. So `dimensionKeys` is
effectively the primary key, and **multiple caps on the same dimension must be multiple `entries` inside one limit**,
not multiple limits — which is exactly why the unvalidated-entry trap above matters: the entry list is where all your
per-tool caps live.

**Update restriction (verified):** `UpdateGatewayRateLimit` accepts ONLY `gatewayIdentifier`,
`rateLimitId`, `description`, `entries` — `dimensionKeys` is absent from its input shape, so it is immutable after
create (and there's no clientToken). Combined with the uniqueness rule above, **changing the dimension of an existing
cap means delete and recreate.**

**Also a release-note error:** it lists the op family under slightly different names (e.g. "PutGatewayRateLimit") — the
real ops are the six below.

Full op family: `CreateGatewayRateLimit` / `Get` / `Update` / `Delete` / `List` + `BatchPutGatewayRateLimits`.
Delete rate limits before deleting the gateway — though note the `DeleteGateway` refusal message names *targets*, not
rate limits, so it will not tell you a rate limit is what's holding the gateway open.

## Wire

Once the gateway is `READY`, attach it to a harness — the **consumer** shape from `references/tools.md`:

```jsonc
{"type": "agentcore_gateway", "name": "my_api", "config": {"agentCoreGateway": {
    "gatewayArn": "<gateway-arn>",
    "outboundAuth": {"oauth": {"providerArn": "<oauth-provider-arn>", "scopes": ["read"]}}
    // or "outboundAuth": {"awsIam": {}}  /  {"none": {}}
}}}
```

The gateway's own inbound `authorizerType` must be satisfied by how the harness connects.

**Then allowlist with the prefixed form: `allowedTools: ["@my_api/*"]`** — where `my_api` is the *harness tool* `name`
above, not the gateway or target name. Measured 2026-08-13, and this is the trap:

- `["@kbgw/*"]` — the agent sees the gateway's tools. Verified end to end.
- `["kb___Retrieve"]` — the bare wire name, spelled exactly right, and the agent sees **nothing**. Silently filtered.

`allowedTools` is a real boundary and it fails *quietly*: with the wrong pattern the tools vanish from the model's
inventory rather than erroring, so the agent improvises — in this campaign it fell back to shelling out `grep -ri` over
the filesystem hunting for the corpus, then answered `NOT FOUND`. **A wrong allowlist pattern looks exactly like a
hallucinating agent, not like a misconfiguration.** Same trap as the `browser_*` glob in `references/tools.md`.

**And validate the allowlist against a live `tools/list`, not against your intended config.** `tools/list` is the union
of every **READY** target — a `FAILED` target is silently *absent* rather than reported, so an agent's inventory can
shrink without warning when one target breaks.

## CLI

The official CLI is now the Node.js **`@aws/agentcore`** package (repo `aws/agentcore-cli`, pre-1.0);
the Python `bedrock-agentcore-starter-toolkit` CLI is **deprecated** ("no longer supported — please use
the AgentCore CLI"). Install and check what your version offers before scripting against it:

```bash
npm install -g @aws/agentcore     # v0.26.x at time of writing; try @preview for newest commands
agentcore --help                  # inventory the gateway-related commands in your installed version
```

Command coverage varies across the pre-1.0 releases — for anything the CLI doesn't cover, use boto3
`bedrock-agentcore-control` directly (all shapes in this file).

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
- **`CreateGatewayTarget` does not require `name`** — only `gatewayIdentifier` and `targetConfiguration`
  (the dev guide says otherwise). Set `name` anyway: tool names and rate-limit dimensions derive from it.
- **`UpdateGatewayTarget` is a full replace, not a patch.** Required: `gatewayIdentifier`, `targetId`,
  `targetConfiguration` — resend the *entire* configuration (and `credentialProviderConfigurations`),
  or the omitted parts are dropped. `GetGatewayTarget` first, mutate, send back.
- **Target creation is asynchronous — poll `GetGatewayTarget` to `READY`.** `CreateGatewayTarget`
  returns immediately with `CREATING`; backend validation (a bad `connectorId`, a nonexistent
  `knowledgeBaseId`, a missing IAM permission) surfaces *later* as `FAILED` + `statusReasons`, not as an
  exception on create. Connector targets take roughly 30 s. Full status enum: `CREATING`, `UPDATING`,
  `UPDATE_UNSUCCESSFUL`, `DELETING`, `READY`, `FAILED`, `SYNCHRONIZING`, `SYNCHRONIZE_UNSUCCESSFUL`,
  and the three `*_PENDING_AUTH` states (an OAuth target waiting on a consent flow).
- **A `FAILED` target still blocks gateway deletion.** Enumerate *all* targets — including `FAILED` and
  `CREATE_PENDING_AUTH` ones that never worked — in teardown, or `DeleteGateway` fails.
- **Connector targets accept only `GATEWAY_IAM_ROLE`, and require it explicitly.** The field is optional in the shape
  but omitting it fails (`Credential provider configurations is not defined`), and anything else fails with
  `Connector target only supports GATEWAY_IAM_ROLE credential provider type`. Verified 2026-08-13 that this holds even
  for the third-party inference connectors: `inference.connector/openai` and `/anthropic` reach `READY` under the IAM
  role **with no API key at all** — the API-key-credential-provider expectation is wrong at the control plane. Whether
  invocation demands one is untested.
- **Omitting a connector `version` pins the DEFAULT version, not the latest** — see
  [§mcp.connector](#mcpconnector). Always read the resolved version back from `GetGatewayTarget`.
- **The gateway execution role does NOT need `bedrock-agentcore:InvokeGateway`.** A full KB retrieval round trip
  succeeded 2026-08-13 with a role holding only the downstream `bedrock:*` actions. `InvokeGateway` is a **caller**
  permission. AWS's KB-connector page lists it under the gateway role; that is a documentation error.
- **`inference.connector` lists models at create time using the gateway role.** A missing list-models permission is
  the difference between `READY` and `FAILED` — and it assumes the role under its own session name
  (`inference-iam-auth-session`), so look for that in CloudTrail. See [§inference.connector](#inferenceconnector).
- **`READY` is a control-plane verdict, not a health check.** An `inference.provider` target pointed at a hostname that
  does not resolve reaches `READY`; a `mcp.connector` `configurations[]` entry missing a required `parameterValues` key
  reaches `READY` and then returns HTTP 200 with `isError=True` at invoke time. **Validate connector configuration by
  calling the tool, never by reading target status.**
- **The `http.*` branch cannot be created today** (all three leaves), which also makes `routeToTarget` rules unusable —
  see [§The `http.*` branch is unreachable today](#the-http-branch-is-unreachable-today).

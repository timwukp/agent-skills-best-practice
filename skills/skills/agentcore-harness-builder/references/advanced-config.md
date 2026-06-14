# Advanced Configuration

These fields control cost, safety, reachability, and security. Set them deliberately — the defaults are not always what
a production agent wants.

## Truncation

Bounds the conversation context fed to the model on long sessions. Verified shape — the window count is **nested**:

```json
"truncation": {
  "strategy": "sliding_window",
  "config": { "slidingWindow": { "messagesCount": 150 } }
}
```

(There is also a `summarization` config under `truncation.config` with `summaryRatio` / `preserveRecentMessages` /
`summarizationSystemPrompt` if you prefer summarizing over dropping.) Do **not** use a flat
`slidingWindowMessagesCount` — that's rejected.

- `sliding_window` keeps the most recent N messages. 150 is a good default for long browse/test sessions.
- Lower it to cut token cost on chatty agents; raise it if early context matters throughout.
- Long-term recall should come from **Memory** (retrieval), not from an enormous window — the window is for recency.
- On `UpdateHarness`, wrap in `optionalValue` (it's a structure field).

## Invocation limits

```json
"maxIterations": 100,
"maxTokens": 65536,
"timeoutSeconds": 1800
```

- **`maxIterations`** — hard cap on agent-loop steps. 100 supports multi-step tool work; lower it for simple agents to
  fail fast on loops.
- **`maxTokens`** — max output tokens per turn. 65536 allows large reports/code. Keep aligned with the model's
  inference config.
- **`timeoutSeconds`** — per-invocation wall clock. 1800 (30 min) suits long sessions; drop to a few minutes for cheap
  quick agents.
- All three are plain integers — **no `optionalValue` wrapper** on update.

## Lifecycle configuration

Controls the per-session microVM lifetime. **Verified location:** nested under
`environment.agentCoreRuntimeEnvironment.lifecycleConfiguration` (NOT top-level), values in **seconds**:

```json
"environment": { "agentCoreRuntimeEnvironment": {
  "lifecycleConfiguration": { "idleRuntimeSessionTimeout": 900, "maxLifetime": 28800 }
} }
```

- **`idleRuntimeSessionTimeout`** — reclaim a session after inactivity (900s = 15 min default).
- **`maxLifetime`** — hard cap regardless of activity (28800s = 8 h default).

Tune down to control cost (sessions hold a microVM); up for genuinely long-running work.

## Network

**Verified location:** nested under `environment.agentCoreRuntimeEnvironment.networkConfiguration` (NOT a top-level
`network` field):

```json
"environment": { "agentCoreRuntimeEnvironment": {
  "networkConfiguration": {
    "networkMode": "PUBLIC",
    "networkModeConfig": { "securityGroups": ["sg-..."], "subnets": ["subnet-..."], "requireServiceS3Endpoint": false }
  }
} }
```

- **`networkMode`** is required. `PUBLIC` reaches the public internet (needed for the browser to hit external sites).
- For **VPC**, set the mode accordingly and provide `networkModeConfig.subnets` + `securityGroups` (both required) to
  reach private resources; `requireServiceS3Endpoint` controls S3 endpoint routing. Use VPC only when you need private
  connectivity — it can block public sites the browser needs.

## Inbound auth

Who is allowed to call `InvokeHarness`, via the top-level `authorizerConfiguration` structure. Verified: the union has
**only `customJWTAuthorizer`** — there is **no `type: IAM`** field.

- **IAM (SigV4)** — the **default**. Simply **omit `authorizerConfiguration`**. Callers use AWS credentials/role; good
  for service-to-service and CI.
- **JWT / OAuth** — set `customJWTAuthorizer` for end-user-facing agents:
  ```json
  "authorizerConfiguration": { "customJWTAuthorizer": {
    "discoveryUrl": "https://issuer/.well-known/openid-configuration",
    "allowedAudience": ["<aud>"], "allowedClients": ["<client-id>"], "allowedScopes": ["<scope>"]
  } }
  ```

On `UpdateHarness`, `authorizerConfiguration` is a structure field → wrap in `optionalValue`.

## Environment variables & custom image (advanced)

- **`environmentVariables`** — a top-level string→string map injected into the session.
- **`environmentArtifact`** — a custom container image
  (`{"containerConfiguration": {"containerUri": "<ecr-uri>"}}`; wrap in `optionalValue` on update). Only with a strong
  reason: a custom image must implement the harness protocol (HTTP server contract, OTel emission, the `agentcore_*`
  tool primitives). The default managed loader image already provides all built-in tools — you almost never need this.

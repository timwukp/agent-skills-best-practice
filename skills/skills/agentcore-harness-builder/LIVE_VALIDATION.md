# Live AWS Validation — 2026-08-13 (Knowledge Bases + Registry relaunch wave)

The 2026-08 additions this skill had **never** covered — **Knowledge Bases (RAG)**, the relaunched
**`agent-registry` namespace**, and the parts of the Gateway target union left unwritten — were validated on a
real AWS account (us-east-1; botocore 1.43.70 live / 1.43.68 locally), executing from an EC2 host via SSM under
a dedicated `skilltest-ec2-role` re-assumed per case. **19 cases, 204 checks, all PASS, 50 findings.** All
`skilltest*` resources deleted (verified by re-listing, not by trusting the delete calls); the campaign launched
zero EC2 instances; total cost ≤ **~$0.03**; account metadata redacted per repo security policy.
**Full per-case log: `TEST_LOG.md`.**

| Check | Result |
|---|---|
| Schema introspection: 11-leaf target union, `agent-registry*` (15+3 ops), MANAGED KB planes, `HarnessToolType` | PASS |
| botocore floor bisected by installation (1.43.64/.65/.66/.68): rate limits **and** `agent-registry*` both floor at **1.43.66** | PASS |
| MANAGED knowledge base created with **no `storageConfiguration`**; ACTIVE in 92s; vector store service-owned and invisible | PASS |
| `MANAGED_KNOWLEDGE_BASE_CONNECTOR` data source + ingestion: 3/3 documents indexed, 0 failed | PASS |
| Data plane: `Retrieve` and `AgenticRetrieveStream` both returned planted sentinel facts | PASS |
| Gateway `mcp.connector` KB target READY; async validation surfaces a bad `knowledgeBaseId` as `FAILED`, not at create | PASS |
| Live MCP `tools/list`: tool names are **`<targetName>___<ToolName>`** (three underscores); `knowledgeBaseId` not agent-visible | PASS |
| `tools/call` through the gateway returned the sentinel; a half-configured but READY target fails at invoke with `isError` | PASS |
| `parameterOverrides[].path` is **JSONPath**; JSON Pointer rejected; widening reveals the path **root**, `visible` defaults to **false** | PASS |
| End to end through a harness: agent answered from the corpus having called `kb___Retrieve` | PASS |
| `allowedTools` for gateway tools needs `@<harness-tool-name>/*` — the bare wire name silently filters the tool out | PASS |
| Connector `version` omitted resolves to the **default** (web-search 1.1.0), not the latest; update without `version` is sticky | PASS |
| Target-union reachability: all three `http.*` leaves **not creatable** (MCP-only gateways); both `inference.*` leaves READY | PASS |
| Rate limits: `toolName` entry values are **not** validated against the tool inventory; one limit per `dimensionKeys` per gateway | PASS |
| `agent-registry` end to end: registry → SKILL record → submit → APPROVED → all three data-plane ops; legacy namespace still live | PASS |
| `toolResultMetadata` channel against a real MCP tool | PASS (**not** emitted by the `bedrock-knowledge-bases` connector — channel is optional) |
| Sweep: zero `skilltest*` leftovers, pre-existing KBs untouched, test EC2 still running as requested | PASS |

## Real-world findings fed back into the skill

1. **A MANAGED KB rejects an `S3` data source.** `CreateDataSource(type="S3")` — the shape every pre-existing
   Bedrock KB example uses — returns `Unsupported data source type for MANAGED knowledge base type.`; the only
   accepted type is `MANAGED_KNOWLEDGE_BASE_CONNECTOR`, whose `connectorParameters` is an untyped Document that
   botocore does not validate at all. The real schema (and its 13-entry connector catalogue, and its bare-integer
   `version`) was recovered by chaining `ValidationException` messages → `knowledge-bases.md`.
2. **`connectorParameters` is validated asynchronously.** A data source missing `connectionConfiguration` is
   *accepted*, goes `CREATING`, then `FAILED`, and `StartIngestionJob` then refuses it → `knowledge-bases.md`.
3. **`READY` is a control-plane verdict, not a health check.** A gateway target with a nonexistent
   `knowledgeBaseId` reaches `FAILED`, but one with a half-filled connector config reaches **`READY`** and only
   fails at invoke time → `gateway.md`.
4. **The gateway role does not need `bedrock-agentcore:InvokeGateway`** — a full `tools/list` + `tools/call`
   round trip succeeded with a role that deliberately omitted it, settling a contradiction between two AWS pages
   → `gateway.md`, `knowledge-bases.md`, `gotchas.md`.
5. **`allowedTools` is the campaign's sharpest trap.** `['@kbgw/*']` works; `['kb___Retrieve']` — the exact wire
   name from `tools/list` — silently filters the tool out, and the agent then improvises (it shelled out to
   `grep -ri` and answered `NOT FOUND`). A wrong pattern looks like a hallucinating model, not a config error
   → `gateway.md`, `harness-config.md`.
6. **`parameterOverrides[].path` is JSONPath**, and an override widens the **root** of the path as a nested
   object, not the leaf as a top-level field; `visible` omitted resolves to **false**, so a description-only
   override reveals nothing → `knowledge-bases.md`, `gotchas.md`.
7. **The `http.*` branch of the target union is unreachable today.** All three leaves are refused on an MCP
   gateway, and `GatewayProtocolType` accepts only `MCP` — so the service model describes a gateway kind the
   service will not create, and `routeToTarget` rules (which address only an `http.*` leaf) are unusable too
   → `gateway.md`.
8. **`inference.connector` does model discovery at create time under the gateway role**, using session name
   `inference-iam-auth-session`; a missing `<service>:ListModels` grant surfaces as an HTTP 401 in
   `statusReasons` → `gateway.md`.
9. **A rate limit on `toolName` does not validate its entry values.** `kb___Retrieve`, `kb_Retrieve` and
   `Retrieve` were all accepted side by side on one gateway, so a mistyped separator yields an `ACTIVE` cap that
   silently never fires → `gateway.md`.
10. **Connector version resolution is "default", not "latest"** (the service model's wording is the wrong one),
    and update without `version` is sticky. The version catalogue is discoverable only through the rejection
    message; a two-part `"1.1"` fails client-side on length and teaches you nothing → `gateway.md`.
11. **The first `CreateRegistry` in an account needs `iam:CreateServiceLinkedRole` for
    `agent-registry.amazonaws.com`** — absent from `AgentRegistryFullAccess` and from the Registry docs, and it
    presents as a service fault → `registry.md`, `gotchas.md`.
12. **Registry records are created asynchronously** (202 + `CREATING`), and both submit *and* delete are refused
    during that window; under `APPROVE_ALL` the submit call is still required but lands directly in `APPROVED`
    → `registry.md`.
13. **Both registry namespaces genuinely coexist** — the legacy `bedrock-agentcore-control.CreateRegistry` still
    succeeds, and there is no deprecation signal anywhere in the SDK. The 2026-09-17 shutdown is the only
    forcing function → `registry.md`.
14. **`harnessName` rejects hyphens** (`[a-zA-Z][a-zA-Z0-9_]{0,39}`), which is awkward because the managed Memory
    the service auto-creates is named `<harnessName>-<suffix>` → `harness-config.md`.
15. **`toolResultMetadata` is opt-in per MCP server**, not a property of Gateway tools — the KB connector emitted
    none, so readers must tolerate its absence. This closes campaign 2's PARTIAL in the negative
    → `integrations.md`.
16. **RAG is not a tool type.** `HarnessToolType` has five members and none is a knowledge base; KBs live on the
    `bedrock-agent` plane and reach an agent only through a Gateway connector target → `tools.md`,
    `decision-guide.md`, `memory.md`.
17. Ops: SSM `StandardOutputContent` truncates near ~24,000 characters, silently corrupting a `tar | base64` log
    retrieval — pull logs in explicit chunks → `TEST_LOG.md`.

---

# Live AWS Validation — 2026-08-12/13 (2026-05..08 feature wave)

The 2026-08 feature-wave update (web search, temporal policies, rate limits, runtime instances,
unified observability, BYO secrets/filesystems/container, export, harness GA additions) was
validated on a real AWS account (us-east-1; boto3 1.43.69, aws-cli 2.36.21, `@aws/agentcore`
0.26.0), executing from an EC2 host via SSM. All resources deleted afterward; zero EC2 instances
launched; account metadata redacted per repo security policy. **Full per-case log: `TEST_LOG.md`.**

| Check | Result |
|---|---|
| Schema introspection: all new op families + unions (harness/capacity/rate-limit/policy/EXTERNAL/filesystems/connector) | PASS |
| Identity BYO secret: `CreateApiKeyCredentialProvider(apiKeySecretSource=EXTERNAL)` against own Secrets Manager ARN | PASS |
| Policy: engine ACTIVE + cedar policy with `enforcementMode=LOG_ONLY` round-trip | PASS |
| Temporal/Dogwood statement syntax | PARTIAL — `definition.policy` slot parses, grammar guess rejected; take syntax from dev-guide examples |
| Web-search connector target (v1.2.0 + domainFilter) READY + live MCP `tools/list` returns `WebSearch` schema | PASS |
| Gateway rate limit ACTIVE; dimension-key grammar extracted from validation regex | PASS |
| Harness: `sessionStorage` mount + **memory auto-attached when `memory` omitted** | PASS |
| InvokeHarness stream event model (`stream` key; messageStart/…/metadata) | PASS (`toolResultMetadata` not emitted by built-in tools) |
| Unified observability: fresh harness log group `/aws/bedrock-agentcore/runtimes/harness_<name>-<id>-DEFAULT` | PASS |
| `agentcore export harness --arn` → Strands project + `EXPORT_NOTES.md` (stable v0.26.0) | PASS |
| Delete semantics: async DELETING; managed memory `managedByResourceArn` + cascade delete | PASS |
| CapacityProvider: `launchTemplateSource` **required**; no object created (cost guardrail) | PARTIAL |
| Sweep: zero leftovers; all temporary IAM removed | PASS |

## Real-world findings fed back into the skill

1. **Managed-memory naming changed**: auto-created Memory observed as `<harnessName>-<suffix>`
   (July validation saw `harness_<name>_*`) → IAM asset now scopes both patterns; memory.md updated.
2. **Web-search connector hard requirements** (configurations non-empty `{"name": "WebSearch"}`,
   GATEWAY_IAM_ROLE, `InvokeWebSearch` on the service-owned tool ARN) → gateway.md.
3. **Rate-limit dimension-key grammar** + `dimensionKeys` immutability → gateway.md §Rate limits.
4. **`s3files:` ARN regex** for `s3FilesAccessPoint` (S3 Files ≠ S3 access point) → harness-config.md,
   advanced-config.md.
5. **Policy lifecycle ConflictExceptions** (delete during CREATING; engine non-empty) → policy.md,
   gotchas.md.
6. **Export requires a project**, no `--output` flag; `EXPORT_NOTES.md` documents allowedTools
   staticization → integrations.md.
7. Ops: SSM Quick Setup drift-remediation reverts instance-profile swaps — use a scoped
   `sts:AssumeRole` to a temporary test role for EC2-hosted campaigns → TEST_LOG.md.

---

# Live AWS Validation — 2026-07-27

The 2026-07 accuracy overhaul of this skill was validated end-to-end on a real AWS
account (us-east-1, boto3 1.43.56). All resources were deleted afterward; account
metadata redacted per repo security policy.

| Check | Result |
|---|---|
| Create execution role from `assets/iam_execution_role.json` (placeholders substituted) | PASS |
| `CreateHarness` with the skill's updated defaults — `global.anthropic.claude-sonnet-5`, `apiFormat: converse_stream`, plain-name `allowedTools` (no globs), built-in code-interpreter with **no** `config` | PASS (harness READY in ~2.4 min) |
| `ListHarnessVersions` (new versioning surface) | PASS |
| `InvokeHarness` real inference — streamed response, `end_turn`, usage metrics returned | PASS |
| Full cleanup (harness + role) | PASS |

## Real-world finding fed back into the skill

First invoke attempt failed with
`AccessDeniedException ... bedrock-agentcore:ListEvents on ...:memory/harness_<name>_...`:
**managed memory (the default) auto-creates a Memory resource named `harness_<name>_*`, and
the execution role needs event/retrieval permissions on it** — the docs' "no IAM grant needed"
phrasing is wrong at runtime. Fixed in `assets/iam_execution_role.json` (`ManagedMemoryEvents`
statement), `references/memory.md`, `references/gotchas.md`, and SKILL.md gotcha #4.

Also confirmed live against the service model (authoritative over docs):
- `apiFormat` enum = `converse_stream | responses | chat_completions` (`CONVERSE` invalid)
- `UpdateHarness` `optionalValue` wraps ONLY `memory` / `environmentArtifact` / `authorizerConfiguration`
- `CreateHarness`/`GetHarness` responses nest under a `harness` key whose ARN field is `arn`
  (not `harnessArn`); `InvokeHarness` returns a `stream`
- skills[] sources: `path | s3 | git | awsSkills`; InvokeHarness supports `qualifier` + invoke-time overrides

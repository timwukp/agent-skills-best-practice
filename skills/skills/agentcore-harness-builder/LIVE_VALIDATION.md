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

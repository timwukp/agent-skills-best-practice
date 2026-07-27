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

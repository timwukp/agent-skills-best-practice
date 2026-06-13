# Skills

Skills give a harness reusable domain knowledge and procedures — the same progressive-disclosure pattern as Kiro
skills. The agent invokes a skill by name through the built-in `skills` tool; the harness loads the `SKILL.md` (and its
bundled files) at session start.

## The source union (exactly one per skill)

`skills` is a list; each entry has **exactly one** source type. Verified shapes (boto3 1.43.29):

```python
# A) path — a STRING path to a file already inside the container (custom-image deployments)
{"path": "/skills/ui-testing"}

# B) s3 — a single S3 URI (NOT bucket/prefix/versionId)
{"s3": {"uri": "s3://my-bucket/skills/ui-testing"}}

# C) git — a path inside a public GitHub repo at the DEFAULT branch
{"git": {"url": "https://github.com/owner/repo", "path": "app/ui-test-agent/skills/ui-testing"}}

# C') private git — add auth referencing an Identity credential provider
{"git": {"url": "https://github.com/owner/private-repo", "path": "skills/x",
         "auth": {"credentialArn": "<credential-provider-arn>", "username": "<optional>"}}}
```

Note `path` is a bare string (not `{"path": {...}}`), and `s3` takes a single `uri` (not separate bucket/prefix).

## git source — critical limitations

- **No `branch` field.** AgentCore fetches the repo's **default branch** (`main`) at session start. You cannot point a
  skill at a feature branch.
- **Implication:** a `SKILL.md` that exists only on a feature branch **cannot be functionally tested pre-merge** via a
  git-source harness. The skill must land on the default branch first, then a fresh session picks it up.
- Public repos need no auth. Private repos set `git.auth.credentialArn` (an Identity credential provider ARN, backed by
  the Token Vault — see `identity.md`), with an optional `username`.

## Mandatory frontmatter (the #1 skills failure)

Every `SKILL.md` referenced by any source type **must begin** with YAML frontmatter:

```markdown
---
name: ui-testing
description: Methodology and rubrics for UI testing
---

# UI Testing Skill
... content ...
```

Without it, `InvokeHarness` fails at **session start**:
```
runtimeClientError: SKILL.md in .agents/skills/git/<hash>/<repo-path>/skills/<name>
has no YAML frontmatter (must start with ---)
```

- `name` — lowercase, no spaces; the identifier the agent passes as `{"skill_name": "<name>"}` to the `skills` tool.
- `description` — one line describing what the skill does.

This requirement is **undocumented** in the official guide. Always validate it before shipping a new skill — start from
`assets/skill.md.template`. `scripts/validate_config.py` checks any local `SKILL.md` you point it at.

## Allowlisting

Add `"skills"` to `allowedTools` (it's a built-in, so the plain name matches). The agent then discovers all configured
skills through that single tool.

## When to use a skill vs the system prompt

Put **stable, reusable methodology** (rubrics, step-by-step procedures, domain checklists) in a skill so it loads only
when relevant and doesn't cost tokens every turn. Keep the **system prompt** for the agent's core role and hard rules.
This mirrors the progressive-disclosure principle: metadata always in context, skill body loaded on demand.

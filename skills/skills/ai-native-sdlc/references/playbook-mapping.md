# Reference — playbook mapping

The skill distills Anthropic's *AI-Native SDLC Playbook*. The canonical, publicly
checkable source is the blog post:
<https://claude.com/blog/the-ai-native-sdlc-playbook> (Anthropic, 2026-08-21, by Louis
Claxton), organised as **six stages** (Plan, Design, Build, Test, Deploy, Maintain) plus
cross-cutting plays. The 14-row numbering below follows the Claude Academy course edition
of the same material ("The AI-Native SDLC Playbook", 14 lessons); where the two disagree,
**the blog post is authoritative**. Each stage ends by committing a machine-readable
artifact; the next stage reads it.

| # | Lesson | Stage | Artifact | Enforcement |
|---|--------|-------|----------|-------------|
| 1 | Introduction | — | the loop model | — |
| 2 | Capture as intent.md | Plan | `intent.md` | advisory + owner accept |
| 3 | Requirements and design | Design | `spec.md` | advisory + sign-off |
| 4 | Plan mode as default start | Build | `plan.md` | deterministic (no edit until accepted) |
| 5 | The CLAUDE.md | Build | `CLAUDE.md` | advisory + PR review |
| 6 | Skills as institutional knowledge | Build | `.claude/skills/<name>/` | advisory |
| 7 | Parallel sessions & subagents | Build | `.claude/agents/*.md` | repo config |
| 8 | Give Claude a feedback loop | Test | verify block + failing tests | deterministic (hook) |
| 9 | Continuous evals in CI | Test | `evals/` + CI workflow | merge gate |
| 10 | AI in the PR review loop | Deploy | `REVIEW.md` | advisory + branch protection |
| 11 | Hooks as approval gates | Deploy | `.claude/settings.json` + gate scripts | deterministic + managed |
| 12 | CI/CD integration & deployment | Deploy | pipeline step (`claude -p`) | production gate + permissions |
| 13 | Closing the loop on metrics | Maintain | `bands.yaml` → new `intent.md` | deterministic detection + tiered permission |
| 14 | Closing thoughts & resources | — | rollout index | — |

## Cross-cutting throughlines
1. **Artifacts are the audit trail** — Git history of these files records ask → produce → approve.
2. **Three enforcement strengths** — advisory (skill), deterministic (hook), non-overridable (managed settings / branch protection).
3. **Humans concentrate at the gates** — the agent acts up to the production gate and cannot pass it; the agent that wrote code cannot approve it.

## Plays in the blog post this skill does NOT implement

Declared here so an unmapped play is a decision on record rather than an omission. Each is
out of scope for a reason, not merely unbuilt:

| Play | Status | Why |
|---|---|---|
| Auto mode / staged autonomy | **Out of scope** | An agent-runtime permission setting, not a repository artifact. The skill's tiered controls (hook → merge gate → branch protection) govern *what lands*, not how autonomously the agent runs. |
| Legacy-system onboarding | **Out of scope** | The playbook's play for bringing an existing large codebase under agent development. This skill assumes a repo that can adopt the artifact loop from the next change onward; a migration guide is a different document. |
| Managed settings (fleet-wide policy) | **Partially covered, cannot be delivered from here** | Named in row 11 and throughline 2 as the non-overridable tier, but an org policy plane is enterprise-owned — see `enterprise-adoption.md`, which scores exactly this gap. |
| Recurring security scans | **Out of scope** | Scheduled scanning is an ops control that runs regardless of any change being in flight; this skill's gates are change-triggered. Compose it alongside, not inside. |
| Claude on call (incident response) | **Adjacent** | Stage 6 covers the *output* of an incident (`bands.yaml` breach → new `intent.md`); the playbook's on-call play — the agent participating in live diagnosis — is an operational practice outside the artifact loop. |

## The loop, closed
A production incident (Stage 6) is not a dead end: the agent's diagnosis is written as a new
`intent.md` that re-enters Stage 1. The SDLC is continuous, not linear.

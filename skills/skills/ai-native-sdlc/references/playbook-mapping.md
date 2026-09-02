# Reference — 14-lesson mapping

The skill distills the Claude Academy *AI-Native SDLC Playbook* (14 lessons). Each stage
ends by committing a machine-readable artifact; the next stage reads it.

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

## The loop, closed
A production incident (Stage 6) is not a dead end: the agent's diagnosis is written as a new
`intent.md` that re-enters Stage 1. The SDLC is continuous, not linear.

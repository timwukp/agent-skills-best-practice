---
name: sprint-security-review
description: >
  Prepares sprint review and retrospective materials that demonstrate security alongside features:
  green build reports aggregating SAST/DAST/dependency scan results, completed security story
  summaries, and security metrics trends. Triggers on: "prepare sprint review", "green build
  report", "security metrics for this sprint", "demo our security work", "sprint security summary",
  "retro on our pipeline".
license: MIT
metadata:
  author: Community
  version: 1.0.0
  category: secure-sdlc
---

# Sprint Security Review

Make security work visible in the sprint review instead of invisible plumbing. Produce a report that lets the team demo security outcomes to stakeholders in 5 minutes, plus metrics that show trend, not just snapshot.

## What to Gather

Ask for (or extract from CI/scan outputs the user provides):

1. **Pipeline results** for the sprint's final build: SAST, DAST, dependency/container scans, test results and coverage.
2. **Security stories completed** this sprint (IDs and one-line outcomes).
3. **Open security debt**: counts by severity, and anything that aged past SLA.
4. **Two or three sprint-over-sprint metrics** — pick from: mean time to remediate by severity, new findings vs. resolved, false-positive rate, security debt trend, coverage trend.

If the user can't supply real numbers, generate the template with placeholders and mark them clearly — never invent metrics.

## Green Build Report Template

```markdown
# Sprint [N] — Green Build Report

## Pipeline Status
| Stage | Status | Details |
|-------|--------|---------|
| SAST | ✅/❌ | [new High/Critical count; accepted Medium count with link to acceptance] |
| DAST | ✅/❌ | [findings against staging] |
| Dependency scan | ✅/❌ | [Critical CVEs; notable upgrades] |
| Container/image scan | ✅/❌ | [base image currency] |
| Unit tests | ✅/❌ | [pass count, coverage %] |
| Integration tests | ✅/❌ | [pass count] |

## Security Stories Completed
- [ID] [Title] — [one-line demonstrable outcome, e.g. "transfer API now rejects malformed amounts; demo: curl with attack payload returns 422"]

## Security Debt Position
- Open: [n Critical / n High / n Medium / n Low] ([↑/↓ vs last sprint])
- Past SLA: [items, owner, plan]

## Metrics
- [Metric]: [value] ([trend vs previous sprint])

## Risks & Asks
- [Anything needing stakeholder decision: risk acceptance, capacity, tooling]
```

## Demo Guidance

For each completed security story, propose a 30-second demonstration that shows the control working — the blocked attack, the alert firing, the audit log entry — rather than describing code. Stakeholders remember "we watched the brute-force attempt get locked out", not "we improved auth".

## Retrospective Prompts (security angle)

Offer these when the team runs the retro:

- Which security findings could have been caught earlier in the pipeline, and what gate would have caught them?
- Did security stories get squeezed out mid-sprint? If so, was the capacity reserve real?
- Any false-positive pain worth tuning rules for?
- Did anything ship with accepted risk — and is that acceptance documented?

## Guidelines

- A red pipeline stage is not shameful in the report — hiding it is. Show the failure, the cause, and the plan; that builds more stakeholder trust than a suspiciously green wall.
- Keep the whole report to one page; link out to scan dashboards for detail.
- Trends beat snapshots: always compare against at least the previous sprint where data exists.

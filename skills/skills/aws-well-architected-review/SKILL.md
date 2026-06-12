---
name: aws-well-architected-review
description: >
  Reviews AWS architectures, IaC, and design docs against the AWS Well-Architected Framework's six
  pillars, producing a findings report with pillar-mapped risks (High/Medium) and concrete
  remediation. Loads only the pillars relevant to the change. Use for AWS architecture reviews,
  not generic code review. Triggers on: "well-architected review", "review this AWS architecture",
  "WAR review", "check this design against AWS best practices", "review my Terraform/CDK for AWS
  pitfalls", "is this architecture production-ready".
license: MIT
metadata:
  author: Community
  version: 1.0.0
  category: cloud-architecture
---

# AWS Well-Architected Review

Run a lightweight Well-Architected review on a concrete artifact — an architecture diagram/description, Terraform/CDK/CloudFormation, or a design doc — and report risks the way the official framework does: per pillar, severity-rated, each with a specific remediation. This is an engineering review to catch issues early; it complements (does not replace) a formal Well-Architected Tool review with an AWS SA.

## Pillar Selection

Load only what the change touches — typically 2-4 pillars, not all six:

| Change involves | Load |
|-----------------|------|
| IAM, network exposure, data handling, secrets | [references/security.md](references/security.md) |
| Availability targets, failover, backups, DR | [references/reliability.md](references/reliability.md) |
| Instance/database sizing, scaling, latency paths | [references/performance.md](references/performance.md) |
| Spend-relevant choices: sizing, storage classes, data transfer, commitment plans | [references/cost.md](references/cost.md) |
| Deployment, observability, runbooks, IaC hygiene | [references/operations.md](references/operations.md) |
| Region choice, instance generations, utilization, data lifecycle | [references/sustainability.md](references/sustainability.md) |

When in doubt for a general "review this architecture" request, default to Security + Reliability + Cost — the three with the highest production-incident and bill impact.

## Review Process

1. **Understand the workload.** From the artifact (and one round of questions if needed): what it does, criticality (user-facing? revenue-path?), availability/RTO expectations, data sensitivity, and rough scale. Severity calibration depends on this — an unencrypted dev sandbox is not an unencrypted payments database.
2. **Select pillars** per the table; state which you're skipping and why in one line each.
3. **Walk each loaded pillar's checklist** against the artifact. For every gap, record: pillar, the specific resource/decision at fault, risk severity (High = likely incident/breach/major waste; Medium = degraded posture or growing risk), and a concrete remediation (the actual setting/service/change, not "improve security").
4. **Credit what's right.** List notable good practices observed — a review that only criticizes loses the audience, and "what's already fine" is information the team needs.
5. **Deliver the report** (format below), risks ordered by severity, with a top-3 "fix first" call-out.

## Report Format

```markdown
# Well-Architected Review: [workload name]
**Date:** [YYYY-MM-DD] · **Artifact:** [what was reviewed] · **Pillars:** [loaded pillars]
> Engineering review — for a formal review, use the AWS Well-Architected Tool with your AWS team.

## Workload Context
[2-3 lines: purpose, criticality, scale assumptions used for severity calibration]

## Fix First
1. [Highest-impact finding, one line each]

## Findings
| # | Pillar | Severity | Resource/Decision | Risk | Remediation |
|---|--------|----------|-------------------|------|-------------|
| 1 | Security | High | [e.g. RDS instance `orders-db`] | [specific risk] | [specific change] |

## Good Practices Observed
- [Pillar] [what's done right]

## Pillars Not Reviewed
- [Pillar] — [one-line reason]
```

## Guidelines

- Anchor every finding to a named resource or decision in the artifact. If you can't point at it, you're reviewing your imagination, not their architecture.
- Severity discipline: High means "an SA would stop the meeting for this" — public S3 with sensitive data, single-AZ production database, `*:*` IAM. Don't inflate Mediums.
- Cost findings need numbers where possible: "gp2 → gp3 saves ~20% on this 2TB volume" beats "consider storage optimization".
- For Singapore/FSI-regulated workloads, note the overlap and recommend the fsi-compliance-checker skill for the regulatory layer; this review covers engineering best practice, not compliance.
- IaC nuance: review the architecture the code *creates*, not the code style. Terraform module structure issues belong to the terraform-module skill.

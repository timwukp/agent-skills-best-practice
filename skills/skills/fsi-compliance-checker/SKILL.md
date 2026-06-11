---
name: fsi-compliance-checker
description: >
  Reviews code, architecture, and infrastructure changes against financial services compliance
  frameworks - PCI-DSS v4.0 for payment card data and MAS TRM for Singapore-regulated institutions -
  producing a control-mapped findings report with remediation guidance. Use for FSI/banking/fintech
  work. Triggers on: "PCI-DSS check", "MAS TRM", "compliance review", "is this compliant", "audit
  this change for banking regulations", "payment data handling review".
license: MIT
metadata:
  author: Community
  version: 1.0.0
  category: fsi-compliance
---

# FSI Compliance Checker

Map a concrete change (code diff, architecture design, IaC, pipeline config) to the specific controls it touches in financial services compliance frameworks, and report gaps with actionable remediation. This is engineering-level compliance triage — it helps teams catch violations before audit, but it does not replace a qualified assessor (QSA) or the institution's compliance function. Say so in every report.

## Framework Selection

Load only the reference file(s) the engagement needs:

| Situation | Load |
|-----------|------|
| Payment card data is stored, processed, or transmitted (PAN, CVV, track data) | [references/pci-dss.md](references/pci-dss.md) |
| Singapore-regulated financial institution (bank, insurer, capital markets, major payment institution) | [references/mas-trm.md](references/mas-trm.md) |
| Both apply (e.g. Singapore bank handling cards) | Both files |
| Other jurisdictions/frameworks (SOX, GDPR, HKMA, APRA) | State that they are out of scope of this skill's bundled references; offer general secure-engineering review instead |

If the user hasn't said which applies, ask one question: what data does the change touch, and is the institution Singapore-regulated?

## Review Process

1. **Scope the change.** Identify what the diff/design actually touches: data elements (card data? customer PII? credentials?), trust boundaries, environments (production? DR?), and third parties.
2. **Select applicable controls** from the loaded reference file(s) — typically 5-15 controls, not the whole framework. List what you ruled out and why (one line each) so the scoping is auditable.
3. **Assess each applicable control** against the change: `Compliant` / `Gap` / `Needs evidence` (can't tell from the artifact — name the evidence required).
4. **Write findings** using the report format below. Every Gap gets: the control ID, what's wrong in this specific change, concrete remediation, and severity (Critical = violation involving live regulated data; High = control absent; Medium = control partial/undocumented).
5. **Recommend story conversion**: offer to turn findings into backlog items (via the security-story-writing skill if available) with the control ID in each story for traceability.

## Report Format

```markdown
# Compliance Review: [change title]
**Frameworks:** [PCI-DSS v4.0 / MAS TRM 2021] · **Date:** [YYYY-MM-DD]
**Scope:** [what was reviewed: files, design doc, pipeline]
> Engineering triage only — not a substitute for QSA assessment or the compliance function.

## Data & Boundary Analysis
- Data elements touched: [e.g. PAN (masked), customer NRIC, none]
- Environments/boundaries: [e.g. CDE-adjacent service, public API]

## Findings
| # | Control | Status | Severity | Finding | Remediation |
|---|---------|--------|----------|---------|-------------|
| 1 | [PCI 3.5.1] | Gap | Critical | [specific issue in this change] | [specific fix] |

## Ruled Out (not applicable)
- [Control area] — [one-line reason]

## Evidence Needed
- [Control]: [what artifact would demonstrate compliance]
```

## Common FSI Engineering Triggers

Changes that almost always have compliance impact — check these proactively when they appear in a diff:

- Logging statements near payment or authentication flows (PAN/CVV must never be logged; MAS TRM requires security event logging — both directions matter)
- New data stores or caches receiving customer or card data (encryption at rest, retention, residency)
- Authentication/session changes (MFA requirements, session timeout, credential storage)
- New third-party SDKs or API integrations (outsourcing/vendor controls, data flows leaving the boundary)
- Infrastructure changes touching network segmentation, security groups, or public exposure
- CI/CD changes that alter who/what can deploy to production (change management, segregation of duties)

## Guidelines

- Cite control IDs precisely (e.g. "PCI-DSS 8.3.6", "MAS TRM 9.1.1") so findings are traceable in audit tooling; the reference files carry the ID schemes.
- Severity discipline: don't inflate. A missing comment is not a Critical; unencrypted PAN at rest is.
- When the change is compliant, say so affirmatively per control — "no findings" plus the checked-control list is a useful audit artifact.
- Never output real card numbers, even as examples; use the standard test PANs (e.g. 4111 1111 1111 1111) when illustrating.

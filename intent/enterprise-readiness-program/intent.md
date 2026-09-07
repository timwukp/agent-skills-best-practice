- **Slug:** enterprise-readiness-program
- **Author:** Kiro (AI agent)
- **Accepted-by:** Tim WU
- **Date:** 2026-09-05
- **Status:** shipped

## Problem

The AI-Native SDLC skill is now a working, released control for individuals and small
teams, but its enterprise positioning is scattered and easy to over-read. It scores
36/80 (45%) on the current enterprise-readiness rubric, while changes contained in this
repository can raise that only to about 48%. The remaining distance is primarily a
category gap, not unfinished gate code.

Three enterprise controls cannot truthfully be implemented by this standalone skill:

1. an organisation/enterprise policy plane that repository administrators cannot weaken;
2. a tamper-evident audit sink outside the governed party's control; and
3. independent assurance performed by a party other than the implementation author.

The repository names these limitations, but does not yet give an adopting enterprise a
clear implementation contract: required owner, minimum control properties, evidence to
retain, verification procedure, failure modes, and the boundary between what this skill
provides and what the enterprise must supply.

The remaining self-addressable work is also not organised as an executable programme.
Telemetry, Stage 6 feedback closure, migration and fleet inventory, operational
commitments, real scale evidence, and long-running operational evidence are listed as
gaps but lack ordering, dependencies, measurable exit criteria, and separate SDLC work
items.

Finally, the skill does not state its four practical adoption tiers prominently enough.
A consumer can confuse “the gate runs” with “enterprise compliance control”, even though
those are materially different claims.

## Desired outcome

Publish an honest enterprise-readiness package inside the skill that:

- states exactly what the skill can and cannot claim at four adoption tiers;
- gives enterprises implementation and verification contracts for the three external
  hard blockers without claiming those controls are shipped here;
- defines a prioritised, dependency-aware roadmap for the six self-addressable workstreams;
- turns each roadmap workstream into a future, separately approved SDLC intent rather than
  attempting one unreviewable mega-change; and
- keeps the current score at 36/80 unless new evidence satisfies an existing rubric item.

This intent authorises documentation, contracts, tests that keep those claims from
regressing, and the roadmap. It does **not** authorise implementing all six roadmap
workstreams in this change.

## Affected users / systems

- Individual developers and small teams deciding whether the skill is production-usable.
- Enterprise platform, security, compliance, audit, and developer-experience teams
  evaluating a controlled pilot or fleet-wide adoption.
- Future maintainers who need a sequenced backlog with evidence-based completion criteria.
- `skills/skills/ai-native-sdlc/SKILL.md` and its enterprise-facing references, tests, and
  compatibility/support statements.
- This repository's own SDLC process, which is being onboarded from this change forward.

## Constraints

- Do not call the skill enterprise-grade, compliant, unbypassable, independently audited,
  or cryptographically separated when those claims are false.
- Preserve the factual score: 36/80 (45%), with a self-contained ceiling of about 48%.
- Clearly separate normative enterprise requirements from examples such as GitHub
  Enterprise rulesets or S3 Object Lock; examples must not be presented as the only valid
  implementation.
- The three external controls remain enterprise-owned integrations. Repository code may
  provide contracts, examples, and verification guidance, but cannot mark them complete.
- Keep the four adoption tiers explicit:
  1. individual/small-team production use — usable now;
  2. controlled enterprise pilot — viable only when the enterprise supplies policy,
     audit, and identity governance;
  3. enterprise-wide mandatory control — not yet achieved;
  4. regulated/auditable compliance control — not yet achieved and requires independent
     assurance plus external evidence custody.
- Use separate intents and human approval for later telemetry, Stage 6, migration/fleet,
  operations, scale-evidence, and longitudinal-evidence implementations.
- Do not self-approve this artifact or any later spec/plan.
- Documentation statements must be protected by machine-checkable tests where a future
  edit could silently overstate readiness or restore stale evidence counts.

## Success criteria

1. `SKILL.md` states the four adoption tiers near the enforceability/adoption guidance and
   links to the detailed enterprise contract and roadmap.
2. A dedicated enterprise-adoption reference documents each external blocker with:
   responsibility boundary, minimum required properties, implementation-neutral control
   contract, example architecture, retained evidence, consumer verification steps,
   failure/bypass modes, and an explicit “not provided by this skill” statement.
3. A dedicated roadmap orders these six workstreams and gives each dependencies,
   deliverables, verification target, exit evidence, and proposed follow-up intent slug:
   telemetry; Stage 6 feedback closure; migration/fleet inventory; operational ownership;
   production scale evidence; longitudinal operational evidence.
4. `references/limitations.md` distinguishes the self-contained ceiling from externally
   supplied enterprise controls, records the four adoption tiers, and removes stale claims
   contradicted by the current 12-suite/65-mutation, polyglot, scale, and Windows evidence.
5. Tests fail if the four-tier positioning, external-control ownership boundary, score,
   roadmap workstreams, or current mutation evidence disappear or are overstated.
6. Existing 12 suites remain green and every mutation remains killed; any new assertion is
   itself mutation-proven where practical.
7. The change advances through committed `intent.md`, accepted `spec.md`, accepted
   `plan.md`, red verification target, implementation, review, and human merge without the
   agent setting its own approval fields.
8. Enterprise readiness remains 36/80 unless a separately reviewed rubric reassessment
   identifies genuinely new control evidence.

## Open questions

None required to define Stage 1. The proposed programme boundary is deliberate: this
change publishes positioning, external implementation contracts, and the executable
roadmap; each roadmap implementation receives its own later intent and approval.

---
Gate: product owner accepts. The accepting commit is the record.

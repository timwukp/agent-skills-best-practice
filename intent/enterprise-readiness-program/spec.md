- **Intent:** ./intent.md
- **Author:** Kiro (AI agent)
- **Accepted-by:** Tim WU
- **Status:** signed-off

## Amendment 1 — planning corrections requiring renewed sign-off

This amendment is authoritative where the original requirements below say “current 65”.
The accepted intent correctly recorded **65/65 as the baseline before this programme
change**. Requirement 11 adds at least five new mutations, so the resulting current count
must be derived from the completed `MUTATIONS` list and is expected to be at least 70; it
must not be falsely frozen at 65. The truthfulness suite will compare documentation with
the harness's actual final count and will continue to reject the stale 27-mutation claim.

Planning also found that `templates/plan.md` advises recording `git rev-parse HEAD` for
`Accepted-for`, while the v2 CI workflow compares that field with the pull request's real
merge base. For this programme plan, acceptance must record
`git merge-base origin/main HEAD` (currently `c4d9f16e0877efb0bfab56aac257efec8db843ad`).
Changing the shipped template is outside this signed programme scope and must receive its
own follow-up intent (`fix-plan-binding-instruction`) rather than being smuggled into this
change.

## Requirements

1. **Four-tier positioning (Intent SC1, SC4).**
   `skills/skills/ai-native-sdlc/SKILL.md` must state, in the adoption/enforcement
   guidance rather than only in a deep reference, all four current positions:
   - individual/small-team production use is usable now;
   - a controlled enterprise pilot is conditional on enterprise-supplied policy,
     evidence custody, and identity governance;
   - enterprise-wide mandatory control is not achieved; and
   - regulated/auditable compliance control is not achieved.
   It must state the current 36/80 (45%) readiness score and approximately 48%
   self-contained ceiling without implying that documentation raises either value.

2. **External-control implementation contracts (Intent SC2).**
   Add `skills/skills/ai-native-sdlc/references/enterprise-adoption.md`. It must cover
   these three enterprise-owned controls in separate normative sections:
   - organisation/enterprise policy plane;
   - tamper-evident external audit sink; and
   - independent assurance.

   Every section must include: responsible enterprise role; responsibility boundary;
   minimum required properties; implementation-neutral acceptance contract; at least one
   clearly labelled non-normative example architecture; evidence to retain; verification
   procedure; known failure/bypass modes; and an explicit statement that the control is
   not delivered or attestable by this standalone skill.

3. **Control-specific minimum properties (Intent SC2).**
   The contracts must require at least:
   - **Policy plane:** centrally managed policy, repository administrators unable to
     weaken it, controlled exception/bypass ownership, verified actor identity, required
     checks that always report, and fleet-visible version/configuration state.
   - **Audit sink:** export outside the governed party's administrative boundary,
     append-only or WORM retention, integrity/timestamp provenance, access separation,
     documented retention, query/retrieval tests, and evidence for denied/failed export.
   - **Independent assurance:** assessor independence and scope, version/commit under
     review, threat-model review, control-design and adversarial testing, finding
     severity/closure evidence, expiration or reassessment trigger, and an explicit rule
     that self-authored tests and badges are not independence.

4. **Implementation-neutral examples (Intent constraints).**
   GitHub Enterprise rulesets, audit-log streaming, S3 Object Lock, signed commits, and
   third-party penetration testing may appear as examples. Each example must be labelled
   non-normative; equivalent controls satisfying the contract remain valid. The document
   must not claim that copying a sample configuration proves compliance.

5. **Executable six-workstream roadmap (Intent SC3).**
   Add `skills/skills/ai-native-sdlc/references/enterprise-roadmap.md`. It must contain all
   six workstreams, each with: problem, enterprise value, dependency, bounded deliverable,
   verification target, exit evidence, non-goals, and proposed follow-up intent slug.
   The required slugs are:
   - `operational-ownership`
   - `enterprise-telemetry`
   - `schema-migration-fleet-inventory`
   - `stage6-feedback-loop`
   - `production-scale-evidence`
   - `longitudinal-operational-evidence`

6. **Roadmap ordering (Intent SC3).**
   The roadmap must define this dependency-aware sequence while allowing separately
   approved work to proceed in parallel where dependencies permit:
   - Phase 0: operational ownership and telemetry contracts/baseline;
   - Phase 1: migration/fleet inventory and Stage 6 feedback closure;
   - Phase 2: representative production-scale evidence;
   - Phase 3: longitudinal operational evidence accumulated over a declared observation
     window.
   Longitudinal evidence must depend on telemetry, operational ownership, and elapsed
   real-world time; it cannot be closed by a synthetic test run.

7. **No mega-change (Intent desired outcome, constraints).**
   This change must not implement the six roadmap workstreams. Every implementation must
   start from its proposed slug with a new human-accepted intent. The roadmap is proposed
   work, not an SLA, funded commitment, or statement that an owner has accepted delivery.

8. **Limitations reconciliation (Intent SC4, SC8).**
   Update `skills/skills/ai-native-sdlc/references/limitations.md` to:
   - link to both new references;
   - distinguish current score, self-contained ceiling, and enterprise-supplied controls;
   - include the four adoption tiers;
   - retain prompt-injection, weak-eval, admin-bypass, attested-not-proven, and external
     evidence limitations;
   - replace stale 27-mutation evidence with the current 65/65 result;
   - replace the stale claim of no monorepo/polyglot/concurrency/Windows evidence with the
     narrower truth: synthetic scale/polyglot/concurrency tests and Windows CI exist, but
     representative independent production adoption and longitudinal evidence do not.

9. **Skill navigation and evidence freshness (Intent SC1, SC4).**
   `SKILL.md` must link the enterprise adoption and roadmap references, list them in its
   file map, and report 65 current mutations rather than 27. It must keep the distinction
   between a passing gate and a meaningful eval/human judgement.

10. **Machine-checkable truthfulness contract (Intent SC5, SC6).**
    Add a stdlib-only suite named
    `skills/skills/ai-native-sdlc/scripts/test_enterprise_readiness.py`. It must fail when:
    - any adoption tier is missing or promoted beyond the accepted intent;
    - 36/80, 45%, or the approximately 48% self-contained ceiling disappears;
    - any external control lacks an enterprise-owned/not-provided boundary;
    - any of the six roadmap slugs is missing;
    - longitudinal evidence is represented as synthetically closable;
    - stale “27 mutations” or stale “no Windows/polyglot/scale tests” claims return; or
    - the new references are absent from `SKILL.md` navigation.

11. **Mutation proof for critical claims (Intent SC5, SC6).**
    Extend `scripts/mutation_proof.py` with mutations that independently remove or weaken
    at least these discriminating claims: one adoption-tier refusal, one external ownership
    boundary, one score/ceiling statement, one roadmap slug/dependency, and the current
    mutation evidence count. Every added mutation must be killed by the new suite with no
    false kill caused by a missing copied reference.

12. **No enforcement-generation change (Intent SC8).**
    This programme-documentation change must not alter v2 gate enforcement semantics,
    `GATE_VERSION`, artifact schema, source suffixes, binding checks, hook behavior, or
    workflow release behavior. It requires no compatibility deprecation or new release
    generation. Existing suites and mutations must remain green.

13. **Dogfood chain (Intent SC7).**
    The repository must retain `.sdlc/version`, `.sdlc/active`, and the committed artifact
    chain for `enterprise-readiness-program`. The agent must not set `accepted` or
    `signed-off` on artifacts it authored. Build work may begin only after this spec and
    the subsequent plan receive human sign-off/acceptance in separate commits.

## Non-functional requirements

- **Truthfulness:** statements must distinguish shipped controls, adopter obligations,
  proposed roadmap work, and permanent/human limitations. Absence of evidence must never
  be rendered as completion.
- **Security:** examples must not include secrets, broad bypass instructions, or sample
  configurations that silently grant administrators an escape path.
- **Auditability:** every normative requirement must name observable evidence and a way an
  adopter can test it; “configured” without verification is insufficient.
- **Portability:** enterprise contracts must be vendor-neutral. GitHub/AWS-specific
  material is illustrative only.
- **Maintainability:** the authoritative detail lives in the two new references. `SKILL.md`
  contains a concise positioning summary and links; `limitations.md` contains residual
  risk and evidence status rather than duplicating entire implementation recipes.
- **Test robustness:** tests assert semantic markers, required sections, enumerated slugs,
  and explicit negative claims rather than entire prose paragraphs.
- **Dependencies:** runtime and tests remain Python standard-library only. No package is
  added.
- **Compatibility:** documentation additions must not turn previously valid consumer
  repositories red or alter the gate's CLI/output contract.

## Design

### 1. Information architecture

Use three layers with distinct ownership:

1. **`SKILL.md` — decision summary.**
   A compact “Adoption positioning” subsection near “Making it enforceable” presents the
   four tiers, score/ceiling, and links. This is the first thing a potential adopter sees.
2. **`references/enterprise-adoption.md` — external control contract.**
   This is the normative integration boundary for controls the skill cannot own. It
   defines outcomes and evidence, then gives non-normative examples.
3. **`references/enterprise-roadmap.md` — proposed self-addressable programme.**
   This orders future intents and defines what evidence would close each workstream. It is
   not a delivery promise.
4. **`references/limitations.md` — residual-risk ledger.**
   This remains the source for what is open, permanent, partly mitigated, or externally
   supplied, and links rather than cloning the new detailed contracts.

### 2. Enterprise-adoption contract shape

The document starts with a prominent boundary statement:

- this repository supplies a gate, evidence format, tests, and verification guidance;
- the adopting enterprise supplies policy authority, external evidence custody, verified
  organisational identity, and independent assessment;
- examples are not proof; retained evidence and negative controls are required.

Each of the three controls uses the same headings so an assessor can compare them:

1. Owner and boundary
2. Minimum required properties
3. Acceptance contract
4. Non-normative reference architecture
5. Evidence package
6. Verification and negative controls
7. Failure and bypass modes
8. What this skill does not provide

A final adoption checklist maps the four tiers to prerequisites. “Controlled pilot” may
be selected only when the three enterprise-owned foundations exist for the pilot scope;
enterprise-wide and regulated tiers remain explicitly unachieved by this project.

### 3. Roadmap model

Use a table for portfolio scanning and one detailed section per workstream. Status for all
six begins `proposed`; no owner, funding, SLA, or completion date is invented.

Phase logic:

- **Phase 0 — establish ownership and measurement.** `operational-ownership` defines
  maintainers, security response targets, escalation, and decision rights;
  `enterprise-telemetry` defines privacy-bounded events and baseline metrics.
- **Phase 1 — control lifecycle and fleet state.**
  `schema-migration-fleet-inventory` makes deployed versions/configurations observable and
  migration-safe. `stage6-feedback-loop` consumes deterministic signals to open a new
  intent without placing a model in the detection path.
- **Phase 2 — representative scale evidence.** `production-scale-evidence` exercises
  consenting external/bounded repositories across monorepo, polyglot, fork, concurrency,
  and platform scenarios with reproducible evidence and redaction.
- **Phase 3 — longitudinal evidence.** `longitudinal-operational-evidence` reports declared
  observation windows, adoption/block/false-positive/bypass rates, incidents, recovery,
  and version distribution. It cannot start meaningfully until earlier telemetry and
  ownership controls operate over time.

### 4. Verification design

`test_enterprise_readiness.py` reads the four Markdown documents as data. Helpers provide:

- required-section and required-token assertions;
- a forbidden-overclaim list (for example, an unqualified “enterprise-ready” or a claim
  that external controls are provided);
- exact roadmap slug set comparison;
- evidence freshness assertions (`65`, no `27 mutations`);
- cross-link assertions from `SKILL.md`.

Tests must discriminate requirements rather than reward word presence alone. For example,
checking for “enterprise-wide mandatory control” is insufficient; the test also requires
its nearby status marker to be “not achieved”. Likewise, the audit contract must contain
both an enterprise-owned boundary and external/WORM evidence properties.

`mutation_proof.py` already copies references into its sandbox. Add the new suite and
reference mutations using anchors designed during implementation. A mutation is accepted
only when the unmutated suite is green and the mutated suite goes red for the intended
assertion.

### 5. Compatibility and release behavior

This is a documentation/programme release with tests, not an enforcement-generation
release. Do not change `GATE_VERSION = 2`, `SUPPORTED_SCHEMA = 1`, release tags, or consumer
workflow semantics. Normal repository PR CI is sufficient; no `sdlc-gate-v3` announcement
is warranted.

### 6. Rejected alternatives

- **Mark the three controls complete after documenting them — rejected.** Documentation is
  not deployment or independent evidence.
- **Ship provider-specific Terraform as the normative solution — rejected.** It would imply
  one cloud/provider is required and could encourage unsafe copy/paste compliance.
- **Implement all six workstreams in one PR — rejected.** Their dependencies, owners, and
  evidence horizons differ; a mega-change defeats review and human approval.
- **Put all content in `SKILL.md` — rejected.** It would bury operating instructions in a
  long compliance manual and create duplicated, drifting detail.
- **Use exact full-paragraph snapshot tests — rejected.** They make legitimate editorial
  improvement painful while failing to distinguish the essential claim.
- **Increase the enterprise score for producing this documentation — rejected.** The
  accepted rubric scores controls and evidence, not prose about missing controls.

## Flagged concerns

| Concern | Policy owner | Resolution |
|---------|--------------|------------|
| Documentation could be mistaken for deployed enterprise control | Product owner / enterprise risk owner | Keep every external section explicitly enterprise-owned and not provided; add negative regression tests. |
| Vendor examples could be read as normative compliance recipes | Enterprise architecture owner | Label every GitHub/AWS example non-normative and test for the implementation-neutral contract. |
| Roadmap could be interpreted as a funded SLA or delivery commitment | Product owner / maintainer | Mark every item proposed, owner/funding unassigned, and require a future accepted intent. |
| Fixed prose tests could block harmless editorial changes | Skill maintainer | Assert semantic markers, section structure, slug sets, and negative status—not full paragraphs. |
| The project could imply its own tests are independent assurance | Independent assessor / security owner | State that self-authored tests are evidence inputs, never independent assurance. |
| Synthetic CI evidence could be overstated as production adoption | Product owner / validation owner | Record synthetic Windows/polyglot/scale evidence accurately while keeping representative external and longitudinal evidence open. |

## Out of scope

- Deploying or administering an organisation/enterprise ruleset.
- Creating cloud accounts, WORM storage, audit-log streaming, IAM roles, or retention policy.
- Performing or certifying an independent audit, penetration test, or compliance assessment.
- Implementing telemetry collection or transmitting repository/user data.
- Implementing the Stage 6 monitor/agent invocation path.
- Building schema migration tooling or a fleet inventory service.
- Creating an SLA, funding commitment, on-call rotation, or legal support obligation.
- Claiming production-scale or longitudinal evidence from synthetic tests.
- Recalculating the 36/80 score without a separate rubric review.
- Changing gate, hook, schema, source-coverage, base-binding, or release semantics.

---
Gate: owner signs off; flagged concerns worked first. Applied org skills/versions recorded:
`ai-native-sdlc` at repository `main` commit c4d9f16e0877efb0bfab56aac257efec8db843ad.

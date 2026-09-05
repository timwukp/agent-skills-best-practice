# Plan: Enterprise-readiness positioning, external contracts, and roadmap

- **Spec:** ./spec.md
- **Author:** Kiro (AI agent)
- **Accepted-by:** pending — engineer acceptance
- **Accepted-for:** pending — set to the pull-request merge base at acceptance
- **Status:** draft

`Accepted-for` must be the output of `git merge-base origin/main HEAD`, not the branch
HEAD. At draft time that merge base is
`c4d9f16e0877efb0bfab56aac257efec8db843ad`. This follows Amendment 1 in `spec.md` and
the v2 CI comparison; the conflicting instruction in the shipped plan template is tracked
for the separate `fix-plan-binding-instruction` intent and is not changed here.

## Files changed (in order of work)

Every source file this change touches is listed here. The intent artifacts and `.sdlc/`
onboarding markers already committed for this dogfood chain are process records rather
than implementation source.

1. `skills/skills/ai-native-sdlc/scripts/test_enterprise_readiness.py` — add the
   stdlib-only red-first truthfulness suite for adoption tiers, score/ceiling, external
   ownership boundaries, roadmap slugs/dependencies, evidence freshness, and navigation.
2. `skills/skills/ai-native-sdlc/references/enterprise-adoption.md` — add the normative,
   implementation-neutral contracts for enterprise policy, external tamper-evident audit,
   and independent assurance, including owners, evidence, verification, examples, and
   explicit standalone-skill limits.
3. `skills/skills/ai-native-sdlc/references/enterprise-roadmap.md` — add the six proposed
   workstreams, exact follow-up slugs, phase/dependency ordering, bounded exits, evidence,
   and non-goals without inventing owners, funding, SLAs, or completion.
4. `skills/skills/ai-native-sdlc/SKILL.md` — add the concise four-tier positioning,
   36/80 (45%) score, approximately 48% standalone ceiling, links/file-map entries, and
   final mutation evidence count while preserving the gate-versus-judgement distinction.
5. `skills/skills/ai-native-sdlc/references/limitations.md` — reconcile the enterprise
   gaps with the new contracts and roadmap; distinguish synthetic CI evidence from
   representative production and longitudinal evidence; replace stale evidence claims.
6. `skills/skills/ai-native-sdlc/COMPATIBILITY.md` — replace the contradictory
   `Polyglot repos | Untested` statement with the narrower tested-synthetically/runtime-
   unproven status, while retaining fork and production-scale limits.
7. `.github/workflows/sdlc-gate-tests.yml` — add `test_enterprise_readiness` to the
   explicit matrix suite list so repository PR CI executes all 13 suites. The release
   workflow already discovers `test_*.py` and will not be edited.
8. `skills/skills/ai-native-sdlc/scripts/mutation_proof.py` — add at least five
   discriminating mutations covering an adoption-tier refusal, external ownership
   boundary, score/ceiling, roadmap slug/dependency, and dynamically verified final
   mutation count.

No gate runtime, hook, schema, binding implementation, source suffix, release workflow, or
release-generation file is changed.

## Work order

1. **Reconfirm the accepted base and boundaries.** Verify the branch merge base is
   `c4d9f16e0877efb0bfab56aac257efec8db843ad`, the spec build gate is open, and the
   working tree is clean. Record the existing baseline as 12 suites and 65/65 mutations;
   do not present that baseline as the final result.
2. **Create the red verification target first.** Add
   `test_enterprise_readiness.py` using semantic/nearby-status assertions rather than
   paragraph snapshots. Derive the expected current mutation total from the harness's
   actual `MUTATIONS` list. Run this suite before adding the documents and capture a
   non-zero result caused by missing contracts/stale positioning, not by an exception in
   the test itself. Commit this red verification target separately.
3. **Write the external contracts.** Add `enterprise-adoption.md` with a common section
   shape for each of the three controls: owner/boundary, minimum properties, acceptance
   contract, labelled non-normative example, evidence package, verification/negative
   controls, bypass modes, and what the standalone skill does not provide. Keep examples
   vendor-neutral in force even when GitHub, AWS, S3 Object Lock, or third-party testing
   illustrate them.
4. **Write the dependency-aware roadmap.** Add `enterprise-roadmap.md` with all six exact
   slugs and statuses `proposed`. Define Phase 0 ownership/telemetry, Phase 1 fleet
   migration/Stage 6, Phase 2 representative production-scale evidence, and Phase 3
   longitudinal evidence. Require real elapsed time, operational ownership, and telemetry
   for Phase 3; synthetic runs cannot close it.
5. **Reconcile entry points and residual limits.** Update `SKILL.md`, `limitations.md`,
   and the stale `COMPATIBILITY.md` row. State all four tiers and the unchanged score and
   ceiling. Distinguish synthetic Windows/polyglot/monorepo/concurrency coverage from live
   fork semantics, representative external production adoption, independent assurance,
   and longitudinal evidence. Documentation and self-authored tests do not raise 36/80.
6. **Turn the focused suite green.** Run `test_enterprise_readiness.py`; fix content or
   assertion discrimination until it passes without weakening required negative claims.
7. **Make repository CI reach the suite.** Add the suite name to the explicit loop in
   `.github/workflows/sdlc-gate-tests.yml`. Do not edit `.github/workflows/release-attest.yml`:
   its `for t in test_*.py` loop already reaches the new test.
8. **Add mutation proof after anchors stabilize.** Add at least the five required
   mutations, with each mutation changing one meaningful claim and being killed by
   `test_enterprise_readiness.py`. The starting baseline is 65; five planned mutations
   make the expected final total 70. The suite must derive the actual total so any
   additional necessary mutation causes documentation to be updated instead of leaving a
   false hard-coded count.
9. **Run focused and full validation.** Run the new suite, all `test_*.py` suites, and
   `mutation_proof.py`; parse the changed workflow YAML; verify no forbidden runtime files
   changed and v2 constants remain unchanged. Repair any failure before implementation is
   committed.
10. **Commit and hand off.** Commit the green implementation without changing artifact
    approval fields. The user pushes the named feature branch; the agent may then open the
    PR. Treat required checks as green only when their actual conclusion is `success`, not
    `skipped`. The user performs merge and any post-merge `shipped` decision.

## Tests that prove it

### Red-first target

Run from `skills/skills/ai-native-sdlc/scripts`:

```sh
python3 test_enterprise_readiness.py
```

Before implementation it must exit non-zero and report semantic failures for the missing
enterprise references and stale positioning/evidence. A traceback, import error, or
missing-file false kill does not count as a valid red result. After implementation the
same command must exit 0.

The suite must prove at least:

- all four adoption tiers exist and enterprise-wide/regulated tiers are `not achieved`;
- 36/80, 45%, and the approximately 48% standalone ceiling remain together;
- every external control is both enterprise-owned and explicitly not provided/attestable
  by the standalone skill;
- each contract has required owner, properties, evidence, verification, negative-control,
  bypass, and non-normative-example semantics;
- the exact six roadmap slug set and required phase dependencies are present;
- longitudinal evidence cannot be closed synthetically and requires elapsed real time;
- `SKILL.md` links both references and stale `27 mutations` wording is absent;
- the documentation states the actual final `len(MUTATIONS)` rather than freezing the
  pre-change 65 baseline;
- synthetic Windows/polyglot/scale/concurrency evidence is acknowledged without being
  promoted to representative production adoption or live fork-token proof.

### Full suites

```sh
cd skills/skills/ai-native-sdlc/scripts
count=0
for t in test_*.py; do
  count=$((count + 1))
  python3 "$t"
done
test "$count" -ge 13
```

Pass condition: at least 13 suites discovered and every suite exits 0. The repository CI
workflow must explicitly name `test_enterprise_readiness`, yielding the same 13-suite set
on all 15 supported OS/Python matrix cells.

### Mutation proof

```sh
python3 skills/skills/ai-native-sdlc/scripts/mutation_proof.py
```

Pass condition: at least 70 mutations, every mutation killed, `0 survived`, and `0 broken`.
Each of the five new required mutation classes must be independently present and killed;
a missing copied document or stale anchor is `broken`, never credited as a kill.

### Workflow and invariant checks

```sh
ruby -e 'require "yaml"; YAML.parse_file(ARGV.fetch(0))' \
  .github/workflows/sdlc-gate-tests.yml

git diff --name-only c4d9f16e0877efb0bfab56aac257efec8db843ad...HEAD
```

Pass condition: YAML parses; only the eight implementation files listed above plus the
committed dogfood artifacts/markers differ from the merge base. Explicitly verify:

- `GATE_VERSION = 2`;
- `SUPPORTED_SCHEMA = 1`;
- `PENDING_SOURCE_SUFFIXES = ()`;
- no gate runtime, CI gate runtime, hook, schema, release workflow, or release tag semantic
  file changed.

Finally run the dogfood test/deploy gate with the same merge-base binding. It must remain
closed while this plan is draft and open only after the human acceptance commit records
that exact base.

## Risks

- **Semantic token tests can reward word scattering.** Require paired/nearby status and
  ownership markers, exact slug sets, section structure, and negative assertions; reject
  full-paragraph snapshots because they overfit prose.
- **Mutation count can become stale immediately.** Treat 65 as historical baseline only;
  calculate the final list length and require docs to match it. Expected final count is 70
  if exactly five are added.
- **A mutation may be falsely killed by a missing reference.** Rely on the existing
  sandbox copy of all Markdown/references and reject any `broken` result or unrelated
  traceback.
- **Synthetic evidence can be overclaimed.** Preserve live fork-token, representative
  external production, independent review, production-scale, and longitudinal gaps even
  while correcting stale statements about CI tests.
- **Workflow reachability can drift.** Add the suite to the repository's hand-maintained
  list and rely on the release workflow's existing glob; do not duplicate a stale release
  subset.
- **Plan approval can bind to the wrong commit.** Use the PR merge base
  `c4d9f16e0877efb0bfab56aac257efec8db843ad`, as the v2 CI gate does, rather than branch
  HEAD. Fixing the shipped template remains a separately approved change.
- **Roadmap prose can be mistaken for commitment.** Mark every workstream proposed and
  require an independent future intent/PR; do not invent funding, owner acceptance, SLA,
  or completion date.

Rejected alternatives: increasing the score because documentation exists; marking
external controls complete; provider-specific normative configuration; implementing six
workstreams in this PR; changing gate/release semantics; silently fixing the plan template;
or allowing a synthetic test to close longitudinal evidence.

---
Gate: engineer accepts BEFORE any implementation file is edited. If implementation departs
from this plan, update the plan and obtain renewed acceptance rather than relying on the
old binding.

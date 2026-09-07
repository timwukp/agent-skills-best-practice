# Spec: the plan template must tell authors the base the gate actually checks

- **Intent:** ./intent.md
- **Author:** Kiro (AI agent)
- **Accepted-by:** Tim WU
- **Status:** signed-off

## Open questions from the intent, now closed

**Q1 — exact command or worded description?** Describe it and show the `main` form as a
labelled example. A consumer's default branch may be `master` or otherwise, so a hard-coded
`origin/main` in normative guidance would mislead exactly the audience this fixes. The
example is illustrative; the instruction names "the default branch".

**Q2 — does the wrong guidance appear elsewhere?** Yes. A scoped search found `git rev-parse
HEAD` in **two** places, not one:

- `templates/plan.md:6` — the field's how-to (the occurrence the intent named).
- `COMPATIBILITY.md:224` — the "How to upgrade" instruction: *"Add the field when a plan is
  accepted (`git rev-parse HEAD` at that moment)."*

Both are in scope: the intent's constraint is that the fix is "the guidance not one file".
The `COMPATIBILITY.md` case is doubly wrong because its very next sentence says to use the
shipped workflow, "so CI passes the **merge base** to the gate" — the paragraph contradicts
itself in three lines.

No other file carries the wrong instruction: `references/limitations.md` and
`references/threat-model.md` mention `Accepted-for` only as `<base-sha>` without prescribing
how to compute it, so they are correct as-is and are not touched.

## Requirements

1. **Correct the plan template (Intent SC1, SC2).**
   `templates/plan.md` line 6 must stop naming `git rev-parse HEAD` and instead instruct the
   author to record the merge base of the branch against the repository's default branch —
   the value the gate verifies. Show `git merge-base origin/main HEAD` as a labelled example,
   noting that a consumer whose default branch is not `main` substitutes it.

2. **Correct the upgrade instruction (Intent SC2).**
   `COMPATIBILITY.md` "How to upgrade" must replace `git rev-parse HEAD` with the merge-base
   guidance, consistent with its own following sentence about the workflow.

3. **Explain why, briefly (Intent constraints).**
   Both edits must say, in a clause, that the merge base is used because the base moves after
   the branch is cut and the approval was granted at the fork point — the reasoning already in
   `templates/github-workflows/sdlc-gate.yml`. This prevents a future editor from "simplifying"
   it back to HEAD.

4. **Guard the template guidance with a test (Intent SC3).**
   `scripts/test_unbound_approval.py` must assert that the `Accepted-for` guidance in
   `templates/plan.md` references a merge base and does **not** reference `rev-parse HEAD`. The
   existing assertion only checks the field line exists; this adds the content check. The
   assertion must read the guidance text, so a mere field line cannot satisfy it.

5. **Mutation proof (Intent SC4).**
   `scripts/mutation_proof.py` must gain a mutation that reintroduces `git rev-parse HEAD`
   into `templates/plan.md` and is killed by `test_unbound_approval.py`. The full harness must
   report 0 survived and 0 broken.

6. **No runtime or enforcement change (Intent constraints, SC5).**
   `scripts/sdlc_ci_gate.py`, the hook, the workflows, the schema, and `GATE_VERSION` are
   untouched. This corrects human guidance to match already-correct enforcement; it cannot
   turn a passing repository red. No deprecation cycle and no release generation.

7. **Count coupling check.**
   Adding one mutation takes the harness from 72 to 73, and `test_enterprise_readiness.py`
   derives that count and requires `SKILL.md` and `references/limitations.md` to state it.
   Those two files are therefore in the file list and updated to 73. (This is the anchor
   coupling flagged after the last change; it is handled explicitly here rather than
   discovered mid-implementation.)

8. **Dogfood chain (Intent SC6).**
   Artifacts for `fix-plan-binding-instruction` stay committed, `.sdlc/active` names this
   slug, and no artifact this agent authored is set to `accepted`/`signed-off` by the agent.

## Non-functional requirements

- **Truthfulness:** the guidance must name the value the gate actually checks; no example may
  imply a default branch that a consumer might not have.
- **Test robustness:** assert the guidance's semantic content (merge-base present, rev-parse
  HEAD absent), not a whole-line snapshot that harmless rewording would break.
- **Portability:** documentation-only edits plus one stdlib test assertion and one mutation.
- **Maintainability:** the "why merge-base" clause travels with each corrected instruction so
  the reasoning is local to the fix.

## Design

### 1. The template edit

Replace line 6's parenthetical. New form, in words with an example:

> the merge base of this branch against the default branch — the commit the branch was cut
> from, which is what the gate verifies (e.g. `git merge-base origin/main HEAD`; substitute
> your default branch for `main`). Not the branch tip: the base moves after the branch is
> cut, and the approval was granted at the fork point.

### 2. The COMPATIBILITY edit

Replace `git rev-parse HEAD` in "How to upgrade" with `git merge-base origin/<default-branch>
HEAD`, so it agrees with the sentence that follows.

### 3. The test

In `test_unbound_approval.py`, beside the existing field-line check, read the line(s) around
`- **Accepted-for:**` in `templates/plan.md` and assert `merge-base` appears and `rev-parse
HEAD` does not. This targets the guidance value, which the field-line existence check does
not.

### 4. The mutation

Anchor on the corrected template text; the mutation swaps the merge-base guidance back to
`git rev-parse HEAD` and must flip the suite red. The harness already mirrors `templates/`,
so it resolves.

### 5. Rejected alternatives

- **Fix only the template — rejected.** `COMPATIBILITY.md` carries the same wrong instruction;
  leaving it is the drift this skill exists to catch.
- **Hard-code `git merge-base origin/main HEAD` as the instruction — rejected.** A consumer on
  `master` would be misled; name the default branch and show `main` as an example only.
- **Snapshot the whole line in the test — rejected.** It would fail on harmless rewording
  while a reworded-but-still-wrong line could pass; assert the two semantic markers instead.
- **Bump `GATE_VERSION` or add a deprecation — rejected.** Nothing enforced changes; this is
  advice catching up to enforcement.

## Flagged concerns

| Concern | Policy owner | Resolution |
|---|---|---|
| A `main`-only example re-misleads non-`main` consumers | Skill maintainer | Instruction names "the default branch"; `main` is a labelled example with an explicit substitute note. |
| Count coupling forces two extra files again | Skill maintainer | Named up front (R7); the dynamic-count refactor stays a separate proposed intent. |
| Guidance could regress silently later | Skill maintainer | R4 test + R5 mutation make a regression to HEAD a red build. |

## Out of scope

- Changing `sdlc_ci_gate.py`, the hook, the workflows, the schema, or `GATE_VERSION`.
- Replacing the hard-coded mutation count with a dynamically read value (separate proposed
  intent).
- Adding a caller workflow so this repository's own PRs are gate-governed (separate intent).
- Any release or tag.

---
Gate: owner signs off; flagged concerns worked first. Applied org skills/versions recorded:
`ai-native-sdlc` at repository `main` commit 1d66929236cb3b506a6796ea7392863648f3b0d8.

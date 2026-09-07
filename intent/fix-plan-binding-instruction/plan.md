# Plan: the plan template must tell authors the base the gate actually checks

- **Spec:** ./spec.md
- **Author:** Kiro (AI agent)
- **Accepted-by:** pending — engineer acceptance
- **Accepted-for:** pending — set to the pull-request merge base at acceptance
- **Status:** draft

`Accepted-for` must be `git merge-base origin/main HEAD`, which at draft time is
`1d66929236cb3b506a6796ea7392863648f3b0d8`. This is the value the v2 CI gate compares
against — and the very correction this change is about, so binding it correctly here is the
first proof the fix is right.

## Files changed (in order of work)

1. `skills/skills/ai-native-sdlc/scripts/test_unbound_approval.py` — add the red assertion
   that the template's `Accepted-for` guidance references a merge base and not `rev-parse
   HEAD`.
2. `skills/skills/ai-native-sdlc/templates/plan.md` — replace the `git rev-parse HEAD`
   guidance with merge-base guidance naming the default branch, plus the why-clause.
3. `skills/skills/ai-native-sdlc/COMPATIBILITY.md` — replace `git rev-parse HEAD` in "How to
   upgrade" with the merge-base form, consistent with its next sentence.
4. `skills/skills/ai-native-sdlc/scripts/mutation_proof.py` — add a mutation reintroducing
   `git rev-parse HEAD` into the template.
5. `skills/skills/ai-native-sdlc/SKILL.md` — update the mutation count 72 → 73.
6. `skills/skills/ai-native-sdlc/references/limitations.md` — update the mutation count
   72 → 73.

`scripts/sdlc_ci_gate.py`, the hook, the workflows, the schema, and `GATE_VERSION` are
**not** touched.

## Work order

1. **Reconfirm base and gate.** Merge base `1d66929`, build gate open, tree clean.
2. **Red first.** Add the guidance-content assertion to `test_unbound_approval.py`. Run it; it
   must fail because the template still says `rev-parse HEAD`. Confirm a real assertion, not an
   exception. Commit this red target separately.
3. **Fix the template.** Replace line 6's parenthetical with the merge-base guidance + example
   + why-clause.
4. **Fix COMPATIBILITY.md.** Replace `git rev-parse HEAD` in "How to upgrade".
5. **Green the guidance suite.** Run `test_unbound_approval.py`.
6. **Add the mutation** to `mutation_proof.py`, anchored on the corrected template text.
7. **Update the count** in `SKILL.md` and `limitations.md` to 73, and update the existing
   stale-count mutation's anchor (`72 mutations, all` → `73 mutations, all`) so it targets live
   text — the anchor coupling from the previous change.
8. **Full validation** (below). Fix any failure before committing.
9. **Commit the implementation.** No artifact approval field set by the agent.
10. **Hand off.** User pushes `fix-plan-binding-instruction`; agent opens the PR; required
    checks green only when `success`, not `skipped`; user merges; user marks the chain
    `shipped` post-merge.

## Tests that prove it

### Red-first target

```sh
cd skills/skills/ai-native-sdlc/scripts
python3 test_unbound_approval.py    # must fail: template guidance still says rev-parse HEAD
```

Non-zero for the intended assertion before the fix; exit 0 after.

### Full suites and mutations

```sh
cd skills/skills/ai-native-sdlc/scripts
count=0; for t in test_*.py; do count=$((count+1)); python3 "$t"; done; test "$count" -ge 13
python3 mutation_proof.py    # expect 73, 0 survived, 0 broken
```

Pass condition: 13 suites all exit 0; mutation total 73 (72 + 1 new), the new mutation
killed, `0 survived`, `0 broken`. `SKILL.md` and `limitations.md` state 73.

### Invariant checks

```sh
git diff 1d66929236cb3b506a6796ea7392863648f3b0d8...HEAD --name-only
git diff 1d66929 -- skills/skills/ai-native-sdlc/scripts/sdlc_ci_gate.py   # empty
```

Pass condition: only the six files above plus the dogfood artifacts differ; `sdlc_ci_gate.py`
byte-identical; `GATE_VERSION = 2`. The dogfood test gate stays closed while this plan is
draft and opens only after the human acceptance commit records `Accepted-for: 1d66929…`.

## Risks

- **A `main`-only example re-misleads.** Instruction names "the default branch"; `main` is a
  labelled example with a substitute note (spec R1).
- **Snapshot test over-fits.** Assert the two semantic markers (merge-base present, rev-parse
  HEAD absent), not the whole line (spec design 3).
- **Count coupling.** Named up front (spec R7); update all three sites (two docs + stale-count
  mutation anchor) in step 7.
- **Wrong acceptance binding.** Bind to `1d66929` (merge base), not branch HEAD — the exact
  mistake this change corrects.

Rejected alternatives: fixing only the template; hard-coding `origin/main`; snapshotting the
line; bumping `GATE_VERSION`. All argued in `spec.md`.

---
Gate: engineer accepts BEFORE any implementation file is edited. If implementation departs
from this plan, update it and obtain renewed acceptance.

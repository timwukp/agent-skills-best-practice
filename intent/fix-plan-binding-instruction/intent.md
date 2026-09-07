# Intent: the plan template must tell authors the base the gate actually checks

- **Slug:** fix-plan-binding-instruction
- **Author:** Kiro (AI agent)
- **Accepted-by:** Tim WU
- **Date:** 2026-09-07
- **Status:** accepted

## Problem

`templates/plan.md` tells an author how to fill in the approval binding:

```
- **Accepted-for:** <base commit SHA this was accepted against — `git rev-parse HEAD`>
```

`git rev-parse HEAD` is the tip of the author's branch. But both shipped gate pipelines —
the vendored template and the reusable workflow, each now using `git merge-base` — verify
the binding against the pull request's **merge base**, not the branch tip. An author who
follows the template records the branch HEAD; on any branch with more than the acceptance
commit, that value does not equal the merge base, and the gate refuses the pull request
with a binding mismatch.

This is the same class of defect just fixed in `fix-reusable-gate-binding`: a shipped
surface disagreeing with the gate about what the base is. There it was the pipeline; here it
is the instruction the human reads. It was found the same way — by dogfooding this skill,
where following the template verbatim would have bound acceptance to the wrong commit had it
not been caught during planning.

How we know the guidance is wrong and not the gate: the reasoning is already written down in
`templates/github-workflows/sdlc-gate.yml` — "merge-base, not the base tip: the base moves
after the branch is cut, and the approval was granted against the fork point." The template's
own workflow contradicts the template's own plan instruction.

Nothing asserts the guidance is correct. `test_unbound_approval.py` checks only that the
`- **Accepted-for:**` field line *exists*; no test reads what value it tells authors to put
there. So the wrong instruction has no guard.

## Desired outcome

An author filling in `Accepted-for` from the template records the value the gate verifies —
the merge base against the default branch — so a correctly-followed template produces a
binding that passes rather than one that is refused. The corrected guidance is protected by a
test, so it cannot silently regress to the branch tip.

## Affected users / systems

- Every author who fills in a `plan.md` from the template — currently guided to the value
  that fails.
- `templates/plan.md` — the one file whose instruction is wrong.
- `scripts/test_unbound_approval.py` — gains an assertion on the guidance content.
- `scripts/mutation_proof.py` — gains a mutation proving the assertion bites.
- `scripts/sdlc_ci_gate.py`, the workflows, and the schema — **unchanged**. They are already
  correct; this aligns the human instruction with them.

## Constraints

- **Documentation and test only.** No gate runtime, workflow, schema, or `GATE_VERSION`
  change. This does not alter which repositories pass; it corrects advice.
- The corrected instruction must name the same computation the pipelines use —
  `git merge-base` against the default branch — not merely delete the wrong one.
- Must not turn a passing repository red: the field already exists and is already required;
  only the parenthetical how-to changes.
- Follow this skill's own SDLC: no source edit before an accepted plan; no self-approval.

## Success criteria

1. `templates/plan.md` no longer instructs `git rev-parse HEAD` for `Accepted-for`.
2. It instructs computing the merge base against the default branch, consistent with both
   shipped workflows.
3. A test asserts the template's `Accepted-for` guidance references a merge base and does not
   reference `rev-parse HEAD`.
4. A mutation reintroducing `rev-parse HEAD` (or removing the merge-base guidance) is killed;
   the full harness reports 0 survived and 0 broken.
5. `sdlc_ci_gate.py` is byte-identical to the merge base; `GATE_VERSION` remains `2`.
6. The dogfood chain for this slug is committed with human acceptance and sign-off in
   separate commits.

## Open questions

1. **Should the template show the exact command** (`git merge-base origin/main HEAD`) or
   describe it in words, given a consumer's default branch may not be `main`? Proposed for
   Design: describe it and show the `main` form as an example, so a `master`/other-default
   consumer is not misled by a hard-coded branch name.
2. **Does the same wrong guidance appear anywhere else** — `references/enforcement.md`, the
   spec template, or `COMPATIBILITY.md`? To be checked in Design; if so, in scope, since the
   fix is the guidance not one file.

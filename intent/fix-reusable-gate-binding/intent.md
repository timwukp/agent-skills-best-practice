# Intent: the reusable gate must verify the binding it demands

- **Slug:** fix-reusable-gate-binding
- **Author:** Kiro (AI agent)
- **Accepted-by:** Tim WU
- **Date:** 2026-09-07
- **Status:** shipped

## Problem

`sdlc-gate-v2` made `Accepted-for:` mandatory on `plan.md` and made the gate **fail closed**
when it cannot verify that binding. The vendored template was updated for this and computes
`git merge-base` before calling the gate. **The reusable workflow was not.**

`.github/workflows/sdlc-gate-reusable.yml` invokes the gate with only:

```
--repo . --changed-files-from changed-files.txt [--require-active]
```

There is no `--base-sha`, so every consumer whose plan carries the now-required binding is
refused — not for violating the process, but because the pipeline never passes the value the
gate needs.

Measured on the merged tree at `a62ff20`, whose `plan.md` was `accepted` with
`Accepted-for: c4d9f16e…`:

- the reusable workflow's exact argument set exits **1**, reporting *"is bound to base
  c4d9f16e0877 but this run was given no --base-sha, so the binding was NOT verified.
  sdlc-gate-v2 fails closed here"*;
- the same tree with `--base-sha` added exits **0** and passes.

Who this hurts: every adopter who followed the **recommended** integration path.
`COMPATIBILITY.md` presents the reusable workflow as the versioned gate surface to pin
(`@v1`, or a full SHA) and exists specifically so consumers do **not** vendor the script. So
the path this project tells people to use is the broken one, while the path it tells them to
avoid works.

How we know it was missed rather than intended: all four workflow-related mutations in
`mutation_proof.py` are anchored on `templates/github-workflows/sdlc-gate.yml`. **No suite
and no mutation asserts that the reusable workflow verifies the binding at all.** The one
suite that reads the reusable file, `test_fork_safety.py`, asserts fork-token properties, not
`--base-sha`. The v2 rollout therefore hardened one of two shipped paths and had no test that
would notice.

This also blocks unrelated work: governing this repository's own pull requests with its own
gate is the natural next step, and the obvious implementation is a caller of this reusable
workflow. Adding that caller today produces a required check that is permanently red for a
reason that has nothing to do with process compliance.

## Desired outcome

A consumer who pins the reusable workflow and records `Accepted-for` as v2 requires gets a
gate that **verifies** the binding: it passes when the approval matches the pull request's
real merge base, and refuses when it does not. The refusal reason a consumer sees reflects
their process state, never a missing pipeline argument.

The absence of that verification becomes impossible to reintroduce silently: a suite asserts
the reusable path computes and passes a merge base, and a mutation proves that assertion
fails when the argument is removed.

## Affected users / systems

- Consumers calling `.github/workflows/sdlc-gate-reusable.yml` — currently blocked whenever
  they comply with v2.
- `scripts/sdlc_ci_gate.py` — **unchanged**. Its fail-closed behaviour is correct and is what
  exposed this.
- `scripts/mutation_proof.py` and the test suites — gain coverage of the reusable path.
- `COMPATIBILITY.md` — records that the v2 enforcement change reached only one of the two
  shipped surfaces.
- The proposed self-governance work for this repository, which depends on this fix.

## Constraints

- **No `GATE_VERSION` bump and no schema change.** This restores intended v2 behaviour on a
  path that was missed; it does not define a new enforcement generation.
- **Do not weaken the gate to accommodate the workflow.** Making a missing `--base-sha`
  tolerable would delete the control that v2 exists to add. The pipeline is what must change.
- The merge base must be computed the same way the vendored template computes it —
  `git merge-base` against the pull request's base ref, not the base branch tip — so both
  shipped paths agree.
- Must behave sanely when the merge base cannot be resolved (shallow or unusual checkout):
  refuse with a legible reason rather than silently substituting the current base, which is
  the exact substitution an existing mutation already forbids in the gate.
- Fork pull requests must keep working: the gate job needs no secret and must stay
  read-only.
- Stdlib and shell only; no new action dependency.
- Follow this skill's own SDLC: no source edit before an accepted plan, and no self-approval
  of any artifact.

## Success criteria

1. The reusable workflow resolves the pull request's merge base and passes it to the gate as
   `--base-sha`.
2. Exercised against a tree whose `plan.md` is `accepted` with a matching `Accepted-for`, the
   reusable argument set exits **0**; the pre-fix argument set is shown to exit **1** on the
   same tree.
3. A binding that does **not** match the merge base is still refused, proving the fix
   verifies rather than merely supplies the value.
4. An unresolvable merge base produces an explicit refusal naming the cause, and never a
   pass.
5. A suite asserts the reusable workflow computes a merge base and passes `--base-sha`, and
   asserts it does not use the base branch tip instead.
6. At least one new mutation removes the argument from the reusable workflow and is
   **killed**; the full harness reports 0 survived and 0 broken.
7. `sdlc_ci_gate.py` is byte-identical to `c5ce8a2`, and `GATE_VERSION` remains `2`.
8. `COMPATIBILITY.md` records the incomplete v2 rollout honestly, in the same voice as the
   existing precedent note about the duties check.
9. The dogfood chain for this slug is committed, with acceptance and sign-off in separate
   human commits.

## Open questions

1. **Does any consumer repository exist that is currently blocked by this?** If so the fix
   should be tagged as a patch release rather than left on `main`, since `@v1` and pinned
   SHAs will not pick it up otherwise. Needs the owner's answer; it changes the release
   decision, not the code.
2. **Should the reusable workflow accept an explicit `base-sha` input** for callers whose
   checkout cannot resolve a merge base, or is computing it internally sufficient? Deferring
   to Design, with the default position being internal computation only — an input a caller
   can set wrongly reintroduces the hole.
3. **Is a `vN` moving-tag update in scope?** Proposed out of scope for this change and
   handled by the normal release process once the fix is on `main`.

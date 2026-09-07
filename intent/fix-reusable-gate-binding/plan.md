# Plan: the reusable gate must verify the binding it demands

- **Spec:** ./spec.md
- **Author:** Kiro (AI agent)
- **Accepted-by:** Tim WU
- **Accepted-for:** c5ce8a203c0ad9719c7e833d1a323bf7fd9f8010
- **Status:** accepted

`Accepted-for` must be `git merge-base origin/main HEAD`, which at draft time is
`c5ce8a203c0ad9719c7e833d1a323bf7fd9f8010`. This is what the v2 CI gate compares against;
do not bind to branch HEAD.

## Files changed (in order of work)

1. `skills/skills/ai-native-sdlc/scripts/test_unbound_approval.py` — add the red assertions
   that the reusable workflow verifies the binding (invokes the gate with `--base-sha`,
   derives it from `git merge-base`, references `github.base_ref`, and does not use the base
   tip).
2. `skills/skills/ai-native-sdlc/scripts/test_support_matrix.py` — add the red assertion that
   `COMPATIBILITY.md` pin examples use the real `sdlc-gate-vN` tag convention and that the
   versioning table does not claim a bare `vN` moving tag.
3. `.github/workflows/sdlc-gate-reusable.yml` — export `base_sha` from `git merge-base` in
   the existing changed-files step and append `--base-sha "${base_sha:-}"` to the gate step.
4. `skills/skills/ai-native-sdlc/COMPATIBILITY.md` — correct the pin examples and the
   moving-tag claim (spec R7), and record that v2 `Accepted-for` enforcement reached the
   template but not the reusable workflow (spec R8).
5. `skills/skills/ai-native-sdlc/scripts/mutation_proof.py` — add two mutations on the
   reusable workflow: remove `--base-sha`, and replace `git merge-base` with the base tip.

`scripts/sdlc_ci_gate.py`, the hook, the schema, `GATE_VERSION`, and
`templates/github-workflows/sdlc-gate.yml` are **not** touched.

## Work order

1. **Reconfirm base and gate.** Merge base is `c5ce8a2`, build gate open, tree clean.
2. **Red first — reusable binding.** Add the reusable-path assertions to
   `test_unbound_approval.py`. Run it; it must fail because the shipped workflow passes no
   `--base-sha`. Confirm failure is a real assertion, not an exception. Commit this red
   target with the pin-guidance red target below.
3. **Red — pin guidance.** Add the pin-convention assertion to `test_support_matrix.py`. Run
   it; it must fail on the current `@v1` example and the moving-tag claim.
4. **Commit both red targets** in one verification commit, separate from the fix.
5. **Fix the workflow.** In `sdlc-gate-reusable.yml`, export `base_sha` from
   `git merge-base "$base" HEAD || echo` into `$GITHUB_ENV` in the changed-files step, and add
   `--base-sha "${base_sha:-}"` to the argument array in the gate step. Do not add a
   `workflow_call` input.
6. **Fix the docs.** In `COMPATIBILITY.md`, change the pin examples to
   `sdlc-gate-v2`/`sdlc-gate-v2.0.2` per the real convention, reconcile the moving-tag row,
   and add the honest note about the incomplete v2 rollout.
7. **Turn both suites green.** Run `test_unbound_approval.py` and `test_support_matrix.py`.
8. **Add the two mutations** to `mutation_proof.py` with anchors matching the workflow edit.
9. **Full validation** (see below). Fix any failure before committing the implementation.
10. **Commit the implementation.** No artifact approval field is set by the agent.
11. **Hand off.** User pushes `fix-reusable-gate-binding`; agent opens the PR; required
    checks are green only when their conclusion is `success`, not `skipped`; user merges.
12. **Post-merge**, user marks the chain `shipped` through the same human process used for
    the previous intents.

## Tests that prove it

### Red-first targets

From `skills/skills/ai-native-sdlc/scripts`:

```sh
python3 test_unbound_approval.py     # must fail: reusable workflow passes no --base-sha
python3 test_support_matrix.py       # must fail: @v1 pin example / moving-tag claim
```

Both must exit non-zero for the intended assertion, not an exception, before the fix. After
the fix both exit 0.

### Behavioural evidence (spec R10)

On a tree whose `plan.md` is `accepted` with a matching `Accepted-for`, record and retain in
the implementation commit message:

```sh
# pre-fix argument set  -> exit 1 (binding NOT verified)
python3 sdlc_ci_gate.py --repo . --changed-files-from changed-files.txt
# post-fix argument set  -> exit 0
python3 sdlc_ci_gate.py --repo . --changed-files-from changed-files.txt --base-sha <merge-base>
# mismatched binding     -> exit 1 (verifies, not merely supplies)
python3 sdlc_ci_gate.py --repo . --changed-files-from changed-files.txt --base-sha <wrong-sha>
```

### Full suites and mutations

```sh
cd skills/skills/ai-native-sdlc/scripts
count=0; for t in test_*.py; do count=$((count+1)); python3 "$t"; done; test "$count" -ge 13
python3 mutation_proof.py    # expect >=72, 0 survived, 0 broken
```

Pass condition: 13 suites all exit 0; mutation total at least 72 (70 existing + 2 new), both
new mutations killed, `0 survived`, `0 broken`.

### Workflow and invariant checks

```sh
ruby -e 'require "yaml"; YAML.parse_file(ARGV.fetch(0))' .github/workflows/sdlc-gate-reusable.yml
git diff --name-only c5ce8a203c0ad9719c7e833d1a323bf7fd9f8010...HEAD
```

Pass condition: YAML parses; only the five files above plus the dogfood artifacts differ.
Verify `sdlc_ci_gate.py` is byte-identical to `c5ce8a2` (`git diff c5ce8a2 -- …sdlc_ci_gate.py`
empty), `GATE_VERSION = 2`, `SUPPORTED_SCHEMA = 1`.

Finally, the dogfood test gate stays closed while this plan is draft and opens only after the
human acceptance commit records `Accepted-for: c5ce8a2…`.

## Risks

- **A comment could satisfy a naive assertion.** Assert against the executed step's argument
  and the `git merge-base` invocation, not mere presence of the string `--base-sha`.
- **The mutation could be falsely broken.** The harness already mirrors `.github/workflows`;
  anchor the mutations on literal text present in the edited workflow and confirm `0 broken`.
- **Empty base could pass on some runner.** Requirement 3 leaves the value empty on failure so
  the gate's existing refusal fires; the base-tip mutation guards the substitution path.
- **Pin fix could creep.** Bound requirement 7 to the pin examples and the moving-tag row
  only; larger doc work is out of scope.
- **Wrong acceptance binding.** Bind to `c5ce8a2` (merge base), not branch HEAD.

Rejected alternatives: changing the gate to tolerate a missing base; adding a caller-settable
`base-sha` input; using the base tip; bundling the self-governance caller. All are argued in
`spec.md`.

---
Gate: engineer accepts BEFORE any implementation file is edited. If implementation departs
from this plan, update it and obtain renewed acceptance.

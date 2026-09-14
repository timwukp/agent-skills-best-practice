# Plan: govern this repository with the gate it ships

- **Spec:** ./spec.md
- **Author:** Kiro (AI agent)
- **Accepted-by:** pending — engineer re-acceptance (Amendment 1 invalidated the prior acceptance by Tim WU)
- **Accepted-for:** pending — set to the pull-request merge base at re-acceptance
- **Status:** draft

## Amendment 1 — new pin, new base, and one piece of evidence that was unreadable

**Raised before implementation. The prior acceptance is invalidated; re-acceptance is required.**

Three corrections, each traced to something measured rather than reconsidered.

### 1. The pin is `582c818fbb6699ed8813df2d5a722a2c4da32f5c`, not `sdlc-gate-v2.0.2`

Step 3 below said to pin the caller to `@sdlc-gate-v2.0.2`. **No released tag can enforce
`Accepted-for`**: the reusable workflow at `sdlc-gate-v1`, `v2`, `v2.0.1` and `v2.0.2` contains zero
occurrences of `--base-sha`, while gate v2 makes the binding mandatory and fails closed without it.
Installing the caller with that pin would have made **every pull request here fail closed, including
the one installing the gate** — the change would have blocked itself.

Corrected in step 3. The spec's Amendment 1 carries the per-tag measurements and the reasoning.

The red assertions committed in the previous step need **no change**, because they assert only *that*
the ref is pinned and never which version. That was a deliberate choice when they were written, and it
is the reason this correction costs one line instead of a rewrite.

### 2. `Accepted-for` moves from `52d3653` to the new merge base

This branch has been **rebased from `52d3653` onto `2e80605`** to take
[PR #66](https://github.com/timwukp/agent-skills-best-practice/pull/66), because both changes edit
`skills/skills/ai-native-sdlc/scripts/test_required_checks.py`. The old binding no longer matches the
merge base, so an approval recorded against it would be unverifiable — exactly the failure this
repository's own gate exists to catch.

The conflict was resolved by keeping **both** sections rather than choosing one: PR #66's section 4
(the caller example consumers copy) keeps its number, and this change's caller assertions become
section 5. One shared closing parenthesis was misattributed by the merge and left section 4's final
`check(` unclosed; that is fixed, the file parses, and both groups of assertions run.

Rebase was safe without a force-push: the branch had never been pushed and had no pull request.

### 3. The mutation evidence in step 9 was unreadable as written

The evidence section asks for `0 survived`. **On a red branch that number means nothing for the suite
that is red.** Measured: `test_required_checks.py` exits 1 with **no mutation applied**, because
section 5 correctly reports that no caller exists yet. The harness infers "killed" from the suite
failing after a mutation is applied, so while the suite already fails, every mutation it owns is
reported killed either way. **Four** mutations are attributed to `test_required_checks.py`, so four of
the harness's current kills are false.

Step 9 is therefore split:

- **9a** — after the caller exists, confirm `test_required_checks.py` passes **unmutated**. Until that
  holds, the harness's verdict on its four mutations is not evidence and must not be quoted as such.
- **9b** — only then run the full harness and record that run. The expected total is **77** unless a
  mutation is added; if one is, the count is propagated by `scripts/sync_mutation_count.py` and never
  typed.

This is a reporting-soundness gap in the harness, not a defect introduced here: any red suite has the
same effect on its own mutations. Whether the harness should refuse to score a suite that fails
unmutated is a separate question, recorded as a follow-up rather than fixed inside this change.

`Accepted-for` must be `git merge-base origin/main HEAD`, which after the rebase in Amendment 1 is
`2e8060593bdb08885a5a81e60968ee317d341acb`.

## Spec requirement 3, settled before planning

The reusable workflow runs `evals/check_*.py` **from the caller's repository root**. This
repository has no `evals/` directory at its root, so the step finds nothing and reports
"nothing to run". It therefore cannot fail the gate job, and `run-evals` is left at its
default rather than being explicitly disabled — disabling it would be a change made for a
problem that does not exist, and would silently drop eval enforcement if evals are added later.

## Files changed (in order of work)

1. `skills/skills/ai-native-sdlc/scripts/test_required_checks.py` — red assertions that the
   caller exists, is pinned to a tag or SHA rather than `@main`, carries no `paths`/`branches`
   filter, and sets `require-active: true`.
2. `.github/workflows/sdlc-gate.yml` — the caller. New file.
3. `.kiro/hooks/sdlc-gate.json` — the write-time hook config, copied from
   `templates/kiro-hooks/sdlc-gate.json` (spec requirement 6).
4. `.sdlc/scripts/sdlc_pretooluse_hook.py` — the hook script the config invokes.
5. `.sdlc/scripts/sdlc_gate.py` — the stage gate the hook calls. Vendored because the hook runs
   locally with no network; `sdlc_ci_gate.py` is deliberately **not** vendored, since the reusable
   workflow fetches it from the pinned upstream ref and a local copy would be a second, drifting
   source of the merge criteria.
6. `skills/skills/ai-native-sdlc/scripts/mutation_proof.py` — two mutations: repin the caller to
   `@main`, and add a `paths` filter to it.
7. `skills/skills/ai-native-sdlc/SKILL.md` — mutation count, written by
   `scripts/sync_mutation_count.py` rather than by hand.
8. `skills/skills/ai-native-sdlc/references/limitations.md` — same count via the same command,
   plus the self-governance record that **keeps** the administrator-bypass statement.
9. `skills/skills/ai-native-sdlc/COMPATIBILITY.md` — record that this repository is governed by
   its own gate, pinned to a named release.

Note on coverage: `intent/`, `evals/`, `.sdlc/` and `.github/` sit outside plan coverage by
design, but `.kiro/hooks/` does **not** — so file 3 is a covered source file and is named here
deliberately, not incidentally.

`scripts/sdlc_ci_gate.py`, the hook script inside the skill, the schema, the templates and
`GATE_VERSION` are not modified.

## Work order

1. **Reconfirm.** Merge base `2e80605`, build gate open on a committed signed-off spec, tree clean.
2. **Red first.** Add the caller assertions to `test_required_checks.py`. Run it; it must fail
   because `.github/workflows/sdlc-gate.yml` does not exist — reported as findings, not a
   traceback. Commit this red target alone.
3. **Add the caller**, pinned to `@582c818fbb6699ed8813df2d5a722a2c4da32f5c` (see Amendment 1), `require-active: true`, `pull_request` with
   no filter, and the warning comment explaining why a filter must never be added.
4. **Green the suite.** Run `test_required_checks.py`.
5. **Install the write-time layer** — copy the hook config and vendor the two scripts. Verify the
   hook refuses a source edit while no plan authorises it, and permits one that is authorised, by
   invoking it directly rather than by reasoning about it.
6. **Add the two mutations**, anchored on the caller's `uses:` line and its trigger block.
7. **Propagate the count** with `python3 scripts/sync_mutation_count.py`, then confirm
   `--check` exits 0. The count must be written by the command, not typed.
8. **Write the documentation** — `COMPATIBILITY.md` and `limitations.md`, keeping the
   administrator-bypass limit and updating the closing "irony" section to say which item this
   closes and which stay open.
9. **Full validation** (below), in two parts, because the order is what makes the mutation result
   mean anything (Amendment 1, item 3):
   - **9a.** Confirm `test_required_checks.py` passes **unmutated**. Until it does, the harness's
     verdict on the four mutations it owns is not evidence and must not be quoted as one.
   - **9b.** Only then run the full harness and record **that** run. Fix anything red before
     committing.
10. **Commit the implementation.** No artifact approval field set by the agent.
11. **Hand off.** Owner pushes; agent opens the PR whose description contains the exact branch
    protection instruction and states plainly that until that setting changes the check is
    advisory. Owner merges, then closes the chain as `shipped`.

## Tests that prove it

### Red-first target

```sh
cd skills/skills/ai-native-sdlc/scripts
python3 test_required_checks.py     # must fail: the caller does not exist yet
```

### Full suites and mutations

```sh
cd skills/skills/ai-native-sdlc/scripts
count=0; for t in test_*.py; do count=$((count+1)); python3 "$t"; done; test "$count" -ge 14
python3 mutation_proof.py           # expect 76, 0 survived, 0 broken
python3 sync_mutation_count.py --check   # exit 0
```

Pass condition: 14 suites all exit 0; the harness reports **76 killed, 0 survived, 0 broken**
(74 existing plus the two new); both new mutations killed by `test_required_checks.py`; and the
documented count agrees with the harness.

### The gate and hook actually bite

```sh
# the caller's own argument set, on this branch, from the repository root
python3 skills/skills/ai-native-sdlc/scripts/sdlc_ci_gate.py \
  --repo . --changed-files-from changed-files.txt \
  --base-sha "$(git merge-base origin/main HEAD)" --require-active
```

Pass condition: this branch passes; and, demonstrated on a throwaway worktree, a source file no
accepted plan names is **refused** with a non-zero exit naming the file. The write-time hook must
likewise refuse an unauthorised edit and permit an authorised one, each shown by invoking it.

### Workflow and invariant checks

```sh
python3 -c "import yaml;yaml.safe_load(open('.github/workflows/sdlc-gate.yml'))"
git diff 2e8060593bdb08885a5a81e60968ee317d341acb...HEAD --name-only
git diff 2e80605 -- skills/skills/ai-native-sdlc/scripts/sdlc_ci_gate.py   # empty
```

Pass condition: the caller's YAML parses; only the nine files above plus the dogfood artifacts
differ; `sdlc_ci_gate.py` byte-identical; `GATE_VERSION = 2`, `SUPPORTED_SCHEMA = 1`; and the
caller contains no `paths:` or `branches:` under `pull_request`.

## Risks

- **A required check that cannot pass would block every pull request.** Already measured in the
  spec across all three PR shapes, and re-verified in step 9 on this branch before handoff.
- **The check is advisory until branch protection changes.** Unavoidable — a merged pull request
  cannot grant itself blocking power. Stated in the PR description rather than implied.
- **An administrator can still merge past a red gate.** `enforce_admins` is `false` and a personal
  repository has no tier above its owner. Requirement 7 keeps this on the record; nothing in this
  change may be described as unbypassable.
- **The pin will go stale.** Deliberate: a deliberate bump is the property being bought. A test
  asserts only that it *is* pinned, not which version, so a bump does not require editing tests.
- **Vendoring could create a second source of merge criteria.** Mitigated by vendoring only the
  local hook path and never `sdlc_ci_gate.py`.
- **`.kiro/hooks/` is inside plan coverage** — omitting it from the file list would make this very
  change fail its own gate. Named above.

Rejected alternatives: vendoring the CI gate and calling it directly; pinning `@main`; a local
`./.github/workflows/` reference; setting `require-active: false`; and weakening the gate if the
repository's own history failed it. All argued in `spec.md`.

---
Gate: engineer accepts BEFORE any implementation file is edited. If implementation departs from
this plan, update it and obtain renewed acceptance.

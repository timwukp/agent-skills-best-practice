# Plan: stop hand-editing the mutation count in three coupled places

- **Spec:** ./spec.md
- **Author:** Kiro (AI agent)
- **Accepted-by:** pending — engineer acceptance
- **Accepted-for:** pending — set to the pull-request merge base at acceptance
- **Status:** draft

`Accepted-for` must be `git merge-base origin/main HEAD`, which at draft time is
`3a343d5d55b8af60d17e033568f1a7908722cb3d`.

## Files changed (in order of work)

1. `skills/skills/ai-native-sdlc/scripts/test_sync_mutation_count.py` — new red suite for the
   sync command: count derivation, rewrite, `--check` exit codes, idempotence, and unmatched
   pattern as a hard error. Operates only on temporary fixtures.
2. `skills/skills/ai-native-sdlc/scripts/sync_mutation_count.py` — new stdlib command that
   derives `len(MUTATIONS)` by parsing the harness and rewrites the count in the two documents,
   with a `--check` mode that changes nothing and exits non-zero when stale.
3. `skills/skills/ai-native-sdlc/scripts/mutation_proof.py` — re-anchor the
   `positioning: stale mutation evidence count` entry on prose containing no count, and add the
   mutation that makes `--check` wrongly report success.
4. `skills/skills/ai-native-sdlc/SKILL.md` — document the sync command in the mutation-proof
   guideline, and carry whatever count the finished harness reports.
5. `skills/skills/ai-native-sdlc/references/limitations.md` — same count, updated by running the
   new command rather than by hand.
6. `.github/workflows/sdlc-gate-tests.yml` — add `test_sync_mutation_count` to the explicit
   matrix suite list so repository CI runs it.

`scripts/sdlc_ci_gate.py`, the hook, the schema, the workflow templates and `GATE_VERSION` are
**not** touched.

## Work order

1. **Reconfirm base and gate.** Merge base `3a343d5`, build gate open, tree clean.
2. **Red first.** Write `test_sync_mutation_count.py` against the command's intended contract.
   Run it; it must fail because the command does not exist yet — and it must fail as assertions
   or a clean "module missing" verdict the suite reports itself, not an uncaught traceback.
   Commit this red target separately.
3. **Implement the command.** Parse the harness with `ast`, handling the annotated assignment.
   Per-target regex with the number as a capture group; unmatched pattern is a hard error;
   `--check` writes nothing.
4. **Green the suite.** Run it until it passes without weakening any assertion.
5. **Re-anchor the stale-count mutation** on prose containing no digits, so a count change can
   never make it `broken`. Verify by running the harness and confirming that entry is
   `KILLED` — and that the kill is caused by a stale `27 mutations` claim appearing, not by
   some unrelated assertion.
6. **Add the `--check` mutation** that makes stale return success, and confirm
   `test_sync_mutation_count.py` kills it.
7. **Run the command for real** to update the two documents' counts. This is the first proof
   that the tool replaces the hand-edit: the count must be written by the command, not typed.
8. **Add the suite to repository CI** in the explicit matrix list.
9. **Full validation** (below). Fix any failure before committing.
10. **Commit the implementation.** No artifact approval field set by the agent.
11. **Hand off.** Owner pushes `dynamic-mutation-count`; agent opens the PR; required checks are
    green only when the conclusion is `success`, never `skipped`; owner merges and closes the
    chain as `shipped`.

## Tests that prove it

### Red-first target

```sh
cd skills/skills/ai-native-sdlc/scripts
python3 test_sync_mutation_count.py    # must fail before the command exists
```

### Full suites and mutations

```sh
cd skills/skills/ai-native-sdlc/scripts
count=0; for t in test_*.py; do count=$((count+1)); python3 "$t"; done; test "$count" -ge 14
python3 mutation_proof.py    # expect 0 survived, 0 broken
```

Pass condition: at least 14 suites (13 existing + the new one), all exit 0; the harness reports
`0 survived, 0 broken`; the re-anchored stale-count entry and the new `--check` entry are both
`KILLED`.

### The decoupling itself

```sh
# 1. the documents already agree with the harness
python3 skills/skills/ai-native-sdlc/scripts/sync_mutation_count.py --check   # exit 0

# 2. adding a mutation makes them disagree, and --check says so
#    (verified against a temporary copy, not the repository)

# 3. the stale-count mutation's anchor contains no digits
grep -n 'stale mutation evidence count' -A 4 \
  skills/skills/ai-native-sdlc/scripts/mutation_proof.py
```

Pass condition: `--check` exits 0 on the committed tree; the anchor shown by the `grep` contains
no mutation count; and `test_enterprise_readiness.py` still fails if a document's count is
altered by hand (verified against a temporary copy).

### Invariant checks

```sh
git diff 3a343d5d55b8af60d17e033568f1a7908722cb3d...HEAD --name-only
git diff 3a343d5 -- skills/skills/ai-native-sdlc/scripts/sdlc_ci_gate.py   # empty
```

Pass condition: only the six files above plus the dogfood artifacts differ; `sdlc_ci_gate.py`
byte-identical; `GATE_VERSION = 2`, `SUPPORTED_SCHEMA = 1`; the changed workflow YAML parses.

## Risks

- **The new anchor could still be number-dependent.** The whole point of requirement 1 is lost if
  it is. Grep the finished entry for digits and confirm `0 broken` after a count change.
- **A rewrite tool could corrupt a document.** Per-target regex with a capture group, hard error
  on no match, idempotence asserted, and tests confined to temporary fixtures so a test run can
  never touch tracked files.
- **The red target could fail as an import traceback** rather than as a reported verdict, which
  proves nothing. The suite must handle the missing module and report it.
- **Net-complexity objection.** Bounded to one small stdlib script plus its suite; the
  alternative is a red build on every future mutation change.
- **Wrong acceptance binding.** Bind to `3a343d5` (merge base), not branch HEAD.

Rejected alternatives: qualitative wording, a generated include, a render-time token, importing
the harness, a git hook, and deleting the stale-count mutation. All argued in `spec.md`.

---
Gate: engineer accepts BEFORE any implementation file is edited. If implementation departs from
this plan, update it and obtain renewed acceptance.

# Plan: assert the content at the ref we recommend

- **Spec:** ./spec.md
- **Author:** Kiro (AI agent)
- **Accepted-by:** Tim WU
- **Accepted-for:** f7cc3d5a3e3a8d1ec13d9ff7ed80abec6c567008
- **Status:** accepted

`Accepted-for` must be `git merge-base origin/main HEAD`, which at draft time is
`f7cc3d5a3e3a8d1ec13d9ff7ed80abec6c567008`.

## Resolved: the spec's two open questions

**Q1 — the recommended pin is `582c818fbb6699ed8813df2d5a722a2c4da32f5c`.** Verified rather than
assumed: it is the merge commit of PR #60 ("fix-reusable-gate-binding"), it is reachable from
`origin/main`, the reusable workflow at that ref contains 2 occurrences of `--base-sha`, and
`sdlc_ci_gate.py` at that ref is byte-identical to `f7cc3d5`. It is chosen over the `main` tip because
it is the *minimal* ref carrying the property — a consumer can read one pull request to see why this
commit is the one that makes the binding verifiable, where the tip would require reading four.

**Q2 — the `fetch-depth: 0` cost is measured and recorded, not hidden.** The plan measures clone time
before and after in the suite job and writes both numbers into the pull request. CI duration is what
tempts the next person to add a path filter, so an unexplained slowdown is a latent defect.

## Files changed (in order of work)

1. `skills/skills/ai-native-sdlc/scripts/test_support_matrix.py` — the pin-**content** assertion. This
   suite already owns pin guidance and already asserts the pin names an existing tag, so the suite that
   made the insufficient claim is the one that gains the sufficient one.
2. `skills/skills/ai-native-sdlc/scripts/test_required_checks.py` — the header-example assertion. This
   suite owns the trigger-filter deadlock class and already has `pull_request_filters()` and
   `FATAL_ON_REQUIRED`; the example is a caller, so its filters belong here rather than in the pin suite.
3. `skills/skills/ai-native-sdlc/COMPATIBILITY.md` — recommended pin becomes the SHA; the versioning
   section states that `sdlc-gate-v1` and `v2`–`v2.0.2` cannot enforce `Accepted-for`.
4. `.github/workflows/sdlc-gate-reusable.yml` — the header caller example: unfiltered `pull_request`,
   pinned `uses:`.
5. `.github/workflows/sdlc-gate-tests.yml` — `fetch-depth: 0` on the suite job so requirement 1 is live
   in CI instead of skipped there.
6. `skills/skills/ai-native-sdlc/scripts/mutation_proof.py` — two mutations (anchoring below).
7. `skills/skills/ai-native-sdlc/SKILL.md` — mutation count, written by `sync_mutation_count.py`.
8. `skills/skills/ai-native-sdlc/references/limitations.md` — same count via the same command.

`scripts/sdlc_ci_gate.py`, the schema, the templates and `GATE_VERSION` are not touched.

## Mutation anchoring — deliberately ref-free

Both mutations **insert** a broken form under prose containing no version number and no SHA, rather
than rewriting the recommended ref itself. Anchoring on the SHA would mean that changing the
recommended pin — the very thing this change makes safe to do — marks the mutation `broken`. That is
the coupling defect fixed in PR #64, and repeating it here would be repeating a mistake this repository
has already paid for once.

- **M-A** inserts an *additional* pin example naming `@sdlc-gate-v2.0.2` beneath the stable
  `### How consumers pin` heading. Requirement 1 checks **every** concrete pin example, so an added
  broken one must fail. Killed by `test_support_matrix.py`.
- **M-B** inserts `#     branches: [main]` into the header example's `on:` block, anchored on the
  comment prose. Killed by `test_required_checks.py`.

## Work order

1. **Reconfirm.** Spec `signed-off` in a committed state, build gate open, merge base recorded, tree
   clean, `582c818` still satisfying every property listed under Q1.
2. **Red first, part one.** Add the pin-content assertion to `test_support_matrix.py`. Run it: it must
   **fail** because `COMPATIBILITY.md` still recommends `@sdlc-gate-v2.0.2`, reported as a finding
   naming the ref and the occurrence count, not as a traceback.
3. **Red first, part two.** Add the header-example assertion to `test_required_checks.py`. Run it: it
   must **fail** on the current `branches: [main]` example. Commit both red targets together, with the
   failing output quoted in the commit message.
4. **Verify the skip path** before fixing anything: point the assertion at a ref that does not exist
   and confirm it reports a **skip naming the ref**, then restore. This is checked while the assertion
   is still red, so a skip cannot be mistaken for a pass.
5. **Fix the documentation** — `COMPATIBILITY.md`: recommended pin becomes
   `@582c818fbb6699ed8813df2d5a722a2c4da32f5c`, with the placeholder `<full-sha>` example left intact,
   and the versioning section naming the versions that cannot enforce the binding. No uncut tag is
   mentioned anywhere (spec requirement 10).
6. **Fix the header example** in `sdlc-gate-reusable.yml`.
7. **Green both suites.**
8. **Deepen the CI checkout** and measure: record suite-job clone time before and after.
9. **Add the two mutations** with the anchors above; run the harness.
10. **Propagate the count** with `python3 scripts/sync_mutation_count.py`, then confirm `--check`
    exits 0. The count is never typed.
11. **Full validation** (below). Fix anything red before committing.
12. **Commit the implementation.** No approval field touched by the agent.
13. **Hand off.** Owner pushes; agent opens the pull request whose description names the tag the owner
    would cut to move from a SHA pin to a tag pin, states that a SHA is currently the only pin that
    enforces the binding, and reports the two clone timings.

## Tests that prove it

### Red-first targets

```sh
cd skills/skills/ai-native-sdlc/scripts
python3 test_support_matrix.py    # must fail: recommended ref carries no --base-sha
python3 test_required_checks.py   # must fail: header example carries branches:
```

### Per-tag evidence, printed not remembered

```sh
for t in $(git tag -l 'sdlc-gate-*'); do
  printf '%s %s\n' "$t" "$(git show "$t:.github/workflows/sdlc-gate-reusable.yml" | grep -c 'base-sha')"
done
git show 582c818fbb6699ed8813df2d5a722a2c4da32f5c:.github/workflows/sdlc-gate-reusable.yml \
  | grep -c 'base-sha'
```

Pass condition: every tag reports 0; `582c818` reports 2.

### Full suites and mutations

```sh
count=0; for t in test_*.py; do count=$((count+1)); python3 "$t"; done; test "$count" -ge 14
python3 mutation_proof.py
python3 sync_mutation_count.py --check
```

Pass condition: 14+ suites exit 0; the harness reports **76 killed, 0 survived, 0 broken** (74 plus
the two new); M-A attributed to `test_support_matrix.py` and M-B to `test_required_checks.py`; the
documented count agrees with the harness.

### Invariants

```sh
git diff f7cc3d5 -- skills/skills/ai-native-sdlc/scripts/sdlc_ci_gate.py    # empty
grep -n 'GATE_VERSION\|SUPPORTED_SCHEMA' skills/skills/ai-native-sdlc/scripts/sdlc_ci_gate.py
grep -rn 'sdlc-gate-v2\.0\.3' skills/ .github/ || echo 'no uncut tag referenced'
python3 -c "import yaml;yaml.safe_load(open('.github/workflows/sdlc-gate-reusable.yml'))"
python3 -c "import yaml;yaml.safe_load(open('.github/workflows/sdlc-gate-tests.yml'))"
```

Pass condition: gate script byte-identical; `GATE_VERSION = 2`, `SUPPORTED_SCHEMA = 1`; no reference
to an uncut tag; both workflows parse; and the reusable workflow's `pull_request` trigger — the real
one, not the example — remains unfiltered.

## Risks

- **Two branches now modify the same two files.** `self-governed-pr-gate` (parked at `af3ba86`) also
  edits `test_required_checks.py` and `mutation_proof.py`. Whichever merges second must rebase and
  re-run the harness; the mutation count will need re-propagating by command, not by hand. Named here
  so it is expected rather than discovered.
- **`fetch-depth: 0` slows the suite job.** Measured and published rather than absorbed silently,
  because an unexplained slowdown is what invites the path filter that PR #48 was blocked by.
- **A SHA pin is less readable than a tag.** Accepted: a readable pin that fails closed is worse than
  an opaque pin that works. The versioning section explains the choice.
- **The recommended pin could later be changed carelessly.** That is what requirement 1 prevents, and
  the ref-free mutation anchoring keeps the guard working across a pin change.
- **A skip could masquerade as a pass** in an environment with no tags. Step 4 verifies the skip path
  while the assertion is still red, which is the only ordering that distinguishes the two.
- **This change cannot make consumers whole by itself.** Until the owner cuts a release, consumers must
  pin a SHA. The pull request says so instead of implying the defect is closed.

Rejected alternatives: recommending `@main`; waiting for the release before fixing the docs; asserting
only that the pin is a tag; backporting onto a v2.0.x branch; and having the test fetch refs over the
network. All argued in `spec.md`.

---
Gate: engineer accepts BEFORE any implementation file is edited. If implementation departs from this
plan, update it and obtain renewed acceptance.

# Spec: make the recommended pin verifiably work

- **Intent:** ./intent.md
- **Author:** Kiro (AI agent)
- **Signed-off-by:** Tim WU
- **Status:** signed-off

## The defect, restated as the property that was missing

`COMPATIBILITY.md` recommends `@sdlc-gate-v2.0.2`. Measured across every tag in the repository, the
reusable workflow at that ref contains **zero** occurrences of `--base-sha`:

| Tag | `--base-sha` in the reusable workflow |
|---|---|
| `sdlc-gate-v1` | 0 |
| `sdlc-gate-v2` | 0 |
| `sdlc-gate-v2.0.1` | 0 |
| `sdlc-gate-v2.0.2` | 0 |
| `origin/main` | 2 |

Gate v2 makes `Accepted-for` mandatory and fails closed when it cannot verify the binding, so the
documented pin refuses every compliant consumer's pull request. Demonstrated on one unchanged tree by
changing only the argument set: the v2.0.2 arg set reports *"bound to base 52d365365aed but this run
was given no `--base-sha`, so the binding was NOT verified"*, while `main`'s reports *"approval bound
to base 52d365365aed, which matches"*.

Three existing assertions all pass while this is true:

- **U9** — the shipped *template* passes `--base-sha`.
- **U10** — the *working tree's* reusable workflow runs the gate with `--base-sha`.
- **`test_support_matrix.py`** — the recommended pin names a tag that **exists**.

Every one of them inspects the working tree, or the ref's *name*. The missing property is that the
**content at the ref we tell consumers to use** actually verifies the binding. That is the property
this change adds, and it is what makes the documentation self-checking rather than aspirational.

## Resolved open questions

**Q1 — the fixed pin is a full SHA now, a tag when one exists.** I cannot cut a release, and the
documentation must never state something false, so the recommended example becomes a **concrete
commit SHA on `main` that contains the fix**. The versioning section states plainly that no released
tag can enforce `Accepted-for` and that a tag pin becomes the recommendation once a release contains
the fix. Because requirement 1 asserts the *content* at whatever ref the document recommends, the
later switch to `sdlc-gate-v2.0.3` cannot be made incorrectly — the test will refuse a tag that does
not pass `--base-sha`. The owner may still cut that release at any time; this change does not wait
for it and does not pre-announce it.

**Q2 — the assertion runs for real in CI, which requires a deeper checkout.** Measured:
`.github/workflows/sdlc-gate-tests.yml` uses `actions/checkout@v4` with **no `fetch-depth`**, so the
job has a shallow clone and no tags. A ref-reading test would therefore skip in precisely the place
releases are made. The job that runs the suites gains `fetch-depth: 0`. The test still skips cleanly
when a ref cannot be resolved, because the skill is installed standalone into repositories that have
never heard of `sdlc-gate-vN`, and a suite that fails there would be worse than the defect.

**Q3 — the unusable versions get an explicit statement, not a deletion.** `COMPATIBILITY.md` states
that `sdlc-gate-v1` and `sdlc-gate-v2` through `v2.0.2` cannot enforce `Accepted-for`. Deleting or
moving those tags is rejected: some consumer may already be pinned to one, and rewriting a published
ref changes history other people depend on.

**Q4 — a release checklist is out of scope.** Four release-time defects in four attempts (#55, #56,
#57, and this one) is evidence about the *process*, not about four mistakes, but fixing the process
is a separate workstream with its own intent. Recorded as a non-requirement so it is not silently
dropped.

## Requirements

1. **The recommended pin's content is asserted.** For every pin example in `COMPATIBILITY.md` that
   names a concrete ref, the reusable workflow at that ref must pass `--base-sha` to the gate.
   Placeholder examples such as `<full-sha>` are skipped by design — they instruct rather than
   recommend. The assertion targets the step that *runs* the gate, so a comment mentioning
   `--base-sha` cannot satisfy it.
2. **The assertion fails against the current text.** Observed failing with `@sdlc-gate-v2.0.2`
   recommended, before the documentation is changed.
3. **Clean skip when a ref is unresolvable**, reported as a skip with the ref named, never as a
   failure or a traceback. Verified by running the suite where the ref does not exist.
4. **CI resolves refs.** The suite-running job checks out with `fetch-depth: 0`, so requirement 1 is
   live in CI rather than skipped there.
5. **The header example stops teaching a deadlock.** The caller example inside
   `.github/workflows/sdlc-gate-reusable.yml` must show an unfiltered `pull_request` trigger and a
   pinned `uses:`. Asserted by a test, because the example is copied by consumers and is therefore an
   interface rather than a comment. Its current form shows `branches: [main]` — the filter that left
   PR #53 permanently blocked, and which the shipped template's own comment forbids — and `@main`,
   contradicted by the next sentence of that same comment.
6. **The versioning section states which releases cannot enforce the binding**, naming `v1` and
   `v2`–`v2.0.2`, and says what a consumer on one of them should do.
7. **Mutation coverage for both defects.** At minimum: reverting the recommended pin to a ref whose
   content omits `--base-sha`, and reintroducing a `branches:` filter into the header example. Each
   must be killed by the assertions above, and the harness must report 0 survived and 0 broken.
8. **The count is propagated by `scripts/sync_mutation_count.py`**, never typed by hand, and
   `--check` exits 0 afterwards.
9. **Gate semantics unchanged.** `GATE_VERSION = 2`, `SUPPORTED_SCHEMA = 1`, and
   `scripts/sdlc_ci_gate.py` byte-identical to `f7cc3d5`. This is a packaging and documentation
   defect; the gate logic is already correct, which is exactly why the defect was invisible from
   inside the working tree.
10. **No release is claimed that does not exist.** No document may reference `sdlc-gate-v2.0.3`, or
    any other uncut tag, as though it were available.
11. **The pull request states the owner action.** It names the tag the owner would cut for the
    documentation to move from a SHA pin to a tag pin, and states that until then a SHA is the only
    pin that enforces the binding.

## Non-requirements

- Cutting the release. Tagging is the owner's action.
- Moving, deleting, or re-pointing any published tag.
- A release checklist or release-process artifact (Q4) — separate workstream.
- Changing the gate, the schema, the templates, or the enforcement generation.
- Backporting the fix onto the v2.0.x line as a new patch branch. Rejected below.

## Acceptance evidence

- The new assertion observed **failing** with the current recommended pin, then passing after the
  documentation change, with both outputs recorded.
- Per-tag `--base-sha` occurrence counts, printed rather than asserted from memory.
- The suite run where the recommended ref does not resolve, showing a **skip** that names the ref.
- 14+ suites green; the harness reporting the new total with **0 survived, 0 broken**; both new
  mutations attributed to the assertions that kill them.
- `python3 scripts/sync_mutation_count.py --check` exits 0.
- `git diff f7cc3d5 -- skills/skills/ai-native-sdlc/scripts/sdlc_ci_gate.py` empty.
- The header example parsed to confirm it carries no `branches:`/`paths:` key and a pinned `uses:`.

## Rejected alternatives

- **Recommending `@main`.** It is the only ref that works today without a release, and it is exactly
  what the reusable workflow's own comment warns against: an upstream change would silently alter a
  consumer's merge criteria. Rejected.
- **Waiting for the owner to cut `v2.0.3` before fixing the docs.** That leaves consumers broken for
  as long as the release takes, and the fix does not depend on the release.
- **Asserting only that a pin is a tag.** That is the assertion that already exists and that passed
  throughout this defect. Existence was never the property that mattered.
- **Backporting onto a v2.0.x branch.** More release surface, and the fix is already on `main`; a
  patch release from `main` is the simpler path when the owner chooses to cut one.
- **Having the test fetch refs over the network.** A unit test that reaches the network is flaky by
  construction and would fail in an offline install. CI supplies the objects instead.

## Open questions for the plan

1. Which concrete SHA does the recommended example use — the fix commit `582c818`, or the current
   `main` tip? The fix commit is the minimal ref that satisfies the requirement; the tip carries
   later improvements. The plan should pick one and say why, and the choice must be a merge commit
   reachable from `main` so a consumer can verify its provenance.
2. Does `fetch-depth: 0` measurably slow the suite job? If it does, the plan should record the cost
   rather than hide it, since CI duration is what tempts the next person to add a filter.

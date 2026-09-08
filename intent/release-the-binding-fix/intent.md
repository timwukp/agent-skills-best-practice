# Intent: the fix exists on main and every consumer is still broken

- **Slug:** release-the-binding-fix
- **Author:** Kiro (AI agent)
- **Accepted-by:** pending — product owner acceptance
- **Date:** 2026-09-08
- **Status:** draft

## Problem

`COMPATIBILITY.md` tells every consumer to pin the reusable gate like this:

```yaml
uses: timwukp/agent-skills-best-practice/.github/workflows/sdlc-gate-reusable.yml@sdlc-gate-v2.0.2
```

**No released tag can satisfy a v2 plan binding.** Measured across every tag in the repository —
`sdlc-gate-v1`, `sdlc-gate-v2`, `sdlc-gate-v2.0.1`, `sdlc-gate-v2.0.2` — the reusable workflow at
that ref contains **zero** occurrences of `--base-sha`. Gate v2 made `Accepted-for` mandatory and
fails closed when it cannot verify the binding, so the documented pin refuses every compliant
consumer's pull request.

Measured on one unchanged tree, changing only the argument set:

| Arg set | Gate result |
|---|---|
| what `@sdlc-gate-v2.0.2` actually runs (no `--base-sha`) | **FAILED** — "bound to base 52d365365aed but this run was given no `--base-sha`, so the binding was NOT verified" |
| what `main` runs today (`--base-sha` supplied) | **PASSED** — "approval bound to base 52d365365aed, which matches" |

PR #60 fixed this on `main` on 2026-09-07 and **shipped no release**. The repository's own CI reads
the working tree, so it went green while every downstream consumer following the documented
instruction stayed broken. This is the same defect as #60 recurring one layer up: #60 was
"the recommended integration path is broken", and this is "the recommended *version* of it is
broken".

**Why the tests did not catch it.** Three assertions added by #60 all pass:

- U9 — the shipped *template* passes `--base-sha`;
- U10 — the *working tree's* reusable workflow runs the gate with `--base-sha`;
- `test_support_matrix.py` — the recommended pin names a tag that **exists**.

Every one of them inspects the working tree or the ref's *name*. Nothing inspects the *content* at
the ref consumers are told to use. #60 moved the question from "does this ref resolve" to "does the
tree work" and stopped one step short of "does the thing we ship work".

**A second defect in the same file.** The reusable workflow's header comment shows consumers a
caller to copy:

```yaml
on:
  pull_request:
    branches: [main]
uses: ...sdlc-gate-reusable.yml@main
```

Both lines are wrong. `branches:` on `pull_request` is the filter that left PR #53 permanently
blocked — a stacked pull request auto-retargeted to `main`, then waiting forever on a check that had
never been triggered — and the shipped template carries a long comment forbidding exactly that.
`@main` is contradicted by the very next sentence of its own comment, which says to pin. A consumer
who copies the documented example gets an unpinned caller that can deadlock.

## Desired outcome

A consumer who follows `COMPATIBILITY.md` gets a gate that works: the pin resolves, and the
workflow at that ref verifies the approval binding rather than failing closed. The example a
consumer copies produces a correctly pinned, unfiltered caller. And a future release cannot
reintroduce this class of defect silently, because a test asserts the released artifact rather than
only the working tree.

## Affected users / systems

- **Every consumer of the reusable workflow**, which is the skill's recommended integration path.
- The `agent-skills-best-practice` release process — a fix merged to `main` is currently assumed
  released.
- `.github/workflows/sdlc-gate-reusable.yml` — its header example.
- `COMPATIBILITY.md` — its pin recommendation and version table.
- The test suites that were supposed to make this impossible.
- **Blocked on this:** `self-governed-pr-gate`, parked at `af3ba86`. Its spec chose
  `@sdlc-gate-v2.0.2` as the pin, which would have made this repository's own gate fail closed on
  every pull request — including the one installing it.

## Constraints

- **I cannot cut a release.** Creating a tag is the owner's action. This change prepares and
  verifies a release; it does not perform one.
- **No rewriting of published tags.** Moving an existing tag would change history other people may
  already depend on. A new patch release, not a retag.
- `GATE_VERSION = 2` and `SUPPORTED_SCHEMA = 1` are unchanged — this is a packaging and
  documentation defect, not a gate-semantics change.
- `scripts/sdlc_ci_gate.py` stays byte-identical: the gate logic is already correct, which is
  precisely why this defect is invisible from inside the working tree.
- A test that reads git tags must **skip cleanly**, not fail, where no tags exist — the skill is
  installed standalone into repositories that have never heard of `sdlc-gate-vN`, and a suite that
  fails there is worse than the defect.
- The mutation count will rise; it is propagated by `scripts/sync_mutation_count.py` and never
  typed by hand.
- Docs may not claim a release exists before the owner has cut it.

## Success criteria

1. A test asserts that the reusable workflow **at the ref `COMPATIBILITY.md` recommends** passes
   `--base-sha`, and it fails against `@sdlc-gate-v2.0.2` before any fix.
2. That test skips cleanly in a repository with no `sdlc-gate-*` tags, verified by running it
   somewhere without them.
3. The reusable workflow's header example shows an unfiltered `pull_request` trigger and a pinned
   `uses:`, consistent with the shipped template rather than contradicting it.
4. A test asserts the header example itself carries no `branches:`/`paths:` filter — the example is
   copied by consumers, so it is an interface, not a comment.
5. `COMPATIBILITY.md` recommends a pin whose content verifies the binding, and says plainly that
   v1 and v2.0.0–v2.0.2 cannot enforce `Accepted-for`.
6. Mutations added for both defects; harness reports 0 survived, 0 broken; count propagated by the
   sync command.
7. All suites green, and `sdlc_ci_gate.py` byte-identical to `f7cc3d5`.
8. The PR states which tag the owner must create for the documentation to become true, and that
   until then consumers must pin a SHA.

## Open questions

1. **What is the fixed pin — a new tag or a commit SHA?** A tag (`sdlc-gate-v2.0.3`) is readable and
   is what the docs already teach, but only the owner can cut it, so the documentation is briefly
   ahead of reality. A full SHA is available immediately and is what GitHub's own hardening guidance
   recommends, but it is opaque and abandons the version story. Proposed: document the SHA as the
   correct pin *today* and the tag as the recommended pin once cut, so no instruction is ever
   false. Owner decides.
2. **Should the test pin-check run in CI, where tags may be absent?** `actions/checkout` does not
   fetch tags by default, so a naive test would skip in exactly the place it matters most. Options:
   fetch tags in the workflow, or read the ref from the GitHub API. Proposed: fetch tags in CI and
   skip locally, so the assertion is real where releases are made.
3. **Do v1 and v2.0.0–v2.0.2 get deprecation notes in the docs, or a stronger signal?** They cannot
   enforce the binding they advertise. Proposed: an explicit table row stating so — deleting a
   release is worse, since some consumer may already be pinned to it.
4. **Does the release process itself need a checklist artifact?** Three prior release PRs (#55, #56,
   #57) each fixed a different release-time defect, and this is a fourth. That pattern suggests the
   process, not the individual mistakes, is the problem. Proposed: out of scope here, raised as a
   separate workstream.

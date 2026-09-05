# Compatibility and versioning

This tool's output is a **policy decision**: when it changes behaviour, someone's build
starts failing on code that was fine yesterday. That makes a change here more disruptive
than a change in an ordinary library, so the rules below are stricter than plain SemVer.

## What the version number covers

Two things are versioned separately.

| Thing | Version | Where |
|---|---|---|
| **Artifact schema** — the files and fields the gate reads | integer, no minor | `.sdlc/version` in the consuming repo |
| **Gate implementation** — script and reusable workflow | SemVer `MAJOR.MINOR.PATCH` | git tags, `vN` moving tag |

They are separate on purpose: the gate can gain features without forcing every repository
to migrate its artifacts.

## The compatibility promise

**MAJOR** — a change that can turn a previously-green repository red. Examples: a new
required field, a stricter rule, dropping a schema version, removing a flag.

**MINOR** — new capability that cannot fail an existing passing repository. A new *optional*
input, a clearer message, a rule that only applies when newly-opt-in configuration is
present.

**PATCH** — bug fixes that do not change which repositories pass. Note the sharp edge: fixing
a bug that made the gate *too permissive* is a **MAJOR**, not a patch, because repositories
that were passing incorrectly will now fail. Correctness of the fix does not make it
non-breaking.

### Rules for a breaking change

A MAJOR release must:

1. Ship the check as a **warning first** in a MINOR release, for at least one release cycle.
   The warning must name the exact remediation, not merely the rule.
2. Provide either a migration script or precise manual steps, in the release notes and in
   `references/enforcement.md`.
3. Keep the previous major supported for **six months** after the successor's release.
4. Be opt-in-able for a grace period where technically possible, so a consumer can adopt on
   their own schedule.

### How consumers pin

```yaml
# Recommended — automatic patches and features, never a breaking change:
uses: timwukp/agent-skills-best-practice/.github/workflows/sdlc-gate-reusable.yml@v1

# Strictest — nothing changes until you change it. Required if the gate is a
# compliance control, because a moving tag means upstream can alter your merge criteria:
uses: timwukp/agent-skills-best-practice/.github/workflows/sdlc-gate-reusable.yml@<full-sha>
```

`@main` is for experimenting only. Pinning a compliance control to a moving branch means
someone else's commit silently changes what your organisation permits.

## Precedent, recorded honestly

**The separation-of-duties check violated the policy above.** It shipped as an immediate
breaking change: repositories with accepted artifacts lacking `Author` / `Accepted-by`
went red with no warning release, no deprecation window and no migration script. That was
wrong, it is the reason this document exists, and it is stated here rather than quietly
fixed so the failure is on the record. Subsequent breaking changes follow the rules above.

## Support matrix

Only the first block is *tested*. The rest is expectation, and expectation is not evidence.

The block below is the **single source of truth**, and `scripts/test_support_matrix.py`
asserts three things about it: the prose table agrees with it, nothing is listed as both
verified and untested, and **CI actually runs everything it claims is verified**. A claim
here that CI does not cover is a build failure, not a documentation nit — this file used to
say "Python 3.12 (CI)" while the workflow pinned 3.11, and only a test can stop that
recurring.

```json support-matrix
{
  "ci_verified": {
    "os": ["ubuntu-latest", "macos-latest", "windows-latest"],
    "python": ["3.9", "3.10", "3.11", "3.12", "3.13"],
    "repo_shapes": ["monorepo-single-intent", "multi-intent-pr-refused", "concurrent-pr-independent"]
  },
  "posix_only": [
    "the local PreToolUse hook command in templates/kiro-hooks/sdlc-gate.json"
  ],
  "known_hazards": [
    "concurrent-pr lost update: .sdlc/active is a single shared value; needs strict status checks"
  ],
  "documented_untested": {
    "os": [],
    "python": [],
    "repo_shapes": ["polyglot", "fork-pr"],
    "forges": ["gitlab", "bitbucket"],
    "surfaces": ["kiro-web"]
  }
}
```

### Verified

| Dimension | Coverage |
|---|---|
| Python | 3.9, 3.10, 3.11, 3.12, 3.13 — stdlib only, no dependencies |
| OS | `ubuntu-latest`, `macos-latest`, `windows-latest` (also run on Amazon Linux 2023) |
| Repo shape | Single-package repo; static single-page site; **monorepo** with a single active intent; a **multi-intent PR is refused** with a diagnostic naming the intent that owns each file |
| Concurrency | Concurrent PRs each declaring their own intent validate **independently** — but see the hazard below |
| Forge | GitHub — Actions and branch protection |
| Surfaces | Kiro IDE and CLI (`PreToolUse`); official Kiro and KiroCrew hook runtimes |

### Monorepo: one intent per change, by design

A monorepo works, with a rule: **exactly one intent may be active per change.** The coverage
check asks "does *this* intent's plan describe *this* change", and that question has no answer
when several intents are active at once.

All three behaviours below are tested in `scripts/test_scale.py`:

- A single-intent change inside a monorepo passes normally.
- A PR spanning two intents is **refused**, and the diagnostic names the intent whose plan
  *does* cover each stray file, then says to split the PR — rather than nudging you to widen
  the active plan to cover work it does not describe.
- `.sdlc/active` listing more than one slug is **refused by both gates**. It previously read
  only the first line and silently discarded the rest, so a change was attributed to an intent
  the author had not chosen, with no diagnostic at all.

### Concurrency hazard: `.sdlc/active` is a shared mutable value

Each pull request is validated against its own merge commit, so two PRs each declaring their
own intent are individually correct. That part is tested.

**What is not solved:** `.sdlc/active` is one file. A branch cut before someone else's merge
still carries the old pointer and overwrites theirs on merge, so that intent's attribution
silently disappears from `main`. No per-PR check can detect it — each PR genuinely is valid on
its own.

Two things narrow it, and neither is a fix:

1. The gate emits a **note whenever a change rewrites `.sdlc/active`**, so a pointer handover
   is visible at review time instead of being folklore.
2. The real mitigation is in branch protection: **require branches to be up to date** (strict
   status checks) when several intents are in flight. That forces a rebase, which is what
   makes the lost update impossible.

### Windows: the CI gate works, the local hook does not

Stated separately because "Windows verified" on its own would be misleading.

The gate **scripts** are pure stdlib Python and are exercised on Windows by the test
matrix, so the **CI gate is verified there**. But **the local PreToolUse hook command in
`templates/kiro-hooks/sdlc-gate.json` is POSIX-only**: it is an `sh -c '...'` string using
`[ -f ]`, `command -v` and `exec`, and Windows has no `/bin/sh`. On Windows the hook
command simply will not run, so a Windows developer gets the merge-time control and **not**
the write-time one.

This was found by the matrix rather than by reasoning: the Windows cells raised
`FileNotFoundError (WinError 2)` on `/bin/sh`. The hook-config suite now skips its
execution cases on non-POSIX hosts and says so out loud.

## ENFORCED IN `sdlc-gate-v2` — polyglot coverage

**This is the completed deprecation record for a breaking change.** Read it if your
repository contains any language below, or if you are upgrading from v1.

Coverage enforcement was extension-based, and v1's enforced list originally held only 13
suffixes. A repository written in an unlisted language was therefore **ungoverned without
knowing it**: a `.cpp` or `.kt` change produced `note: no product source files changed` and
the gate reported `PASSED`. That was a silent hole precisely where the tool claimed to be
strict.

v1 detected and warned about the following suffixes. `sdlc-gate-v2` now **enforces** all of
them:

`.c` `.cc` `.cpp` `.cxx` `.h` `.hpp` `.cs` `.kt` `.kts` `.swift` `.php` `.scala` `.m` `.mm`
`.dart` `.ex` `.exs` `.lua` `.pl` `.vue` `.svelte` `.scss` `.sass` `.less` `.tf`

**Current v2 behaviour.** A changed file in one of these languages is an ordinary governed
source file. If the active intent's `plan.md` does not name it, the gate **fails**, exactly
as it does for an uncovered `.py` file. No v1 `DEPRECATION`/"passes today" text remains.

**How to upgrade.** Name those files in your active intent's `plan.md`, which is what the
originally-enforced languages already required.

**Why this waited for v2.** Promoting a suffix turns a previously-green repository red
without it changing a line of its own code — a MAJOR change under the rules above. v1
provided the required warning release and named the remediation; v2 consumes that promise.
The history stays here so the break is auditable rather than silently rewritten.

### ENFORCED IN `sdlc-gate-v2` — `Accepted-for:` is required

**This is the completed second deprecation under the same policy.** Read it if your
repository has any accepted `plan.md`, or if you are upgrading from v1.

An acceptance used to be open-ended. The gate could ask whether an accepted plan *named* a
changed file, but never whether the approval had been granted *for the change in front of
it*. Because `.sdlc/active` is not reset when a change merges, a merged, signed chain kept
authorising every later edit to every file its `plan.md` listed. This was observed, not
predicted: a documentation fix passed under a chain signed for an entirely different change,
and the gate printed `SDLC CI GATE PASSED`.

`plan.md` carries `- **Accepted-for:** <base-sha>`, the commit the approval was granted
against. The workflow template supplies the real base with
`--base-sha "$(git merge-base "$base" HEAD)"` — the *merge base*, not the base branch tip,
because the base moves after a branch is cut while the approval was granted at the fork point.

**Current v2 behaviour.** All three unverifiable shapes fail closed:

- no `Accepted-for:` field → **fails**;
- `Accepted-for:` differs from `--base-sha` → **fails**, showing both values;
- the pipeline omits `--base-sha` → **fails** rather than silently downgrading the control.

A matching recorded and actual base passes.

**How to upgrade.** Add the field when a plan is accepted (`git rev-parse HEAD` at that
moment). If the base moves and the plan is re-confirmed, update it. Use the shipped workflow
template so CI passes the merge base to the gate.

**Why this waited for v2.** Every accepted artifact predating the field needed migration;
enforcing immediately would have turned green repositories red without their code changing —
a MAJOR change under the rules above. v1 warned and named the enforcement release; v2
consumes that promise. The history remains here rather than pretending the field was always
mandatory.

**What this still does not solve.** `Status: shipped` and this binding are both recorded *by
the author*. Nothing stops an author editing either one, so both are attested rather than
proven, in the same class as separation of duties. See Gap 12 in
`references/limitations.md`.

### Fork-based pull requests: the CI gate runs, the review pass does not

A pull request from a fork receives **no secrets** and a **read-only** workflow token —
GitHub enforces both regardless of the `permissions:` block a workflow requests.

What that means in practice:

- **The `sdlc-gate` job works normally.** It only reads the repository, needs no secret, and
  refuses the same violations it would on a same-repo branch. Fork contributions are governed.
- **The `sdlc-review` advisory pass self-skips.** It needs `KIRO_API_KEY`, which a fork PR
  never receives, so the guard step turns it off and says so in the log.
- **The review comment cannot be posted** even if a key were somehow present, because the
  token is read-only. That path is wrapped in `try`/`catch`, emits a `core.warning`, and
  writes the review to the job summary instead — an advisory job must never fail a build.
  The job also carries `continue-on-error: true`, so "advisory" is structurally true rather
  than a promise in a comment.
- **`pull_request_target` is never used, and must never be.** It would run with a
  write-scoped token in the base repository's context while processing an untrusted fork's
  diff, converting every prompt-injection risk in `references/threat-model.md` into
  repository compromise.

**Honest limit:** the four properties above are asserted against the shipped template by
`scripts/test_fork_safety.py`, so they cannot be edited away silently. **The live token
semantics are still unverified** — reproducing them needs a pull request from a second
GitHub account, and a user cannot fork their own repository. `fork-pr` therefore stays in
`documented_untested`: contract tested, runtime unproven.

### Not tested — do not assume
| Dimension | Status |
|---|---|
| Polyglot repos | **Untested.** Source-file detection is extension-based. |
| Fork-based contributions | **Untested.** |
| GitLab / Bitbucket | **Unsupported.** The gate logic is portable; the workflow is not. |
| Kiro Web surface | **Unsupported** — `PreToolUse` does not exist there; CI is the only control. |
| Scale | Largest exercise is a few dozen files. No evidence at thousands. |

## Deprecation process

A deprecated feature warns on every run, naming the replacement and the removal version;
appears in `CHANGELOG.md` under `Deprecated`; and is removed no sooner than the next MAJOR
and at least six months later.

## What is explicitly not promised

No SLA. No guaranteed response time for issues or security reports (best-effort — see
`SECURITY.md`). No funded maintenance commitment. No backport of fixes to versions older
than the previous major. This is a small-team tool with real tests, not a supported product;
`references/limitations.md` sets out the full picture.

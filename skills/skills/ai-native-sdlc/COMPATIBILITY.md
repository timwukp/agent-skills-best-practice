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

## ANNOUNCED DEPRECATION — more languages become enforced in `sdlc-gate-v2`

**This is the announcement required before a breaking change.** Read it if your repository
contains any language below.

Coverage enforcement is extension-based, and the enforced list originally held only 13
suffixes. A repository written in an unlisted language was therefore **ungoverned without
knowing it**: a `.cpp` or `.kt` change produced `note: no product source files changed` and the
gate reported `PASSED`. That is a silent hole precisely where the tool claims to be strict.

These suffixes are now **detected and warned about**, and will be **enforced in
`sdlc-gate-v2`**:

`.c` `.cc` `.cpp` `.cxx` `.h` `.hpp` `.cs` `.kt` `.kts` `.swift` `.php` `.scala` `.m` `.mm`
`.dart` `.ex` `.exs` `.lua` `.pl` `.vue` `.svelte` `.scss` `.sass` `.less` `.tf`

**What happens now (this version).** A changed file in one of these languages that is *not*
named in the active intent's `plan.md` produces a `DEPRECATION` note listing the files. The
build still **passes**.

**What happens in `sdlc-gate-v2`.** The same situation **fails** the gate, exactly as an
unlisted `.py` file does today.

**How to prepare.** Name those files in your active intent's `plan.md`, which is what the
enforced languages already require. The warning lists every affected path, so the remediation
is mechanical.

**Why it is not enforced immediately.** Promoting a suffix turns a previously-green repository
red without it changing a line of its own code — a MAJOR change under the rules above. The
policy requires a warning release first, and this is the project honouring its own policy
rather than repeating the separation-of-duties mistake recorded below.

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

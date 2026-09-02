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

### Verified

| Dimension | Coverage |
|---|---|
| Python | 3.12 (CI), 3.9+ expected — stdlib only, no dependencies |
| OS | Linux (`ubuntu-latest`, Amazon Linux 2023) |
| Repo shape | Single-package repo; one static single-page site; one Python feature branch |
| Forge | GitHub — Actions and branch protection |
| Surfaces | Kiro IDE and CLI (`PreToolUse`); official Kiro and KiroCrew hook runtimes |

### Not tested — do not assume

| Dimension | Status |
|---|---|
| Windows / macOS | **Untested.** The slug regex is conservative but path semantics are unverified. |
| Monorepo, multi-intent PRs | **Untested.** One PR touching several intents is unmodelled. |
| Polyglot repos | **Untested.** Source-file detection is extension-based. |
| Concurrent PRs | **Untested.** Racing on one `.sdlc/active` value is unmodelled. |
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

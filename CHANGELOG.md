# Changelog

Notable changes to the **`ai-native-sdlc` gate**. Format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/); versioning follows
[Semantic Versioning](https://semver.org/) as qualified in
`skills/skills/ai-native-sdlc/COMPATIBILITY.md`.

## Two version series in this repository — do not confuse them

| Series | Tags | Covers |
|---|---|---|
| Repository | `v0.1.0`, `v0.2.0` | the skills collection as a whole |
| Gate | `sdlc-gate-v1`, … | the `ai-native-sdlc` gate scripts and reusable workflow |

The gate is versioned separately because it is the only artifact here whose output is a
**policy decision** — it can start failing builds that passed yesterday, so it needs a
compatibility promise the rest of the collection does not.

The artifact **schema** (`.sdlc/version`) is versioned separately again, as a plain integer,
so the gate can gain features without forcing every consuming repository to migrate.

---

## [Unreleased]

### Added
- Reusable `workflow_call` gate (`.github/workflows/sdlc-gate-reusable.yml`). Consuming
  repositories reference it by ref instead of vendoring a copy that ages independently. The
  job logs the gate's commit and SHA-256 so a failure identifies which version refused.
- Release pipeline (`.github/workflows/release-attest.yml`): CycloneDX SBOM, Sigstore
  keyless signatures, SLSA build provenance, and self-verification before publishing.
- `scripts/verify_gate_integrity.sh` for consumers, pinning the expected signer to this
  repository's release workflow.
- `scripts/build_review_prompt.py` — fences the PR diff as untrusted data for the review
  job. Mitigation, not a fix; prompt injection has no general solution.
- `references/threat-model.md`, `references/limitations.md`, `COMPATIBILITY.md`,
  `SECURITY.md`.
- Cross-platform test matrix (3 OS × 5 Python) and `scripts/test_support_matrix.py`, which
  fails the build when the documented support matrix claims more than CI covers.
- `.gitattributes` pinning LF so SBOM component hashes are stable across platforms.

### Changed
- Coverage rule now resolves `.sdlc/active` and requires that intent's chain to be complete
  **and** its `plan.md` to name every changed source file.

### Fixed
- **Path traversal (security).** `.sdlc/active` was interpolated into a path, so `..`
  resolved to the repository root and `/etc` escaped it entirely. Both gates now validate
  the slug against `^[A-Za-z0-9][A-Za-z0-9._-]*$`.
- A field regex used `\s*`, which matches newlines, so an empty field captured the *next*
  line's content. Now `[ \t]*`.
- A missing `import re` made the hook raise `NameError`, which its fail-open handler turned
  into a **silent allow** — every traversal slug passed.
- `test_hook_config` was not hermetic: it passed only when the skill happened to be
  installed under the developer's real `$HOME`, and on a clean machine one of its
  assertions passed *for the wrong reason*.
- SBOM fixture hashing broke on Windows because text-mode writes translate LF to CRLF.

### Known limitations
See `references/limitations.md`. In particular: an administrator can still bypass the gate
without an organization-level ruleset, and **no gate can judge whether an eval is
meaningful**.

---

## Versioning notes for future entries

A change that can turn a previously-green repository **red** is a MAJOR, and must ship as a
warning in a MINOR release first — see `COMPATIBILITY.md` for the full rule and the
six-month support window.

Note the sharp edge: fixing a bug that made the gate **too permissive** is a MAJOR, not a
patch, because repositories that were passing incorrectly will begin to fail. Correctness of
the fix does not make it non-breaking.

**Recorded precedent:** the separation-of-duties check (`Author` / `Accepted-by`) shipped as
an immediate breaking change with no warning release, no deprecation window and no migration
script. That violated the policy above. It is recorded here rather than quietly forgotten,
and it is the reason the policy was written.

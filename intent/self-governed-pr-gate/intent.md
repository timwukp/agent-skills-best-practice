# Intent: govern this repository with the gate it ships

- **Slug:** self-governed-pr-gate
- **Author:** Kiro (AI agent)
- **Accepted-by:** Tim WU
- **Date:** 2026-09-07
- **Status:** accepted

## Problem

This repository ships a merge gate, tells adopters to make it a required status check, and does
not apply it to itself.

Verified against `main` and the live branch protection:

- **No caller workflow exists.** `.github/workflows/` holds `release-attest.yml`,
  `sdlc-gate-reusable.yml`, `sdlc-gate-tests.yml` and `validate-skills.yml`. A grep for
  `sdlc-gate-reusable` matches only the reusable workflow itself — nothing calls it, and a
  `workflow_call` workflow with no caller never runs.
- **The required checks are `gate tests green` and `validate`.** Neither is the SDLC gate. Both
  prove the skill's *tests* pass; neither asks whether the change in front of them was authorised
  by an accepted artifact chain.
- **`.sdlc/` exists but `.kiro/hooks/` does not**, so not even the advisory write-time layer is
  installed here.

The consequence is that every `SDLC CI GATE PASSED` recorded in this session came from a command
*I* ran by hand on a developer machine. Nothing in CI would have refused a pull request that
skipped the process, edited a file no plan named, or carried an approval bound to the wrong base.
The four defects this session fixed were all found by a human choosing to run the gate — not by
the repository enforcing it.

`references/limitations.md` already says the quiet part in its closing section: this is a
governance tool that asks adopters to do things it does not do itself. Items 2, 4, 6 and 8 remain
open there. This intent closes the narrower and most embarrassing one: the gate is not applied to
the gate.

## Desired outcome

A pull request to this repository cannot merge unless the SDLC gate has actually run and passed on
it. The gate that adopters are told to trust is demonstrably the same gate this repository submits
to, and the evidence is a check run on each pull request rather than a developer's terminal.

Where the control genuinely cannot be closed — an administrator bypass in a personal repository —
that remains stated rather than implied to be solved.

## Affected users / systems

- **This repository's contributors**, including the owner: after this, a source change needs an
  accepted chain naming the files it touches, enforced rather than remembered.
- `.github/workflows/` — gains one caller workflow.
- **Branch protection on `main`** — gains one required check. This is an owner action in repository
  settings, not something a merged pull request can do.
- `.kiro/hooks/` — optionally gains the write-time hook, so the advisory layer exists locally too.
- No change to the skill's gate logic, schema, templates, or `GATE_VERSION`. This is an
  application of what already ships.

## Constraints

- **The gate must not be weakened to fit this repository.** If this repository's own history
  cannot satisfy the gate, the finding is about the history, not a reason to relax the check.
- **Artifact paths must stay writable.** `intent/`, `evals/`, `.sdlc/` and `.github/` are outside
  plan coverage by design; a change that gated them would make it impossible to start a change or
  to close a chain.
- **Closeout pull requests must keep working.** The four `shipped` closeouts in this session touch
  only `intent/`. A configuration that refused them would break the very step that prevents spent
  approvals.
- **Pin the reusable workflow to a tag or SHA, not `@main`.** `COMPATIBILITY.md` says a moving ref
  means an upstream commit silently changes merge criteria. Pinning this repository to its own
  moving `main` would be that mistake with extra irony.
- **No new enforcement generation.** No `GATE_VERSION` bump, no schema change.
- **The admin bypass is out of reach here.** `enforce_admins` is currently `false`, and a personal
  repository has no tier above its owner, so even with the check required an administrator can
  merge past a red gate. Whatever this change achieves, it must not be described as unbypassable.
- Follow this skill's own lifecycle: no implementation before an accepted plan; no self-approval.

## Success criteria

1. A caller workflow exists that invokes `sdlc-gate-reusable.yml` on `pull_request`, pinned to a
   tag or full SHA rather than `@main`.
2. The gate job reports on every pull request, including one that touches no source file, so it can
   never become a check that silently never arrives.
3. A pull request whose source change is **not** named in an accepted plan is refused by the gate,
   demonstrated on a real branch rather than asserted.
4. A pull request touching only `intent/` — a closeout — passes, demonstrated the same way.
5. A test asserts the caller exists, is pinned, and is not path-filtered, so the guard cannot be
   removed or narrowed silently.
6. A mutation proves that assertion bites.
7. `COMPATIBILITY.md` and `references/limitations.md` record that this repository is now
   self-governed, and restate the administrator-bypass limit rather than dropping it.
8. `sdlc_ci_gate.py`, the schema and `GATE_VERSION` are unchanged.
9. The owner has the exact instruction for the one step only they can perform: adding the new
   check to branch protection's required list.
10. The dogfood chain for this slug is committed, with acceptance and sign-off in separate human
    commits.

## Open questions

1. **`require-active: true` or `false`?** With it true, every pull request must have
   `.sdlc/active` naming an existing intent. That is the stronger control and the honest one for a
   repository that teaches it — but it needs verifying that a closeout pull request still passes
   when the active chain is `shipped`. Design must test this, not assume it.
2. **Should the write-time hook be installed here too?** It fails open and is trivially removable,
   so it adds little enforcement; it does add fidelity to what adopters are told to install.
   Proposed: yes, because a repository that ships a hook and does not run it is the same class of
   gap as the one being closed.
3. **What pin?** Proposed the current release tag `sdlc-gate-v2.0.2` for honesty about which
   published version governs this repository, accepting that the pin must be bumped deliberately.
   The alternative is a full SHA. The owner decides.
4. **Does the gate pass on this repository's current `main` at all?** Unknown until tried under CI
   conditions. If it does not, that result is a finding to report before any protection change —
   turning on a required check that cannot pass would block every pull request.

# Limitations

Read this before adopting the gate. It is the honest positioning of what this skill is.

**This is a working tool for an individual or a small team. It is not an enterprise-grade
compliance product, and it should not be presented as one.** The distance is a category
gap, not a polish gap: three of the missing pieces cannot be closed by writing more code
here.

What is defensible: the gate really runs, it has been proven live on a real repository, it
found and fixed six substantive bugs in itself, and its test suite is mutation-verified
(27 mutations, 27 killed). Judged as a personal/small-team tool, the quality holds up.

---

## Part 1 — The twelve known gaps

| # | Gap | Status |
|---|-----|--------|
| 1 | Distribution drift | **Fixed** — reusable `workflow_call`; consumers pin a ref instead of vendoring |
| 2 | Bypassable by admins | **Partly** — needs an *org-level* ruleset; not closable in a personal repo |
| 3 | `sdlc-review` prompt injection | **Mitigated, not solved** — see the threat model |
| 4 | Zero telemetry | **Open** — no metrics are emitted; adoption and block rates are invisible |
| 5 | Stage 6 unimplemented | **Open** — the loop does not close back into a new intent automatically |
| 6 | Coverage coarseness | **Fixed** — a change must be named in the active intent's plan |
| 7 | Weak-eval hole | **Permanent limitation** — see below |
| 8 | Validation breadth | **Open** — needs diverse real repos and time, not code |
| 9 | Path traversal / env robustness | **Fixed** — strict slug validation in both gates |
| 10 | No schema versioning | **Fixed** — `.sdlc/version`; migration tooling still absent |
| 11 | Separation of duties | **Attested, not proven** — see below |

### Gap 7 — the weak-eval hole is not solvable here

The gate can verify that `evals/check_*.py` **exists and passes**. It cannot verify the
eval is any *good*. An eval asserting `"id" in html` passes while the element it names is
invisible, unreachable, or behind `display:none` — a mistake that actually happened during
this skill's development and was caught by a human reading the page, not by any gate.

A green gate therefore means "the declared checks passed", never "the change is correct".
Judging whether an eval measures the thing that matters is a human responsibility, and no
amount of automation in this repository moves it.

### Gap 11 — duties are attested, not proven

`Author` and `Accepted-by` must be present and must differ. Nothing stops one person
typing two names. This is **attestation**: the claim is committed, reviewable and
attributable, where previously there was nothing to point at. It is not cryptographic
proof of two humans. Requiring signed commits from two distinct verified identities, gated
by an org ruleset, is what proof would look like — and that needs infrastructure this
repository does not control.

### Gap 12 — `shipped` narrows the unbound-approval hole, it does not close it

A merged, signed chain used to keep authorising later changes: `.sdlc/active` is never
reset after merge, and the coverage check asked only whether an accepted chain *named*
the changed file — never whether that acceptance covered *this* change. A signature
outlived the diff it signed. Observed, not theorised: a documentation fix passed under a
chain signed for a completely different change, printing `SDLC CI GATE PASSED`.

An intent whose change has merged is now `shipped`, and a `shipped` chain refuses to
authorise work in all three copies of the gate (CI, local, hook).

**What this does not do.** `shipped` is a *marker*, not a binding. Nothing stops an
author editing the status back to `accepted` and reusing the sign-off — exactly like
separation of duties (Gap 11), it is attested rather than proven. The refusal message
now argues against doing so, which is persuasion, not enforcement.

**What would actually close it** is recording *what* the approval covered:
`Accepted-for: <base-sha>` in `plan.md`, compared against the real base at merge time,
so an approval granted for one diff cannot silently cover another. **This now exists**
and the shipped workflow template passes `--base-sha "$(git merge-base "$base" HEAD)"`,
so a plan bound to a different base is refused.

**But it is opt-in, and that is the remaining hole.** A `plan.md` with no
`Accepted-for:` line still passes — it only earns a warning naming `sdlc-gate-v2` as
the release that will enforce it. The deprecation window is deliberate: enforcing
immediately would turn every existing accepted artifact red, which is the breaking
change the duties check (Gap 11) already inflicted once. The consequence is that until
`sdlc-gate-v2`, an author who simply omits the field gets the old open-ended behaviour.
The gate says so on every run rather than passing quietly, which is the most an opt-in
control can honestly claim.

Two further limits worth naming: the write-time hook does **not** check the binding (at
write time there is no base to compare against, so putting it there would be inventing a
check rather than enforcing one), and a run given no `--base-sha` cannot verify the
binding at all — it passes and says explicitly that it did not verify, so a
misconfigured pipeline is visible instead of silently toothless.

Detection of `shipped` is per-artifact, so a half-marked chain is treated as terminal
deliberately — refusing is the safe direction.

### Gap 2 — the bypass is live-proven, not theoretical

With `enforce_admins=false`, an administrator merged a pull request whose required
`sdlc-gate` check was **red**. The gate correctly reported `failure` and
`mergeable_state=blocked`; the merge still succeeded. So: **binding for non-admins,
advisory for administrators.**

Only an **organization- or enterprise-level ruleset** whose bypass list excludes repository
admins is genuinely unbypassable — an org ruleset can be edited only by org owners, and a
repo admin may add stricter rules but can never weaken it. In a personal repository there
is no tier above the owner, so this gap cannot be closed there at all.

---

## Part 2 — Eight things an enterprise needs that this does not have

Stated plainly because the gap is a category difference, not a to-do list.

1. **Supply-chain integrity** — *partly addressed.* Releases now publish an SBOM, Sigstore
   signatures and SLSA provenance, and `verify_gate_integrity.sh` lets a consumer check
   them. This matters because the gate script is granted authority over merges, so
   tampering with it defeats the control. But GitHub's own attestations reach **SLSA Build
   Level 2** by default; Level 3 requires the build to run in a vetted reusable workflow and
   consumers to verify with `--signer-workflow`. Nobody has audited this pipeline.
2. **Tamper-evident audit** — *not addressed.* The audit trail is git history in the repo
   being governed, and the governed party can rewrite it. An auditor needs an append-only
   record held **outside** the audited party's control (GitHub audit-log streaming to WORM
   storage such as S3 Object Lock). Self-audit is not audit.
3. **Formal threat model and penetration test** — *threat model now written, pen test
   absent.* `references/threat-model.md` covers the two surfaces this skill introduces. No
   independent security testing has been performed.
4. **Centralised policy governance** — *not addressed.* Enterprises need one policy change
   to take effect fleet-wide, un-disableable by engineers. Anyone with write access can
   delete `.sdlc/` and the local control is gone.
5. **Compatibility guarantees** — *now addressed going forward.* See `COMPATIBILITY.md`.
   Note the precedent honestly: the duties check **was itself an unannounced breaking
   change** that turns previously-green repositories red.
6. **Independent verification** — *not addressed, and not self-addressable.* Every test here
   was written by the same author as the implementation. Third-party review is required by
   definition, and no badge substitutes for it.
7. **Operational commitments** — *partly addressed.* `SECURITY.md` adds a disclosure
   channel and a CVE path. There is no SLA and no funded maintenance commitment.
8. **Scale and environment evidence** — *not addressed.* Validated on one single-file static
   site and one feature. No monorepo, no polyglot repo, no concurrent PRs, no fork-based
   contributions, no Windows. See the support matrix in `COMPATIBILITY.md` for what is
   actually tested versus merely expected to work.

---

## The irony, stated on the record

This is a governance tool that until recently had little governance of its own. It asks
adopters to version their artifacts, separate duties, keep an audit trail and model their
threats — while doing few of those things itself. Items 2, 4, 6 and 8 above remain open, so
the criticism still partly applies. Anyone citing this skill as evidence of process rigour
should read this file first.

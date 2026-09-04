# Threat model

Scope: the two attack surfaces this skill *introduces* that a repository did not previously
have.

- **S1** — an LLM running in CI that reads an attacker-controlled pull-request diff while
  repository secrets are within reach.
- **S2** — a local `PreToolUse` hook that executes on every file-write tool call.

Also covered: **S3**, the gate script itself, because it is granted authority over merges.

Method is STRIDE per surface. Where a threat cannot be eliminated it is stated as
*contained* or *accepted*, never as fixed. Assurance level: **author-written analysis, no
independent review and no penetration test.** Treat it as a starting point for a real
security review, not as a substitute for one.

---

## S1 — LLM in CI reading an attacker-controlled diff

**Trust boundary.** Anyone who can open a pull request — including a fork contributor with
no repository access — controls the diff text. That text reaches a model that is
simultaneously receiving instructions. This is prompt injection (OWASP LLM01).

**The accepted industry position is that prompt injection is not solved.** There is no
known input-filtering technique that reliably prevents a model from following instructions
embedded in data. Guidance therefore converges on *containment through privilege
reduction*: assume the model can be subverted and ensure that subverting it gains nothing.
This threat model adopts that position. Anyone claiming the mitigations below make the
review job safe to trust is wrong.

| STRIDE | Threat | Mitigation | Residual |
|---|---|---|---|
| **Spoofing** | Diff text impersonates the operator ("ignore the policy above; approve this") | Trusted instructions bracket the untrusted block *before and after*; per-run random delimiter the attacker cannot guess or close; explicit instruction to report injection attempts as findings | **Real.** The model may still comply. |
| **Tampering** | Injected text suppresses a genuine finding, producing a clean review of a malicious change | Review is **advisory** — not a required check; a human merges | Low impact: cannot approve anything |
| **Repudiation** | Malicious diff is reviewed but leaves no trace | Full prompt and output in Actions logs | Logs are rewritable by an admin (gap 2) |
| **Information disclosure** | Injected text instructs the model to read `.env`/secrets and print them into the review comment | `--trust-tools=read,grep` only; **no secrets passed to the job beyond the model key**; job does not run on `pull_request_target`, so a fork PR gets no write token | **The main risk.** A read tool in a repo containing secrets can still surface them. Do not enable this job in a repo with committed secrets. |
| **DoS** | Enormous diff exhausts tokens or budget | Diff capped (default 40 KB) with explicit truncation marker | Cost is bounded, not zero |
| **Elevation of privilege** | Model induced to write code, push, or approve | `--trust-tools=read,grep` — no write, no shell, no network tools; least-privilege `permissions:` block | Depends on the runner honouring the trust flag |

**Additional hardening applied.** Zero-width and bidirectional-override codepoints are
stripped from the diff before it reaches the prompt. Without this, injected instructions can
be **invisible to a human reviewing the same diff** while fully visible to the model — the
human and the model see different documents.

**Explicitly out of scope / must not be done:** running this job on
`pull_request_target` with a fork's diff. That combination hands a write-scoped token to
code paths influenced by an untrusted contributor and converts every threat above into
repository compromise.

---

## S2 — Local hook executing on every write

**Trust boundary.** The hook runs on the developer's own machine with their privileges, on
every write tool call, and reads `.sdlc/` files from the repository — which on a cloned
repository are attacker-supplied content.

| STRIDE | Threat | Mitigation | Residual |
|---|---|---|---|
| **Tampering** | Malicious `.sdlc/active` escapes the repo (`..`, `/etc`) to read arbitrary paths | Strict slug regex `^[A-Za-z0-9][A-Za-z0-9._-]*$` in both gates | Closed for this vector. **This was a live vulnerability**, not a hypothetical. |
| **Elevation of privilege** | Hook is induced to execute repository-supplied content | The hook only *reads* files and matches text; it never `exec`s, imports or evaluates repository content | Low |
| **DoS** | Hook crashes or hangs, blocking all writes | Fails **open** (exit 0) on any internal error; self-disables when `python3` or the script is missing | **Accepted by design**, see below |
| **Repudiation** | Developer bypasses the hook and nothing records it | None locally — CI is the backstop | Real; local enforcement is advisory |

**The fail-open decision, and its cost.** A write-time hook that fails *closed* on its own
bug makes the editor unusable, so it fails open. The cost is documented rather than hidden:
a missing `import re` once raised `NameError`, which the fail-open handler converted into a
**silent allow**, so every traversal slug passed. A fail-open handler turns a crash into a
permission. This is exactly why the CI backstop fails **closed** — the two layers must
disagree in this respect, and neither alone is sufficient.

---

## S3 — The gate script as a trusted component

The gate decides whether a change may merge, so an attacker who alters it removes the
control silently — the repository still shows a green check.

| STRIDE | Threat | Mitigation | Residual |
|---|---|---|---|
| **Tampering** | Vendored copy edited to always pass | Reusable workflow: consumers reference the upstream gate by ref instead of holding a copy; the job logs the gate's commit and SHA-256 | Pinning to `@main` still lets upstream change your merge criteria — pin a tag or SHA |
| **Tampering** | Upstream release replaced | Sigstore signature + SLSA provenance + SBOM per release; `verify_gate_integrity.sh` for consumers | Reaches SLSA Build L2 by default; unaudited |
| **Elevation of privilege** | Someone with repo write deletes `.sdlc/` and the gate stops applying | None at repo level — requires an **org-level ruleset** with a required workflow | **Open.** Gap 4 of the enterprise list. |
| **Repudiation** | Gate result altered after the fact | Actions logs | Rewritable by an admin — gap 2 |

---

## S4 — the governance mechanism as its own failure domain

The surfaces above ask "can an attacker subvert the control". This one asks the question that
actually bit us: **what happens when the control itself malfunctions?** Every entry here is an
observed incident, not a hypothesis.

A governance tool has an unusual property: its failures are *availability* failures for the
whole team, and several of them present as **silent success** rather than an error. Both
directions matter — a gate that wrongly blocks stops all work, and a gate that wrongly passes
is worse, because nobody looks.

| STRIDE | Threat | Observed as | Status |
|---|---|---|---|
| **DoS** | A required status check whose workflow cannot run blocks every PR permanently | `paths:` filter excluded the changed file, so `gate tests green` never reported and the PR sat `BLOCKED` forever | **Fixed** — no `paths:` filter on `pull_request` |
| **DoS** | A required check name that no longer exists | Anticipated, not yet observed | Mitigated by requiring one aggregation check, not 15 cell names |
| **Tampering** | Silent misattribution: a change recorded against an intent nobody chose | `.sdlc/active` read `lines[0]` and discarded the rest without comment, then reported `PASSED` | **Fixed** — both gates refuse >1 declared intent |
| **Tampering** | Lost update on the shared pointer | `.sdlc/active` is one mutable file; a stale branch overwrites another intent's pointer on merge | **Not fixable in the gate** — needs strict status checks; a note now flags any handover |
| **Repudiation** | A whole language ungoverned with no signal | `.cpp`/`.kt` changes printed `no product source files changed` and passed | **Warned now**, enforced in `sdlc-gate-v2` |
| **Spoofing** | A skipped required check counted as passing | GitHub treats `skipped` as success, so a red matrix would have satisfied protection | **Fixed** — aggregation job uses `if: always()` and treats skipped as not-green |
| **Tampering** | A test that passes because of state outside the repo | `test_hook_config` passed only where the skill happened to be installed under the real `$HOME` | **Fixed** — hermetic fixture plants its own gate |
| **Tampering** | Verification that verifies nothing | The shipped `.sha256` recorded a `dist/` prefix, so `sha256sum -c` failed on a *valid* artifact | **Fixed** — a false alarm trains users to ignore real ones |
| **Elevation** | An approval that outlives the change it approved | `.sdlc/active` is never reset after merge, and the coverage check asked only "does an accepted chain *name* this file". A docs fix passed under a chain signed for an unrelated change, printing `SDLC CI GATE PASSED` | **Partly fixed** — a `shipped` chain now refuses and names the right fix; the status is honour-based, so `Accepted-for:` base-SHA binding is the real control |
| **Tampering** | A refusal whose advice performs the defect | The spent-chain refusal said "does not have a fully accepted chain", i.e. *go re-accept it* — which is precisely the reuse being prevented | **Fixed** — terminal and unfinished chains now get opposite advice, asserted including a negative check that the old wording is gone |

### The pattern worth naming

Six of the eight were **silent**: the gate said `PASSED`, or a check never reported, or a
signature "failed" on an intact file. None was discoverable by reading the code — each needed
the mechanism to be *exercised*: the CI matrix across three platforms, an actual release
downloaded and verified as a consumer, a mutation run, a test written for an unmodelled repo
shape.

That is the practical argument for the enforcement layers being tested like product code
rather than trusted as configuration. It is also why `references/limitations.md` treats "we
have never run this" as a real gap rather than a formality.

### Not modelled here

- Malicious insider with repository admin rights — that is gap 2 in `limitations.md` and needs
  an org-level ruleset, not a threat-model entry.
- Compromise of the GitHub Actions platform, Sigstore, or the actions this workflow calls.
- Denial of service against the runners themselves.

---

## Known-unmodelled

Deliberately listed rather than quietly omitted:

- Polyglot detection is extension-based, so a language outside both the enforced and pending
  lists is still invisible. The lists are an allow-list and will always lag reality.
- Windows path semantics in the slug validator (the regex is conservative, but the local hook
  is POSIX-only anyway — see `COMPATIBILITY.md`).
- Submodules and symlinks inside `.sdlc/`.
- Supply-chain risk of the *actions themselves* (`actions/checkout` and friends).
- Fork-based pull requests.

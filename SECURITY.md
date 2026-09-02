# Security Policy

## Reporting a vulnerability

**Do not open a public issue for a security problem.**

Use GitHub Private Vulnerability Reporting: go to the **Security** tab of this repository
and choose **Report a vulnerability**. That opens a private draft advisory visible only to
you and the maintainers. If it is unavailable, open a normal issue containing only
"security report, please provide a private channel" — with no detail — and wait for a reply.

Please include: what an attacker can achieve, the affected file or skill, reproduction
steps, and the version or commit you tested.

### What to expect

This is a **best-effort, unfunded** project. There is **no SLA**.

| Stage | Target |
|---|---|
| Acknowledgement | within 7 days |
| Initial assessment | within 14 days |
| Fix or documented mitigation | depends on severity and maintainer availability |

If you get no acknowledgement in 14 days, treat the report as unread and escalate publicly
after a further 30 days. Disclosing an unfixed issue after a good-faith wait is legitimate
and will not be treated as hostile.

### CVE handling

For a confirmed vulnerability in this repository's own code, a CVE will be requested through
GitHub (a CNA) from the draft advisory. A CVE will be requested even for low severity,
because otherwise a third party may assign one with an inaccurate description that cannot
easily be corrected.

## Scope

### In scope

- The `ai-native-sdlc` gate scripts (`sdlc_gate.py`, `sdlc_ci_gate.py`,
  `sdlc_pretooluse_hook.py`) — especially anything that lets a repository-supplied file
  escape the repository, or lets a change merge that the gate should have refused.
- The prompt-assembly script (`build_review_prompt.py`).
- The release and reusable workflows under `.github/workflows/`.
- Any skill in this repository that executes code or reads outside its working directory.

### Known and already documented — please do not report as new

These are recorded in `skills/skills/ai-native-sdlc/references/limitations.md` and
`references/threat-model.md`. A report that simply restates one of them adds nothing; a
report that shows one is **worse than documented**, or that a documented mitigation does not
actually work, is very welcome.

- **Prompt injection via the PR diff in the review job.** Known, mitigated, not solved.
  Prompt injection has no general solution; the containment is least privilege
  (`--trust-tools=read,grep`), the job being advisory rather than required, and human merge.
- **Administrators bypassing the gate.** Known and live-proven. `enforce_admins=false`
  lets an admin merge a red required check. Only an org-level ruleset fixes it.
- **The local hook fails open.** Deliberate: a write-time hook that fails closed on its own
  bug makes the editor unusable. The CI gate fails closed as the backstop.
- **The gate cannot judge whether an eval is meaningful.** A permanent limitation.

### Out of scope

- Vulnerabilities in GitHub Actions, Python, or third-party actions — report upstream.
- The absence of enterprise controls that are already documented as absent (tamper-evident
  audit, centralised policy, independent verification). These are known gaps, not findings.
- Social engineering, and any testing against infrastructure you do not own.

## Verifying what you downloaded

The gate script is granted authority over whether a pull request may merge, so verify it
before trusting it:

```bash
skills/skills/ai-native-sdlc/scripts/verify_gate_integrity.sh <artifact.tar.gz>
```

This checks the SHA-256, the Sigstore signature **and that the signer was this repository's
release workflow**, and the SLSA build provenance. Verification proves origin and integrity
only — not that the gate is correct or sufficient for your compliance regime.

## Assurance status — stated plainly

No independent security audit. No penetration test. The threat model was written by the same
author as the implementation, which is the weakest form of assurance. Read
`skills/skills/ai-native-sdlc/references/limitations.md` before relying on any of this for
compliance purposes.

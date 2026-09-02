# REVIEW.md

Every PR gets the same severity-ranked passes. Findings inform the human approver;
they do not approve or block on their own. Branch protection requires a human code owner.

## Passes (in order)
1. **Bugs** — correctness, edge cases, error handling.
2. **Security** — injection, authz, secrets in diff, unsafe deps.
3. **Compliance** — does the diff match `spec.md` and `plan.md`? Design principles upheld?

## Severity
- **Important** — must be addressed before merge (correctness, security, spec deviation).
- **Nit** — style/preference. Cap: <= N nits per PR; beyond that, summarize.

## Do not report
Generated files, vendored code, formatting the linter already owns.

## Feedback into CLAUDE.md
A mistake flagged twice becomes a correction in `CLAUDE.md`.

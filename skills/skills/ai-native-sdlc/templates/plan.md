# Plan: <short title>

- **Spec:** ./spec.md
- **Author:** <who wrote this>
- **Accepted-by:** <who accepted it — MUST NOT be the Author>
- **Status:** draft | accepted | shipped

## Files changed (in order of work)

Every source file this change touches MUST be listed here. The CI gate refuses a
diff that touches a file this plan does not name.

1. `path/to/file` — what changes and why
2. ...

## Work order
Step-by-step sequence an unfamiliar engineer could follow.

## Tests that prove it
Which tests are added/changed and what each asserts. Name the verification target
(e.g. `make test`) and the quantifiable pass condition.

## Risks
Riskiest step, what could break, rejected alternatives.

---
Gate: engineer (tech lead for higher-risk) accepts BEFORE any file is edited.
If implementation departs from this plan, update this file in the same commit.

# Plan: <short title>

- **Spec:** ./spec.md
- **Author:** <who wrote this>
- **Accepted-by:** <who accepted it — MUST NOT be the Author>
- **Accepted-for:** <base commit SHA this was accepted against — `git rev-parse HEAD`>
- **Status:** draft | accepted | shipped

`Accepted-for:` records *what* the approval covered. Without it an acceptance is
open-ended: it keeps authorising later, unrelated changes to every file named below,
because the gate can only ask whether an accepted plan names the file, not whether the
approval was granted for the change in front of it. Fill it in at the moment the plan
is accepted. If the base moves and the plan is re-confirmed, update it.

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

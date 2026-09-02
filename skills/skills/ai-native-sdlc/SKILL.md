---
name: ai-native-sdlc
description: Drive a change through an AI-native software development lifecycle as a loop of committed, machine-readable artifacts — intent.md, spec.md, plan.md, diff plus tests, PR review, control bands — and make the stage order enforceable with a PreToolUse hook and a CI gate instead of relying on discipline. Use when the user wants to start a feature, capture intent, write a spec, plan before coding, run a change from idea to production, onboard an existing repo to a governed process, add stage gates to CI, or turn a production incident back into backlog work. Trigger phrases include "start a feature", "capture intent", "write a spec", "plan before coding", "run this through the SDLC", "add a stage gate", "enforce our process", "close the loop on this incident".
license: MIT
---

# AI-Native SDLC

Take a change from idea to production as a **loop around the agent**, not a linear human
relay. Each stage **ends by committing one machine-readable artifact**, and the next stage
**begins by reading it**. The chain of commits becomes the audit trail: who asked for what,
what the agent produced, and who approved it.

```
Plan     ->  intent.md
Design   ->  spec.md
Build    ->  plan.md  ->  diff + tests
Test     ->  a verification target + evals/
Deploy   ->  PR + REVIEW.md findings  ->  gated release
Maintain ->  bands.yaml breach  ->  writes a new intent.md   (loop closes)
```

## Instructions

1. **Identify the stage.** Read `.sdlc/active` for the current slug; artifacts live in
   `intent/<slug>/`. If there is no active slug, the work starts at Stage 1.
2. **Read the input artifact before producing the output artifact.** Never write `spec.md`
   without reading an accepted `intent.md`, and never edit source before `plan.md` is accepted.
3. **Run the gate rather than judging by eye:**
   ```bash
   python3 scripts/sdlc_gate.py intent/<slug> <design|build|test|deploy>
   # exit 0 = gate open, exit 2 = gate closed (reason on stderr)
   ```
4. **Write the verification target BEFORE the implementation**, run it, and confirm it
   FAILS. A test that has only ever been seen green is not evidence.
5. **Implement, then re-run it until green.** If the implementation departs from `plan.md`,
   update `plan.md` in the same commit.
6. **Commit the artifact at the end of each stage.** The commit is what advances the loop.
7. **Never approve your own work.** Acceptance of `intent.md` / sign-off of `spec.md` is a
   human decision; do not flip a Status field on an artifact you authored.

## Stage detail

### Stage 1 — Plan → `intent/<slug>/intent.md`
Interview the originator until the idea is concrete: problem, desired outcome, affected
users and systems, constraints, success criteria, open questions. Copy
`templates/intent.md`. **Gate:** the product owner sets `Status: accepted`.

### Stage 2 — Design → `intent/<slug>/spec.md`
Read the accepted `intent.md`. Produce requirements and design in one pass, constrained by
the organisation's standards. Flag concerns and name their owner; work flagged concerns
first. Copy `templates/spec.md`. **Gate:** owner sets `Status: signed-off`.

### Stage 3 — Build → `intent/<slug>/plan.md`, then the diff
Read the codebase and change **nothing** while planning. The plan names the files that
change, the order of work, the risks, and the tests that prove it — detailed enough that an
engineer who never saw the conversation could implement it. Record approaches you rejected
and why, so a later session does not re-walk them. Copy `templates/plan.md`.
**Gate:** `Status: accepted` before any file is edited.

### Stage 4 — Test
**Verification target:** one command that exits non-zero on failure. The session runs and
fixes against it *before* a human sees the work. For a bug fix, commit the failing test
first, then make it pass without editing the test.
**Evals:** keep `evals/`; run them in CI on any change to the agent's own configuration
(instructions, skills, hooks) and on a schedule. Every production incident becomes a
permanent eval case.

### Stage 5 — Deploy
`REVIEW.md` (copy `templates/REVIEW.md`) defines identical severity-ranked passes for every
PR: bugs, security, then compliance against `spec.md` and `plan.md`. Define Important vs
Nit and cap nit volume. **A human code owner still merges** — the agent that wrote the code
must not be the thing that passes it. The agent may act up to the production gate and
cannot pass it; everything it produces becomes a PR.

### Stage 6 — Maintain → `bands.yaml` → a new `intent.md`
Runs headless. A **deterministic** script watches a metric and invokes the agent on a
control-band breach — the model is never in the detection path. Tier by deviation: 1σ log,
2σ diagnose read-only, 3σ act only by opening a PR or running a pre-approved runbook. The
diagnosis is written as a new `intent.md`, which re-enters Stage 1. Copy
`templates/bands.yaml`.

## Making it enforceable

A skill is an **advisory** control: it makes the agent likely to follow the process but
forces nothing. Anything that must always hold needs one of the stronger layers.

| Strength | Mechanism | Bypassable |
|---|---|---|
| Advisory | this skill | yes, by not consulting it |
| Deterministic | `templates/kiro-hooks/sdlc-gate.json` (write time, fails **open**) | yes, by removing it |
| Merge gate | `templates/github-workflows/sdlc-gate.yml` (fails **closed**) | only by an admin unsetting the required check |

Install both into a repo:

```bash
SKILL=<this skill's directory>
mkdir -p .kiro/hooks .sdlc/scripts .github/workflows
cp "$SKILL"/templates/kiro-hooks/sdlc-gate.json        .kiro/hooks/
cp "$SKILL"/scripts/sdlc_pretooluse_hook.py            .sdlc/scripts/
cp "$SKILL"/scripts/sdlc_gate.py                       .sdlc/scripts/
cp "$SKILL"/scripts/sdlc_ci_gate.py                    .sdlc/scripts/
cp "$SKILL"/templates/github-workflows/sdlc-gate.yml   .github/workflows/
echo "<slug>" > .sdlc/active
```

**A green-or-red check is not a gate.** Until `sdlc-gate` is marked *required* in branch
protection, a red check can still be merged. See `references/enforcement.md` for the
runtime differences that silently disable a hook — the event-name casing, the exit-code
contract, and why an infrastructure failure must exit 0 rather than block every write.

## Guidelines

- **A stage may not advance until its gate passes and its artifact is committed.** If the
  prior artifact is missing, stop and produce it — do not proceed and backfill.
- **Every source file the change touches must be named in `plan.md`.** The CI gate refuses a
  diff that touches a file the active plan does not mention. This is what ties a change to
  the intent that authorised it; without it, one historical acceptance would launder every
  later change.
- **`Author` and `Accepted-by` must differ.** Both fields are required on any artifact
  claiming approval, and the gate refuses them being the same person. This is an attested,
  committed, blameable claim — not cryptographic proof, but not an honour-system sentence
  either.
- **`.sdlc/active` must be a plain directory name.** A slug containing `/`, `\` or `..` is
  refused: `intent/..` resolves back to the repo root and an absolute slug escapes the repo
  entirely. Both were real path traversals.
- **`.sdlc/version` declares the artifact schema.** A gate older than the repo refuses
  outright rather than misreading newer artifacts.
- **Do not write the eval to match the code.** Assert the property the requirement actually
  demands. An eval checking "the identifier exists" when the requirement is "the element is
  reachable" passes while the work is wrong.
- **Prove a test can fail.** Mutate the implementation and confirm the suite goes red
  (`scripts/mutation_proof.py` does this for this skill's own gates — 27 mutations, all
  killed). A surviving mutation is an untested behaviour, not a pass. Beware the subtler
  case: a test that blocks for the *wrong reason* still looks green.
- **Do not self-approve.** Never set `accepted` or `signed-off` on an artifact you wrote.
- **Brownfield:** name one source of truth per artifact, then start the loop at the *first*
  change. Do not retrofit artifacts for past work.
- **Do not gate the artifacts themselves.** `intent/`, `evals/`, `.sdlc/` and `.github/`
  must stay writable or a change can never be started.
- Neither gate can judge whether an eval is any *good*. That stays a human review
  responsibility; record known traps in `REVIEW.md` for the next reviewer.

## Examples

**User says:** "Let's start work on rate limiting for the upload endpoint."

Create `intent/upload-rate-limit/intent.md` from the template, interview until the problem,
constraints and success criteria are concrete, then stop and ask the owner to accept it.
Do not write a spec or any code yet.

**User says:** "The spec is signed off, go build it."

Read `spec.md`, produce `plan.md` naming the files, order, risks and proving tests, and
present it for acceptance. Only after acceptance write the verification target, watch it
fail, then implement until it passes.

**User says:** "Add stage gates to this repo so nobody can skip the process."

Install the hook and the CI workflow, vendor the gate scripts into `.sdlc/scripts/`, then
tell the user the remaining step only they can do: mark `sdlc-gate` as a required status
check in branch protection.

## Files

```
ai-native-sdlc/
  SKILL.md
  COMPATIBILITY.md             versioning promise, breaking-change rules, support matrix
  evals/                       task evals + trigger evals
  scripts/                     sdlc_gate.py, the hook, the CI gate, their tests, mutation_proof.py
                               make_sbom.py, build_review_prompt.py, verify_gate_integrity.sh
  templates/                   intent/spec/plan/REVIEW/bands + the hook config + the workflow
  references/enforcement.md    how to make it binding; runtime traps; what neither gate catches
  references/playbook-mapping.md   stage -> artifact -> enforcement mapping
  references/limitations.md    READ FIRST: the eleven known gaps and the eight things an
                               enterprise needs that this does not have
  references/threat-model.md   STRIDE for the two surfaces this skill introduces
```

Before adopting this as a control rather than a habit, read `references/limitations.md`.
It states plainly what a green gate does and does not mean — in particular that the gate
cannot judge whether an eval is meaningful, and that an administrator can still bypass it.

# Spec: govern this repository with the gate it ships

- **Intent:** ./intent.md
- **Author:** Kiro (AI agent)
- **Accepted-by:** pending — owner sign-off
- **Status:** draft

## Open questions from the intent, now closed — by measurement, not by reasoning

Every answer below was obtained by running the shipped gate under CI-equivalent conditions
(`--repo . --changed-files-from <three-dot diff> --base-sha <merge base>`) in throwaway worktrees.

**Q4 — does the gate pass on this repository today?** **Yes**, on all three shapes of pull request
this repository actually produces:

| Pull request shape | Changed files | Result |
|---|---|---|
| Stage 1 PR — `intent/` + `.sdlc/active` (this branch) | 2 | **PASSED** |
| Closeout PR — `intent/` only, active chain `shipped` | 3 | **PASSED** |
| Source-touching PR — the merged #64 | 10 | **PASSED** |

So turning the check on does not block the repository's own workflow. That was the risk that could
have invalidated this change, and it is retired.

**Q1 — `require-active: true` or `false`?** **True.** All three shapes above pass with
`--require-active` as well as without, so the stronger setting costs nothing here. A repository
that teaches the control should run it at full strength.

**Q3 — what pin?** **`sdlc-gate-v2.0.2`**, the current published release. It states which released
version governs this repository, and `COMPATIBILITY.md` already forbids pinning a compliance
control to a moving ref — pinning this repository to its own `main` would be that exact mistake.
Cost accepted: the pin must be bumped deliberately when a new gate release lands, which is the
point rather than a drawback.

**Q2 — install the write-time hook here too?** **Yes.** It fails open and is removable, so it adds
little enforcement; it adds fidelity, because a repository that ships a hook and does not run it is
the same class of gap being closed. It is a separate, smaller requirement below so it can be struck
at sign-off without affecting the merge gate.

### The negative control, also measured

A source file that no accepted plan names was edited on a branch off `main` and the gate was run:

```
exit=1
SDLC CI GATE FAILED (1 problem(s)):
  - these changed source files are not named in intent/dynamic-mutation-count/plan.md, so the
    plan does not describe the change being made:
    skills/skills/ai-native-sdlc/scripts/make_sbom.py
```

The control refuses unauthorised source changes for the right reason. Requirement 4 below turns
this from a one-off demonstration into retained evidence.

## Requirements

1. **A caller workflow (Intent SC1, SC2).**
   Add `.github/workflows/sdlc-gate.yml` calling
   `timwukp/agent-skills-best-practice/.github/workflows/sdlc-gate-reusable.yml@sdlc-gate-v2.0.2`
   with `require-active: true`, triggered on `pull_request` with **no `branches` and no `paths`
   filter**. The job id must be stable, because the job id is the check name branch protection
   requires.

2. **No path or branch filter, ever (Intent SC2).**
   A required check whose workflow is filtered never reports on a pull request that touches other
   files, and GitHub then blocks that pull request forever waiting for a check that cannot arrive.
   This repository has already been bitten by exactly that (recorded in `sdlc-gate-tests.yml`), so
   the caller must carry the same warning comment and a test must enforce the absence.

3. **Evals must not break the job (Intent SC2).**
   The reusable workflow runs `evals/check_*.py` when `run-evals` is true. Design must establish
   whether this repository's `evals/` pass in that context and set the input accordingly, rather
   than discovering it when the check is already required.

4. **Retained proof that the gate bites (Intent SC3, SC4).**
   Extend `scripts/test_required_checks.py` — which already owns the "a required check must be able
   to report" contract — to assert that the caller exists, is pinned to a tag or SHA rather than
   `@main`, carries no `paths`/`branches` filter, and sets `require-active: true`.

5. **Mutation proof (Intent SC6).**
   Add mutations that (a) repin the caller to `@main` and (b) add a `paths` filter to it, each
   killed by the suite from requirement 4. The harness must report `0 survived, 0 broken`.

6. **The write-time layer, separably (Intent constraints; strikable).**
   Install `templates/kiro-hooks/sdlc-gate.json` into `.kiro/hooks/` and the hook script into
   `.sdlc/scripts/`, so this repository runs the advisory layer it ships. **Strike this requirement
   at sign-off if unwanted**; the merge gate does not depend on it.

7. **Documentation of what is and is not achieved (Intent SC7).**
   `COMPATIBILITY.md` records that this repository is now governed by its own gate, pinned to a
   named release. `references/limitations.md` records the same and **keeps** the administrator
   bypass: `enforce_admins` is `false` and a personal repository has no tier above its owner, so an
   administrator can still merge past a red gate. The closing "irony" section must be updated to
   say which item this closed and which remain open, not deleted.

8. **No enforcement-generation change (Intent SC8).**
   `scripts/sdlc_ci_gate.py`, the hook script, the schema, the templates and `GATE_VERSION` are
   untouched. This change only *applies* what already ships.

9. **The owner's one step, written out (Intent SC9).**
   The pull request description must contain the exact instruction to add the new check to branch
   protection's required list, and state plainly that until that is done the check is advisory and
   this change has achieved nothing enforceable.

10. **Dogfood chain (Intent SC10).**
    `.sdlc/active` names `self-governed-pr-gate`, the chain stays committed, and no artifact this
    agent authored is set to `accepted`/`signed-off` by the agent.

## Non-functional requirements

- **Least privilege.** The caller grants `contents: read` only; the gate needs no write and no
  secret, so it must work on a fork pull request.
- **No new dependency.** The caller is YAML; the assertions are stdlib Python.
- **Fail closed, loudly.** A refusal must name the file and the artifact that failed to authorise
  it — already true of the gate; the caller must not swallow its output.
- **Test robustness.** Assertions must target the executed `uses:` line and the trigger block, not
  a comment mentioning them.

## Design

### 1. The caller

```yaml
name: SDLC Gate
on:
  pull_request:
    # DO NOT add a branches or paths filter. This is a REQUIRED check; a filtered workflow
    # simply never reports on a PR that touches other files, and GitHub blocks that PR
    # forever waiting for a check that can never arrive.
jobs:
  sdlc-gate:
    uses: timwukp/agent-skills-best-practice/.github/workflows/sdlc-gate-reusable.yml@sdlc-gate-v2.0.2
    with:
      require-active: true
```

The job id `sdlc-gate` is the check name the owner adds to branch protection. It is chosen to match
the name the skill's own documentation uses, so an adopter reading either finds the same string.

A repository calling its own reusable workflow by full `owner/repo@ref` rather than a local path is
deliberate: it exercises the *consumer* path, which is the path adopters use and the one that was
broken until [#60](https://github.com/timwukp/agent-skills-best-practice/pull/60). A local
`./.github/workflows/...` reference would test a path no adopter takes.

### 2. Where the assertions live

`test_required_checks.py` already asserts that this repository's required checks can report, and
holds the mutations for the `branches` filter that caused a real permanent block. The caller's
contract belongs beside them, so a future reader sees every "can this check actually report"
assertion in one file.

### 3. Sequencing, and the one irreducible gap

The caller can merge before the check is required — it simply runs and reports without blocking.
That ordering is deliberate: it produces several real pull requests' worth of evidence that the
check passes before it is given the power to block. The owner then flips it to required.

Between merge and that flip, the control is advisory. This is stated in requirement 9 rather than
hidden, because a reader who assumes otherwise has been misled about when the repository actually
became governed.

### 4. Rejected alternatives

- **Vendor the gate script into `.sdlc/scripts/` and call it directly — rejected.** It would test a
  path adopters are told not to take, and reintroduce the per-repository drift the reusable workflow
  exists to prevent.
- **Pin to `@main` — rejected.** `COMPATIBILITY.md` forbids it for a compliance control; an upstream
  commit would silently change this repository's merge criteria.
- **Use a local `./.github/workflows/` reference — rejected.** See design 1.
- **Add the required check in the same change — impossible.** Branch protection is a settings
  action; a merged pull request cannot grant itself the power to have blocked itself.
- **Set `require-active: false` to be safe — rejected.** Measurement shows `true` passes on all
  three pull request shapes, so the weaker setting buys nothing and would understate the control.
- **Weaken the gate if this repository's history fails it — rejected**, and moot: it passes.

## Flagged concerns

| Concern | Policy owner | Resolution |
|---|---|---|
| A required check could block every PR | Owner | Q4 measured: all three PR shapes pass, with `require-active` both ways. Caller merges before being required, producing live evidence first. |
| A filtered or repinned caller could silently stop governing | Skill maintainer | Requirements 4 and 5: assertions plus two mutations. |
| `evals/` failing could break the gate job | Skill maintainer | Requirement 3: establish it in design, not after the check is required. |
| The repository could be described as unbypassable | Owner | Requirement 7 keeps the administrator-bypass statement; `enforce_admins` is `false` and cannot be fixed in a personal repository. |
| The pin will go stale | Skill maintainer | Accepted deliberately: a deliberate bump is the property being bought. |

## Out of scope

- Changing branch protection (owner settings action).
- Changing `sdlc_ci_gate.py`, the hook script, the schema, the templates, or `GATE_VERSION`.
- Closing the administrator bypass — impossible in a personal repository.
- An organisation ruleset, telemetry, or any of the six roadmap workstreams.
- Raising the 36/80 readiness score. Applying an existing control to one repository is not the
  fleet-wide policy plane that score is waiting on.

---
Gate: owner signs off; flagged concerns worked first. Applied org skills/versions recorded:
`ai-native-sdlc` at repository `main` commit 52d365365aedd150fbdd7aa980394379c030c8ef.

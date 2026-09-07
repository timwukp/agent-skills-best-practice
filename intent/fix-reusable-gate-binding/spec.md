# Spec: the reusable gate must verify the binding it demands

- **Intent:** ./intent.md
- **Author:** Kiro (AI agent)
- **Accepted-by:** Tim WU
- **Status:** signed-off

## Open questions from the intent, now closed

**Q1 — is any consumer currently blocked?** No caller is discoverable. A GitHub code search
for `sdlc-gate-reusable.yml` returns only files inside this repository: `CHANGELOG.md`,
`COMPATIBILITY.md`, `test_fork_safety.py`, and the workflow itself. **Honest limit:** that
search indexes public repositories only, so a private consumer would not appear. Treat the
answer as "none known", not "none exist". Consequence for release: a patch tag is **not
required by evidence**, so it is left to the owner's normal release decision and is out of
scope here.

**Q2 — should the workflow accept a caller-supplied base SHA?** No. The workflow computes the
merge base itself and takes no new input. An input a caller can set is an input a caller can
set wrongly, which reintroduces exactly the hole being closed — and the gate cannot tell a
wrong value from a right one.

**Q3 — is a moving-tag update in scope?** No, and investigating it surfaced a **second
defect on the same surface**, recorded as a flagged scope decision below.

## The second defect found while closing Q3

`COMPATIBILITY.md` tells consumers to pin the recommended way:

```yaml
uses: timwukp/agent-skills-best-practice/.github/workflows/sdlc-gate-reusable.yml@v1
```

The tags that actually exist are `sdlc-gate-v1`, `sdlc-gate-v2`, `sdlc-gate-v2.0.1`,
`sdlc-gate-v2.0.2`, `v0.1.0`, `v0.2.0`. **There is no `v1` ref**, and no `vN` moving tag of
any kind, though the versioning table claims one. A consumer following the recommendation
does not get a red gate — they get a workflow that cannot be resolved at all.

So the recommended integration path is broken twice: the pin does not resolve, and if it did,
the gate would refuse every compliant plan. Fixing only the second leaves the documented
entry point still unusable.

## Requirements

1. **Compute and pass the merge base (Intent SC1).**
   `.github/workflows/sdlc-gate-reusable.yml` must resolve the pull request's merge base
   against `github.base_ref` and pass it to the gate as `--base-sha`.

2. **Identical mechanism to the vendored template (Intent constraints).**
   Use `git merge-base "origin/<base_ref>" HEAD`, not the base branch tip, matching
   `templates/github-workflows/sdlc-gate.yml`. The two shipped paths must not be able to
   reach different verdicts on the same pull request.

3. **Fail closed on an unresolvable base (Intent SC4).**
   When `git merge-base` produces nothing, the value passed must stay empty so the gate's
   existing "binding was NOT verified" refusal fires. No substitution of the base tip, the
   base ref, or `HEAD` — that substitution is already forbidden inside the gate by an existing
   mutation, and the pipeline must not perform it either.

4. **Gate runtime untouched (Intent SC7).**
   `scripts/sdlc_ci_gate.py` must remain byte-identical to `c5ce8a2`. `GATE_VERSION` stays
   `2`, `SUPPORTED_SCHEMA` stays `1`. The fix is in the pipeline, never in the check.

5. **Contract test for the reusable path (Intent SC5).**
   Extend `scripts/test_unbound_approval.py` so it asserts, against the shipped reusable
   workflow, that it: invokes the gate with `--base-sha`; derives that value from
   `git merge-base`; references `github.base_ref`; and does **not** pass the base tip in place
   of the merge base. The suite must fail if any of those is absent, and must not be
   satisfiable by a comment mentioning the flag.

6. **Mutation proof for the reusable path (Intent SC6).**
   Add at least two mutations on `.github/workflows/sdlc-gate-reusable.yml`: one removing the
   `--base-sha` argument, one replacing `git merge-base` with the base tip. Both must be
   killed by `test_unbound_approval.py`. The full harness must report 0 survived and 0 broken.

7. **FLAGGED SCOPE ADDITION — correct the pin guidance.**
   `COMPATIBILITY.md` must stop recommending a ref that does not exist. Its pin examples must
   use the tag convention actually in use (`sdlc-gate-vN` / `sdlc-gate-vMAJOR.MINOR.PATCH`),
   and the versioning table must not claim a `vN` moving tag unless one exists. A test must
   assert that the documented pin examples use the real convention.
   **This is separable.** If the owner prefers, strike this requirement and requirement 10's
   corresponding test at sign-off; the fix then ships as its own intent
   (`fix-consumer-pin-guidance`) and the recommended path stays unusable until that lands.
   Recommendation: keep it here, because shipping a working gate behind an unresolvable pin
   fixes nothing a consumer can observe.

8. **Record the incomplete v2 rollout (Intent SC8).**
   `COMPATIBILITY.md` must state that the v2 `Accepted-for` enforcement reached the vendored
   template but not the reusable workflow, in the same register as the existing note that the
   duties check was itself an unannounced breaking change. No retroactive rewriting.

9. **No new enforcement generation (Intent constraints).**
   No `GATE_VERSION` bump, no schema change, no deprecation cycle. This restores intended v2
   behaviour on a missed path. It cannot turn a passing consumer red: a consumer with no
   binding is unaffected, and a consumer with a binding is currently failing.

10. **Evidence of the before/after difference (Intent SC2, SC3).**
    Implementation must record, on a tree whose `plan.md` is `accepted` with a matching
    `Accepted-for`: the pre-fix argument set exiting 1, the post-fix argument set exiting 0,
    and a deliberately mismatched binding still exiting 1. The third is what distinguishes
    verifying from merely supplying.

11. **Dogfood chain (Intent SC9).**
    Artifacts for `fix-reusable-gate-binding` stay committed, `.sdlc/active` names this slug,
    and no artifact this agent authored is set to `accepted` or `signed-off` by the agent.

## Non-functional requirements

- **Security:** the gate job keeps `permissions: contents: read`, needs no secret, and stays
  usable on fork pull requests. `pull_request_target` must not appear.
- **Portability:** shell and stdlib only. No new action, no new dependency.
- **Determinism:** no network call beyond the existing `git fetch`, and no reliance on a
  runner-local default branch name.
- **Test robustness:** assertions read the shipped workflow as data and target the executed
  step, so a comment or a doc sentence cannot satisfy them.
- **Auditability:** the before/after exit codes are recorded in the implementation commit
  message, not merely asserted in prose.

## Design

### 1. The change to the reusable workflow

The workflow already resolves the caller's checkout with `fetch-depth: 0` and already
references `github.base_ref` when listing changed files. So the merge base is computable in
the step that already exists; add its export there and consume it in the gate step:

- in the "List files changed in this PR" step, after writing `changed-files.txt`, export
  `base_sha` from `git merge-base "$base" HEAD` into `$GITHUB_ENV`, tolerating failure so the
  value is empty rather than the step aborting;
- in the "Validate the SDLC artifact chain" step, append `--base-sha "${base_sha:-}"` to the
  argument array it builds.

Keeping `require-active` as the only conditional argument preserves the existing input
contract. Nothing is added to `workflow_call.inputs`.

Empty-on-failure is deliberate and is requirement 3's mechanism: the gate already refuses an
empty base with a message naming the unverified binding, so the failure mode is a legible
refusal rather than a false pass.

### 2. Where the assertions live

`test_unbound_approval.py` owns the binding contract — it holds the existing mutation for the
template's `--base-sha` and documents the unbound-approval defect. The reusable path belongs
in the same suite, so both shipped surfaces are asserted side by side and a future reader
cannot conclude that only the template needs the flag.

The pin-guidance assertion (requirement 7) belongs in `test_support_matrix.py`, which already
exists to make documentation drift a build failure and already reads `COMPATIBILITY.md`.

### 3. Why the gate is not changed

The gate behaved correctly throughout: it demanded a binding it was told was mandatory, could
not verify it, and refused. Relaxing that would convert a fail-closed control into an
advisory one and delete the reason v2 exists. The defect is that one of two shipped pipelines
never supplied the input.

### 4. Rejected alternatives

- **Let the gate default a missing base to the current merge base — rejected.** That is the
  precise substitution an existing mutation forbids, and it makes the binding unfalsifiable.
- **Add a `base-sha` workflow input — rejected.** See Q2: a caller-settable value reopens the
  hole and the gate cannot detect a wrong one.
- **Use the base branch tip — rejected.** The base moves after a branch is cut; the approval
  was granted against the fork point. The template's comment already records this reasoning.
- **Vendor the script and drop the reusable workflow — rejected.** Per-repo drift is the
  problem the reusable workflow was introduced to solve.
- **Fix the workflow and leave the `@v1` pin guidance wrong — rejected as the default**, but
  offered as requirement 7's opt-out so the owner decides rather than the agent.
- **Bundle the self-governance caller for this repository — rejected.** It is separate work
  with its own risk (it changes this repository's own merge criteria) and needs its own
  intent; it merely depends on this fix.

## Flagged concerns

| Concern | Policy owner | Resolution |
|---|---|---|
| Fixing the pipeline could be mistaken for loosening the gate | Skill maintainer | Requirement 4 pins the gate byte-identical; the mismatched-binding case in requirement 10 proves refusal still works. |
| An empty base could silently pass on some runner | Skill maintainer | Requirement 3 plus a mutation; the gate's existing empty-base refusal is the backstop. |
| Scope addition could grow into a documentation rewrite | Product owner | Requirement 7 is bounded to the pin examples and the moving-tag claim, and is strikable at sign-off. |
| A private consumer may be blocked today and invisible to us | Product owner | Q1 states the search's limit; the release decision stays with the owner rather than being asserted as unnecessary. |

## Out of scope

- Creating or moving any tag, or cutting a release.
- Changing `sdlc_ci_gate.py`, the hook, the artifact schema, or `GATE_VERSION`.
- Adding a caller workflow so this repository's own pull requests are gate-governed.
- Changing `templates/github-workflows/sdlc-gate.yml`, which already behaves correctly.
- Fixing the plan template's `git rev-parse HEAD` advice, still owned by
  `fix-plan-binding-instruction`.
- Raising the enterprise readiness score.

---
Gate: owner signs off; flagged concerns worked first. Applied org skills/versions recorded:
`ai-native-sdlc` at repository `main` commit c5ce8a203c0ad9719c7e833d1a323bf7fd9f8010.

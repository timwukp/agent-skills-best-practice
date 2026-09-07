# Intent: stop hand-editing the mutation count in three coupled places

- **Slug:** dynamic-mutation-count
- **Author:** Kiro (AI agent)
- **Accepted-by:** Tim WU
- **Date:** 2026-09-07
- **Status:** accepted

## Problem

The number of mutations in `scripts/mutation_proof.py` is written by hand in three other
places, and every change to the mutation set must update all three by hand or the build goes
red:

1. `SKILL.md` — "N mutations, all killed".
2. `references/limitations.md` — "(N mutations, N killed)".
3. `scripts/mutation_proof.py` itself — the `positioning: stale mutation evidence count`
   mutation anchors on the exact string "N mutations, all", so when the docs change N the
   anchor goes stale and the harness reports it BROKEN.

This coupling fired twice in one working session: adding two mutations forced 65→70→72, and
adding one more forced 72→73. Each time, forgetting any of the three sites is a red build for
a reason unrelated to the change being made. `test_enterprise_readiness.py` already derives
the true count from the harness by parsing its `MUTATIONS` list, so the machine can compute
the number — but the documents still carry it as a literal, and the mutation harness's own
anchor still carries it as a literal.

## Desired outcome

Adding or removing a mutation updates the reported count without a human editing three
separate literals, while the guarantee that the docs cannot silently carry a STALE count is
preserved. The point of the count in the docs is that a reader sees current evidence; that
protection must not be lost in the name of convenience.

## Affected users / systems

- Anyone adding a mutation to `mutation_proof.py` — currently must edit three other sites.
- `SKILL.md`, `references/limitations.md` — carry the literal today.
- `scripts/mutation_proof.py` — its stale-count mutation anchors on the literal.
- `scripts/test_enterprise_readiness.py` — already derives the count; the likely home for a
  changed contract.
- `scripts/sdlc_ci_gate.py`, the hook, the workflows, the schema, `GATE_VERSION` —
  **unchanged**.

## Constraints

- **The staleness protection must survive.** Whatever replaces the hand-edit, a doc that
  states a WRONG or OLD count must still fail the build. Removing the coupling by removing the
  check is not acceptable — that reintroduces the stale-27-mutations class of defect.
- **No enforcement/schema/release change.** Documentation, tests, and possibly a small
  generator/checker only. No `GATE_VERSION` bump.
- **Stdlib only.** No new dependency.
- **The docs must stay human-readable.** A reader opening `SKILL.md` should still see what the
  evidence is, not a placeholder that only resolves in CI.
- Follow this skill's own SDLC: no source edit before an accepted plan; no self-approval.

## Success criteria

1. Adding or removing a mutation no longer requires editing a literal count in `SKILL.md`,
   `references/limitations.md`, or the `mutation_proof.py` stale-count anchor by hand.
2. A documentation count that does not match the harness's actual `len(MUTATIONS)` still fails
   the build (staleness protection retained).
3. The stale-27-mutations regression is still caught — a mutation proving the freshness check
   works remains, and does not itself reintroduce a hand-maintained literal.
4. `sdlc_ci_gate.py` is byte-identical to the merge base; `GATE_VERSION` remains `2`.
5. All existing suites and mutations remain green: 0 survived, 0 broken.
6. The dogfood chain for this slug is committed with human acceptance and sign-off in separate
   commits.

## Open questions

1. **What replaces the literal?** This is the real design decision, deferred to spec/design.
   Candidate directions, to be weighed there:
   - a checked-in generator that writes the count into the docs from the harness, run in CI,
     with the build failing if the generated text is out of date (the "committed generated
     value" pattern — keeps docs readable, moves the edit to a command);
   - a single source-of-truth token the docs reference, with the freshness test comparing it
     to `len(MUTATIONS)`;
   - keeping the literal but making the stale-count MUTATION anchor not depend on the exact
     number (removing site 3 from the coupling, leaving only the two docs, which the
     truthfulness test already guards).
   The last is the smallest change and removes one of three coupled sites for free; the first
   removes all hand-editing but adds a generator. Design must pick and justify.
2. **Does the count belong in prose at all,** or should the docs state "mutation-verified"
   qualitatively and let the exact number live only where it is computed? To be decided in
   design; changing what the docs promise is a scope question for the owner.

# Spec: stop hand-editing the mutation count in three coupled places

- **Intent:** ./intent.md
- **Author:** Kiro (AI agent)
- **Accepted-by:** pending — owner sign-off
- **Status:** draft

## Open questions from the intent, now closed

**Q1 — what replaces the literal?** Neither a generator nor a placeholder token. The design
below removes the *coupling* rather than the number, in two independent moves:

1. **Re-anchor the stale-count mutation on number-free prose.** Site 3 exists only because the
   mutation's `find` string contains the current count (`"73 mutations, all"`). A mutation that
   anchors on surrounding prose containing no digits and *inserts* a stale claim kills exactly
   the same assertion while never going stale itself. This removes site 3 permanently, with no
   new machinery.
2. **Add a one-command sync for the two documents.** `scripts/sync_mutation_count.py` reads
   `len(MUTATIONS)` from the harness and rewrites the count in `SKILL.md` and
   `references/limitations.md`. The human runs one command instead of editing two files, and
   the existing freshness assertion in `test_enterprise_readiness.py` remains the thing that
   fails when they forget.

**Q2 — does the count belong in prose at all?** Yes, it stays. Removing the number would end
the coupling completely, but "73 mutations, all killed" is the concrete evidence that makes the
claim checkable; "mutation-verified" is the kind of unfalsifiable phrasing this project exists
to avoid. Keeping the number and automating its propagation preserves the evidence and still
removes the hand-editing. Recorded as a rejected alternative below.

## Requirements

1. **Number-free mutation anchor (Intent SC1, SC3).**
   The `positioning: stale mutation evidence count` entry in `scripts/mutation_proof.py` must
   anchor on text containing no mutation count, and must still be **killed** by
   `test_enterprise_readiness.py` for the intended reason — that a stale `27 mutations` claim
   appears in a document. After this change, adding or removing a mutation must not be able to
   make that entry `broken`.

2. **A sync command (Intent SC1).**
   Add `scripts/sync_mutation_count.py`. It must:
   - derive the count by parsing the harness's `MUTATIONS` list, not by importing and running it;
   - rewrite the count in `SKILL.md` and `references/limitations.md` in place;
   - support a check-only mode that exits non-zero when a document is out of date and changes
     nothing, so CI can use the same code path as the human;
   - be idempotent, and exit non-zero rather than guess if a target sentence is not found.

3. **Freshness protection retained (Intent SC2, constraints).**
   `test_enterprise_readiness.py` must continue to fail when a document's count does not equal
   the harness's actual `len(MUTATIONS)`, and must continue to reject a stale `27 mutations`
   claim. Neither assertion may be weakened, and removing the coupling must not be achieved by
   removing a check.

4. **Proof the new machinery is itself covered (Intent SC3, SC5).**
   Add mutations proving the sync command cannot silently stop working: one that makes the
   check-only mode return success when a document is stale, killed by a test that exercises
   check-only mode against a deliberately stale fixture.

5. **No runtime or enforcement change (Intent SC4).**
   `scripts/sdlc_ci_gate.py`, the hook, the schema, the workflows and `GATE_VERSION` are
   untouched. `GATE_VERSION` stays `2`, `SUPPORTED_SCHEMA` stays `1`. No release generation.

6. **Suites and mutations stay green (Intent SC5).**
   All suites pass and the harness reports `0 survived, 0 broken` at the new total.

7. **Dogfood chain (Intent SC6).**
   Artifacts for `dynamic-mutation-count` stay committed, `.sdlc/active` names this slug, and no
   artifact this agent authored is set to `accepted`/`signed-off` by the agent.

## Non-functional requirements

- **Stdlib only.** `ast` for parsing, `re` for the rewrite. No dependency.
- **Human-readable docs.** The rendered sentences must read exactly as they do today; only how
  the number gets there changes.
- **Test robustness.** The sync command's tests must operate on temporary fixtures, never on the
  repository's own documents, so a test run cannot mutate tracked files.
- **Determinism.** No network, no clock, no environment dependence.

## Design

### 1. Removing site 3

The entry today is:

```
"73 mutations, all"  ->  "27 mutations, all"
```

Both halves carry a number, so the anchor dies whenever the count moves. Replace it with an
insertion anchored on prose that has no digits — for example anchoring inside
`references/limitations.md` on the phrase that follows the count and inserting a stale claim
ahead of it. The mutated document then contains `27 mutations`, the freshness assertion fires,
and the entry is killed. Because the anchor names no count, changing the count cannot break it.

The exact anchor is chosen during implementation against the real file text and verified by
running the harness: a stale anchor reports `broken`, which is the failure this requirement
exists to prevent.

### 2. The sync command

```
python3 scripts/sync_mutation_count.py            # rewrite the documents
python3 scripts/sync_mutation_count.py --check    # exit 1 if any document is stale
```

Count derivation reuses the approach already proven in `test_enterprise_readiness.py`: parse
the harness with `ast` and measure the `MUTATIONS` assignment, handling the annotated form.
Importing the harness is rejected — it would execute module-level code and couple the sync tool
to the harness's runtime.

Each target is described by a file plus a regex with the number as a capture group, so the
sentence wording can change without touching the tool as long as the shape holds. A target
whose pattern does not match is a hard error, not a silent skip: silently skipping is how the
stale claim survived for months in the first place.

### 3. Where the assertions live

- The freshness comparison stays in `test_enterprise_readiness.py`, unchanged.
- The sync command gets its own suite, `scripts/test_sync_mutation_count.py`, covering: the
  derived count matches a fixture's list length; a rewrite makes a stale fixture current;
  `--check` exits non-zero on a stale fixture and zero on a current one; a rewrite is
  idempotent; and an unmatched pattern is an error.

### 4. What this does not do

It does not run the sync automatically on commit. A hook that rewrites tracked documents during
a commit surprises the author and can fight the gate's own coverage check. The command is
explicit, and the existing test is what catches a human who forgets to run it.

### 5. Rejected alternatives

- **Make the documents qualitative ("mutation-verified") — rejected.** It ends the coupling by
  deleting the evidence. An unfalsifiable claim is worse than a number that can go stale, and a
  number that a test enforces cannot in fact go stale.
- **A checked-in generated file the docs include — rejected.** Markdown has no include; it would
  require a build step this project deliberately does not have.
- **A placeholder token resolved at render time — rejected.** The documents are read directly on
  GitHub and from the installed skill directory, where nothing resolves tokens.
- **Import the harness to count — rejected.** Executes module-level code and couples the tool to
  the harness's runtime behaviour rather than its data.
- **Run the sync from a git hook — rejected.** See design 4.
- **Remove the stale-count mutation instead of re-anchoring it — rejected.** That is removing a
  check to remove a coupling, which the intent forbids.

## Flagged concerns

| Concern | Policy owner | Resolution |
|---|---|---|
| The new anchor could itself go stale | Skill maintainer | Requirement 1 forbids a count in the anchor; verified by the harness reporting `0 broken`. |
| A sync tool could rewrite the wrong thing | Skill maintainer | Explicit per-target patterns; unmatched pattern is a hard error; tests run on temporary fixtures only. |
| Adding machinery to remove two hand-edits could be net complexity | Product owner | Bounded to one ~80-line stdlib script plus its suite; the alternative is a recurring red build on every mutation change. |
| Automation could weaken the freshness guarantee | Skill maintainer | Requirement 3 keeps both assertions intact; requirement 4 adds a mutation proving check-only mode still bites. |

## Out of scope

- Changing `sdlc_ci_gate.py`, the hook, the schema, the workflows, or `GATE_VERSION`.
- Running the sync automatically from a hook or CI commit step.
- Any other hard-coded evidence figure (the 36/80 score and the ~48% ceiling are rubric results,
  not derived counts, and stay literal).
- Adding a caller so this repository's own PRs are gate-governed (separate intent).
- Any release or tag.

---
Gate: owner signs off; flagged concerns worked first. Applied org skills/versions recorded:
`ai-native-sdlc` at repository `main` commit 3a343d5d55b8af60d17e033568f1a7908722cb3d.

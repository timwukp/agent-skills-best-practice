---
name: legacy-code-testing
description: >
  Adds tests to legacy code that has none, safely: characterization tests that pin current behavior
  (including bugs) before any refactoring, seam identification for breaking untestable dependencies,
  and a risk-ranked coverage strategy. Use for untested or inherited codebases. Triggers on: "add
  tests to legacy code", "this code has no tests", "characterization tests", "make this testable",
  "safe to refactor?", "pin down current behavior", "test this old module before we change it".
license: MIT
metadata:
  author: Community
  version: 1.0.0
  category: engineering-workflow
---

# Legacy Code Testing

Untested code you must change is a trap: you can't refactor safely without tests, and you can't test cleanly without refactoring. The way out is characterization testing — pin down what the code *currently does* (not what it should do), then refactor under that safety net.

The golden rule: **before refactoring, tests assert current behavior — even buggy behavior.** A characterization test that "fails" because the code has a bug is wrong; the test must pass against today's code. Log suspected bugs separately for the team to triage.

## Process

1. **Scope and rank.** Identify what actually needs a safety net: code you're about to change, plus its blast radius (callers and shared state). Rank by `change-likelihood × consequence-of-breaking`. Do not attempt whole-codebase coverage — legacy coverage is bought module by module, just-in-time.
2. **Find the seams.** For each target, identify where behavior can be observed and where dependencies can be substituted without editing the logic under test (see Seams table). If there is no seam, apply the *minimal* enabling refactor (extract method, parameterize constructor, wrap static call) — mechanical, behavior-preserving, small enough to eyeball.
3. **Write characterization tests.**
   - Start with the happy path for the most common input; then boundaries (empty, null, max, malformed); then the weird branches the code visibly handles.
   - When you don't know the expected output, **run the code and capture it**: write the assertion against the observed result. If you can't execute it, write the assertion as your best reading of the code and mark it `// CHARACTERIZATION: verify against production behavior before trusting`.
   - For outputs too large/complex to assert piecewise, use snapshot/golden-master testing: capture the full output once, assert future runs match byte-for-byte (or with explicit normalization for timestamps/ids).
4. **Log suspected bugs, don't fix them.** Maintain a `SUSPECTED-BUGS.md` (or ticket list): behavior pinned by a test that looks wrong, with the test name, why it looks wrong, and the blast radius of fixing it. Fixing comes after the net exists, as separate, deliberate changes.
5. **Refactor under the net.** Only after the characterization suite is green and running in CI: refactor in small steps, keeping the suite green at each step. As real intent becomes clear, graduate characterization tests into proper specification tests (rename, assert intent, delete redundant pins).
6. **Report.** Deliver: tests written, observed coverage of the target module, seams introduced (with the enabling refactors listed), suspected bugs logged, and what remains unprotected.

## Seams

| Dependency problem | Seam technique |
|--------------------|----------------|
| Hard-coded `new` of a collaborator | Extract creation to overridable factory method, or parameterize the constructor |
| Static call / singleton | Wrap in an instance method or injectable adapter |
| Database / network / filesystem inline | Extract a gateway interface; in tests, substitute an in-memory fake |
| Clock / randomness | Inject a clock/seed provider |
| Global mutable state | Pass it in; or snapshot-and-restore around each test as a last resort |
| Monster method (hundreds of lines) | Test it as a black box first (inputs → outputs/side effects); extract pieces only under that net |

Prefer fakes over mocks for legacy work: characterization cares about end behavior, and deep mock setups just restate the implementation you're trying to free yourself from.

## What Good Looks Like

- Tests run fast and deterministically (no real network/DB/clock) — otherwise they won't be run, and an unrun net catches nothing.
- Each test name says what behavior it pins: `retains_trailing_whitespace_in_legacy_export` beats `test_export_3`.
- The suite is in CI before any refactoring PR merges.
- Suspected-bug log exists and has owners — pinned bugs that nobody triages become permanent.

## Guidelines

- Resist "while I'm here" fixes: cleanups, renames, and bug fixes during the characterization phase invalidate the whole exercise. One phase at a time.
- Coverage percentage is not the goal; *confidence to change the code you must change* is. 60% coverage of the volatile core beats 90% spread thin.
- If the code is about to be deleted or rewritten wholesale, characterization tests at the system boundary (API in/out) are worth more than unit tests of doomed internals.
- For language-specific test generation mechanics, hand off to the matching generator skill if available (e.g. java-unit-test-generator); this skill owns the strategy and the characterization discipline.

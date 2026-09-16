# Plan: one wrapper, one suite, five honest documents

- **Spec:** ./spec.md
- **Author:** Claude (AI agent)
- **Accepted-for:** 2e8060593bdb08885a5a81e60968ee317d341acb
- **Status:** draft

`Accepted-for` must be `git merge-base origin/main HEAD`, which at draft time is
`2e80605` (full sha recorded above).

## Approach

The hook script already speaks Claude Code's contract (stdin event shape, exit-2 block,
`$HOME/.claude/skills/` in the resolver), so the change is deliberately thin: a config
wrapper, a test that would catch the two ways this can silently rot (template drift, and
an exit code that blocks on one runtime and warns on the other), and documentation that
claims exactly what is tested and no more.

## Files changed (in work order)

1. `skills/skills/ai-native-sdlc/scripts/test_claude_hook_config.py` — NEW. Written and
   observed failing FIRST (FileNotFoundError on the template it tests).
2. `.github/workflows/sdlc-gate-tests.yml` — add `test_claude_hook_config` to the suite
   list, in the same commit as the red test: from that commit on, CI's failure names the
   missing template rather than silently not running the suite.
3. `skills/skills/ai-native-sdlc/templates/claude-code-hooks/settings.json` — NEW. The
   green step. Command string byte-identical to the Kiro template's; anchored regex
   matcher `^(Write|Edit|MultiEdit|NotebookEdit)$`.
4. `skills/skills/ai-native-sdlc/SKILL.md` — enforcement table names both templates; the
   install block gains the Claude Code line and the merge-don't-overwrite caveat.
5. `skills/skills/ai-native-sdlc/COMPATIBILITY.md` — Surfaces row, support-matrix block
   (`posix_only` wording, `documented_untested.surfaces` gains
   `claude-code-live-runtime`), POSIX-only prose, and a "Not tested" row stating the
   contract-tested / runtime-unproven split.
6. `skills/skills/ai-native-sdlc/references/enforcement.md` — section 1 becomes
   dual-surface: both install paths, the three-runtime exit-code intersection, and the
   matcher-convention trap (Kiro category vs Claude Code regex).
7. `skills/skills/ai-native-sdlc/references/playbook-mapping.md` — canonical blog
   citation (URL, date, author), Academy-edition note with the blog authoritative, and
   the not-implemented plays table.

## What is deliberately NOT changed

`scripts/sdlc_pretooluse_hook.py`, `scripts/sdlc_gate.py`, `scripts/sdlc_ci_gate.py`,
`scripts/test_hook_config.py`, and the Kiro template. The mutation count is untouched
because no gate logic changes.

## Verification

- `python3 scripts/test_claude_hook_config.py` red before step 3, green after.
- Full local run of every suite in the CI list, plus `sdlc_ci_gate.py --require-active
  --base-sha 2e8060593bdb08885a5a81e60968ee317d341acb` against this tree.

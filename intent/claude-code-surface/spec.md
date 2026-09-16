# Spec: ship the Claude Code surface without forking the hook

- **Intent:** ./intent.md
- **Author:** Claude (AI agent)
- **Signed-off-by:** Tim WU
- **Accepted-by:** Tim WU
- **Status:** signed-off

## Requirements

1. **A shipped Claude Code hook config.** `templates/claude-code-hooks/settings.json`
   exists, in Claude Code's `hooks.PreToolUse` schema, with a `matcher` that is a regex
   over tool names anchored to the write tools (`Write`, `Edit`, `MultiEdit`,
   `NotebookEdit`) and matching no read or exec tool.

2. **One command string, two templates.** The `command` inside the Claude Code template is
   byte-identical to the one in `templates/kiro-hooks/sdlc-gate.json`. This is asserted by
   a test, not by review: a fix applied to one template and not the other is the drift
   failure mode this repository's single-source rule exists for.

3. **The contract difference is asserted, not assumed.** A new suite,
   `scripts/test_claude_hook_config.py`, drives the shipped command with Claude
   Code-shaped events (`hook_event_name: "PreToolUse"`, `tool_name: "Write"`,
   `tool_input.file_path`) and asserts under Claude Code's exit contract:
   - a refusal exits **exactly 2** (any other non-zero is a warning there, not a block);
   - an accepted chain exits 0;
   - a repo-local `.sdlc/scripts/` copy takes precedence over the
     `$HOME/.claude/skills/` copy — the resolver leg the Kiro suite never exercises;
   - missing `python3` and missing gate script self-disable with exit 0;
   - the suite skips its execution cases loudly on non-POSIX hosts, like the Kiro suite.
   The suite is written and observed failing BEFORE the template exists, and it runs in
   CI in the same job as the existing suites.

4. **Documentation states the surface honestly.** `COMPATIBILITY.md` lists Claude Code in
   the Surfaces row as *contract tested*, records the live runtime as untested in both the
   support-matrix block and the "Not tested" table, and extends the POSIX-only caveat to
   the new template. `SKILL.md` and `references/enforcement.md` show the Claude Code
   install path next to the Kiro one, including the merge-don't-overwrite caveat for an
   existing `.claude/settings.json`.

5. **The mapping cites its source.** `references/playbook-mapping.md` links the canonical
   blog URL with date and author, states that the 14-row numbering follows the Claude
   Academy course edition and that the blog is authoritative where they disagree, and
   carries a table declaring each blog play the skill does NOT implement (auto mode,
   legacy-system onboarding, managed settings, recurring security scans, Claude on call)
   with the reason it is out of scope.

## Out of scope

- Any change to `scripts/sdlc_pretooluse_hook.py`, `sdlc_gate.py`, or `sdlc_ci_gate.py`.
- Any claim of CI coverage for the live Claude Code IDE/CLI runtime.

## Verification target

`python3 scripts/test_claude_hook_config.py` exits 0, and every pre-existing suite in
`.github/workflows/sdlc-gate-tests.yml` still exits 0 — in particular
`test_support_matrix.py`, which cross-checks the COMPATIBILITY.md claims this spec edits.

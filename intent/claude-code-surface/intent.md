# Intent: the skill ships in Claude Code's format but enforces only in Kiro's

- **Slug:** claude-code-surface
- **Author:** Claude (AI agent)
- **Date:** 2026-09-15
- **Accepted-by:** Tim WU
- **Status:** accepted

## Problem

An external review (deep-research over the skill, Anthropic's *AI-Native SDLC Playbook*
blog post, and Anthropic's skill-authoring guidance, 2026-09-10) confirmed a divergence
this repository already half-knows about: the skill's *format* is Claude Code's — SKILL.md,
frontmatter, progressive disclosure — but its *deterministic layer* installs only into
Kiro's hook runtime. `templates/kiro-hooks/sdlc-gate.json` uses Kiro's trigger/matcher
schema, and `COMPATIBILITY.md`'s support matrix names only Kiro surfaces. A Claude Code
user who reads the playbook, installs this skill, and asks for the write-time gate has no
supported path to one.

The gap is smaller than it looks, which is exactly why leaving it open is unjustified:
`scripts/sdlc_pretooluse_hook.py` already speaks Claude Code's contract. It reads the same
stdin event shape (`hook_event_name` / `tool_name` / `tool_input` / `cwd`), it blocks with
exit code 2 and stderr — which is precisely Claude Code's blocking convention — and its
resolver already searches `$HOME/.claude/skills/ai-native-sdlc/`. Only the config wrapper
is missing.

The same review found two documentation defects in `references/playbook-mapping.md`:

1. **Attribution.** The file cites "the Claude Academy *AI-Native SDLC Playbook* (14
   lessons)" and never links the canonical, publicly checkable source — the claude.com
   blog post (2026-08-21), which is organised as six stages, not fourteen lessons. A
   reader cannot verify the mapping against the source the mapping claims to distill.
2. **Coverage.** The blog contains plays the mapping neither maps nor declares out of
   scope: auto mode, legacy-system onboarding, recurring security scans, and Claude on
   call. An unmapped play is indistinguishable from a forgotten one.

## Desired outcome

- A Claude Code user can install the write-time gate from a shipped template, and the
  command inside that template is exercised by CI the same way the Kiro template's is.
- `COMPATIBILITY.md` states the Claude Code surface honestly: the *command contract* is
  tested; the live IDE runtime is not, which is the same epistemic status the Kiro rows
  have.
- `references/playbook-mapping.md` cites the canonical blog URL, explains what the
  14-lesson numbering refers to, and closes the coverage question: every play in the blog
  is either mapped or explicitly declared out of scope with a reason.

## Non-goals

- No change to the hook script or the gate scripts. The review verified the contract
  match; this change is a wrapper and documentation, and must stay that.
- No claim that the Claude Code IDE runtime is CI-verified. It is not, and saying so
  would be the overclaiming failure mode the skill warns about.

## Acceptance

Accepted on the owner's explicit authorization of the external review's recommendations
(review session, 2026-09-15). Merging the pull request that carries this chain is the
recorded confirmation of that acceptance.

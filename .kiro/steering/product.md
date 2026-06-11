---
inclusion: always
---

# Product Overview

This repository teaches AWS SAs and developers how to build agent skills — folders of instructions, scripts, and resources that AI agents (Kiro, Claude Code, Claude.ai) load dynamically to improve performance on specialized tasks.

It contains:

- **Example skills** in `skills/skills/`: Apache 2.0 examples from Anthropic (skill-creator, mcp-builder, canvas-design, etc.) plus MIT-licensed software engineering workflow skills built for this repo (api-design, git-workflow, cicd-pipeline, terraform-module, and others).
- **A 6-hour workshop** in `skills-workshop/` with slides, exercises, labs, and test cases.
- **Tooling**: a validation script used by CI, an install script for Kiro, and per-skill evals.

Skills here conform to the [Agent Skills specification](https://agentskills.io/specification) and are portable across Kiro, Claude Code, Claude.ai, and the Claude API. Anthropic's source-available document skills (docx, pdf, pptx, xlsx) are intentionally not included; this repo only carries open-source content.

## Key Principles

- A skill is a self-contained folder whose `SKILL.md` has YAML frontmatter (`name`, `description`) followed by instructions.
- Descriptions drive activation: third person, what the skill does plus when to use it, with concrete trigger phrases.
- Progressive disclosure: keep `SKILL.md` under 500 lines; push details into `references/`, code into `scripts/`.
- Evaluation-first: engineering skills ship `evals/` with task evals and should-trigger / should-not-trigger queries.

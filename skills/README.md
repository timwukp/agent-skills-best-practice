> **Note:** This directory follows the open [Agent Skills standard](https://agentskills.io/specification). Many example skills here originate from Anthropic's official [anthropics/skills](https://github.com/anthropics/skills) repository (Apache 2.0); the engineering workflow skills were built for this repository (MIT).

# Skills

Skills are folders of instructions, scripts, and resources that AI agents (Kiro, Claude Code, Claude.ai) load dynamically to improve performance on specialized tasks. Skills teach an agent how to complete specific tasks in a repeatable way, whether that's creating documents with your company's brand guidelines, analyzing data using your organization's specific workflows, or automating personal tasks.

For more information, check out:
- [Kiro Skills documentation](https://kiro.dev/docs/skills/)
- [What are skills?](https://support.claude.com/en/articles/12512176-what-are-skills)
- [How to create custom skills](https://support.claude.com/en/articles/12512198-creating-custom-skills)
- [Equipping agents for the real world with Agent Skills](https://anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills)

# About This Directory

This directory contains skills that demonstrate what's possible with agent skills. They range from creative applications (art, design) to technical tasks (testing web apps, MCP server generation, API design, CI/CD) to enterprise workflows (communications, branding).

Each skill is self-contained in its own folder with a `SKILL.md` file containing the instructions and metadata the agent uses. Browse the [full catalog](CATALOG.md) to get inspiration for your own skills or to understand different patterns and approaches.

Anthropic's source-available document skills (docx, pdf, pptx, xlsx) are **not** included here — find them in the official [anthropics/skills](https://github.com/anthropics/skills) repository.

## Disclaimer

**These skills are provided for demonstration and educational purposes only.** Always test skills thoroughly in your own environment before relying on them for critical tasks.

# Skill Sets
- [./skills](./skills): Skill examples for Creative & Design, Development & Technical, Software Engineering Workflow, and Enterprise & Communication — see [CATALOG.md](CATALOG.md)
- [./shared](./shared): Shared utilities used by multiple skills (not skills themselves)
- [./spec](./spec): Pointer to the Agent Skills specification
- [./template](./template): Skill template

# Try in Kiro, Claude Code, Claude.ai, and the API

## Kiro

Copy any skill folder into `~/.kiro/skills/` (global) or `.kiro/skills/` (workspace), or use the install script from the repository root:

```bash
./install.sh hello-world api-design   # or ./install.sh --all
```

## Claude Code

You can register this repository as a Claude Code Plugin marketplace by running the following command in Claude Code:

```
/plugin marketplace add timwukp/agent-skills-best-practice
```

Then install a skill set:

```
/plugin install example-skills@agent-skills-best-practice
/plugin install engineering-skills@agent-skills-best-practice
/plugin install claude-api@agent-skills-best-practice
```

After installing a plugin, use a skill by just mentioning it — for example: "Use the api-design skill to draft an OpenAPI spec for a bookstore service."

## Claude.ai

To upload custom skills to Claude.ai, follow the instructions in [Using skills in Claude](https://support.claude.com/en/articles/12512180-using-skills-in-claude#h_a4222fa77b).

## Claude API

You can upload custom skills via the Claude API. See the [Skills API Quickstart](https://docs.claude.com/en/api/skills-guide#creating-a-skill) for more.

# Creating a Basic Skill

Skills are simple to create - just a folder with a `SKILL.md` file containing YAML frontmatter and instructions. You can use the **template-skill** in this repository as a starting point:

```markdown
---
name: my-skill-name
description: A clear description of what this skill does and when to use it
---

# My Skill Name

[Add your instructions here that the agent will follow when this skill is active]

## Examples
- Example usage 1
- Example usage 2

## Guidelines
- Guideline 1
- Guideline 2
```

The frontmatter requires only two fields:
- `name` - A unique identifier for your skill (lowercase, hyphens for spaces; must match the folder name)
- `description` - A complete description of what the skill does and when to use it

The markdown content below contains the instructions, examples, and guidelines that the agent will follow. Keep the body under 500 lines and move detailed reference material into separate files — see the [Claude Skills best practices](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices).

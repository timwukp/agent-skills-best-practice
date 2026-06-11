# Kiro Skills Quickstart

Get from zero to a working skill in 5 minutes.

## Prerequisites

- [Kiro IDE](https://kiro.dev) installed and authenticated
- Git installed

## Step 1: Clone this repo

```bash
git clone https://github.com/timwukp/agent-skills-best-practice.git
cd agent-skills-best-practice
```

## Step 2: Install the hello-world skill into Kiro

```bash
./install.sh hello-world
```

(Or manually: `mkdir -p ~/.kiro/skills/ && cp -r skills/skills/hello-world ~/.kiro/skills/hello-world`. Run `./install.sh --list` to see all installable skills, or `./install.sh --all` to install everything.)

## Step 3: Test it

Open Kiro and type:

> "Test my skills setup"

The hello-world skill should activate, greet you, and explain how progressive disclosure works.

## Step 4: Build your own

Create a new skill folder:

```bash
mkdir -p ~/.kiro/skills/my-first-skill
```

Create `~/.kiro/skills/my-first-skill/SKILL.md`:

```markdown
---
name: my-first-skill
description: Describe what this skill does and when to use it.
  Include trigger phrases like "do X", "create Y", or "help with Z".
---

# My First Skill

## Instructions

1. Step one
2. Step two
3. Step three
```

The two required frontmatter fields:
- **`name`** — kebab-case identifier (must match folder name)
- **`description`** — what it does AND when to trigger (this is the most important part)

## Step 5: Iterate

Test with 10-20 different phrasings. If the skill doesn't trigger:
- Add more trigger phrases to the description
- Be specific about user intents ("Use when user says...")
- Make the description "pushier"

## What's Next

- **Workshop**: Work through `skills-workshop/` for the full 6-hour training
- **Examples**: Browse `skills/skills/` for production skill patterns
- **Spec**: Read the [Agent Skills Specification](https://agentskills.io/specification)
- **Create with AI**: Use the `skill-creator` skill to build skills interactively

## Project-Level Skills

> For a quick overview of project-level vs global skills, see the [README](README.md).

Skills installed to `~/.kiro/skills/` are global (available in all projects). You can also install skills at the **project level** by placing them in `.kiro/skills/` inside your repository:

```bash
# Project-level (shared with all contributors)
mkdir -p .kiro/skills/my-team-skill
cp -r path/to/skill/* .kiro/skills/my-team-skill/

# Global (personal, across all projects)
cp -r path/to/skill/* ~/.kiro/skills/my-team-skill/
```

**When to use project-level skills:**
- The skill encodes team-specific workflows or conventions
- You want everyone who clones the repo to get the same skill
- The skill references project-specific paths, APIs, or architecture

**When to use global skills:**
- The skill is a personal productivity tool
- It applies generically across unrelated projects
- You are experimenting and do not want to commit it yet

## Kiro Web

Skills also work in [Kiro Web](https://kiro.dev), the browser-based interface. Kiro Web offers two modes:

- **Vibe mode** - Have a back-and-forth conversation with Kiro to iteratively refine outputs. Good for exploration and creative tasks.
- **Autonomous mode** - Describe a task and let Kiro work independently. Good for well-defined implementation work.

Upload or reference your skills in either mode to get the same domain-specific assistance as in the desktop IDE.

## Steering Files

> For a quick overview of steering files, see the [README](README.md).

Steering files (`.kiro/steering/*.md`) complement skills by defining **project-wide conventions** rather than task-specific instructions. While a skill tells Kiro *how to do a specific task*, steering files tell Kiro *how to behave across all tasks* in this project.

Example use cases for steering files:
- Coding style (naming, formatting, error handling)
- Architecture decisions (folder structure, allowed dependencies)
- Review standards (what to check before committing)

Create a steering file:

```bash
mkdir -p .kiro/steering
echo "# Conventions\n\n- Use kebab-case for file names\n- All functions must have docstrings" > .kiro/steering/conventions.md
```

Kiro reads all `.md` files in `.kiro/steering/` and applies them as persistent context for every interaction in the project.

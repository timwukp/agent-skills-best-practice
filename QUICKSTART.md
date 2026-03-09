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

## Step 2: Copy the hello-world skill to Kiro

```bash
mkdir -p ~/.kiro/skills/
cp -r skills/skills/hello-world ~/.kiro/skills/hello-world
```

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

---
name: hello-world
description: A minimal example skill that greets users and explains how skills work. Use when user says "hello world skill", "test my skills setup", or "show me how skills work".
license: MIT
metadata:
  author: Example
  version: 1.0.0
  category: getting-started
---

# Hello World Skill

A minimal working skill to verify your setup and understand the basic pattern.

## Instructions

When triggered, do the following:

1. Greet the user and confirm this skill was activated
2. Ask for their name if not already provided
3. Generate a personalized welcome message
4. Explain the three-level progressive disclosure system:
   - Level 1: YAML frontmatter (always loaded, ~100 words)
   - Level 2: SKILL.md body (loaded when triggered — you're reading it now)
   - Level 3: Linked references (loaded as needed)

## Example

User says: "Test my skills setup"

Response:
- Confirm the hello-world skill activated successfully
- Greet the user
- Briefly explain what just happened (skill triggering via description match)

## Guidelines

- Keep responses concise and friendly
- This skill is for learning — point users to more complex skills as next steps
- Suggest they look at `skills/skills/skill-creator/` to build their own

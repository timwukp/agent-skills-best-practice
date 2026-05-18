---
name: kiro-project-setup
description: Helps users set up a complete Kiro project structure with steering files, skills directory, and proper configuration. Use when user says "set up kiro project", "initialize kiro", "create kiro structure", or "add kiro configuration".
license: MIT
metadata:
  author: Kiro
  version: 1.0.0
  category: project-setup
---

# Kiro Project Setup Skill

Sets up a complete Kiro project structure so your AI assistant understands your project conventions, has access to custom skills, and respects your configuration preferences.

## Instructions

When triggered, perform the following steps:

1. **Create the `.kiro/steering/` directory** with a `conventions.md` file containing:
   - Project naming conventions (file naming, variable naming)
   - Code style preferences (formatting, linting rules)
   - Architecture patterns used in the project
   - Any team-specific rules the user provides

2. **Create the `.kiro/skills/` directory** for project-level skills:
   - Add a placeholder `SKILL.md` explaining that project-specific skills live here
   - These skills are scoped to the repository and not shared globally

3. **Add `.gitignore` entries** for `.kiro/` temp files:
   - Add `.kiro/cache/` to ignore cached data
   - Add `.kiro/tmp/` to ignore temporary files
   - Keep `.kiro/steering/` and `.kiro/skills/` tracked in version control

4. **Create a README section** (or suggest additions) covering:
   - How the project uses Kiro steering files
   - Where to find and add project-level skills
   - How new team members can customize their setup

Ask the user about their project before generating files. Gather:
- Programming language(s) used
- Preferred code style (tabs vs spaces, naming conventions)
- Any existing linting or formatting tools
- Team size and collaboration patterns

## Guidelines

- Always ask before overwriting existing files in `.kiro/`
- Keep `conventions.md` concise and actionable - avoid vague guidance
- Use the project's existing style as the basis for conventions when possible
- Suggest committing `.kiro/steering/` files so the whole team benefits
- Do not add secrets, credentials, or personal preferences to tracked files
- If the project already has a `.kiro/` directory, offer to enhance rather than replace

## Examples

**User says:** "Set up Kiro for my TypeScript project"

**Response:**

Create the following structure:

```
.kiro/
  steering/
    conventions.md
  skills/
```

Where `conventions.md` contains:

```markdown
# Project Conventions

## Naming
- Files: kebab-case (e.g., user-service.ts)
- Classes: PascalCase
- Functions and variables: camelCase
- Constants: UPPER_SNAKE_CASE

## Code Style
- Use TypeScript strict mode
- Prefer async/await over raw promises
- Maximum line length: 100 characters

## Architecture
- Follow domain-driven structure under src/
- Keep business logic separate from infrastructure
- Use dependency injection for testability
```

And add to `.gitignore`:

```
# Kiro temp files
.kiro/cache/
.kiro/tmp/
```

# Coding Standards and Conventions

## Language

- All documentation must be written in English.

## Agent Skills Specification Compliance

- Skill names must be **kebab-case** (lowercase letters, digits, and hyphens only).
- Skill descriptions must not exceed **1024 characters**.
- Skill descriptions must not contain angle brackets (`<` or `>`).
- Every skill directory must contain a `SKILL.md` file with valid YAML frontmatter including `name` and `description` fields.
- Skills must conform to the [Agent Skills Specification](https://agentskills.io/specification).

## Python

- Python scripts must be compatible with **Python 3.10+**.
- Dependencies are listed in `requirements.txt` at the repository root.

## SKILL.md Frontmatter

All `SKILL.md` files must begin with YAML frontmatter containing at minimum:

```yaml
---
name: my-skill-name
description: A concise description of what this skill does.
---
```

Allowed frontmatter properties: `name`, `description`, `license`, `allowed-tools`, `metadata`, `compatibility`.

## Workshop Materials

Workshop chapters follow a consistent structure with these files:

- `slides.md` - Presentation content
- `exercises.md` - Hands-on exercises
- `examples.md` - Example implementations
- `templates.md` - Reusable templates
- `test-cases.md` - Validation test cases

## Repository Rules

- **No binary document files** (PDF, PPTX, DOCX, or similar) in the repository.
- **No PII or customer data** in any file.
- **No hardcoded credentials or secrets** in code or configuration.
- All content must comply with the **MIT License**.

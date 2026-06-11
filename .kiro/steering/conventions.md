---
inclusion: always
---

# Coding Standards and Conventions

## Language

- All documentation must be written in English.

## Agent Skills Specification Compliance

- Skill names must be **kebab-case** (lowercase letters, digits, and hyphens only) and must **match the skill's directory name**.
- Skill descriptions must not exceed **1024 characters**, must be written in the **third person**, and should state both what the skill does and when to use it (with concrete trigger phrases).
- Skill descriptions must not contain angle brackets (`<` or `>`).
- Every skill directory must contain a `SKILL.md` file with valid YAML frontmatter including `name` and `description` fields.
- Keep the `SKILL.md` body under **500 lines**; move detailed reference material into separate files within the skill folder (progressive disclosure).
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
- New content is licensed under the **MIT License**; skills imported from [anthropics/skills](https://github.com/anthropics/skills) remain **Apache 2.0** (see each skill's `LICENSE.txt`). Do not add content under non-open-source licenses.

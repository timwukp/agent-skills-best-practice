# Contributing

Thank you for your interest in contributing to this repository! This guide explains how to add new skills, run validation, and submit changes.

## How to Add a New Skill

### Naming Conventions

- Skill names must be **kebab-case**: lowercase letters, digits, and hyphens only (e.g., `my-new-skill`).
- Names cannot start or end with a hyphen, and cannot contain consecutive hyphens.
- Maximum name length is 64 characters.

### Required Files

Every skill directory must contain at minimum:

- `SKILL.md` - The skill definition file with YAML frontmatter.

### Folder Structure

Create your skill directory under `skills/skills/`:

```
skills/skills/my-new-skill/
  SKILL.md
  templates/        (optional)
  examples/         (optional)
```

### Testing Your Skill

Before submitting, validate your skill locally:

```bash
python3 skills-workshop/scripts/quick_validate.py skills/skills/my-new-skill
```

## Skill Structure Requirements

Skills must conform to the [Agent Skills Specification](https://agentskills.io/specification).

### Frontmatter Fields

Your `SKILL.md` must begin with YAML frontmatter:

```yaml
---
name: my-new-skill
description: A clear description of what this skill does (max 1024 characters).
---
```

**Required fields:**
- `name` - Kebab-case identifier for the skill.
- `description` - Plain text description (no angle brackets, max 1024 characters).

**Optional fields:**
- `license` - License identifier.
- `allowed-tools` - Tools the skill is allowed to use.
- `metadata` - Additional metadata.
- `compatibility` - Compatibility notes (max 500 characters).

### Directory Layout

After the frontmatter, `SKILL.md` contains the skill instructions in Markdown. Additional files (templates, examples) can be placed in subdirectories within the skill folder.

## How to Run Validation Locally

1. Install dependencies:

```bash
pip install pyyaml
```

2. Run the validation script against your skill:

```bash
python3 skills-workshop/scripts/quick_validate.py skills/skills/your-skill-name
```

3. To validate all skills at once:

```bash
for d in skills/skills/*/; do
  if [ -f "${d}SKILL.md" ]; then
    python3 skills-workshop/scripts/quick_validate.py "$d"
  fi
done
```

## PR Process

1. **Fork** this repository.
2. **Create a branch** for your changes (e.g., `add-skill/my-new-skill`).
3. **Add your skill** following the structure described above.
4. **Test** your skill with `quick_validate.py`.
5. **Submit a pull request** to the `main` branch.

Pull requests are validated automatically by CI. Your skill must pass validation before it can be merged.

## Code Style

- All documentation must be written in **English**.
- Do not commit binary document files (PDF, PPTX, DOCX, etc.).
- Do not include PII or customer data.
- Do not include hardcoded credentials or secrets.
- All contributions must be compatible with the **MIT License**.

## Important Note

Do **NOT** modify existing Anthropic skills in `skills/skills/`. These come from the upstream Anthropic repository and are maintained separately. Only add new skill directories or modify your own contributions.

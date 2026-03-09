# Agent Skills Specification

The full specification is maintained at [agentskills.io/specification](https://agentskills.io/specification).

## Quick Reference

A valid skill is a folder containing a `SKILL.md` file with YAML frontmatter:

```yaml
---
name: my-skill-name          # Required. kebab-case, max 64 chars
description: What it does     # Required. Max 1024 chars, no < or >
  and when to use it.
license: MIT                  # Optional
compatibility: Requires X     # Optional. Max 500 chars
metadata:                     # Optional. Custom key-value pairs
  author: Your Name
  version: 1.0.0
---

# Skill instructions go here (markdown)
```

### Required Fields

| Field | Rules |
|-------|-------|
| `name` | kebab-case (`[a-z0-9-]+`), no leading/trailing/consecutive hyphens, max 64 chars |
| `description` | What the skill does AND when to trigger it, max 1024 chars, no `<` or `>` |

### Progressive Disclosure

- **Level 1** (always loaded): YAML frontmatter (~100 words) - determines if skill triggers
- **Level 2** (on trigger): SKILL.md body - full instructions
- **Level 3** (as needed): Linked files in `references/`, `scripts/`, `assets/`

### Validation

Use the workshop validation script to check your skill:

```bash
python skills-workshop/scripts/quick_validate.py path/to/your-skill/
```

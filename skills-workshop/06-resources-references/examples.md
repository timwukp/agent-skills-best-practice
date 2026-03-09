# Chapter 6 Examples

## Example: Quick Reference Card

### Minimal Skill
```yaml
---
name: my-skill
description: What it does and when to use it.
---
# Instructions here
```

### Naming Rules
- kebab-case only: `my-cool-skill`
- No spaces, capitals, or underscores
- Max 64 characters
- No "claude" or "anthropic" prefix

### Description Rules
- Include WHAT and WHEN
- Max 1024 characters
- No angle brackets
- Add negative triggers if needed

### File Structure
```
skill-name/
├── SKILL.md        # Required
├── scripts/        # Optional
├── references/     # Optional
└── assets/         # Optional
```

### Installation
```bash
# Kiro
cp -r skill ~/.kiro/skills/skill-name

# Claude.ai
# Zip → Settings → Capabilities → Skills → Upload
```

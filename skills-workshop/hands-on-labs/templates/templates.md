# Lab Templates

## Skill Starter Template

```
your-skill/
├── SKILL.md
├── scripts/
│   └── validate.py
├── references/
│   └── guide.md
└── evals/
    └── evals.json
```

## SKILL.md Starter

```yaml
---
name: your-skill-name
description: What it does. Use when [triggers]. Do NOT use for [exclusions].
license: MIT
metadata:
  version: 1.0.0
---
```

## evals.json Starter

```json
{
  "skill_name": "your-skill-name",
  "evals": [
    {
      "id": 1,
      "prompt": "Your test prompt",
      "expected_output": "What should happen",
      "files": []
    }
  ]
}
```

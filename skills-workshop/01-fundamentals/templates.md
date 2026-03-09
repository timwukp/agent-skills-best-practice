# Chapter 1 Templates

## SKILL.md Starter Template

```yaml
---
name: your-skill-name
description: What this skill does and when to use it. Include trigger phrases users would say.
---
```

```markdown
# Skill Instructions

## Overview
Brief description of what this skill accomplishes.

## Workflow
1. Step one
2. Step two
3. Step three

## Important
- Key constraint or requirement
- Error handling note
```

---

## Full SKILL.md Template

```yaml
---
name: your-skill-name
description: Detailed description of what this skill does. Use when [trigger scenarios]. Supports [specific capabilities]. Do NOT use for [exclusions].
license: MIT
allowed-tools: "Bash(python:*)"
metadata:
  author: Your Name
  version: 1.0.0
  category: your-category
  tags: [tag1, tag2]
---
```

```markdown
# Skill Name

## Overview
What this skill does and why it exists.

## Workflow

### Step 1: Gather Information
- What to collect from the user
- Validation requirements

### Step 2: Execute
- Core actions to perform
- Tool usage instructions

### Step 3: Validate and Report
- How to verify success
- What to report back

## Error Handling
- If X fails, do Y
- If Z is missing, ask the user

## Examples

**Example 1:**
Input: "user request"
Output: Description of expected result
```

---

## Directory Structure Template

```
your-skill-name/
├── SKILL.md              # Required: Instructions + frontmatter
├── scripts/              # Optional: Executable code
│   └── validate.py
├── references/           # Optional: Documentation
│   └── guide.md
└── assets/               # Optional: Templates, icons
    └── template.txt
```

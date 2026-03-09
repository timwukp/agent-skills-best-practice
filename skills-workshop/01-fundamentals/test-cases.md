# Chapter 1 Test Cases

## Test Case 1.1: Valid Frontmatter Parsing

**Input SKILL.md:**
```yaml
---
name: test-skill
description: A test skill for validation
---
```
**Expected:** Valid, no errors

---

## Test Case 1.2: Missing Name Field

```yaml
---
description: A skill without a name
---
```
**Expected:** Error - "Missing 'name' in frontmatter"

---

## Test Case 1.3: Invalid Name Format

```yaml
---
name: My Skill
description: Has spaces in name
---
```
**Expected:** Error - "Name should be kebab-case"

---

## Test Case 1.4: Angle Brackets in Description

```yaml
---
name: bad-skill
description: Handles <user> input data
---
```
**Expected:** Error - "Description cannot contain angle brackets"

---

## Test Case 1.5: Description Too Long

```yaml
---
name: verbose-skill
description: [1025+ character string]
---
```
**Expected:** Error - "Description is too long. Maximum is 1024 characters"

---

## Test Case 1.6: Reserved Name Prefix

```yaml
---
name: claude-helper
description: A helper skill
---
```
**Expected:** Error - Reserved prefix "claude"

---

## Test Case 1.7: Full Valid Skill

```yaml
---
name: project-docs
description: Creates standardized project documentation including README, CONTRIBUTING, and LICENSE files. Use when setting up a new project or standardizing existing documentation.
license: MIT
allowed-tools: "Bash(python:*)"
metadata:
  author: Workshop Team
  version: 1.0.0
  category: documentation
---
```
**Expected:** Valid, no errors

---

## Validation Script

Use the quick_validate.py from skill-creator:
```bash
python scripts/quick_validate.py /path/to/your-skill/
```

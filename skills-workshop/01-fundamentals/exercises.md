# Chapter 1 Exercises: Fundamentals

## Exercise 1.1: Identify the Three Levels

Look at this skill structure and label each progressive disclosure level:

```
my-skill/
├── SKILL.md          # Level ?
│   ├── frontmatter   # Level ?
│   └── body          # Level ?
├── references/       # Level ?
└── scripts/          # Level ?
```

Write your answers before checking the solution at the bottom of this file.

---

## Exercise 1.2: Fix the Frontmatter

This frontmatter has **4 errors**. Find and fix all of them:

```yaml
name: My Cool Skill
description: "Does things
license: MIT
metadata:
  author: <Team Name>
```

Write your corrected version here:
```yaml
---

---
```

---

## Exercise 1.3: Naming Convention Practice

Convert these to valid kebab-case skill names:

| Input | Your Answer |
|-------|-------------|
| Sprint Planner | |
| AWS_Deploy_Tool | |
| myCodeReviewer | |
| --double-dash-- | |

---

## Exercise 1.4: Security Check

Which of these are allowed in SKILL.md? Mark ✅ or ❌ and explain why:

1. `description: Handles <user> data` → 
2. `name: claude-helper` → 
3. `allowed-tools: "Bash(python:*)"` → 
4. `metadata: { version: 1.0 }` → 
5. `name: anthropic-tool` → 

---

## Exercise 1.5: Build Your First Frontmatter

Create valid YAML frontmatter for a skill that:
- Generates API documentation from code comments
- Should trigger when users ask about API docs
- Uses Python scripts
- Is MIT licensed

```yaml
---
name: ___
description: ___
license: ___
allowed-tools: ___
metadata:
  version: ___
  category: ___
---
```

---

---

## Solutions (Don't peek until you've tried!)

<details>
<summary>Exercise 1.1 Solution</summary>

- Frontmatter = Level 1 (always loaded in system prompt)
- Body = Level 2 (loaded when skill is triggered)
- references/ and scripts/ = Level 3 (loaded on demand as needed)

</details>

<details>
<summary>Exercise 1.2 Solution</summary>

**Errors found:**
1. Missing `---` delimiters around frontmatter
2. Name has spaces and capitals → should be `my-cool-skill`
3. Unclosed quote on description
4. Angle brackets `<Team Name>` are forbidden

**Corrected:**
```yaml
---
name: my-cool-skill
description: Does things for project management workflows
license: MIT
metadata:
  author: Team Name
---
```

</details>

<details>
<summary>Exercise 1.3 Solution</summary>

| Input | Valid Name |
|-------|-----------|
| Sprint Planner | `sprint-planner` |
| AWS_Deploy_Tool | `aws-deploy-tool` |
| myCodeReviewer | `my-code-reviewer` |
| --double-dash-- | `double-dash` |

</details>

<details>
<summary>Exercise 1.4 Solution</summary>

1. ❌ — Angle brackets `<>` are forbidden (security restriction)
2. ❌ — "claude" prefix is reserved
3. ✅ — Valid allowed-tools syntax
4. ✅ — Valid YAML metadata
5. ❌ — "anthropic" prefix is reserved

</details>

<details>
<summary>Exercise 1.5 Solution (example)</summary>

```yaml
---
name: api-doc-generator
description: Generates API documentation from code comments and docstrings. Use when asked to create API docs, generate endpoint documentation, or document REST APIs. Supports Python, JavaScript, and TypeScript.
license: MIT
allowed-tools: "Bash(python:*)"
metadata:
  version: 1.0.0
  category: documentation
---
```

</details>

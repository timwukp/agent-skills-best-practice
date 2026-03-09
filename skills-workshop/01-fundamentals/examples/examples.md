# Chapter 1 Examples: Skill Structures

## Example 1: Minimal Skill

```
hello-world/
└── SKILL.md
```

```yaml
---
name: hello-world
description: Greets users and provides a friendly welcome message. Use when someone says hello or asks for a greeting.
---
```

```markdown
# Hello World Skill

When greeted, respond warmly and offer to help with their current task.
```

---

## Example 2: Skill with References

```
code-reviewer/
├── SKILL.md
└── references/
    ├── style-guide.md
    └── common-issues.md
```

```yaml
---
name: code-reviewer
description: Reviews code for quality, style, and common issues. Use when asked to review, audit, or check code quality. Supports Python, JavaScript, and TypeScript.
license: MIT
metadata:
  version: 1.0.0
  category: development
---
```

---

## Example 3: Skill with Scripts and MCP

```
sprint-planner/
├── SKILL.md
├── scripts/
│   └── validate_sprint.py
└── references/
    └── workflow.md
```

```yaml
---
name: sprint-planner
description: Plans and organizes sprints using Linear. Use when asked to plan a sprint, organize tasks, or manage project iterations. Requires Linear MCP connection.
allowed-tools: "Bash(python:*)"
metadata:
  version: 1.0.0
  mcp-server: linear
  category: project-management
---
```

---

## Example 4: Enterprise Skill with Full Metadata

```yaml
---
name: employee-onboarding
description: Automates employee onboarding workflows including account creation, access provisioning, and team setup. Use when onboarding new team members or setting up new hire accounts. Requires HR and IT system MCP connections.
license: MIT
allowed-tools: "Bash(python:*) Bash(node:*)"
compatibility: Designed for Kiro IDE and CLI. Works with Claude.ai and API with MCP support.
metadata:
  author: Platform Team
  version: 2.1.0
  category: enterprise
  tags: [hr, onboarding, automation]
---
```

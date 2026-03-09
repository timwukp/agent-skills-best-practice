# Lab Examples

## Lab 1 Solution: project-docs SKILL.md

```yaml
---
name: project-docs
description: Creates standardized project documentation including README, CONTRIBUTING, LICENSE, and .gitignore files. Use when setting up a new project, standardizing existing documentation, or asked to create project docs. Supports Python, JavaScript, TypeScript, Go, and Rust projects.
license: MIT
metadata:
  version: 1.0.0
  category: documentation
---
```

```markdown
# Project Documentation Generator

## Workflow

### Step 1: Gather Project Info
Ask the user for:
- Project name
- Tech stack (language/framework)
- License preference (default: MIT)

### Step 2: Create README.md
Include:
- Project title and description
- Installation instructions (stack-specific)
- Usage examples
- Contributing link
- License badge

### Step 3: Create CONTRIBUTING.md
Include:
- How to submit issues
- PR guidelines
- Code style requirements
- Development setup

### Step 4: Create LICENSE
Use the specified license type.

### Step 5: Create .gitignore
Use stack-appropriate ignore patterns.

### Step 6: Verify
Confirm all files created and report summary.

## Error Handling
- If tech stack unknown, ask for clarification
- If directory not empty, confirm before overwriting
```

## Lab 2 Solution: sprint-planner SKILL.md

```yaml
---
name: sprint-planner
description: Plans and organizes sprints by coordinating Linear for task management and Slack for team notifications. Use when asked to plan a sprint, organize backlog, estimate capacity, or set up iteration tasks. Requires Linear and Slack MCP connections.
license: MIT
allowed-tools: "Bash(python:*)"
metadata:
  version: 1.0.0
  mcp-server: linear, slack
  category: project-management
---
```

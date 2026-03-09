# Chapter 2 Examples: Planning and Design

## Example: Good vs Bad Descriptions

**Bad — Too generic:**
```
description: Helps with projects
```

**Bad — No trigger context:**
```
description: Manages tasks
```

**Good — Specific with triggers:**
```
description: Creates and manages sprint plans using Linear. Use when asked to plan a sprint, organize backlog items, or estimate team capacity. Requires Linear MCP connection.
```

**Good — With negative triggers:**
```
description: Advanced data analysis for CSV files. Use for statistical modeling, regression, clustering. Do NOT use for simple data exploration (use data-viz skill instead).
```

---

## Example: Use Case Definition

```
Use Case: Project Sprint Planning
Trigger: "help me plan this sprint" or "create sprint tasks"
Steps:
  1. Fetch current project status from Linear (via MCP)
  2. Analyze team velocity and capacity
  3. Suggest task prioritization
  4. Create tasks with labels and estimates
Result: Fully planned sprint with tasks created
```

---

## Example: Planning Worksheet (Completed)

```
Skill Name: api-doc-generator
Category: [x] Document

Use Case 1: Generate API docs from code comments
Use Case 2: Update existing docs when endpoints change

Success Criteria (Quantitative):
- Time saved: 2 hours per API update
- Error reduction: 90% fewer missing endpoints

Success Criteria (Qualitative):
- Consistent formatting across all APIs
- Always includes examples and error codes

Required Tools: Bash(python:*), file system access
Target Users: Backend developers
```

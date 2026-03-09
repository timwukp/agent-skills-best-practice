# Chapter 2: Planning and Design
## From Use Case to Working Skill

**Duration:** 90 minutes  
**Format:** Presentation + Hands-On Exercise

---

## Start with Use Cases

Before writing any code, identify **2-3 concrete use cases** your skill should enable.

### Good Use Case Definition

**Use Case:** Project Sprint Planning

**Trigger:** User says "help me plan this sprint" or "create sprint tasks"

**Steps:**
1. Fetch current project status from Linear (via MCP)
2. Analyze team velocity and capacity
3. Suggest task prioritization
4. Create tasks in Linear with proper labels and estimates

**Result:** Fully planned sprint with tasks created

---

## Ask Yourself

- What does a user want to accomplish?
- What multi-step workflows does this require?
- Which tools are needed (built-in or MCP)?
- What domain knowledge or best practices should be embedded?

---

## Common Skill Use Case Categories

### Category 1: Document & Asset Creation
**Used for:** Creating consistent, high-quality output

**Real Example:** `frontend-design` skill
```yaml
description: Create distinctive, production-grade frontend interfaces 
  with high design quality. Use when building web components, pages, 
  artifacts, posters, or applications.
```

**Key Techniques:**
- Embedded style guides and brand standards
- Template structures for consistent output
- Quality checklists before finalizing
- No external tools required - uses Claude's built-in capabilities

---

### Category 2: Workflow Automation
**Used for:** Multi-step processes with consistent methodology

**Real Example:** `skill-creator` skill
```yaml
description: Interactive guide for creating new skills. Walks the user 
  through use case definition, frontmatter generation, instruction 
  writing, and validation.
```

**Key Techniques:**
- Step-by-step workflow with validation gates
- Templates for common structures
- Built-in review and improvement suggestions
- Iterative refinement loops

---

### Category 3: MCP Enhancement
**Used for:** Workflow guidance to enhance MCP server tool access

**Real Example:** `sentry-code-review` skill (from Sentry)
```yaml
description: Automatically analyzes and fixes detected bugs in GitHub 
  Pull Requests using Sentry's error monitoring data via their MCP server.
```

**Key Techniques:**
- Coordinates multiple MCP calls in sequence
- Embeds domain expertise
- Provides context users would otherwise need to specify
- Error handling for common MCP issues

---

## Define Success Criteria

How will you know your skill is working?

### Quantitative Metrics

**Skill triggers on 90% of relevant queries**
- How to measure: Run 10-20 test queries
- Track automatic loading vs explicit invocation

**Completes workflow in X tool calls**
- How to measure: Compare with/without skill
- Count tool calls and total tokens consumed

**0 failed API calls per workflow**
- How to measure: Monitor MCP server logs
- Track retry rates and error codes

---

### Qualitative Metrics

**Users don't need to prompt Claude about next steps**
- How to assess: Note how often you need to redirect
- Ask beta users for feedback

**Workflows complete without user correction**
- How to assess: Run same request 3-5 times
- Compare outputs for consistency and quality

**Consistent results across sessions**
- How to assess: Can new user accomplish task on first try?

---

## Writing Effective Descriptions

The description field is **the most important part** of your skill.

### Structure
```
[What it does] + [When to use it] + [Key capabilities]
```

### Good Examples

```yaml
# ✅ Good - specific and actionable
description: Analyzes Figma design files and generates developer handoff 
  documentation. Use when user uploads .fig files, asks for "design specs", 
  "component documentation", or "design-to-code handoff".

# ✅ Good - includes trigger phrases
description: Manages Linear project workflows including sprint planning, 
  task creation, and status tracking. Use when user mentions "sprint", 
  "Linear tasks", "project planning", or asks to "create tickets".

# ✅ Good - clear value proposition
description: End-to-end customer onboarding workflow for PayFlow. Handles 
  account creation, payment setup, and subscription management. Use when 
  user says "onboard new customer", "set up subscription", or "create 
  PayFlow account".
```

---

### Bad Examples

```yaml
# ❌ Too vague
description: Helps with projects.

# ❌ Missing triggers
description: Creates sophisticated multi-page documentation systems.

# ❌ Too technical, no user triggers
description: Implements the Project entity model with hierarchical 
  relationships.
```

---

## Combat Undertriggering

Claude has a tendency to "undertrigger" skills - not use them when they'd be useful.

### Make Descriptions "Pushy"

```yaml
# Instead of:
description: How to build a simple fast dashboard to display internal data.

# Write:
description: How to build a simple fast dashboard to display internal data. 
  Make sure to use this skill whenever the user mentions dashboards, data 
  visualization, internal metrics, or wants to display any kind of company 
  data, even if they don't explicitly ask for a 'dashboard.'
```

---

## Choosing Your Approach

### Problem-First vs Tool-First

Think of it like Home Depot:

**Problem-First:**
- User: "I need to fix a kitchen cabinet"
- Employee points you to the right tools
- **In skills:** User describes outcomes; skill handles the tools

**Tool-First:**
- User: "I have this new drill"
- Employee shows you how to use it
- **In skills:** User has access; skill provides expertise

Most skills lean one direction. Know which fits your use case.

---

## Writing Main Instructions

### Recommended Structure

```markdown
---
name: your-skill
description: [What it does]. Use when [triggers].
---

# Your Skill Name

## Instructions

### Step 1: [First Major Step]
Clear explanation of what happens.

Example:
\`\`\`bash
python scripts/fetch_data.py --project-id PROJECT_ID
\`\`\`

Expected output: [describe what success looks like]

### Step 2: [Next Step]
...

## Examples

### Example 1: [common scenario]
User says: "Set up a new marketing campaign"

Actions:
1. Fetch existing campaigns via MCP
2. Create new campaign with provided parameters

Result: Campaign created with confirmation link

## Troubleshooting

### Error: [Common error message]
**Cause:** [Why it happens]  
**Solution:** [How to fix]
```

---

## Best Practices for Instructions

### Be Specific and Actionable

```markdown
✅ Good:
Run `python scripts/validate.py --input {filename}` to check data format.

If validation fails, common issues include:
- Missing required fields (add them to the CSV)
- Invalid date formats (use YYYY-MM-DD)

❌ Bad:
Validate the data before proceeding.
```

---

### Include Error Handling

```markdown
## Common Issues

### MCP Connection Failed
If you see "Connection refused":

1. Verify MCP server is running: Check Settings > Extensions
2. Confirm API key is valid
3. Try reconnecting: Settings > Extensions > [Your Service] > Reconnect
```

---

### Reference Bundled Resources Clearly

```markdown
Before writing queries, consult `references/api-patterns.md` for:
- Rate limiting guidance
- Pagination patterns
- Error codes and handling
```

---

## Use Progressive Disclosure

Keep SKILL.md focused on core instructions.

Move detailed documentation to `references/` and link to it.

```
your-skill/
├── SKILL.md                    # Core workflow (< 500 lines)
└── references/
    ├── api-guide.md           # Detailed API docs
    ├── examples/              # Example files
    └── troubleshooting.md     # Extended troubleshooting
```

---

## Planning Checklist

Before you start building:

- [ ] Identified 2-3 concrete use cases
- [ ] Defined success criteria (quantitative + qualitative)
- [ ] Chosen skill category (Document, Workflow, MCP Enhancement)
- [ ] Written description with WHAT + WHEN
- [ ] Identified tools needed (built-in or MCP)
- [ ] Planned folder structure
- [ ] Listed edge cases to handle
- [ ] Determined what goes in SKILL.md vs references/

---

## Hands-On Exercise

**Time:** 30 minutes

### Task
Plan your first skill using the worksheet in `exercises/exercises.md`

**👉 Open [exercises/exercises.md](exercises/exercises.md) now**

### Steps
1. Identify a workflow in your team (10 min)
2. Define 2-3 use cases (5 min)
3. Write a description with triggers (10 min)
4. Outline the instruction structure (5 min)

### Deliverable
A completed planning worksheet ready for implementation

---

## Key Takeaways

1. **Start with use cases** - Don't write code first
2. **Description determines triggering** - Include WHAT + WHEN
3. **Be "pushy" with triggers** - Combat undertriggering
4. **Define success criteria** - Know how you'll measure success
5. **Choose your approach** - Problem-first or tool-first
6. **Use progressive disclosure** - Keep SKILL.md focused

---

## Next: Testing and Iteration

In Chapter 3, you'll learn how to:
- Test triggering accuracy
- Validate functional correctness
- Measure performance improvements
- Iterate based on feedback

**Break:** 15 minutes

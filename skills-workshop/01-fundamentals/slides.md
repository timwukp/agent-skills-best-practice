# Chapter 1: Fundamentals
## Understanding Agent Skills Architecture

**Duration:** 60 minutes  
**Format:** Presentation + Discussion

---

## What Are Agent Skills?

### Definition
A skill is a **folder** containing instructions that teaches Claude/Kiro how to handle specific tasks or workflows.

```
my-skill/
├── SKILL.md          # Required: Instructions + metadata
├── scripts/          # Optional: Executable code
├── references/       # Optional: Documentation
└── assets/           # Optional: Templates, files
```

### Key Concept
Skills let you **teach once, benefit every time** instead of re-explaining your workflow in every conversation.

---

## Why Skills Matter

### Without Skills
- ❌ Repeat instructions every conversation
- ❌ Inconsistent results
- ❌ Users don't know what's possible
- ❌ 15+ back-and-forth messages
- ❌ Failed API calls requiring retry

### With Skills
- ✅ Automatic workflow execution
- ✅ Consistent, reliable results
- ✅ Pre-built workflows activate automatically
- ✅ 2-3 clarifying questions only
- ✅ Zero failed API calls

---

## Core Design Principle: Progressive Disclosure

Skills use a **three-level loading system** to minimize token usage while maintaining expertise:

### Level 1: YAML Frontmatter (Always Loaded)
- **~100 words** always in Claude's system prompt
- Provides just enough info for Claude to know **when** to use the skill
- Contains: `name` and `description`

```yaml
---
name: project-setup
description: Creates standardized project workspaces with templates. 
  Use when user says "set up project", "create workspace", or 
  "initialize new project".
---
```

### Level 2: SKILL.md Body (Loaded When Triggered)
- **<500 lines ideal**
- Full instructions and guidance
- Loaded only when Claude thinks skill is relevant

### Level 3: Linked Resources (Loaded As Needed)
- **Unlimited size**
- Scripts, references, assets
- Claude navigates and discovers only when needed

---

## Progressive Disclosure Example

```
aws-deployment/
├── SKILL.md                    # Level 2: Core instructions
│   ├── --- (frontmatter) ---  # Level 1: Always loaded
│   └── # Instructions...       # Level 2: Loaded when triggered
└── references/                 # Level 3: Loaded as needed
    ├── aws-guide.md
    ├── azure-guide.md
    └── gcp-guide.md
```

**Smart Loading:** Claude only reads the relevant cloud provider guide when needed.

---

## Core Design Principles

### 1. Progressive Disclosure
Minimize token usage, maximize expertise

### 2. Composability
- Claude can load **multiple skills simultaneously**
- Your skill should work alongside others
- Don't assume it's the only capability available

### 3. Portability
- Works identically across **Claude.ai, Kiro IDE, Kiro CLI, and API**
- Create once, use everywhere
- Cross-platform compatibility

---

## File Structure Requirements

### Critical Rules

#### SKILL.md Naming
```bash
✅ SKILL.md          # Correct - exact spelling, case-sensitive
❌ skill.md          # Wrong - lowercase
❌ SKILL.MD          # Wrong - wrong extension case
❌ Skill.md          # Wrong - mixed case
```

#### Skill Folder Naming
```bash
✅ project-setup     # Correct - kebab-case
❌ Project Setup     # Wrong - spaces
❌ project_setup     # Wrong - underscores
❌ ProjectSetup      # Wrong - capitals
```

#### No README.md Inside Skill Folder
```bash
my-skill/
├── SKILL.md        # ✅ Required
├── README.md       # ❌ Don't include inside skill
└── scripts/
```

**Note:** When distributing via GitHub, you'll have a repo-level README for humans, but not inside the skill folder itself.

---

## YAML Frontmatter: The Most Important Part

The frontmatter determines **whether Claude loads your skill**.

### Minimal Required Format
```yaml
---
name: your-skill-name
description: What it does. Use when user asks to [specific phrases].
---
```

### Required Fields

#### `name` (required)
- **kebab-case only**
- No spaces or capitals
- Should match folder name

```yaml
✅ name: project-setup
❌ name: Project Setup
❌ name: project_setup
```

#### `description` (required)
- **MUST include BOTH:**
  - What the skill does
  - When to use it (trigger conditions)
- Under 1024 characters
- No XML tags (`<` or `>`)
- Include specific tasks users might say
- Mention file types if relevant

```yaml
# Good - includes WHAT and WHEN
description: Analyzes Figma design files and generates developer 
  handoff documentation. Use when user uploads .fig files, asks for 
  "design specs", "component documentation", or "design-to-code handoff".

# Bad - too vague
description: Helps with projects.

# Bad - missing triggers
description: Creates sophisticated multi-page documentation systems.
```

---

## Optional Frontmatter Fields

### `license` (optional)
```yaml
license: MIT
license: Apache-2.0
```

### `compatibility` (optional)
- 1-500 characters
- Indicates environment requirements

```yaml
compatibility: Requires Python 3.8+, npm, and network access
```

### `metadata` (optional)
- Any custom key-value pairs

```yaml
metadata:
  author: Your Company
  version: 1.0.0
  mcp-server: your-mcp-server
  category: productivity
  tags: [project-management, automation]
```

---

## Security Restrictions

### Forbidden in Frontmatter
```yaml
❌ description: Use <script> tags    # No XML angle brackets
❌ name: claude-helper                # No "claude" or "anthropic" prefix
```

**Why?** Frontmatter appears in Claude's system prompt. Malicious content could inject instructions.

---

## Complete Frontmatter Example

```yaml
---
name: project-setup
description: Creates standardized project workspaces with folder 
  structure, README, and configuration files. Use when user says 
  "set up project", "create workspace", "initialize project", or 
  "start new project".
license: MIT
compatibility: Requires git and npm
metadata:
  author: Engineering Team
  version: 1.0.0
  category: productivity
  tags: [project-management, setup, automation]
---
```

---

## Kiro-Specific Features

### Skills in Kiro IDE
- Located in `~/.kiro/skills/`
- Automatically loaded when Kiro starts
- Can be enabled/disabled per workspace

### Skills in Kiro CLI
- Same `~/.kiro/skills/` directory
- Available in terminal sessions
- Supports MCP integration

### Agent Steering Files
- Located in `~/.kiro/steering/`
- Provides additional context to skills
- Can reference skills explicitly

---

## MCP Integration

### What is MCP?
**Model Context Protocol** - Connects Claude/Kiro to external services

### Skills + MCP Analogy
- **MCP** = Professional kitchen (tools, ingredients, equipment)
- **Skills** = Recipes (step-by-step instructions)

### How They Work Together

| MCP (Connectivity) | Skills (Knowledge) |
|---|---|
| Connects to your service | Teaches how to use it effectively |
| Provides real-time data access | Captures workflows and best practices |
| What Claude can do | How Claude should do it |

---

## Skills Categories

### Category 1: Document & Asset Creation
Creating consistent, high-quality output

**Example:** `frontend-design` skill
- Embedded style guides
- Template structures
- Quality checklists
- No external tools required

### Category 2: Workflow Automation
Multi-step processes with consistent methodology

**Example:** `skill-creator` skill
- Step-by-step workflow
- Validation gates
- Iterative refinement loops

### Category 3: MCP Enhancement
Workflow guidance for MCP servers

**Example:** `sentry-code-review` skill
- Coordinates multiple MCP calls
- Embeds domain expertise
- Error handling for MCP issues

---

## Key Takeaways

1. **Progressive Disclosure** is the foundation
   - Level 1: Frontmatter (always loaded)
   - Level 2: SKILL.md body (loaded when triggered)
   - Level 3: Resources (loaded as needed)

2. **Description field determines triggering**
   - Must include WHAT and WHEN
   - Include specific trigger phrases
   - Be "pushy" to combat undertriggering

3. **File structure matters**
   - SKILL.md (exact spelling)
   - kebab-case folder names
   - No README.md inside skill folder

4. **Skills are composable and portable**
   - Work alongside other skills
   - Cross-platform compatibility

---

## Discussion Questions

1. What workflows in your team would benefit from skills?
2. How would you describe those workflows to trigger correctly?
3. What external tools (MCP servers) do you currently use?
4. What documentation would you move to references/ vs keep in SKILL.md?

---

## Next: Hands-On Exercise

In the exercises file, you'll:
1. Examine example skills
2. Identify good vs bad descriptions
3. Plan your first skill structure

**Time:** 15 minutes

---

## Resources

- [Agent Skills Specification](https://agentskills.io/specification)
- [Complete Guide to Building Skills](../06-resources-references/slides.md)
- [Example Skills Repository](https://github.com/anthropics/skills)

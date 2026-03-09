# Chapter 4: Distribution and Sharing
## Getting Your Skills to Users

**Duration:** 45 minutes  
**Format:** Presentation + Demo

---

## Distribution Methods

### 1. Kiro IDE Installation
**Location:** `~/.kiro/skills/`

**Method 1: Manual Installation**
```bash
# Copy skill folder
cp -r my-skill ~/.kiro/skills/

# Restart Kiro IDE or reload skills
```

**Method 2: Zip Upload** (if supported)
```bash
# Zip the skill folder
cd my-skill
zip -r ../my-skill.zip .

# Upload via Kiro IDE Settings > Skills
```

---

### 2. Kiro CLI Installation
**Same location:** `~/.kiro/skills/`

Skills are automatically available in both IDE and CLI once installed.

```bash
# Verify installation
ls ~/.kiro/skills/

# Test in CLI
kiro chat
> "Use my-skill to..."
```

---

### 3. Organization-Level Deployment

**For Enterprise Teams:**
- Admins can deploy skills workspace-wide
- Automatic updates
- Centralized management
- Consistent experience across team

**Deployment via IAM Identity Center:**
- Configure in Kiro Administrator Console
- Assign to users/groups
- Monitor usage and adoption

---

## GitHub Distribution

### Recommended Approach

1. **Host on GitHub** with public repo
2. **Clear README** for human visitors (separate from SKILL.md)
3. **Example usage** with screenshots
4. **Installation instructions**

### Repository Structure
```
my-skill-repo/
├── README.md              # For GitHub visitors
├── LICENSE
├── .gitignore
├── my-skill/              # The actual skill folder
│   ├── SKILL.md
│   ├── scripts/
│   ├── references/
│   └── assets/
└── examples/
    └── usage-examples.md
```

---

## Installation Guide Template

```markdown
# Installing the [Your Service] Skill

## Prerequisites
- Kiro IDE or CLI installed
- [Any MCP servers or dependencies]

## Installation Steps

1. **Download the skill:**
   ```bash
   git clone https://github.com/yourcompany/your-skill
   cd your-skill
   ```

2. **Install in Kiro:**
   ```bash
   cp -r your-skill ~/.kiro/skills/
   ```

3. **Enable the skill:**
   - Restart Kiro IDE
   - Or reload skills in settings

4. **Test:**
   Ask Kiro: "Set up a new project in [Your Service]"

## Troubleshooting
- Ensure SKILL.md exists in the folder
- Check folder name is kebab-case
- Verify MCP server is connected (if applicable)
```

---

## Documentation Best Practices

### For Users (README.md)
- What the skill does
- When to use it
- Installation instructions
- Example usage
- Troubleshooting
- Support contact

### For Developers (SKILL.md)
- Clear instructions for Claude/Kiro
- Error handling
- Edge cases
- Examples
- References to additional resources

---

## Positioning Your Skill

### Focus on Outcomes, Not Features

✅ **Good:**
"The ProjectHub skill enables teams to set up complete project workspaces in seconds—including pages, databases, and templates—instead of spending 30 minutes on manual setup."

❌ **Bad:**
"The ProjectHub skill is a folder containing YAML frontmatter and Markdown instructions that calls our MCP server tools."

---

### Highlight MCP + Skills Story

"Our MCP server gives Claude access to your Linear projects. Our skills teach Claude your team's sprint planning workflow. Together, they enable AI-powered project management."

---

## Skills via API

For programmatic use cases (applications, agents, automated workflows):

### Key Capabilities
- `/v1/skills` endpoint for listing and managing skills
- Add skills to Messages API requests via `container.skills` parameter
- Version control via Claude Console
- Works with Claude Agent SDK

### When to Use API vs IDE/CLI

| Use Case | Best Surface |
|----------|--------------|
| End users interacting directly | Kiro IDE / CLI |
| Manual testing and iteration | Kiro IDE / CLI |
| Individual, ad-hoc workflows | Kiro IDE / CLI |
| Applications using programmatically | API |
| Production deployments at scale | API |
| Automated pipelines and agents | API |

---

## An Open Standard

Agent Skills is an open standard (like MCP).

**Benefits:**
- Portable across tools and platforms
- Same skill works in Claude.ai, Kiro, and other AI platforms
- Community-driven development
- Ecosystem collaboration

**Note:** Some skills may be optimized for specific platforms - indicate this in the `compatibility` field.

---

## Version Management

### In metadata
```yaml
metadata:
  version: 1.0.0
  author: Your Team
  last_updated: 2026-03-05
  changelog: |
    1.0.0 - Initial release
    0.9.0 - Beta version
```

### Semantic Versioning
- **Major (1.x.x):** Breaking changes
- **Minor (x.1.x):** New features, backward compatible
- **Patch (x.x.1):** Bug fixes

---

## Monitoring and Analytics

### Track Usage
- Skill trigger frequency
- Success/failure rates
- User feedback
- Common error patterns

### Iterate Based on Data
- Undertriggering → Improve description
- Overtriggering → Add negative triggers
- Errors → Improve error handling
- User feedback → Refine instructions

---

## Distribution Checklist

### Before Distribution
- [ ] Skill tested thoroughly
- [ ] README.md created for users
- [ ] Installation instructions clear
- [ ] Examples provided
- [ ] License specified
- [ ] Version number set
- [ ] Support contact provided

### After Distribution
- [ ] Monitor adoption
- [ ] Collect feedback
- [ ] Track issues
- [ ] Provide support
- [ ] Release updates
- [ ] Communicate changes

---

## Key Takeaways

1. **Multiple distribution methods:** IDE, CLI, organization-level, API
2. **GitHub is recommended** for open distribution
3. **Separate README.md** for humans, SKILL.md for AI
4. **Focus on outcomes** when positioning
5. **Version management** is important
6. **Monitor and iterate** based on usage data

---

## Next: Patterns and Troubleshooting

In Chapter 5, you'll learn:
- Common skill patterns
- Sequential workflows
- Multi-MCP coordination
- Troubleshooting techniques
- Debugging strategies

**Break:** 10 minutes

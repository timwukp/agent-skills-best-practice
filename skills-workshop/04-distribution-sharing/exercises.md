# Chapter 4 Exercises: Distribution and Sharing

## Exercise 4.1: Install to Kiro

Install your Lab 1 skill to Kiro:

```bash
# 1. Create the skills directory
mkdir -p ~/.kiro/skills/

# 2. Copy your skill
cp -r project-docs ~/.kiro/skills/project-docs

# 3. Verify
ls ~/.kiro/skills/project-docs/SKILL.md
```

Test it by asking Kiro: "Create project documentation for my app"

---

## Exercise 4.2: Prepare for GitHub Distribution

Create a README.md (for humans) alongside your SKILL.md (for AI):

```markdown
# Your Skill Name

## What it does
Brief human-readable description.

## Installation

### Kiro IDE/CLI
Copy to `~/.kiro/skills/your-skill-name/`

### Claude.ai
1. Zip the folder
2. Upload via Settings > Capabilities > Skills

## Usage
Example prompts that trigger this skill.

## Requirements
- List any MCP dependencies
- List any tool requirements
```

---

## Exercise 4.3: Version Your Skill

Update your skill's metadata with proper versioning:

```yaml
metadata:
  version: 1.0.0  # major.minor.patch
```

When do you bump each?
- **Patch (1.0.1):** ___
- **Minor (1.1.0):** ___
- **Major (2.0.0):** ___

---

## Exercise 4.4: Organization Deployment Checklist

- [ ] Skill validated with quick_validate.py
- [ ] Tested triggering (obvious + paraphrased)
- [ ] Functional tests pass
- [ ] README.md for humans created
- [ ] Version set in metadata
- [ ] License specified
- [ ] Security review completed
- [ ] Admin approval obtained

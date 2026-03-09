# Chapter 6: Resources and References
## Your Continued Learning Path

**Duration:** 15 minutes  
**Format:** Reference Guide + Q&A

---

## Official Documentation

### Anthropic Resources
- **Agent Skills Specification:** https://agentskills.io/specification
- **Skills Documentation:** https://docs.anthropic.com/claude/docs/agent-skills
- **Best Practices Guide:** https://docs.anthropic.com/claude/docs/agent-skills/best-practices
- **API Reference:** https://docs.anthropic.com/claude/reference
- **MCP Documentation:** https://modelcontextprotocol.io/

### Kiro Resources
- **Kiro Skills Documentation:** https://kiro.dev/docs/skills/
- **Kiro CLI Guide:** https://kiro.dev/docs/cli/
- **MCP Support:** https://kiro.dev/docs/mcp/
- **Privacy & Security:** https://kiro.dev/docs/privacy-and-security/

---

## Example Skills Repository

**GitHub:** https://github.com/anthropics/skills

**Contains:**
- 400+ production skills
- Document creation skills (PDF, DOCX, PPTX, XLSX)
- Workflow automation examples
- Partner skills (Asana, Figma, Sentry, Zapier, etc.)

**How to Use:**
```bash
git clone https://github.com/anthropics/skills
cd skills
# Browse skills/ directory for examples
```

---

## Tools and Utilities

### skill-creator Skill
- Built into Claude.ai and Kiro
- Generates skills from descriptions
- Reviews and provides recommendations
- **Use:** "Help me build a skill using skill-creator"

### Validation
- skill-creator can assess your skills
- **Ask:** "Review this skill and suggest improvements"

---

## Community Resources

### Claude Developers Discord
- General questions and discussions
- Share skills and get feedback
- Learn from other builders

### GitHub Issues
- **Repository:** anthropics/skills/issues
- Report bugs and request features
- **Include:** Skill name, error message, steps to reproduce

---

## Quick Reference Cheat Sheet

### File Structure
```
skill-name/
├── SKILL.md          # Required
├── scripts/          # Optional
├── references/       # Optional
└── assets/           # Optional
```

### Minimal SKILL.md
```yaml
---
name: skill-name
description: What it does. Use when [triggers].
---

# Instructions
[Your instructions here]
```

### Naming Rules
- **Folder:** kebab-case (my-skill)
- **File:** SKILL.md (exact spelling)
- **Name field:** kebab-case, no spaces

### Description Formula
```
[What it does] + [When to use it] + [Trigger phrases]
```

---

## Common Commands

### Kiro IDE
```bash
# Skills location
~/.kiro/skills/

# Install skill
cp -r my-skill ~/.kiro/skills/

# Restart to reload
```

### Kiro CLI
```bash
# Start chat
kiro chat

# Test skill
> "Use my-skill to..."
```

### Validation
```bash
# Check SKILL.md exists
ls ~/.kiro/skills/my-skill/SKILL.md

# Verify folder name
ls ~/.kiro/skills/ | grep my-skill
```

---

## Troubleshooting Quick Reference

| Issue | Solution |
|-------|----------|
| Skill won't upload | Check SKILL.md spelling (case-sensitive) |
| Invalid frontmatter | Verify YAML has `---` delimiters |
| Invalid name | Use kebab-case, no spaces/capitals |
| Doesn't trigger | Add more trigger phrases to description |
| Triggers too often | Add negative triggers, be more specific |
| MCP fails | Test MCP independently, check auth |
| Instructions ignored | Move critical info to top, be specific |

---

## Next Steps After Workshop

### Week 1: Build Your First Production Skill
- Identify a repeatable workflow in your team
- Create and test the skill
- Deploy to 2-3 beta users
- Collect initial feedback

### Week 2-3: Iterate Based on Feedback
- Monitor triggering accuracy
- Collect user feedback
- Refine description and instructions
- Fix any bugs or edge cases

### Week 4: Scale Deployment
- Deploy organization-wide
- Create user documentation
- Train team members
- Set up support process

### Ongoing: Build Skill Library
- Identify additional use cases
- Create skill packs for related workflows
- Share with community
- Contribute to open source

---

## Skill Development Checklist

### Planning
- [ ] Identified 2-3 concrete use cases
- [ ] Defined success criteria
- [ ] Chosen skill category
- [ ] Written description with triggers
- [ ] Planned folder structure

### Development
- [ ] Created SKILL.md with frontmatter
- [ ] Written clear instructions
- [ ] Added error handling
- [ ] Included examples
- [ ] Referenced resources appropriately

### Testing
- [ ] Tested triggering (obvious, paraphrased, negative)
- [ ] Verified functional correctness
- [ ] Measured performance improvement
- [ ] Collected user feedback
- [ ] Iterated based on results

### Distribution
- [ ] Created README.md for users
- [ ] Documented installation steps
- [ ] Specified license
- [ ] Set version number
- [ ] Provided support contact

---

## Workshop Evaluation

Please provide feedback on:
- Content clarity and depth
- Hands-on exercise difficulty
- Pacing and timing
- Materials quality
- Instructor effectiveness
- What you'll apply immediately
- What needs more coverage

---

## Getting Support

### For Workshop Questions
- Instructor contact: [Your contact]
- Workshop materials: [GitHub repo]

### For Kiro Support
- Documentation: https://kiro.dev/docs/
- Support: https://kiro.dev/support

### For Claude Support
- Documentation: https://docs.anthropic.com/
- Support: https://support.claude.com

### For Community Help
- Claude Developers Discord
- GitHub Issues: anthropics/skills

---

## Final Key Takeaways

1. **Progressive disclosure** is the foundation (3 levels)
2. **Description determines triggering** (WHAT + WHEN)
3. **Test systematically** (triggering, functional, performance)
4. **Iterate continuously** (skills are living documents)
5. **Use patterns** (sequential, multi-MCP, iterative, etc.)
6. **Troubleshoot systematically** (isolate, test, fix)
7. **Share and contribute** (open standard, community-driven)

---

## You're Ready!

You now have:
- ✅ Understanding of Agent Skills architecture
- ✅ Ability to plan and design skills
- ✅ Testing and iteration strategies
- ✅ Distribution and deployment knowledge
- ✅ Common patterns and troubleshooting techniques
- ✅ Resources for continued learning

**Go build amazing skills!**

---

## Q&A Session

**Time:** 30 minutes

Open floor for questions on:
- Any workshop content
- Specific use cases
- Technical challenges
- Best practices
- Next steps

---

## Thank You!

**Workshop Complete** 🎉

Stay in touch:
- Share your skills
- Contribute to the community
- Help others learn
- Keep building

**Happy skill building!**

# Agent Skills Building Workshop
## Best Practices and Training for AWS Kiro IDE and CLI

**Duration:** 4-6 hours (full day workshop)  
**Target Audience:** Developers, DevOps engineers, and technical teams building AI-powered workflows  
**Prerequisites:** Basic understanding of YAML, Markdown, and command-line tools

---

## Workshop Overview

This hands-on workshop teaches you how to build, test, and deploy Agent Skills for AWS Kiro IDE and CLI. You'll learn the complete lifecycle from planning to production deployment, with practical exercises using real-world examples.

### What You'll Learn
- Agent Skills architecture and progressive disclosure patterns
- SKILL.md format with YAML frontmatter
- Writing descriptions that trigger correctly
- Testing strategies (triggering, functional, performance)
- Distribution and deployment approaches
- Common patterns and troubleshooting techniques

### What You'll Build
By the end of this workshop, you'll have:
- 2-3 working skills deployed to your Kiro environment
- A testing framework for validating skills
- Understanding of best practices and anti-patterns
- Resources for continued learning

---

## Workshop Structure

### Chapter 1: Fundamentals (60 minutes)
- What are Agent Skills?
- Progressive disclosure architecture
- Core design principles
- File structure and naming conventions
- YAML frontmatter requirements

### Chapter 2: Planning and Design (90 minutes)
- Identifying use cases
- Defining success criteria
- Choosing your approach (problem-first vs tool-first)
- Writing effective descriptions
- Hands-on: Plan your first skill

### Chapter 3: Testing and Iteration (90 minutes)
- Triggering tests
- Functional tests
- Performance comparison
- Using skill-creator for iteration
- Hands-on: Build and test a skill

### Chapter 4: Distribution and Sharing (45 minutes)
- Installation methods (Kiro IDE, CLI, API)
- Organization-level deployment
- GitHub distribution patterns
- Documentation best practices

### Chapter 5: Patterns and Troubleshooting (60 minutes)
- Sequential workflow orchestration
- Multi-MCP coordination
- Iterative refinement patterns
- Common issues and solutions
- Hands-on: Debug problematic skills

### Chapter 6: Resources and References (15 minutes)
- Official documentation
- Community resources
- Getting support
- Next steps

---

## Prerequisites Setup

Before the workshop, ensure you have:

1. **AWS Kiro IDE or CLI installed**
   - Download from: https://kiro.dev
   - Authenticate with IAM Identity Center, Builder ID, or social login

2. **Skills directory configured**
   ```bash
   # Kiro skills are installed in:
   ~/.kiro/skills/
   ```

3. **Git installed** (for cloning example skills)
   ```bash
   git --version
   ```

4. **Text editor** (VS Code, Sublime, or your preference)

5. **Optional: MCP server** (for advanced exercises)

---

## Workshop Materials

All workshop materials are in this directory:

```
skills-workshop/
├── README.md                          # This file
├── INDEX.md                           # Quick navigation
├── 01-fundamentals/
│   ├── slides.md                      # Chapter slides
│   ├── exercises.md                   # Hands-on exercises
│   ├── examples.md                    # Skill structure examples
│   ├── templates.md                   # SKILL.md starter templates
│   └── test-cases.md                  # Validation test cases
├── 02-planning-design/
│   ├── slides.md
│   ├── exercises.md                   # Planning worksheet
│   ├── examples.md
│   ├── templates.md
│   └── test-cases.md
├── 03-testing-iteration/
│   ├── slides.md
│   ├── exercises.md                   # Testing exercises
│   ├── examples.md                    # evals.json examples
│   ├── templates.md                   # Test matrix templates
│   └── test-cases.md
├── 04-distribution-sharing/
│   ├── slides.md
│   ├── exercises.md
│   ├── examples.md
│   ├── templates.md
│   └── test-cases.md
├── 05-patterns-troubleshooting/
│   ├── slides.md
│   ├── exercises.md                   # Debug exercises
│   ├── examples.md                    # Pattern examples
│   ├── templates.md                   # Troubleshooting checklists
│   └── test-cases.md
├── 06-resources-references/
│   ├── slides.md
│   ├── exercises.md                   # Capstone exercise
│   ├── examples.md                    # Quick reference card
│   ├── templates.md
│   └── test-cases.md
├── hands-on-labs/
│   ├── LAB1-SIMPLE-SKILL.md          # Beginner (30 min)
│   ├── LAB2-MCP-INTEGRATION.md       # Intermediate (45 min)
│   ├── LAB3-ENTERPRISE-WORKFLOW.md   # Advanced (60 min)
│   ├── exercises.md                   # Bonus exercises
│   ├── examples.md                    # Lab solutions
│   ├── templates.md
│   └── test-cases.md
└── scripts/
    └── quick_validate.py              # Skill validation script
```

---

## Learning Objectives

By the end of this workshop, you will be able to:

✅ Explain the three-level progressive disclosure system  
✅ Create a SKILL.md file with proper YAML frontmatter  
✅ Write descriptions that trigger at the right moments  
✅ Design workflows with appropriate degrees of freedom  
✅ Test skills using triggering, functional, and performance tests  
✅ Deploy skills to Kiro IDE and CLI  
✅ Apply common patterns (sequential workflows, MCP coordination, iterative refinement)  
✅ Troubleshoot common issues (undertriggering, overtriggering, MCP failures)  
✅ Iterate on skills based on user feedback  

---

## Hands-On Labs

### Lab 1: Simple Document Creation Skill (30 min)
Build a skill that creates standardized project documentation with your team's templates.

**Skills practiced:**
- SKILL.md structure
- YAML frontmatter
- Basic instructions
- Testing triggering

### Lab 2: MCP Integration Skill (45 min)
Create a skill that orchestrates multiple MCP server calls for a workflow.

**Skills practiced:**
- MCP coordination
- Error handling
- Sequential workflows
- Validation

### Lab 3: Enterprise Workflow Skill (60 min)
Build a production-ready skill for your organization's specific workflow.

**Skills practiced:**
- Planning from requirements
- Security considerations
- Enterprise deployment
- Documentation

---

## Instructor Notes

### Timing Recommendations
- **Morning Session (3 hours):** Chapters 1-2 + Lab 1
- **Afternoon Session (3 hours):** Chapters 3-5 + Labs 2-3
- **Wrap-up (30 min):** Chapter 6 + Q&A

### Key Teaching Points
1. **Progressive disclosure is critical** - Emphasize the three-level system
2. **Description field determines triggering** - Spend extra time on this
3. **Iterate quickly** - Encourage rapid prototyping over perfection
4. **Real use cases matter** - Use participants' actual workflows
5. **Testing prevents issues** - Don't skip testing exercises

### Common Participant Questions
- "How do I know if my skill will trigger?" → Test with 10-20 queries
- "Can I use multiple skills together?" → Yes, skills are composable
- "What if my skill is too long?" → Use progressive disclosure, move content to references/
- "How do I debug MCP issues?" → Test MCP independently first
- "Can I share skills across my team?" → Yes, via organization-level deployment

---

## Additional Resources

### Official Documentation
- [Agent Skills Specification](https://agentskills.io/specification)
- [Kiro Skills Documentation](https://kiro.dev/docs/skills/)
- [Claude Skills Guide](https://docs.anthropic.com/claude/docs/agent-skills)
- [MCP Documentation](https://modelcontextprotocol.io/)

### Example Skills Repository
- [Anthropic Skills Repository](https://github.com/anthropics/skills)
- 400+ production skills including document creation, workflow automation, and partner integrations

### Community
- Claude Developers Discord
- GitHub Issues: anthropics/skills/issues

---

## Workshop Feedback

After completing the workshop, please provide feedback on:
- Content clarity and depth
- Hands-on exercise difficulty
- Pacing and timing
- Materials quality
- Instructor effectiveness

---

## Next Steps After Workshop

1. **Build your first production skill** (Week 1)
   - Identify a repeatable workflow in your team
   - Create and test the skill
   - Deploy to 2-3 beta users

2. **Iterate based on feedback** (Week 2-3)
   - Monitor triggering accuracy
   - Collect user feedback
   - Refine description and instructions

3. **Scale deployment** (Week 4)
   - Deploy organization-wide
   - Create documentation
   - Train team members

4. **Build skill library** (Ongoing)
   - Identify additional use cases
   - Create skill packs for related workflows
   - Share with community

---

## License

Workshop materials: MIT License  
Example skills: See individual skill licenses  
Kiro Service: AWS Service Terms (Section 50)

---

## Contact

For questions or support:
- Workshop issues: [Create GitHub issue]
- Kiro support: https://kiro.dev/support
- Claude support: https://support.claude.com

---

**Ready to get started? Proceed to Chapter 1: Fundamentals →**

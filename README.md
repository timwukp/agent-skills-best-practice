# Agentic Skills Best Practices

Best practices, examples, and training materials for building agent skills. Agent skills are folders of instructions, scripts, and resources that AI agents (Kiro IDE, Claude Code, Claude.ai) load dynamically to improve performance on specialized tasks.

This repo is designed for **AWS SAs and developers** learning to build skills for [Kiro IDE](https://kiro.dev), but the skills themselves are portable across all platforms that support the [Agent Skills specification](https://agentskills.io/specification).

## Quickstart

**New here?** Follow the [Kiro Skills Quickstart](QUICKSTART.md) to go from zero to a working skill in 5 minutes.

## What's Inside

- **Example Skills**: Production-quality examples in `skills/skills/` (creative, technical, enterprise, document creation)
- **Hello World**: Minimal working skill to verify your setup in `skills/skills/hello-world/`
- **Skills Workshop**: 6-hour hands-on training in `skills-workshop/`
- **Skill Template**: Starting point for new skills in `skills/template/`

## Repository Structure

```
.
├── QUICKSTART.md              # 5-minute quickstart guide
├── skills/                    # Skills collection (from Anthropic)
│   ├── skills/               # Individual skill folders
│   │   ├── hello-world/      # Minimal example (start here)
│   │   ├── skill-creator/    # Build skills with AI assistance
│   │   ├── frontend-design/  # Example: creative skill
│   │   ├── mcp-builder/      # Example: MCP integration
│   │   ├── docx/             # Document skills (source-available)
│   │   └── ...
│   ├── template/             # Blank skill template
│   └── README.md             # Skills collection docs
├── skills-workshop/           # Workshop training materials
│   ├── 01-fundamentals/      # Progressive disclosure, YAML, structure
│   ├── 02-planning-design/   # Use cases, descriptions, triggers
│   ├── 03-testing-iteration/ # Testing strategies
│   ├── 04-distribution-sharing/
│   ├── 05-patterns-troubleshooting/
│   ├── 06-resources-references/
│   └── hands-on-labs/        # 3 hands-on labs (beginner to advanced)
```

## Learning Path

| Step | What | Time |
|------|------|------|
| 1 | [Quickstart](QUICKSTART.md) — copy hello-world, see it trigger | 5 min |
| 2 | [Workshop Ch.1](skills-workshop/01-fundamentals/slides.md) — understand progressive disclosure | 60 min |
| 3 | [Lab 1](skills-workshop/hands-on-labs/LAB1-SIMPLE-SKILL.md) — build a real skill | 30 min |
| 4 | Browse `skills/skills/` — study production patterns | self-paced |
| 5 | [Full Workshop](skills-workshop/README.md) — complete training | 6 hours |

## Platform Compatibility

Skills built with this repo work across:

| Platform | Install Location | Docs |
|----------|-----------------|------|
| **Kiro IDE** | `~/.kiro/skills/` | [kiro.dev/docs/skills](https://kiro.dev/docs/skills/) |
| **Kiro CLI** | `~/.kiro/skills/` | [kiro.dev/docs/skills](https://kiro.dev/docs/skills/) |
| **Claude Code** | Via plugin marketplace | [skills/README.md](skills/README.md) |
| **Claude.ai** | Upload or built-in | [Claude Skills Guide](https://support.claude.com/en/articles/12512180-using-skills-in-claude) |
| **Claude API** | Via Skills API | [Skills API Quickstart](https://docs.claude.com/en/api/skills-guide) |

## Reference Documentation

- [Agent Skills Specification](https://agentskills.io/specification)
- [Kiro Skills Documentation](https://kiro.dev/docs/skills/)
- [Claude Skills Overview](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview)
- [Claude Skills Best Practices](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices)
- [Anthropic Skills Repository](https://github.com/anthropics/skills)

## Repository Guidelines

- No PDF, PPTX, DOCX, or other document files (gitignored)
- No PII or customer data
- No hardcoded credentials or secrets
- All code must be open source compliant (MIT License)

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

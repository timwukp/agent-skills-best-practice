**English** | [中文](README.zh-CN.md)

# Agentic Skills Best Practices

Best practices, examples, and training materials for building agent skills. Agent skills are folders of instructions, scripts, and resources that AI agents (Kiro IDE, Claude Code, Claude.ai) load dynamically to improve performance on specialized tasks.

This repo is designed for **AWS SAs and developers** learning to build skills for [Kiro IDE](https://kiro.dev), but the skills themselves are portable across all platforms that support the [Agent Skills specification](https://agentskills.io/specification).

## Quickstart

**New here?** Follow the [Kiro Skills Quickstart](QUICKSTART.md) to go from zero to a working skill in 5 minutes.

To install skills from this repo into Kiro in one step:

```bash
./install.sh hello-world api-design git-workflow   # or ./install.sh --all
```

## What's Inside

- **Example Skills**: Production-quality examples in `skills/skills/` (creative, technical, enterprise)
- **Hello World**: Minimal working skill to verify your setup in `skills/skills/hello-world/`
- **Skills Workshop**: 6-hour hands-on training in `skills-workshop/`
- **Skill Template**: Starting point for new skills in `skills/template/`
- **Software Engineering Skills**: 8 practical workflow skills covering code review, Git workflow, API design, Docker Compose generation, database schema design, CI/CD pipelines, Terraform modules, and Python project setup
- **Secure SDLC Skills**: 5 Scrum + DevSecOps role skills (threat modeling, security/user story writing, sprint planning with security debt, sprint security review)
- **FSI Compliance**: compliance checker mapping changes to PCI-DSS v4.0 and MAS TRM controls, with domain-organized reference files

> **Looking for the document skills (docx, pdf, pptx, xlsx)?** Those are Anthropic's source-available (not open source) production skills. They were removed from this repo to keep all content under open-source licenses — find them in the official [anthropics/skills](https://github.com/anthropics/skills) repository.

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
│   │   ├── api-design/       # Example: engineering workflow skill
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

## Kiro Features

### Steering Files

Kiro supports **steering files** in the `.kiro/steering/` directory at your project root. These are markdown files that define project-wide conventions, coding standards, and behavioral rules that Kiro follows whenever it works in your repository.

This repo uses `.kiro/steering/conventions.md` to enforce consistent formatting, naming, and structure across all contributions.

### Project-Level Skills

Skills can be installed at two levels:

| Scope | Location | Use Case |
|-------|----------|----------|
| **Project-level** | `.kiro/skills/` (checked into repo) | Shared with all contributors; project-specific workflows |
| **Global** | `~/.kiro/skills/` (user home) | Personal productivity skills; cross-project utilities |

Project-level skills are version-controlled with your codebase and automatically available to everyone who clones the repo.

### Kiro Web

[Kiro Web](https://kiro.dev) provides browser-based access with two interaction modes:

- **Vibe mode** - Conversational iteration where you and Kiro go back and forth refining outputs
- **Autonomous mode** - Kiro works independently on tasks, reporting back when complete

Both modes support skills for enhanced, domain-specific assistance.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on adding new skills, code standards, and the pull request process.

## Continuous Integration

GitHub Actions validates all skills on every push and pull request. The workflow checks SKILL.md frontmatter, required fields, and naming conventions. See `.github/workflows/validate-skills.yml` for details.

## Reference Documentation

- [Agent Skills Specification](https://agentskills.io/specification)
- [Kiro Skills Documentation](https://kiro.dev/docs/skills/)
- [Claude Skills Overview](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview)
- [Claude Skills Best Practices](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices)
- [Anthropic Skills Repository](https://github.com/anthropics/skills)

## Repository Guidelines

- No PDF, PPTX, DOCX, or other binary document files (gitignored)
- No PII or customer data
- No hardcoded credentials or secrets
- All content must be under an open-source license (MIT or Apache 2.0; see Licensing below)

## Licensing

This repository contains content under two open-source licenses:

| Content | License |
|---------|---------|
| Repository docs, workshop materials, engineering skills, tooling | [MIT](LICENSE) |
| Example skills imported from [anthropics/skills](https://github.com/anthropics/skills) (e.g. skill-creator, mcp-builder, canvas-design) | Apache 2.0 — see each skill's `LICENSE.txt` |

Anthropic's source-available document skills (docx, pdf, pptx, xlsx) are **not** included here; use the official [anthropics/skills](https://github.com/anthropics/skills) repository for those.

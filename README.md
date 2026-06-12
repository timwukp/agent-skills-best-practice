**English** | [中文](README.zh-CN.md)

# Agentic Skills Best Practices

Best practices, examples, and training materials for building agent skills. Agent skills are folders of instructions, scripts, and resources that AI agents load dynamically to improve performance on specialized tasks.

**Write once, run on any compatible agent.** Every skill in this repo follows the open [Agent Skills specification](https://agentskills.io/specification) using only standard fields — no platform-private extensions. The same skill folder works, unmodified, on any platform that implements the spec: Kiro (IDE and CLI), Claude Code, Claude.ai, the Claude API, and other compatible agents. Skills from this repo have been verified end-to-end on both Kiro and Claude Code (see [TESTING.md](TESTING.md)).

This repo is designed for **AWS SAs and developers** learning to build skills with [Kiro](https://kiro.dev) as the primary environment, but nothing here locks you in — the instruction-only skills are fully portable, and the few skills that bundle executable `scripts/` additionally require a platform that permits code execution and their listed dependencies.

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
- **Cloud Architecture**: AWS Well-Architected review skill with per-pillar reference files (security, reliability, cost, performance, operations, sustainability)
- **AI Adoption Skills**: code-standards-adopter (make AI-written code match your team's style) and legacy-code-testing (characterization tests before refactoring)

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

Skills in this repo are **portable by construction**: they use only the standard fields of the [Agent Skills specification](https://agentskills.io/specification) (`name`, `description`, `license`, `metadata`) and no platform-private extensions. Any agent that implements the spec can load them. Platforms verified or documented:

| Platform | Install Location | Docs |
|----------|-----------------|------|
| **Kiro IDE** | `~/.kiro/skills/` (global) or `.kiro/skills/` (workspace) | [kiro.dev/docs/skills](https://kiro.dev/docs/skills/) |
| **Kiro CLI** | `~/.kiro/skills/` | [kiro.dev/docs/skills](https://kiro.dev/docs/skills/) |
| **Claude Code** | `~/.claude/skills/` or via plugin marketplace | [skills/README.md](skills/README.md) — verified end-to-end, see [TESTING.md](TESTING.md) |
| **Claude.ai** | Upload as custom skill | [Claude Skills Guide](https://support.claude.com/en/articles/12512180-using-skills-in-claude) |
| **Claude API** | Via Skills API | [Skills API Quickstart](https://docs.claude.com/en/api/skills-guide) |
| **Other spec-compatible agents** | Per platform | [agentskills.io](https://agentskills.io/specification) |

Portability notes:

- **Instruction-only skills** (the Secure SDLC, FSI Compliance, Cloud Architecture, and most engineering skills) are fully portable — they are plain markdown and need nothing from the host beyond spec support.
- **Skills bundling executable `scripts/`** (e.g. test generators, webapp-testing) additionally require a platform that permits code execution and the dependencies each skill declares.
- Activation behavior can differ slightly per platform (each agent decides when a description matches); the trigger phrasing in our skill descriptions is tested on Claude Code and follows Kiro's guidance.

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

## Testing

Skills are tested in four layers — static spec validation, blind trigger routing, independently graded task execution, and real-environment verification on Claude Code. See [TESTING.md](TESTING.md) for the methodology and recorded results.

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

# Agentic Skills Best Practices

Best practices, documentation, and examples for building agent skills for Claude. Agent skills are folders of instructions, scripts, and resources that Claude loads dynamically to improve performance on specialized tasks.

## What's Inside

- **Example Skills**: Demonstrations of creative, technical, and enterprise capabilities in `skills/skills/`
- **Document Skills**: Source-available document creation skills (DOCX, PDF, PPTX, XLSX) that power Claude's document capabilities
- **Skills Workshop**: Hands-on training materials for building agent skills in `skills-workshop/`
- **Specifications**: Agent Skills specification and templates in `skills/spec/`

## Repository Structure

```
.
├── skills/                    # Main skills directory
│   ├── skills/               # Individual skill folders
│   ├── spec/                 # Agent Skills specification
│   ├── template/             # Skill template
│   └── README.md             # Detailed skills documentation
├── skills-workshop/           # Workshop training materials
│   ├── 01-fundamentals/
│   ├── 02-planning-design/
│   ├── ...
│   └── hands-on-labs/
└── README.md                  # This file
```

## Getting Started

1. **Explore Skills**: Browse the `skills/skills/` directory to see example implementations
2. **Read Documentation**: See reference links below for specifications and guides
3. **Try the Workshop**: Work through `skills-workshop/` for hands-on training
4. **Create Skills**: Use `skills/template/` as a starting point

For detailed information, see:
- [skills/README.md](skills/README.md) - Comprehensive skills documentation
- [skills-workshop/README.md](skills-workshop/README.md) - Workshop training guide
- [skills/spec/agent-skills-spec.md](skills/spec/agent-skills-spec.md) - Agent Skills specification

## Reference Documentation

- [Agent Skills Specification](https://agentskills.io/specification) - The AgentSkills.io spec
- [Agent Skills Home](https://agentskills.io/home) - AgentSkills.io home page
- [Claude Skills Overview](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview) - Overview documentation
- [Claude Skills Quickstart](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/quickstart) - Quickstart guide
- [Claude Skills Best Practices](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices) - Best practices guide
- [Claude Skills Enterprise](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/enterprise) - Enterprise guide
- [Kiro Skills Documentation](https://kiro.dev/docs/skills/) - Kiro skills docs

## Repository Guidelines

This repository follows strict guidelines:
- No PDF, PPTX, DOCX, or other document files (gitignored)
- No PII or customer data
- No hardcoded credentials or secrets
- All code must be open source compliant (MIT License)

## Technology

- Node.js with npm (minimal dependencies)
- Python with venv (for Python-based tooling)
- Primary dependency: `pptxgenjs` for PowerPoint generation

Install dependencies:
```bash
npm install
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

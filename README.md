# Agentic Skills Best Practices

This repository contains best practices, documentation, and examples for building agent skills for Claude. Agent skills are folders of instructions, scripts, and resources that Claude loads dynamically to improve performance on specialized tasks.

## What's Inside

- **Example Skills**: Demonstrations of creative, technical, and enterprise capabilities in `skills/skills/`
- **Document Skills**: Source-available document creation skills (DOCX, PDF, PPTX, XLSX) that power Claude's document capabilities
- **Specifications**: Agent Skills specification and templates
- **Best Practices**: Documentation and guides for skill development
- **Steering Documents**: AI assistant guidance in `.kiro/steering/` for working with this codebase

## Repository Structure

```
.
├── skills/                    # Main skills directory
│   ├── skills/               # Individual skill folders
│   │   ├── frontend-design/
│   │   ├── claude-api/
│   │   ├── docx/            # Document creation skills
│   │   └── ...
│   └── README.md            # Detailed skills documentation
├── .kiro/
│   └── steering/            # AI assistant guidance documents
├── agentskills-*.md         # Specification and best practices
└── README.md                # This file
```

## Getting Started

1. **Explore Skills**: Browse the `skills/skills/` directory to see example implementations
2. **Read Documentation**: Check the markdown files in the root for specifications and guides
3. **Review Steering**: See `.kiro/steering/` for project conventions and structure
4. **Create Skills**: Use the skill template pattern - a folder with `SKILL.md` containing YAML frontmatter and instructions

For detailed information, see:
- [skills/README.md](skills/README.md) - Comprehensive skills documentation
- [agentskills-specification.md](agentskills-specification.md) - Agent Skills specification
- [.kiro/steering/](.kiro/steering/) - Project conventions and guidance

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

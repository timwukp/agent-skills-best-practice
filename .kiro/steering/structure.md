---
inclusion: auto
---

# Project Structure

## Root Directory

- Documentation files: Various markdown files covering best practices, specifications, and guides
- `LICENSE`: MIT License for the project
- `package.json`: Node.js dependencies (minimal - only pptxgenjs)
- `.gitignore`: Comprehensive ignore rules for documents, system files, dependencies, and build outputs

## Skills Directory (`skills/`)

The main content of the repository, organized as:

```
skills/
├── .claude-plugin/
│   └── marketplace.json          # Claude Code plugin marketplace configuration
├── README.md                      # Skills overview and usage instructions
├── THIRD_PARTY_NOTICES.md        # License attributions
└── skills/                        # Individual skill folders
    ├── algorithmic-art/
    ├── brand-guidelines/
    ├── canvas-design/
    ├── claude-api/
    ├── doc-coauthoring/
    ├── docx/                      # Document creation skills (source-available)
    ├── frontend-design/
    ├── internal-comms/
    ├── mcp-builder/
    ├── pdf/                       # Document creation skills (source-available)
    ├── pptx/                      # Document creation skills (source-available)
    ├── skill-creator/
    ├── slack-gif-creator/
    ├── theme-factory/
    ├── web-artifacts-builder/
    ├── webapp-testing/
    └── xlsx/                      # Document creation skills (source-available)
```

## Skill Folder Structure

Each skill folder contains:
- `SKILL.md`: Main skill file with YAML frontmatter and instructions
- `LICENSE.txt`: License information (Apache 2.0 for open source skills)
- Additional resources: templates, fonts, examples, or supporting files as needed

Example skill structure:
```
skills/skills/example-skill/
├── SKILL.md                       # Required: skill definition
├── LICENSE.txt                    # Required: license information
├── templates/                     # Optional: template files
└── resources/                     # Optional: supporting assets
```

## SKILL.md Format

Every skill must have a `SKILL.md` file with:
1. YAML frontmatter with required fields:
   - `name`: Unique identifier (lowercase, hyphens for spaces)
   - `description`: Complete description of what the skill does and when to use it
   - `license`: License reference (optional)
2. Markdown content with instructions, examples, and guidelines

## Kiro Configuration (`.kiro/`)

- `.kiro/hooks/`: Agent hooks for automated workflows
- `.kiro/steering/`: Steering documents for AI assistant guidance

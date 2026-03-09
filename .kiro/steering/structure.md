---
inclusion: auto
---

# Project Structure

## Root Directory

- `README.md`: Project overview, learning path, and platform compatibility
- `QUICKSTART.md`: 5-minute quickstart guide for Kiro IDE
- `LICENSE`: MIT License for the project
- `.gitignore`: Ignore rules for documents, system files, dependencies, and build outputs

## Skills Directory (`skills/`)

The main content of the repository, organized as:

```
skills/
├── .claude-plugin/
│   └── marketplace.json          # Claude Code plugin marketplace configuration
├── README.md                      # Skills overview and usage instructions
├── THIRD_PARTY_NOTICES.md        # License attributions
├── spec/
│   └── agent-skills-spec.md      # Quick reference for the Agent Skills spec
├── template/
│   └── SKILL.md                  # Blank skill template
└── skills/                        # Individual skill folders
    ├── hello-world/               # Minimal example skill (start here)
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

## Workshop Directory (`skills-workshop/`)

Training materials for building skills:

```
skills-workshop/
├── README.md                      # Workshop overview (6 hours)
├── INDEX.md                       # Quick navigation
├── 01-fundamentals/               # Chapter slides + exercises/examples/templates/test-cases
├── 02-planning-design/
├── 03-testing-iteration/
├── 04-distribution-sharing/
├── 05-patterns-troubleshooting/
├── 06-resources-references/
├── hands-on-labs/                 # 3 labs (beginner to advanced)
└── scripts/
    └── quick_validate.py          # Skill validation script
```

## Skill Folder Structure

Each skill folder contains:
- `SKILL.md`: Main skill file with YAML frontmatter and instructions
- `LICENSE.txt`: License information (Apache 2.0 for open source skills)
- Additional resources: templates, scripts, references as needed

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

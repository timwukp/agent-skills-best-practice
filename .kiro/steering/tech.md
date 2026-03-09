---
inclusion: auto
---

# Technology Stack

## Dependencies

- Node.js with npm package manager
- Python with venv for Python-based tooling
- Primary dependency: `pptxgenjs` (v4.0.1) for PowerPoint generation

## Project Structure

This is primarily a documentation and example repository with minimal build requirements. The main technical components are:

- Markdown documentation files
- JavaScript utilities (e.g., `create-kiro-skills-presentation.js`)
- Skill folders containing SKILL.md files with YAML frontmatter

## Common Commands

```bash
# Install dependencies
npm install

# Python virtual environment (if needed)
python -m venv .venv
source .venv/bin/activate  # macOS/Linux
```

## File Restrictions

The repository enforces strict guidelines:
- NO document files: PDF, PPTX, DOCX, XLS, etc. (gitignored)
- NO PII or customer data
- NO hardcoded credentials or secrets
- All code must be open source compliant (MIT License)

## Development Environment

- IDE files (.vscode, .idea) are gitignored
- System files (.DS_Store, Thumbs.db) are gitignored
- Build outputs (dist/, build/, *.min.js) are gitignored
- Environment variables (.env files) are gitignored

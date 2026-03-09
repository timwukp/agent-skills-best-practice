---
inclusion: auto
---

# Technology Stack

## Dependencies

- Python (for office scripts and validation tooling in document skills)
- Node.js `pptxgenjs` (for PPTX skill only — installed per-skill, not at repo level)

## Project Structure

This is primarily a documentation and example repository with minimal build requirements. The main technical components are:

- Markdown documentation and training materials
- Skill folders containing SKILL.md files with YAML frontmatter
- Python scripts for document validation and office file manipulation
- Font assets for canvas-design skill

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
- Dependencies (node_modules/, .venv/) are gitignored

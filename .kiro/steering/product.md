---
inclusion: auto
---

# Product Overview

This repository contains best practices, documentation, and examples for building agent skills for Claude. Agent skills are folders of instructions, scripts, and resources that Claude loads dynamically to improve performance on specialized tasks.

The repository includes:
- Example skills demonstrating creative, technical, and enterprise capabilities
- Document creation skills (DOCX, PDF, PPTX, XLSX) that power Claude's document capabilities
- Agent Skills specification and templates
- Best practices documentation for skill development

Skills teach Claude how to complete specific tasks in a repeatable way, whether creating documents with brand guidelines, analyzing data using specific workflows, or automating tasks.

## Key Principles

- Skills are self-contained folders with a `SKILL.md` file containing YAML frontmatter and instructions
- Each skill should have a clear, specific purpose and activation criteria
- Skills range from simple instruction sets to complex workflows with templates and resources
- All code must be open source compliant (MIT License for most skills)

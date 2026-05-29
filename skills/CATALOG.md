# Skills Catalog

All available skills organized by category. Each skill lives in `skills/skills/<name>/` with a `SKILL.md` defining its behavior.

---

## Getting Started

| Skill | Description |
|-------|-------------|
| [hello-world](skills/hello-world/) | A minimal example skill that greets users and explains how skills work. Use when user says "hello world skill", "test my skills setup", or "show me how skills work". |

## Creative & Design

| Skill | Description |
|-------|-------------|
| [algorithmic-art](skills/algorithmic-art/) | Creating algorithmic art using p5.js with seeded randomness and interactive parameter exploration. Use for generative art, flow fields, or particle systems. |
| [brand-guidelines](skills/brand-guidelines/) | Applies Anthropic's official brand colors and typography to artifacts that benefit from Anthropic's look-and-feel. |
| [canvas-design](skills/canvas-design/) | Create beautiful visual art in .png and .pdf documents using design philosophy. Use for posters, art, designs, or other static pieces. |
| [frontend-design](skills/frontend-design/) | Create distinctive, production-grade frontend interfaces with high design quality. Use for web components, pages, dashboards, or any web UI styling. |
| [theme-factory](skills/theme-factory/) | Toolkit for styling artifacts with a theme. Includes 10 pre-set themes with colors/fonts that can be applied to slides, docs, HTML pages, and more. |
| [slack-gif-creator](skills/slack-gif-creator/) | Knowledge and utilities for creating animated GIFs optimized for Slack. Provides constraints, validation tools, and animation concepts. |

## Development & Technical

| Skill | Description |
|-------|-------------|
| [mcp-builder](skills/mcp-builder/) | Guide for creating high-quality MCP (Model Context Protocol) servers that enable LLMs to interact with external services through well-designed tools. |
| [java-unit-test-generator](skills/java-unit-test-generator/) | Generates JUnit unit tests for Java classes with loop prevention and incremental generation. |
| [rest-api-test-generator](skills/rest-api-test-generator/) | Generates REST API tests using RestAssured or MockMvc with loop prevention and incremental validation. |
| [selenium-ui-test-generator](skills/selenium-ui-test-generator/) | Generates Selenium WebDriver tests for React/Angular front-ends with strict loop prevention. |
| [webapp-testing](skills/webapp-testing/) | Toolkit for interacting with and testing local web applications using Playwright. Supports verifying frontend functionality and capturing screenshots. |
| [web-artifacts-builder](skills/web-artifacts-builder/) | Suite of tools for creating elaborate, multi-component claude.ai HTML artifacts using React, Tailwind CSS, and shadcn/ui. |
| [shared-test-runner](skills/shared-test-runner/) | Shared testing utility (provides `run_tests.py` used by other test-generation skills). |

## Software Engineering Workflow

| Skill | Description |
|-------|-------------|
| [code-review-assistant](skills/code-review-assistant/) | Performs code reviews analyzing security, performance, and maintainability. Applies SOLID principles and checks for anti-patterns with structured feedback. |
| [git-workflow](skills/git-workflow/) | Git workflow automation including conventional commit messages, branching strategies, merge conflict resolution, and changelog generation. |
| [api-design](skills/api-design/) | Designs RESTful and GraphQL APIs with OpenAPI spec generation, proper resource naming, pagination, filtering, error responses, and versioning. |
| [docker-compose-generator](skills/docker-compose-generator/) | Generates multi-stage Dockerfiles and docker-compose.yml files optimized for size, security, and common technology stacks. |
| [database-schema-design](skills/database-schema-design/) | Designs normalized database schemas with migration scripts, indexing strategies, and relationship best practices. |
| [cicd-pipeline](skills/cicd-pipeline/) | Generates CI/CD pipeline configurations for GitHub Actions, GitLab CI, and AWS CodePipeline with build, test, and deploy stages. |
| [terraform-module](skills/terraform-module/) | Creates Terraform modules following AWS Well-Architected Framework with proper variables, outputs, and module composition patterns. |
| [python-project-setup](skills/python-project-setup/) | Sets up Python projects with modern tooling including pyproject.toml, ruff, mypy, pytest, and pre-commit hooks. |

## Enterprise & Communication

| Skill | Description |
|-------|-------------|
| [internal-comms](skills/internal-comms/) | Resources to help write internal communications using company-preferred formats (status reports, leadership updates, newsletters, FAQs, incident reports). |
| [doc-coauthoring](skills/doc-coauthoring/) | Guide users through a structured workflow for co-authoring documentation, proposals, technical specs, and decision docs. |

## Document Skills

| Skill | Description |
|-------|-------------|
| [docx](skills/docx/) | Create, read, edit, and manipulate Word documents (.docx files). Handles formatting, tables of contents, page numbers, tracked changes, and more. |
| [pdf](skills/pdf/) | Read, extract, merge, split, rotate, watermark, create, fill forms, encrypt/decrypt, and OCR PDF files. |
| [pptx](skills/pptx/) | Create, read, edit, and manipulate PowerPoint presentations (.pptx files). Handles slide decks, templates, layouts, speaker notes, and comments. |
| [xlsx](skills/xlsx/) | Create, read, edit, and manipulate spreadsheet files (.xlsx, .xlsm, .csv, .tsv). Handles formulas, formatting, charting, and data cleaning. |

## Meta Skills

| Skill | Description |
|-------|-------------|
| [skill-creator](skills/skill-creator/) | Create new skills, modify existing skills, measure skill performance, run evals, and optimize descriptions for better triggering accuracy. |
| [kiro-project-setup](skills/kiro-project-setup/) | Helps users set up a complete Kiro project structure with steering files, skills directory, and proper configuration. |

## AI & API

| Skill | Description |
|-------|-------------|
| [claude-api](skills/claude-api/) | Build apps with the Claude API or Anthropic SDK. Use when code imports anthropic SDK packages or user asks to use Claude API. |

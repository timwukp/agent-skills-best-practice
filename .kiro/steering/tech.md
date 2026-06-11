---
inclusion: always
---

# Technology Stack

This is primarily a documentation and examples repository; the only runtime dependency is Python for tooling.

## Dependencies

- Python 3.10+ with `pyyaml` (see `requirements.txt`) — used by the skill validation script.
- Some individual skills declare their own dependencies inside their folders (e.g. `requirements.txt` in slack-gif-creator, mcp-builder).

## Common Commands

```bash
# Install tooling dependencies
pip install -r requirements.txt

# Validate one skill
python3 skills-workshop/scripts/quick_validate.py skills/skills/<name>

# Validate all skills (same loop CI runs)
for d in skills/skills/*/; do
  [ -f "${d}SKILL.md" ] && python3 skills-workshop/scripts/quick_validate.py "$d"
done

# Install skills into Kiro
./install.sh hello-world api-design   # or --all
```

## CI

GitHub Actions (`.github/workflows/validate-skills.yml`) runs `quick_validate.py` against every skill on push and pull request. Validation enforces the Agent Skills spec (frontmatter fields, kebab-case naming, name matches folder, length limits) and the 500-line SKILL.md body limit.

## Repository Rules

- No binary document files (PDF, PPTX, DOCX — gitignored).
- No PII, customer data, credentials, or secrets.
- New content is MIT; skills imported from anthropics/skills remain Apache 2.0.

---
inclusion: always
---

# Project Structure

```
.
├── README.md / README.zh-CN.md   # English and Chinese overviews
├── QUICKSTART.md                 # 5-minute Kiro quickstart
├── CONTRIBUTING.md               # How to add skills, evals convention, PR process
├── install.sh                    # Copies skills into ~/.kiro/skills/
├── requirements.txt              # Python tooling deps (pyyaml)
├── .github/workflows/            # CI: validate-skills.yml
├── .kiro/steering/               # This directory: product/tech/structure/conventions
├── skills/
│   ├── .claude-plugin/marketplace.json  # Claude Code plugin marketplace config
│   ├── README.md                 # Skills collection docs
│   ├── CATALOG.md                # All skills by category
│   ├── THIRD_PARTY_NOTICES.md    # License attributions
│   ├── shared/                   # Shared utilities (NOT skills — no SKILL.md)
│   │   └── test-runner/run_tests.py
│   ├── spec/                     # Pointer to agentskills.io specification
│   ├── template/SKILL.md         # Blank skill template
│   └── skills/                   # One folder per skill
│       └── <skill-name>/
│           ├── SKILL.md          # Required; frontmatter name == folder name
│           ├── evals/            # evals.json + trigger_evals.json (engineering skills)
│           ├── scripts/          # Optional executable code
│           ├── references/       # Optional docs loaded on demand
│           └── LICENSE.txt       # Per-skill license where applicable
└── skills-workshop/              # Training materials
    ├── 01-fundamentals ... 06-resources-references/
    │   └── slides.md, exercises.md, examples.md, templates.md, test-cases.md
    ├── hands-on-labs/            # LAB1-3
    ├── credit-estimation/        # Credit usage measurement materials
    └── scripts/quick_validate.py # Validation script used by CI
```

## Rules

- Everything under `skills/skills/` must be a valid skill (a folder with `SKILL.md`). Shared code that is not a skill belongs in `skills/shared/`.
- Skill folder name, frontmatter `name`, and the CATALOG.md entry must stay in sync.
- When adding a skill: create the folder, add it to `skills/CATALOG.md`, add it to the right plugin group in `skills/.claude-plugin/marketplace.json`, and include `evals/`.

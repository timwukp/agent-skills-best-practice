# Chapter 4 Examples

## Example: GitHub Repository Structure

```
your-skill/
├── README.md           # For humans
├── SKILL.md            # For AI
├── LICENSE
├── scripts/
│   └── validate.py
├── references/
│   └── guide.md
└── evals/
    └── evals.json
```

## Example: Kiro CLI Installation

```bash
# Install from local
cp -r ./my-skill ~/.kiro/skills/my-skill

# Verify installation
ls ~/.kiro/skills/my-skill/SKILL.md

# Test
kiro-cli chat
> "Use my-skill to do X"
```

## Example: API Usage

```python
# Skills via Claude API
response = client.messages.create(
    model="claude-sonnet-4-20250514",
    messages=[{"role": "user", "content": "Plan my sprint"}],
    container={"skills": ["sprint-planner"]}
)
```

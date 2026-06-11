# Eval Notes — fsi-compliance-checker

Real-environment finding (Claude Code 2.1.152 on Bedrock, June 2026): this skill competes with Claude Code's **built-in `security-review` skill** for queries phrased as "review this change ...". Observed behavior:

- Queries naming MAS TRM, or explicitly mentioning the skill, trigger correctly and load the right reference file.
- "Review this change for PCI-DSS compliance" can route to the built-in `security-review` instead.
- Short yes/no compliance questions may be answered directly from model knowledge without invoking any skill.

Mitigation for users: phrase requests as a compliance audit ("compliance check against PCI-DSS", "map this to MAS TRM controls") or invoke the skill explicitly. See TESTING.md at the repo root for the full test data.

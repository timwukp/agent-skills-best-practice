---
name: code-standards-adopter
description: >
  Infers a codebase's implicit coding conventions (naming, structure, imports, comments, error
  handling) by analyzing the existing code, then makes them explicit: generates linter/formatter
  configs that match current reality, a conventions document, and agent steering rules so AI-written
  code blends in. Use when adopting AI coding tools on an existing codebase or onboarding to an
  unfamiliar team style. Triggers on: "match our coding style", "infer our conventions", "generate
  lint config from this codebase", "make the AI write code like our team", "extract our code
  standards", "set up steering rules from existing code".
license: MIT
metadata:
  author: Community
  version: 1.0.0
  category: engineering-workflow
---

# Code Standards Adopter

Most teams' real conventions live in the code, not in a style guide. This skill reads the codebase, infers the conventions actually in force, and turns them into enforceable artifacts — so newly written code (human or AI) matches what's already there instead of fighting it.

The output is descriptive first, prescriptive second: capture what IS, flag inconsistencies, and let the team decide what SHOULD be.

## Process

1. **Sample the codebase.** Don't read everything. Pick 10-20 representative files: the most-recently-changed files (current style), the largest modules (dominant style), and one file per major directory. Note the languages and frameworks in play.
2. **Infer conventions per dimension** (see checklist below). For each, record: the dominant pattern, observed frequency (e.g. "camelCase in 18/20 files"), and exceptions worth flagging.
3. **Detect existing enforcement.** Check for linter/formatter configs (.eslintrc, ruff.toml, .editorconfig, checkstyle, prettier, gofmt assumptions), CI lint steps, and pre-commit hooks. Never generate a config that conflicts with one that exists — propose amendments instead.
4. **Generate the artifacts** the user needs (ask if unclear, default to all three):
   - **Conventions document** — concise markdown, one section per dimension, with real examples lifted from the codebase (anonymized if sensitive).
   - **Tool configs** — linter/formatter configuration matching the inferred style, with each non-default rule commented with its evidence ("18/20 files use single quotes").
   - **Agent steering rules** — a steering/context file for AI coding tools (Kiro `.kiro/steering/code-style.md`, CLAUDE.md section, or equivalent) containing only the conventions an agent would otherwise get wrong.
5. **Report inconsistencies separately.** Where the codebase splits (e.g. two naming styles 60/40), present both options with counts and let the team pick — do not silently impose the majority.

## Convention Checklist

| Dimension | What to look for |
|-----------|------------------|
| Naming | Case styles per identifier kind (files, classes, functions, constants, DB columns); abbreviation habits; test file naming |
| Structure | Directory layout logic; one-class-per-file or not; where interfaces/types live; co-location of tests |
| Imports | Ordering and grouping; absolute vs relative; barrel files; aliasing |
| Functions | Typical length; early-return vs nested; parameter object thresholds |
| Errors | Exceptions vs result types; error wrapping; logging at throw site or boundary; custom error classes |
| Comments | Density; docstring format and coverage; TODO conventions; license headers |
| Tests | Framework idioms; naming (`should_x` vs `test_x` vs `it('...')`); fixture patterns; assertion style |
| Formatting | Quotes, semicolons, line length, trailing commas — only where no formatter already decides |
| Git | Commit message style; branch naming (read recent history) |

## Steering Rules Quality Bar

The steering file is the highest-leverage artifact. Keep it under ~50 lines:

- Include only conventions a competent agent would plausibly get wrong (project-specific idioms, unusual choices, the chosen side of any inconsistency).
- Exclude anything a formatter/linter already enforces — tools enforce, steering informs.
- One example per rule, drawn from the actual codebase.
- State the why where it isn't obvious ("we use result types because exceptions cross a WASM boundary here").

## Guidelines

- Evidence over taste: every rule you emit must cite observed frequency. If you can't count it, don't claim it.
- Respect the formatter hierarchy: if prettier/gofmt/black is present, formatting dimensions are settled — don't relitigate them in the conventions doc.
- For polyglot repos, produce per-language sections; don't average conventions across languages.
- If the codebase is too small (<10 source files) or too inconsistent to infer anything, say so and recommend starting from a community standard instead, listing what was actually observed.

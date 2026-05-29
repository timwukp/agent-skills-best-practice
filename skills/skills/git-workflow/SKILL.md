---
name: git-workflow
description: >
  Helps with git workflows including conventional commit messages, branching strategies,
  merge conflict resolution, and changelog generation.
  Triggers on: "git commit message", "branching strategy", "resolve conflict", "generate changelog".
license: MIT
metadata:
  author: Community
  version: 1.0.0
  category: developer-workflow
---

# Git Workflow

## Instructions

### Step 1: Identify the Task

Determine which workflow the user needs:
1. **Commit message** - writing or improving a commit message
2. **Branching strategy** - choosing or implementing a branching model
3. **Conflict resolution** - resolving merge conflicts
4. **Changelog** - generating release notes from commit history

Ask clarifying questions only if the intent is ambiguous.

### Step 2: Conventional Commits

When writing commit messages, follow the Conventional Commits specification:

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

**Types (in order of frequency):**
- `feat` - new feature (correlates with MINOR in semver)
- `fix` - bug fix (correlates with PATCH in semver)
- `docs` - documentation only
- `style` - formatting, no code change
- `refactor` - neither fix nor feature
- `perf` - performance improvement
- `test` - adding or fixing tests
- `chore` - build process, tooling, dependencies
- `ci` - CI/CD configuration changes

**Rules:**
- Description is lowercase, no period at end, max 72 characters
- Body wraps at 72 characters, explains what and why (not how)
- Breaking changes: add `!` after type or `BREAKING CHANGE:` in footer

**Examples:**
```
feat(auth): add OAuth2 login with Google provider

Implements the OAuth2 authorization code flow for Google.
Stores tokens in encrypted session storage.

Closes #142
```

```
fix(api): prevent race condition in concurrent order creation

Added optimistic locking with version column check.
Returns 409 Conflict when version mismatch detected.
```

### Step 3: Branching Strategies

Recommend based on team size and release cadence:

**Trunk-Based Development** (recommended for most teams):
- Single `main` branch, always deployable
- Short-lived feature branches (max 2 days)
- Feature flags for incomplete work
- Best for: CI/CD, small teams, frequent releases

**GitHub Flow:**
- `main` branch + feature branches
- PR-based review before merge
- Deploy from `main` after merge
- Best for: open source, SaaS with continuous deployment

**GitFlow** (only for complex release schedules):
- `main`, `develop`, `feature/*`, `release/*`, `hotfix/*`
- Best for: packaged software, multiple supported versions
- Avoid unless you have a specific reason to use it

Provide the branching diagram and example commands for the chosen strategy.

### Step 4: Conflict Resolution

When helping resolve conflicts:

1. **Identify the conflict type:**
   - Content conflict (same lines changed)
   - Rename conflict (file renamed differently)
   - Delete/modify conflict (one branch deleted, other modified)

2. **Show both sides clearly:**
   ```
   <<<<<<< HEAD (your changes)
   [your code]
   =======
   [their code]
   >>>>>>> feature-branch (incoming changes)
   ```

3. **Suggest resolution strategy:**
   - Take ours (keep current branch)
   - Take theirs (accept incoming)
   - Merge both (combine changes)
   - Rewrite (neither version is correct)

4. **Provide the resolved code** and the commands:
   ```bash
   # After resolving
   git add <resolved-files>
   git commit  # or git rebase --continue
   ```

### Step 5: Changelog Generation

Generate changelogs from conventional commits:

```markdown
## [1.2.0] - 2024-01-15

### Added
- OAuth2 login with Google provider (#142)
- Rate limiting on public API endpoints (#156)

### Fixed
- Race condition in concurrent order creation (#163)
- Memory leak in WebSocket connection handler (#158)

### Changed
- Upgraded Node.js requirement to v18+ (BREAKING)
```

**Process:**
1. Parse commits since last tag: `git log v1.1.0..HEAD --oneline`
2. Group by type (feat=Added, fix=Fixed, refactor/perf=Changed)
3. Include PR/issue numbers
4. Highlight breaking changes prominently
5. Use Keep a Changelog format

## Example

User says: "Write a commit message for adding email validation to the signup form"

Response:
```
feat(signup): add email validation with DNS MX record check

Validates email format client-side and verifies MX records server-side.
Displays inline error message when validation fails.
Debounces server check by 500ms to reduce API calls.

Closes #89
```

## Guidelines

- Default to Conventional Commits format unless the project uses a different convention
- Keep commit descriptions under 72 characters
- Recommend trunk-based development unless the team has a specific need for GitFlow
- When resolving conflicts, always explain why the chosen resolution is correct
- For changelogs, include only user-facing changes unless generating internal release notes
- Never suggest force-pushing to shared branches without explicit warning

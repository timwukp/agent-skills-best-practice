---
name: code-review-assistant
description: >
  Analyzes code changes for security vulnerabilities, performance issues, and maintainability concerns.
  Provides structured feedback with SOLID principle checks and anti-pattern detection.
  Triggers on: "review this code", "code review", "check my PR", "review my changes".
license: MIT
metadata:
  author: Community
  version: 1.0.0
  category: code-quality
---

# Code Review Assistant

## Instructions

### Step 1: Gather Context

Before reviewing, determine:
1. What language and framework is the code written in?
2. Is this a PR diff, a single file, or a full module?
3. What is the review scope? (Security | Performance | Maintainability | All)

If reviewing a PR, ask for the diff or file list. If a single file, ask for the surrounding context (what calls it, what it calls).

### Step 2: Security Analysis

Check for these categories in order of severity:

**Critical:**
- SQL injection (string concatenation in queries)
- Command injection (unsanitized shell commands)
- Path traversal (user input in file paths without validation)
- Hardcoded secrets (API keys, passwords, tokens)

**High:**
- Missing authentication/authorization checks
- Insecure deserialization
- SSRF vulnerabilities (user-controlled URLs)
- Missing input validation on public endpoints

**Medium:**
- Missing rate limiting on public APIs
- Verbose error messages leaking internals
- Missing CSRF protection
- Insecure random number generation for security contexts

### Step 3: Performance Review

Look for:
1. **N+1 queries** - database calls inside loops
2. **Unbounded collections** - loading all records without pagination
3. **Missing indexes** - queries filtering on non-indexed columns
4. **Unnecessary allocations** - creating objects in hot paths
5. **Blocking I/O** - synchronous calls in async contexts
6. **Missing caching** - repeated expensive computations with same inputs

### Step 4: SOLID Principles Check

Evaluate each principle:

| Principle | Red Flag |
|-----------|----------|
| Single Responsibility | Class has multiple reasons to change |
| Open/Closed | Modifying existing code instead of extending |
| Liskov Substitution | Subclass breaks parent contract |
| Interface Segregation | Forcing implementation of unused methods |
| Dependency Inversion | High-level module depends on concrete class |

Only flag violations that cause real maintainability problems, not theoretical ones.

### Step 5: Anti-Pattern Detection

Check for:
- **God objects** - classes with more than 10 public methods or 300+ lines
- **Feature envy** - methods that use another class's data more than their own
- **Primitive obsession** - using strings/ints where a value object improves clarity
- **Long parameter lists** - functions with more than 4 parameters
- **Deep nesting** - more than 3 levels of indentation in conditionals

### Step 6: Produce Structured Feedback

Format findings as:

```markdown
## Code Review Summary

**Risk Level:** Critical | High | Medium | Low

### Findings

#### [Category] Finding Title
- **Location:** file:line
- **Severity:** Critical | High | Medium | Low
- **Issue:** What is wrong
- **Impact:** What could happen
- **Fix:** Concrete suggestion with code

### Positive Observations
- List things done well (always include at least one)

### Recommendations
1. Prioritized action items
```

**STOP after producing the summary.** Ask if the user wants deeper analysis on any specific finding.

## Example

User says: "Review this Python function"

```python
def get_user(user_id):
    query = f"SELECT * FROM users WHERE id = {user_id}"
    result = db.execute(query)
    return result
```

Response:
- **Critical: SQL Injection** at line 2 - string interpolation in SQL query
- **Medium: Overfetching** - SELECT * returns all columns
- **Fix:** Use parameterized queries: `db.execute("SELECT id, name, email FROM users WHERE id = ?", [user_id])`

## Guidelines

- Always start with security findings, then performance, then style
- Be specific with line numbers and concrete fix suggestions
- Do not nitpick formatting or style unless it impacts readability significantly
- Acknowledge good patterns alongside problems
- If the code is already good, say so briefly and suggest one area for further improvement
- Limit findings to the top 5 most impactful issues unless asked for exhaustive review
- Never suggest changes that alter business logic without flagging it as a behavioral change

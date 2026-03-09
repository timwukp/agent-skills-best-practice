# Chapter 3 Examples: Testing

## Example: evals.json

```json
{
  "skill_name": "project-docs",
  "evals": [
    {
      "id": 1,
      "prompt": "Create project documentation for a Python Flask API",
      "expected_output": "README.md, CONTRIBUTING.md, LICENSE created with Flask-specific content",
      "files": [],
      "expectations": [
        "README includes installation instructions",
        "README mentions Flask and Python",
        "CONTRIBUTING.md has PR guidelines",
        "LICENSE file is created"
      ]
    },
    {
      "id": 2,
      "prompt": "Set up docs for my React TypeScript project",
      "expected_output": "Documentation files with React/TS specific content",
      "files": [],
      "expectations": [
        "README includes npm/yarn commands",
        "README mentions React and TypeScript",
        "Component documentation section exists"
      ]
    }
  ]
}
```

---

## Example: Triggering Test Matrix

| # | Prompt | Expected | Actual | Pass? |
|---|--------|----------|--------|-------|
| 1 | "Create project docs" | Trigger | Trigger | ✅ |
| 2 | "Set up documentation for my repo" | Trigger | Trigger | ✅ |
| 3 | "Help me write a README" | Trigger | No trigger | ❌ |
| 4 | "What's the weather?" | No trigger | No trigger | ✅ |
| 5 | "Debug my Python code" | No trigger | Trigger | ❌ |

**Action:** Add "README" and "documentation" to description triggers. Add negative trigger for debugging.

---

## Example: Iteration Log

```
Iteration 1: Initial version
- Triggering: 60% (3/5 cases)
- Fix: Added more trigger phrases to description

Iteration 2: Improved description
- Triggering: 80% (4/5 cases)
- Functional: Missing LICENSE file
- Fix: Added explicit LICENSE step to instructions

Iteration 3: Added LICENSE step
- Triggering: 100% (5/5 cases)
- Functional: 100% pass
- Performance: 20% faster than manual
- Status: READY
```

# Chapter 3 Exercises: Testing and Iteration

## Exercise 3.1: Write Triggering Tests

For a skill with this description:
```
description: Creates database migration scripts for PostgreSQL. Use when asked to migrate, alter tables, or update database schemas.
```

Write 3 test prompts for each category:

**Should trigger:**
1. ___
2. ___
3. ___

**Should NOT trigger:**
1. ___
2. ___
3. ___

---

## Exercise 3.2: Create an evals.json

Write an evals.json for a documentation skill:

```json
{
  "skill_name": "project-docs",
  "evals": [
    {
      "id": 1,
      "prompt": "___",
      "expected_output": "___",
      "files": []
    },
    {
      "id": 2,
      "prompt": "___",
      "expected_output": "___",
      "files": []
    }
  ]
}
```

---

## Exercise 3.3: Diagnose the Problem

For each scenario, identify the issue and fix:

**Scenario A:** Skill never triggers
- Signal: ___
- Likely cause: ___
- Fix: ___

**Scenario B:** Skill triggers for unrelated queries
- Signal: ___
- Likely cause: ___
- Fix: ___

**Scenario C:** Skill triggers but produces wrong output
- Signal: ___
- Likely cause: ___
- Fix: ___

---

## Exercise 3.4: Iteration Practice

Your skill's test results show:
- Triggering: 2/3 obvious prompts work, 0/3 paraphrased
- Functional: Creates files but wrong format
- Performance: 40% slower than manual

Write your iteration plan:
1. Description change: ___
2. Instruction fix: ___
3. Performance improvement: ___

---

## Exercise 3.5: With-Skill vs Baseline Comparison

Run your skill against a baseline (no skill) and fill in:

| Metric | With Skill | Without Skill | Improvement |
|--------|-----------|---------------|-------------|
| Correct output | | | |
| Time to complete | | | |
| Steps taken | | | |
| Errors | | | |

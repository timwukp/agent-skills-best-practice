# Chapter 3 Templates

## Triggering Test Template

| # | Prompt | Expected | Actual | Pass? |
|---|--------|----------|--------|-------|
| 1 | [obvious trigger] | Trigger | | |
| 2 | [paraphrased trigger] | Trigger | | |
| 3 | [edge case trigger] | Trigger | | |
| 4 | [unrelated prompt] | No trigger | | |
| 5 | [similar but different] | No trigger | | |

## evals.json Template

```json
{
  "skill_name": "your-skill-name",
  "evals": [
    {
      "id": 1,
      "prompt": "Primary use case prompt",
      "expected_output": "Description of expected result",
      "files": [],
      "expectations": [
        "Expectation 1",
        "Expectation 2"
      ]
    }
  ]
}
```

## Iteration Log Template

```
Iteration #: ___
Date: ___
Changes Made: ___
Results:
  - Triggering: __/__ cases pass
  - Functional: __/__ expectations pass
  - Performance: ___
Next Steps: ___
```

## Comparison Template

| Metric | With Skill | Baseline | Delta |
|--------|-----------|----------|-------|
| Correct output | | | |
| Completeness | | | |
| Time | | | |
| Tool calls | | | |
| Errors | | | |

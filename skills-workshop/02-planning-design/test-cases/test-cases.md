# Chapter 2 Test Cases: Planning Validation

## Test Case 2.1: Description Triggers Correctly

**Prompt:** "Help me plan this sprint"
**Expected:** Sprint planner skill triggers
**Skill description:** "Plans and organizes sprints using Linear. Use when asked to plan a sprint, organize backlog items, or estimate team capacity."

---

## Test Case 2.2: Description Doesn't Over-trigger

**Prompt:** "What's the weather today?"
**Expected:** Sprint planner skill does NOT trigger

---

## Test Case 2.3: Paraphrased Trigger

**Prompt:** "I need to organize our next iteration's work items"
**Expected:** Sprint planner skill triggers (paraphrased version of sprint planning)

---

## Test Case 2.4: Negative Trigger Works

**Skill description:** "Advanced data analysis for CSV files. Do NOT use for simple data exploration."
**Prompt:** "Show me a quick chart of this data"
**Expected:** Skill does NOT trigger

---

## Test Case 2.5: Use Case Coverage

For your planned skill, verify each use case triggers:

| Use Case | Test Prompt | Triggers? |
|----------|-------------|-----------|
| UC1 | | [ ] Yes [ ] No |
| UC2 | | [ ] Yes [ ] No |
| UC3 | | [ ] Yes [ ] No |

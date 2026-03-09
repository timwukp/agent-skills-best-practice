# Chapter 3 Test Cases

## Test Case 3.1: Skill-Creator Validation

Run quick_validate.py against your skill:
```bash
python quick_validate.py /path/to/your-skill/
```
**Expected:** "Skill is valid!"

---

## Test Case 3.2: Triggering - Obvious Prompt

Ask: "When would you use the [skill-name] skill?"
**Expected:** Claude quotes the description back accurately

---

## Test Case 3.3: Triggering - Paraphrased

Rephrase your primary use case in 3 different ways.
**Expected:** Skill triggers for at least 2 of 3

---

## Test Case 3.4: Functional - Primary Use Case

Execute the skill's primary workflow end-to-end.
**Expected:** All output files created, correct format, no errors

---

## Test Case 3.5: Functional - Error Handling

Provide invalid input (missing required info).
**Expected:** Skill asks for clarification rather than failing silently

---

## Test Case 3.6: Performance - With vs Without

Run same task with and without skill.
**Expected:** With-skill produces better or equal results in less time

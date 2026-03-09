# Chapter 3: Testing and Iteration
## Ensuring Your Skill Works Reliably

**Duration:** 90 minutes  
**Format:** Presentation + Hands-On Lab

---

## Testing Approaches

Skills can be tested at varying levels of rigor:

- **Manual testing** in Claude.ai/Kiro - Fast iteration, no setup
- **Scripted testing** in Kiro CLI - Automate test cases
- **Programmatic testing** via API - Systematic evaluation suites

Choose based on your quality requirements and skill visibility.

---

## Pro Tip: Iterate on Single Task First

Most effective approach:
1. Iterate on ONE challenging task until Claude succeeds
2. Extract the winning approach into a skill
3. Expand to multiple test cases for coverage

This leverages Claude's in-context learning and provides faster signal.

---

## Three Testing Areas

### 1. Triggering Tests
**Goal:** Ensure skill loads at the right times

**Test Cases:**
- ✅ Triggers on obvious tasks
- ✅ Triggers on paraphrased requests
- ❌ Doesn't trigger on unrelated topics

**Example Test Suite:**
```
Should trigger:
- "Help me set up a new ProjectHub workspace"
- "I need to create a project in ProjectHub"
- "Initialize a ProjectHub project for Q4 planning"

Should NOT trigger:
- "What's the weather in San Francisco?"
- "Help me write Python code"
- "Create a spreadsheet" (unless ProjectHub handles sheets)
```

---

### 2. Functional Tests
**Goal:** Verify skill produces correct outputs

**Test Cases:**
- Valid outputs generated
- API calls succeed
- Error handling works
- Edge cases covered

**Example:**
```
Test: Create project with 5 tasks

Given: Project name "Q4 Planning", 5 task descriptions
When: Skill executes workflow
Then:
  - Project created in ProjectHub
  - 5 tasks created with correct properties
  - All tasks linked to project
  - No API errors
```

---

### 3. Performance Comparison
**Goal:** Prove skill improves results vs baseline

**Baseline Comparison:**

Without skill:
- User provides instructions each time
- 15 back-and-forth messages
- 3 failed API calls requiring retry
- 12,000 tokens consumed

With skill:
- Automatic workflow execution
- 2 clarifying questions only
- 0 failed API calls
- 6,000 tokens consumed

---

## Using skill-creator Skill

The `skill-creator` skill can help you build and iterate.

**Creating skills:**
- Generate from natural language descriptions
- Produce properly formatted SKILL.md
- Suggest trigger phrases and structure

**Reviewing skills:**
- Flag common issues
- Identify over/under-triggering risks
- Suggest test cases

**Iterative improvement:**
- Bring edge cases back to skill-creator
- "Use the issues identified to improve how the skill handles [edge case]"

**To use:** "Use the skill-creator skill to help me build a skill for [your use case]"

---

## Iteration Based on Feedback

Skills are living documents. Iterate based on signals:

### Undertriggering Signals
- Skill doesn't load when it should
- Users manually enabling it
- Support questions about when to use it

**Solution:** Add more detail and nuance to description - include keywords for technical terms

---

### Overtriggering Signals
- Skill loads for irrelevant queries
- Users disabling it
- Confusion about purpose

**Solution:** Add negative triggers, be more specific

**Example:**
```yaml
description: Advanced data analysis for CSV files. Use for statistical 
  modeling, regression, clustering. Do NOT use for simple data exploration 
  (use data-viz skill instead).
```

---

### Execution Issues
- Inconsistent results
- API call failures
- User corrections needed

**Solution:** Improve instructions, add error handling

---

## Testing in Kiro IDE

### Manual Testing
1. Enable your skill in Kiro IDE
2. Try various trigger phrases
3. Observe when skill loads
4. Check output quality
5. Note any errors or issues

### Location
```bash
~/.kiro/skills/your-skill/
```

---

## Testing in Kiro CLI

### CLI Testing
```bash
# Start Kiro CLI
kiro chat

# Try trigger phrases
> "Help me set up a new project"
> "Create a workspace for Q4 planning"
> "Initialize project structure"

# Observe skill activation
# Check output correctness
```

---

## Debugging Triggering Issues

### Skill Doesn't Trigger

**Quick Checklist:**
- Is description too generic? ("Helps with projects" won't work)
- Does it include trigger phrases users would actually say?
- Does it mention relevant file types if applicable?

**Debugging Approach:**
Ask Claude: "When would you use the [skill name] skill?"

Claude will quote the description back. Adjust based on what's missing.

---

### Skill Triggers Too Often

**Solutions:**

1. **Add negative triggers**
```yaml
description: Advanced data analysis for CSV files. Use for statistical 
  modeling, regression, clustering. Do NOT use for simple data exploration.
```

2. **Be more specific**
```yaml
# Too broad
description: Processes documents

# More specific
description: Processes PDF legal documents for contract review
```

3. **Clarify scope**
```yaml
description: PayFlow payment processing for e-commerce. Use specifically 
  for online payment workflows, not for general financial queries.
```

---

## Testing Checklist

### Before Upload
- [ ] Tested triggering on obvious tasks
- [ ] Tested triggering on paraphrased requests
- [ ] Verified doesn't trigger on unrelated topics
- [ ] Functional tests pass
- [ ] Tool integration works (if applicable)
- [ ] Error handling tested
- [ ] Edge cases covered

### After Upload
- [ ] Test in real conversations
- [ ] Monitor for under/over-triggering
- [ ] Collect user feedback
- [ ] Iterate on description and instructions
- [ ] Update version in metadata

---

## Hands-On Lab: Build and Test a Skill

**Time:** 60 minutes

### Task
Build a simple skill and test it thoroughly

### Steps
1. Use your planning worksheet from Chapter 2 (10 min)
2. Create SKILL.md with frontmatter and instructions (20 min)
3. Install in ~/.kiro/skills/ (5 min)
4. Run triggering tests (10 min)
5. Run functional tests (10 min)
6. Iterate based on results (5 min)

### Deliverable
A working, tested skill installed in your Kiro environment

---

## Key Takeaways

1. **Test three areas:** Triggering, functional, performance
2. **Iterate on single task first** before expanding
3. **Use skill-creator** for generation and review
4. **Monitor signals:** Undertriggering, overtriggering, execution issues
5. **Test in real environment:** Kiro IDE and CLI
6. **Iterate continuously:** Skills are living documents

---

## Next: Distribution and Sharing

In Chapter 4, you'll learn how to:
- Deploy skills to Kiro IDE and CLI
- Share skills across your organization
- Distribute via GitHub
- Document for users

**Break:** 15 minutes

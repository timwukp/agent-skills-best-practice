# Chapter 5: Patterns and Troubleshooting
## Common Approaches and Solutions

**Duration:** 60 minutes  
**Format:** Presentation + Hands-On Debugging

---

## Five Common Patterns

These patterns emerged from early adopters and internal teams.

Not prescriptive templates - adapt to your use case.

---

## Pattern 1: Sequential Workflow Orchestration

**Use when:** Users need multi-step processes in a specific order

**Example:** Customer Onboarding
```markdown
## Workflow: Onboard New Customer

### Step 1: Create Account
Call MCP tool: `create_customer`
Parameters: name, email, company

### Step 2: Setup Payment
Call MCP tool: `setup_payment_method`
Wait for: payment method verification

### Step 3: Create Subscription
Call MCP tool: `create_subscription`
Parameters: plan_id, customer_id (from Step 1)

### Step 4: Send Welcome Email
Call MCP tool: `send_email`
Template: welcome_email_template
```

**Key Techniques:**
- Explicit step ordering
- Dependencies between steps
- Validation at each stage
- Rollback instructions for failures

---

## Pattern 2: Multi-MCP Coordination

**Use when:** Workflows span multiple services

**Example:** Design-to-Development Handoff
```markdown
## Phase 1: Design Export (Figma MCP)
1. Export design assets from Figma
2. Generate design specifications
3. Create asset manifest

## Phase 2: Asset Storage (Drive MCP)
1. Create project folder in Drive
2. Upload all assets
3. Generate shareable links

## Phase 3: Task Creation (Linear MCP)
1. Create development tasks
2. Attach asset links to tasks
3. Assign to engineering team

## Phase 4: Notification (Slack MCP)
1. Post handoff summary to #engineering
2. Include asset links and task references
```

**Key Techniques:**
- Clear phase separation
- Data passing between MCPs
- Validation before moving to next phase
- Centralized error handling

---

## Pattern 3: Iterative Refinement

**Use when:** Output quality improves with iteration

**Example:** Report Generation
```markdown
## Iterative Report Creation

### Initial Draft
1. Fetch data via MCP
2. Generate first draft report
3. Save to temporary file

### Quality Check
1. Run validation script: `scripts/check_report.py`
2. Identify issues:
   - Missing sections
   - Inconsistent formatting
   - Data validation errors

### Refinement Loop
1. Address each identified issue
2. Regenerate affected sections
3. Re-validate
4. Repeat until quality threshold met

### Finalization
1. Apply final formatting
2. Generate summary
3. Save final version
```

**Key Techniques:**
- Explicit quality criteria
- Iterative improvement
- Validation scripts
- Know when to stop iterating

---

## Pattern 4: Context-Aware Tool Selection

**Use when:** Same outcome, different tools depending on context

**Example:** Smart File Storage
```markdown
## Decision Tree
1. Check file type and size
2. Determine best storage location:
   - Large files (>10MB): Use cloud storage MCP
   - Collaborative docs: Use Notion/Docs MCP
   - Code files: Use GitHub MCP
   - Temporary files: Use local storage

## Execute Storage
Based on decision:
- Call appropriate MCP tool
- Apply service-specific metadata
- Generate access link

## Provide Context to User
Explain why that storage was chosen
```

**Key Techniques:**
- Clear decision criteria
- Fallback options
- Transparency about choices

---

## Pattern 5: Domain-Specific Intelligence

**Use when:** Skill adds specialized knowledge beyond tool access

**Example:** Financial Compliance
```markdown
## Payment Processing with Compliance

### Before Processing (Compliance Check)
1. Fetch transaction details via MCP
2. Apply compliance rules:
   - Check sanctions lists
   - Verify jurisdiction allowances
   - Assess risk level
3. Document compliance decision

### Processing
IF compliance passed:
  - Call payment processing MCP tool
  - Apply appropriate fraud checks
  - Process transaction
ELSE:
  - Flag for review
  - Create compliance case

### Audit Trail
- Log all compliance checks
- Record processing decisions
- Generate audit report
```

**Key Techniques:**
- Domain expertise embedded in logic
- Compliance before action
- Comprehensive documentation
- Clear governance

---

## Troubleshooting: Skill Won't Upload

### Error: "Could not find SKILL.md in uploaded folder"
**Cause:** File not named exactly SKILL.md

**Solution:**
```bash
# Rename to SKILL.md (case-sensitive)
mv skill.md SKILL.md

# Verify
ls -la | grep SKILL.md
```

---

### Error: "Invalid frontmatter"
**Cause:** YAML formatting issue

**Common Mistakes:**
```yaml
# ❌ Wrong - missing delimiters
name: my-skill
description: Does things

# ❌ Wrong - unclosed quotes
name: my-skill
description: "Does things

# ✅ Correct
---
name: my-skill
description: Does things
---
```

---

### Error: "Invalid skill name"
**Cause:** Name has spaces or capitals

```yaml
# ❌ Wrong
name: My Cool Skill

# ✅ Correct
name: my-cool-skill
```

---

## Troubleshooting: Skill Doesn't Trigger

**Symptom:** Skill never loads automatically

**Fix:** Revise your description field

**Quick Checklist:**
- Is it too generic? ("Helps with projects" won't work)
- Does it include trigger phrases users would actually say?
- Does it mention relevant file types if applicable?

**Debugging Approach:**
Ask Claude: "When would you use the [skill name] skill?"

Claude will quote the description back. Adjust based on what's missing.

---

## Troubleshooting: MCP Connection Issues

**Symptom:** Skill loads but MCP calls fail

**Checklist:**

1. **Verify MCP server is connected**
   - Kiro IDE: Settings > Extensions > [Your Service]
   - Should show "Connected" status

2. **Check authentication**
   - API keys valid and not expired
   - Proper permissions/scopes granted
   - OAuth tokens refreshed

3. **Test MCP independently**
   - Ask Claude to call MCP directly (without skill)
   - "Use [Service] MCP to fetch my projects"
   - If this fails, issue is MCP not skill

4. **Verify tool names**
   - Skill references correct MCP tool names
   - Check MCP server documentation
   - Tool names are case-sensitive

---

## Troubleshooting: Instructions Not Followed

**Symptom:** Skill loads but Claude doesn't follow instructions

**Common Causes:**

1. **Instructions too verbose**
   - Keep instructions concise
   - Use bullet points and numbered lists
   - Move detailed reference to separate files

2. **Instructions buried**
   - Put critical instructions at the top
   - Use ## Important or ## Critical headers
   - Repeat key points if needed

3. **Ambiguous language**
```markdown
# ❌ Bad
Make sure to validate things properly

# ✅ Good
CRITICAL: Before calling create_project, verify:
- Project name is non-empty
- At least one team member assigned
- Start date is not in the past
```

4. **Model "laziness"**
Add explicit encouragement:
```markdown
## Performance Notes
- Take your time to do this thoroughly
- Quality is more important than speed
- Do not skip validation steps
```

---

## Advanced Technique: Validation Scripts

For critical validations, use scripts instead of language instructions.

**Why:** Code is deterministic; language interpretation isn't.

**Example:**
```python
# scripts/validate_project.py
def validate_project(name, team, start_date):
    errors = []
    if not name or name.strip() == "":
        errors.append("Project name is empty")
    if not team or len(team) == 0:
        errors.append("No team members assigned")
    if start_date < datetime.now():
        errors.append("Start date is in the past")
    return errors
```

See Office skills for examples of this pattern.

---

## Hands-On: Debug Problematic Skills

**Time:** 30 minutes

### Task
Debug 3 broken skills and fix them

### Scenarios
1. Skill with undertriggering issues
2. Skill with MCP connection failures
3. Skill with ambiguous instructions

### Steps
1. Identify the problem (10 min)
2. Apply troubleshooting techniques (15 min)
3. Test the fix (5 min)

### Deliverable
3 fixed skills with documented solutions

---

## Key Takeaways

1. **Five common patterns:** Sequential, Multi-MCP, Iterative, Context-aware, Domain-specific
2. **Troubleshooting is systematic:** Check frontmatter, description, MCP, instructions
3. **Use validation scripts** for critical checks
4. **Test independently:** Isolate MCP issues from skill issues
5. **Iterate based on signals:** Undertriggering, overtriggering, execution failures

---

## Next: Resources and References

In Chapter 6, you'll get:
- Official documentation links
- Community resources
- Quick reference cheat sheet
- Next steps for continued learning

**Final Chapter:** 15 minutes

# Chapter 5 Examples: Patterns

## Pattern 1: Sequential Workflow

```markdown
## Workflow: Customer Onboarding

### Step 1: Create Account
Call MCP tool: `create_customer`
Parameters: name, email, company

### Step 2: Setup Payment
Call MCP tool: `setup_payment_method`
Wait for: payment method verification

### Step 3: Create Subscription
Call MCP tool: `create_subscription`
Parameters: plan_id, customer_id (from Step 1)

### Step 4: Send Welcome
Call MCP tool: `send_email`
Template: welcome_email_template

### Error Handling
- If Step 1 fails: Report error, stop
- If Step 2 fails: Delete account from Step 1
- If Step 3 fails: Delete account, report
```

## Pattern 2: Multi-MCP Coordination

```markdown
## Design-to-Dev Handoff

### Phase 1: Design Export (Figma MCP)
1. Export design assets
2. Generate specifications

### Phase 2: Storage (Drive MCP)
1. Create project folder
2. Upload assets

### Phase 3: Tasks (Linear MCP)
1. Create development tasks
2. Attach asset links

### Phase 4: Notify (Slack MCP)
1. Post summary to #engineering
```

## Pattern 3: Iterative Refinement

```markdown
## Report Generation

### Initial Draft
1. Fetch data via MCP
2. Generate first draft

### Quality Check
1. Run: `scripts/check_report.py`
2. Identify issues

### Refinement Loop
1. Fix each issue
2. Re-validate
3. Repeat until passing

### Finalization
1. Apply formatting
2. Save final version
```

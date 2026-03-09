# Lab 3: Build an Enterprise Workflow Skill

**Duration:** 60 minutes  
**Difficulty:** Advanced  
**Prerequisites:** Labs 1-2 completed

---

## Objective

Build a production-ready skill for your organization's specific workflow with enterprise considerations.

## Skills You'll Practice

- Planning from requirements
- Security considerations
- Enterprise deployment
- Documentation

---

## Scenario

Your organization needs a skill for the complete employee onboarding workflow:
1. Create accounts across multiple systems
2. Assign appropriate permissions
3. Set up development environment
4. Schedule training sessions
5. Notify relevant teams
6. Track onboarding progress

This must be secure, auditable, and compliant with company policies.

### No Enterprise MCP Servers?
This lab focuses on **designing** an enterprise-grade skill. You don't need actual HR/IT MCP servers:
- Write the complete SKILL.md with all security, audit, and compliance sections
- Use placeholder MCP tool names (e.g., `hr_create_employee`)
- Test triggering and description quality in Kiro
- The learning is in the **design patterns**: security checks, audit trails, rollback, compliance

---

## Step 1: Gather Requirements (15 minutes)

### Functional Requirements

**Must Have:**
- Create user accounts in HR system, IT systems, development tools
- Assign role-based permissions
- Generate onboarding checklist
- Schedule required training
- Notify manager and IT team

**Should Have:**
- Track onboarding progress
- Send reminders for incomplete tasks
- Generate onboarding report

**Nice to Have:**
- Integrate with calendar for scheduling
- Auto-provision hardware
- Create welcome package

### Non-Functional Requirements

**Security:**
- Only HR and IT admins can trigger
- Audit log all actions
- No PII in logs
- Encrypted data transmission

**Compliance:**
- GDPR compliant data handling
- SOC 2 audit trail
- Data retention policies

**Performance:**
- Complete onboarding in < 5 minutes
- Handle 10+ concurrent onboardings
- 99.9% success rate

---

## Step 2: Design the Skill (15 minutes)

### Architecture

```
employee-onboarding/
├── SKILL.md
├── scripts/
│   ├── validate_permissions.py
│   ├── audit_log.py
│   └── encrypt_data.py
├── references/
│   ├── security-policy.md
│   ├── compliance-checklist.md
│   └── role-permissions.md
└── assets/
    └── onboarding-template.md
```

### Security Design

**Authentication:**
- Verify user has HR or IT admin role
- Check permissions before each action
- Log all permission checks

**Data Protection:**
- Encrypt PII in transit and at rest
- Mask sensitive data in logs
- Auto-delete temporary data after 24 hours

**Audit Trail:**
- Log every action with timestamp
- Include user ID, action, result
- Store logs in secure, immutable storage

---

## Step 3: Implement SKILL.md (30 minutes)

```yaml
---
name: employee-onboarding
description: Automates complete employee onboarding workflow including account 
  creation, permission assignment, training scheduling, and team notifications. 
  Use when HR or IT admin says "onboard new employee", "create employee accounts", 
  "set up new hire", or "start onboarding for [name]". SECURITY: Only authorized 
  HR and IT admins can use this skill.
metadata:
  author: IT Security Team
  version: 1.0.0
  category: hr-automation
  security-level: high
  compliance: GDPR, SOC2
  audit-required: true
---

# Employee Onboarding Automation

Automates secure, compliant employee onboarding across all company systems.

## Security Notice

⚠️ **RESTRICTED ACCESS**: This skill is restricted to HR and IT administrators only.

All actions are logged and audited. Misuse will be reported to security team.

## Instructions

### Pre-Flight Security Check

**CRITICAL:** Before proceeding, verify:
1. User has HR_ADMIN or IT_ADMIN role
2. Request includes valid employee data
3. Manager approval is documented

Run validation script:
```bash
python scripts/validate_permissions.py --user {current_user} --action onboard
```

If validation fails:
- Log the attempt
- Notify security team
- Return error to user
- **DO NOT PROCEED**

### Phase 1: Data Collection and Validation

#### Step 1: Gather Employee Information
Request from user:
- Full name
- Email address (company domain only)
- Department
- Role/Title
- Manager name
- Start date
- Office location

#### Step 2: Validate Data
Run validation checks:
```python
# scripts/validate_data.py
- Email format: {firstname}.{lastname}@company.com
- Start date: Not in past, not > 90 days future
- Manager: Exists in system
- Department: Valid department code
```

If validation fails:
- Return specific error
- Request corrected information
- Log validation failure

#### Step 3: Encrypt Sensitive Data
Before processing:
```bash
python scripts/encrypt_data.py --input employee_data.json
```

All PII must be encrypted before transmission to external systems.

### Phase 2: Account Creation

#### Step 4: Create HR System Account
Call HR MCP: `hr_create_employee`

Parameters:
- Encrypted employee data
- Department code
- Manager ID
- Start date

**Validation:** Verify employee ID returned

**Audit Log:**
```python
audit_log.log({
  "action": "hr_account_created",
  "employee_id": employee_id,
  "timestamp": now(),
  "user": current_user,
  "result": "success"
})
```

#### Step 5: Create IT System Accounts
For each system (Email, VPN, Dev Tools):

1. Call appropriate MCP tool
2. Assign role-based permissions from `references/role-permissions.md`
3. Validate account created
4. Log action

**Error Handling:**
If account creation fails:
- Log the failure
- Continue with other systems
- Collect all failures
- Report at end
- **DO NOT leave partial accounts**

#### Step 6: Provision Development Environment
If role requires dev access:

1. Create GitHub account
2. Add to appropriate teams
3. Provision AWS access
4. Set up development tools

**Security:** Apply principle of least privilege

### Phase 3: Training and Onboarding

#### Step 7: Schedule Required Training
Based on role and department:

1. Fetch required training from `references/training-requirements.md`
2. Call calendar MCP to schedule sessions
3. Send calendar invites
4. Add to onboarding checklist

#### Step 8: Generate Onboarding Checklist
Create checklist with:
- Account credentials (encrypted)
- Training schedule
- First week tasks
- Key contacts
- Important links

Save to secure location, share with employee and manager.

### Phase 4: Notifications and Tracking

#### Step 9: Notify Stakeholders
Send notifications to:

**Manager:**
- Employee start date
- Onboarding checklist link
- First week schedule

**IT Team:**
- Hardware provisioning needed
- Office setup required
- Access granted summary

**Employee (if start date is today):**
- Welcome message
- Account credentials (secure link)
- First day schedule

#### Step 10: Create Audit Report
Generate comprehensive audit report:
```markdown
# Onboarding Audit Report

**Employee:** [Name] ([ID])
**Date:** [Timestamp]
**Initiated By:** [Admin User]

## Actions Completed
- [x] HR account created
- [x] Email account created
- [x] VPN access granted
- [x] Dev tools provisioned
- [x] Training scheduled
- [x] Stakeholders notified

## Security Checks
- [x] Permission validation passed
- [x] Data encryption applied
- [x] Audit log created
- [x] Compliance verified

## Summary
All onboarding steps completed successfully.
No security violations detected.
```

Save to audit log storage.

### Phase 5: Completion

#### Step 11: Verify Completion
Run final validation:
```bash
python scripts/verify_onboarding.py --employee-id {id}
```

Checks:
- All accounts created
- Permissions assigned correctly
- Training scheduled
- Notifications sent
- Audit log complete

#### Step 12: Provide Summary
Return to user:
- Onboarding status: Complete
- Employee ID
- Accounts created (list)
- Training schedule
- Audit report link
- Next steps

## Error Handling

### Critical Errors (Stop Execution)
- Permission validation failed
- Data encryption failed
- Audit log write failed

**Action:** Stop immediately, log error, notify security team

### Non-Critical Errors (Continue with Logging)
- Single account creation failed
- Notification delivery failed
- Calendar scheduling failed

**Action:** Log error, continue, report at end

### Rollback Procedure
If critical error after accounts created:

1. Log rollback initiation
2. Delete created accounts
3. Revoke granted permissions
4. Notify security team
5. Generate incident report

## Security Checklist

Before completing, verify:
- [ ] User permissions validated
- [ ] All PII encrypted
- [ ] Audit log complete
- [ ] No sensitive data in logs
- [ ] Compliance requirements met
- [ ] Security team notified (if required)

## Compliance Notes

**GDPR:**
- Employee data encrypted
- Consent documented
- Data retention policy applied
- Right to deletion supported

**SOC 2:**
- Complete audit trail
- Access controls enforced
- Security monitoring active
- Incident response ready

## Troubleshooting

### Error: Permission Denied
**Cause:** User lacks required role  
**Solution:** Request access from IT admin, document business justification

### Error: Data Validation Failed
**Cause:** Invalid employee data  
**Solution:** Correct data, retry validation

### Error: Account Creation Failed
**Cause:** System unavailable or duplicate account  
**Solution:** Check system status, verify employee doesn't already exist

### Error: Audit Log Failed
**Cause:** Storage unavailable  
**Solution:** **CRITICAL** - Stop execution, notify security team immediately
```

---

## Step 4: Test Enterprise Scenarios (15 minutes)

### Test 1: Authorized User, Happy Path
```
User: HR Admin
Request: "Onboard new employee John Doe, Software Engineer, 
         starting March 15, manager Sarah Smith"
```

**Expected:**
- Permission check passes
- All accounts created
- Training scheduled
- Notifications sent
- Audit log complete

### Test 2: Unauthorized User
```
User: Regular Employee
Request: "Onboard new employee"
```

**Expected:**
- Permission check fails immediately
- Security team notified
- Attempt logged
- Error returned to user

### Test 3: Partial Failure
```
Scenario: Email system unavailable during onboarding
```

**Expected:**
- Other accounts created successfully
- Email failure logged
- User notified of partial completion
- Manual email setup instructions provided

### Test 4: Rollback Required
```
Scenario: Audit log write fails after accounts created
```

**Expected:**
- Rollback initiated
- Accounts deleted
- Permissions revoked
- Security team notified
- Incident report generated

---

## Success Criteria

You've successfully completed this lab if:
- ✅ Skill enforces security requirements
- ✅ All actions are audited
- ✅ Handles errors gracefully with rollback
- ✅ Complies with GDPR and SOC 2
- ✅ Provides complete audit trail
- ✅ Ready for production deployment

---

## Deployment Checklist

Before deploying to production:
- [ ] Security review completed
- [ ] Compliance review completed
- [ ] Penetration testing passed
- [ ] Load testing passed
- [ ] Documentation complete
- [ ] Training provided to admins
- [ ] Incident response plan ready
- [ ] Monitoring and alerting configured

---

## Next Steps

- Submit for security review
- Complete compliance audit
- Deploy to staging environment
- Train HR and IT admins
- Monitor initial usage
- Collect feedback and iterate

---

## Congratulations!

You've built an enterprise-grade skill with:
- Security best practices
- Compliance requirements
- Audit trails
- Error handling and rollback
- Production-ready documentation

You're ready to build skills for your organization!

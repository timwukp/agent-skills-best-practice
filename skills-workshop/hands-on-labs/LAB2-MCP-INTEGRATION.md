# Lab 2: Build an MCP Integration Skill

**Duration:** 45 minutes  
**Difficulty:** Intermediate  
**Prerequisites:** Lab 1 completed, MCP server available

---

## Objective

Create a skill that orchestrates multiple MCP server calls for a complete workflow.

## Skills You'll Practice

- MCP coordination
- Error handling
- Sequential workflows
- Validation

---

## Scenario

Your team uses Linear for project management. Creating a new sprint involves:
1. Fetching current project status
2. Analyzing team capacity
3. Creating sprint milestone
4. Creating tasks with estimates
5. Assigning tasks to team members
6. Notifying team via Slack

This is tedious and error-prone. You'll create a skill to automate sprint planning.

---

## Prerequisites

### Required MCP Servers
- Linear MCP server (for project management)
- Slack MCP server (for notifications)

### No MCP? No Problem!
If you don't have Linear/Slack MCP servers, you can still complete this lab:
- **Option A:** Write the SKILL.md as-is and test triggering only (skip functional MCP tests)
- **Option B:** Substitute with any two MCP servers you DO have (e.g., GitHub + filesystem)
- **Option C:** Replace MCP calls with placeholder comments and focus on the workflow design, error handling, and description writing

The key learning is the **multi-service coordination pattern**, not the specific MCP servers.

### Setup (if you have MCP servers)
```bash
# Verify MCP servers are connected
# In Kiro IDE: Settings > Extensions
# Should see Linear and Slack as "Connected"
```

---

## Step 1: Plan the Workflow (10 minutes)

### Map the MCP Calls

**Phase 1: Data Gathering**
- `linear_get_project` - Get current project
- `linear_list_issues` - Get open issues
- `linear_get_team_members` - Get team list

**Phase 2: Sprint Creation**
- `linear_create_milestone` - Create sprint milestone
- `linear_create_issue` - Create tasks (multiple calls)
- `linear_assign_issue` - Assign to team members

**Phase 3: Notification**
- `slack_post_message` - Notify team channel

### Define Error Handling

- What if project doesn't exist?
- What if team member is unavailable?
- What if Slack notification fails?

---

## Step 2: Create SKILL.md (25 minutes)

```yaml
---
name: sprint-planner
description: Automates sprint planning in Linear including milestone creation, 
  task generation, team assignment, and Slack notifications. Use when user says 
  "plan sprint", "create sprint", "set up new sprint", "start sprint planning", 
  or mentions "Linear sprint".
metadata:
  author: Your Name
  version: 1.0.0
  mcp-server: linear, slack
  category: project-management
---

# Sprint Planner

Automates complete sprint planning workflow across Linear and Slack.

## Instructions

### Phase 1: Gather Information

#### Step 1: Get Project Details
Ask user for:
- Project name or ID
- Sprint duration (1-2 weeks)
- Sprint goals (2-3 sentences)

#### Step 2: Fetch Current Status
Call `linear_get_project` with project ID.

If project not found:
- List available projects using `linear_list_projects`
- Ask user to select correct project

#### Step 3: Analyze Team Capacity
Call `linear_get_team_members` for project.

For each team member:
- Check current workload
- Calculate available capacity
- Note any time off or unavailability

### Phase 2: Create Sprint

#### Step 4: Create Sprint Milestone
Call `linear_create_milestone` with:
- Name: "Sprint [Number] - [Start Date]"
- Description: Sprint goals
- Start date: Today
- End date: Today + sprint duration

**Validation:** Verify milestone created successfully before proceeding.

#### Step 5: Generate Sprint Tasks
Based on sprint goals, create 5-10 tasks.

For each task:
1. Call `linear_create_issue` with:
   - Title: Clear, actionable task name
   - Description: Detailed requirements
   - Estimate: Story points (1, 2, 3, 5, 8)
   - Milestone: Sprint milestone ID from Step 4
   - Labels: Appropriate labels (feature, bug, tech-debt)

2. **Validation:** Check issue created successfully

3. **Error Handling:** If creation fails:
   - Log the error
   - Continue with remaining tasks
   - Report failures at end

#### Step 6: Assign Tasks
Distribute tasks across team based on:
- Available capacity
- Skill match
- Current workload balance

For each task:
1. Select appropriate team member
2. Call `linear_assign_issue` with issue ID and assignee ID
3. **Validation:** Verify assignment successful

### Phase 3: Notify Team

#### Step 7: Send Slack Notification
Call `slack_post_message` to team channel with:

```markdown
🚀 **New Sprint Created: Sprint [Number]**

**Duration:** [Start Date] - [End Date]
**Goals:** [Sprint goals]

**Tasks Created:** [Count] tasks
**Team Assignments:**
- @[Member 1]: [Count] tasks ([Points] points)
- @[Member 2]: [Count] tasks ([Points] points)
...

**Linear Link:** [Sprint milestone URL]

Let's make it a great sprint! 💪
```

**Error Handling:** If Slack fails:
- Log the error
- Provide Linear link to user
- Suggest manual notification

#### Step 8: Confirm Completion
Provide summary to user:
- Sprint milestone created
- Tasks created and assigned
- Team notified
- Link to Linear sprint

## Examples

### Example 1: Standard Sprint
User says: "Plan a 2-week sprint for the Mobile App project"

Actions:
1. Fetch Mobile App project details
2. Get team members and capacity
3. Create sprint milestone
4. Generate 8 tasks based on project backlog
5. Assign tasks evenly across 4 team members
6. Post notification to #mobile-team Slack channel

Result: Sprint ready in Linear, team notified

### Example 2: Sprint with Specific Goals
User says: "Create sprint for API project focused on authentication features"

Actions:
1. Fetch API project
2. Create milestone with authentication goals
3. Generate tasks specific to auth features
4. Assign to backend team members
5. Notify #backend-team

Result: Focused sprint created

## Troubleshooting

### Error: Project not found
**Cause:** Invalid project name or ID  
**Solution:** List available projects, ask user to select

### Error: Team member unavailable
**Cause:** Team member on leave or overallocated  
**Solution:** Skip assignment, note in summary, assign manually later

### Error: MCP connection failed
**Cause:** Linear or Slack MCP not connected  
**Solution:**
1. Check Settings > Extensions
2. Verify MCP servers are connected
3. Reconnect if needed
4. Retry operation

### Error: Insufficient permissions
**Cause:** User lacks permissions in Linear  
**Solution:** Request admin to grant permissions, provide manual steps

## Validation Checklist

Before completing:
- [ ] Sprint milestone created in Linear
- [ ] All tasks created successfully
- [ ] Tasks assigned to team members
- [ ] Team notified via Slack
- [ ] No errors in MCP calls
- [ ] User provided with Linear link
```

---

## Step 3: Test the Workflow (15 minutes)

### Test Case 1: Happy Path
```
"Plan a 2-week sprint for the Mobile App project focused on user onboarding"
```

**Expected:**
- Fetches Mobile App project
- Creates sprint milestone
- Generates 5-10 onboarding tasks
- Assigns to team
- Posts to Slack
- Provides summary

### Test Case 2: Error Handling
```
"Create sprint for NonExistentProject"
```

**Expected:**
- Detects project not found
- Lists available projects
- Asks user to select
- Continues workflow

### Test Case 3: Partial Failure
Disconnect Slack MCP, then:
```
"Plan sprint for API project"
```

**Expected:**
- Creates sprint in Linear successfully
- Attempts Slack notification
- Handles Slack failure gracefully
- Provides Linear link to user
- Suggests manual notification

---

## Step 4: Iterate (5 minutes)

### Improvements to Consider

1. **Add Capacity Validation**
   - Check if team is overallocated
   - Warn before creating sprint

2. **Add Task Templates**
   - Pre-defined task types
   - Consistent task structure

3. **Add Sprint Retrospective**
   - Fetch completed sprint data
   - Generate retrospective summary

4. **Add Rollback**
   - If sprint creation fails midway
   - Clean up partial changes

---

## Success Criteria

You've successfully completed this lab if:
- ✅ Skill coordinates multiple MCP calls
- ✅ Handles errors gracefully
- ✅ Validates each step before proceeding
- ✅ Provides clear feedback to user
- ✅ Works end-to-end without manual intervention

---

## Bonus Challenges

1. **Add Velocity Tracking:** Fetch previous sprint velocity, suggest task estimates
2. **Add Dependencies:** Handle task dependencies in creation order
3. **Add Burndown:** Generate burndown chart link
4. **Add Automation:** Auto-assign based on past performance

---

## Next Steps

- Test with real team data
- Collect feedback from team
- Add team-specific customizations
- Move on to Lab 3 for enterprise deployment

---

## Solution

Complete solution available in `../hands-on-labs/examples/examples.md`

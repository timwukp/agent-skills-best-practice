# Lab 1: Build a Simple Document Creation Skill

**Duration:** 30 minutes  
**Difficulty:** Beginner  
**Prerequisites:** Kiro IDE or CLI installed

---

## Objective

Build a skill that creates standardized project documentation with your team's templates.

## Skills You'll Practice

- SKILL.md structure
- YAML frontmatter
- Basic instructions
- Testing triggering

---

## Scenario

Your team needs to create project documentation for every new project. The documentation should include:
- Project README with standard sections
- CONTRIBUTING.md with team guidelines
- LICENSE file
- .gitignore for your tech stack

Currently, team members copy-paste from old projects or forget sections. You'll create a skill to automate this.

---

## Step 1: Plan Your Skill (10 minutes)

### Define Use Cases

**Use Case 1:** Create new project documentation
- **Trigger:** "Set up project docs", "create project documentation", "initialize project files"
- **Steps:** Create README, CONTRIBUTING, LICENSE, .gitignore
- **Result:** Complete documentation set

**Use Case 2:** Add missing documentation
- **Trigger:** "Add CONTRIBUTING file", "create LICENSE"
- **Steps:** Create specific missing file
- **Result:** Single file created

### Define Success Criteria

**Quantitative:**
- Triggers on 90% of "project docs" queries
- Creates all 4 files in < 30 seconds
- 0 formatting errors

**Qualitative:**
- Team members don't need to ask what sections to include
- Consistent documentation across all projects

---

## Step 2: Create SKILL.md (20 minutes)

### Create Folder Structure

```bash
mkdir -p ~/.kiro/skills/project-docs
cd ~/.kiro/skills/project-docs
touch SKILL.md
```

### Write SKILL.md

```yaml
---
name: project-docs
description: Creates standardized project documentation including README, 
  CONTRIBUTING, LICENSE, and .gitignore files. Use when user says "set up 
  project docs", "create project documentation", "initialize project files", 
  or "add project README".
metadata:
  author: Your Name
  version: 1.0.0
  category: documentation
---

# Project Documentation Creator

Creates complete, standardized project documentation for new projects.

## Instructions

### Step 1: Gather Project Information
Ask the user for:
- Project name
- Project description (1-2 sentences)
- Tech stack (e.g., Python, Node.js, React)
- License type (MIT, Apache-2.0, or other)

### Step 2: Create README.md
Generate README with these sections:
```markdown
# [Project Name]

[Project Description]

## Features
- [Key feature 1]
- [Key feature 2]
- [Key feature 3]

## Installation
\`\`\`bash
# Installation commands based on tech stack
\`\`\`

## Usage
\`\`\`bash
# Basic usage examples
\`\`\`

## Contributing
See CONTRIBUTING.md for guidelines.

## License
This project is licensed under the [License Type] License - see LICENSE file.
```

### Step 3: Create CONTRIBUTING.md
Generate CONTRIBUTING with:
- Code of conduct
- How to report bugs
- How to suggest features
- Pull request process
- Coding standards

### Step 4: Create LICENSE
Generate LICENSE file based on user's choice:
- MIT License
- Apache 2.0 License
- Or other specified license

### Step 5: Create .gitignore
Generate .gitignore based on tech stack:
- Python: `__pycache__/`, `*.pyc`, `.env`, `venv/`
- Node.js: `node_modules/`, `.env`, `dist/`
- General: `.DS_Store`, `*.log`, `.vscode/`

### Step 6: Confirm Completion
List all created files and their locations.

## Examples

### Example 1: New Python Project
User says: "Set up project docs for a new Python API"

Actions:
1. Ask for project name, description, license
2. Create README.md with Python-specific installation
3. Create CONTRIBUTING.md
4. Create LICENSE (MIT)
5. Create .gitignore with Python patterns

Result: 4 files created in current directory

### Example 2: Add Missing File
User says: "Add a CONTRIBUTING file"

Actions:
1. Create only CONTRIBUTING.md
2. Use team's standard guidelines

Result: CONTRIBUTING.md created

## Troubleshooting

### Error: File already exists
**Cause:** Documentation files already present  
**Solution:** Ask user if they want to overwrite or skip

### Error: Unknown tech stack
**Cause:** User specified unfamiliar technology  
**Solution:** Ask for clarification or use general .gitignore patterns
```

---

## Step 3: Test Your Skill (10 minutes)

### Test Triggering

Try these phrases in Kiro:

**Should Trigger:**
- "Set up project docs"
- "Create project documentation"
- "Initialize project files"
- "Add project README"
- "I need documentation for a new project"

**Should NOT Trigger:**
- "What's the weather?"
- "Write Python code"
- "Explain documentation"

### Test Functionality

1. **Full Documentation Set:**
```
"Set up project docs for a new Python API called 'FastAPI Demo' 
that provides REST endpoints. Use MIT license."
```

Expected: 4 files created (README, CONTRIBUTING, LICENSE, .gitignore)

2. **Single File:**
```
"Add a CONTRIBUTING file"
```

Expected: Only CONTRIBUTING.md created

3. **Different Tech Stack:**
```
"Create project docs for a React app"
```

Expected: .gitignore includes node_modules/, not Python patterns

---

## Step 4: Iterate (5 minutes)

### If Skill Doesn't Trigger
- Add more trigger phrases to description
- Make description more "pushy"
- Include specific keywords like "documentation", "README", "project setup"

### If Output is Incorrect
- Clarify instructions for each file
- Add more examples
- Specify exact format expected

### If Errors Occur
- Add error handling for edge cases
- Include troubleshooting section
- Test with various inputs

---

## Success Criteria

You've successfully completed this lab if:
- ✅ Skill triggers on project documentation requests
- ✅ Creates all 4 documentation files
- ✅ Files contain appropriate content for tech stack
- ✅ Skill doesn't trigger on unrelated queries
- ✅ You can explain how progressive disclosure works

---

## Bonus Challenges

1. **Add Templates:** Create `assets/` folder with template files
2. **Add Validation:** Check if files already exist before creating
3. **Add Customization:** Let users specify which files to create
4. **Add Styling:** Include team-specific branding in README

---

## Next Steps

- Deploy to your team
- Collect feedback
- Iterate on description and instructions
- Move on to Lab 2 for MCP integration

---

## Solution

A complete solution is available in `./examples.md`

Compare your implementation and note differences.

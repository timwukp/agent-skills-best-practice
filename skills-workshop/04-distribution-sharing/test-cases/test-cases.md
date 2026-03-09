# Chapter 4 Test Cases

## Test Case 4.1: Kiro Installation
Copy skill to `~/.kiro/skills/`, verify SKILL.md is found.

## Test Case 4.2: Skill Triggers After Install
Ask Kiro a prompt matching the skill description. Verify it activates.

## Test Case 4.3: Zip Upload
Zip skill folder, upload to Claude.ai. Verify it appears in Skills list.

## Test Case 4.4: GitHub Clone and Install
```bash
git clone https://github.com/user/skill-name
cp -r skill-name ~/.kiro/skills/
```
Verify skill works after clone.

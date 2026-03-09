# Pre-Push Validation Hook - User Guide

## Overview
This hook validates your repository before pushing to https://github.com/timwukp, ensuring code quality, security, and compliance.

## Hook Location
`.kiro/hooks/pre-push-validation.kiro.hook`

## How to Use

### Method 1: Via Kiro UI
1. Open Command Palette (Cmd+Shift+P)
2. Search for "Trigger Hook"
3. Select "Pre-Push Validation & Cleanup"
4. Review the validation report
5. Fix any issues found
6. Run again until all checks pass

### Method 2: Via Test Script
```bash
./test-pre-push-hook.sh
```

## Validation Checks

### 1. Git Status & Commit
- Checks if repository is initialized
- Commits any uncommitted changes
- Ensures working directory is clean

### 2. File Type Restrictions
**BLOCKED:** PDF, PPTX, DOCX, DOC files
**ALLOWED:** Code files (.js, .py, .ts, etc.) and Markdown (.md)

### 3. PII & Customer Data Scan
Searches for:
- Email addresses (excluding examples)
- Phone numbers
- Customer names
- Confidential information
- Personal identifiable information

### 4. License Compliance
- Verifies MIT LICENSE file exists
- Checks for incompatible licenses in dependencies
- Ensures open source compliance

### 5. Security Scan
Detects:
- Hardcoded API keys
- Passwords and tokens
- Private keys
- Credentials in code
- Security vulnerabilities

### 6. Code Quality
- Basic syntax checks
- Code pattern validation
- Best practices verification

### 7. .gitignore Configuration
Ensures proper exclusions for:
- Document files (PDF, PPTX, DOCX)
- System files (.DS_Store, etc.)
- Dependencies (node_modules, .venv)
- Environment files (.env)

## Current Test Results

### ✓ PASSING
- LICENSE file exists (MIT)
- .gitignore properly configured
- No hardcoded secrets detected
- No PII in code files

### ✗ FAILING
1. **Not a Git Repository**
   - Fix: Run `git init` to initialize
   
2. **Blocked Files Found**
   - `./The-Complete-Guide-to-Building-Skill-for-Claude.pdf`
   - `./skills/skills/theme-factory/theme-showcase.pdf`
   - `./Kiro-Skills-Technical-Training.pptx`
   - `./Tech_Talks_Presentation_Deck_CONFIDENTIAL-2026.pptx`
   - Fix: Remove these files or add to .gitignore (already configured)

## Setup Steps

### 1. Initialize Git Repository
```bash
git init
git add .gitignore LICENSE README.md
git commit -m "Initial commit with license and gitignore"
```

### 2. Remove Blocked Files
```bash
# These files are already in .gitignore, so they won't be tracked
git status  # Verify they're not staged
```

### 3. Add Remote Repository
```bash
git remote add origin https://github.com/timwukp/[your-repo-name].git
```

### 4. Run Validation
```bash
./test-pre-push-hook.sh
```

### 5. Push When Ready
```bash
git push -u origin main
```

## Files Created

1. **`.gitignore`** - Excludes unwanted files
2. **`LICENSE`** - MIT License for open source compliance
3. **`README.md`** - Repository documentation
4. **`test-pre-push-hook.sh`** - Standalone validation script
5. **`.kiro/hooks/pre-push-validation.kiro.hook`** - Kiro hook configuration

## Troubleshooting

### Hook Not Appearing
- Check `.kiro/hooks/` directory exists
- Verify hook file has `.kiro.hook` extension
- Restart Kiro if needed

### Validation Fails
- Review the specific error messages
- Fix issues one by one
- Re-run validation after each fix

### Files Still Being Tracked
```bash
# Remove from git tracking but keep locally
git rm --cached *.pdf *.pptx *.docx
git commit -m "Remove document files from tracking"
```

## Best Practices

1. **Always run validation before pushing**
2. **Never commit sensitive data**
3. **Keep .gitignore updated**
4. **Review PII scan results carefully**
5. **Maintain MIT license compliance**
6. **Use meaningful commit messages**

## Support

For issues or questions:
1. Check this guide first
2. Review the test script output
3. Examine `.kiro/hooks/pre-push-validation.kiro.hook`
4. Verify .gitignore configuration

#!/bin/bash

echo "=========================================="
echo "PRE-PUSH VALIDATION TEST"
echo "=========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

ISSUES_FOUND=0

# 1. Git Status Check
echo "1. GIT STATUS CHECK"
if git rev-parse --git-dir > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Git repository initialized${NC}"
    git status --short
else
    echo -e "${RED}✗ Not a git repository - run 'git init' first${NC}"
    ISSUES_FOUND=$((ISSUES_FOUND + 1))
fi
echo ""

# 2. File Type Check
echo "2. FILE TYPE CHECK (PDF, PPTX, DOCX)"
BLOCKED_FILES=$(find . -type f \( -name "*.pdf" -o -name "*.pptx" -o -name "*.docx" -o -name "*.doc" \) ! -path "./node_modules/*" ! -path "./.venv/*" ! -path "./skills/.git/*")
if [ -z "$BLOCKED_FILES" ]; then
    echo -e "${GREEN}✓ No blocked file types found${NC}"
else
    echo -e "${RED}✗ Found files that should not be pushed:${NC}"
    echo "$BLOCKED_FILES"
    ISSUES_FOUND=$((ISSUES_FOUND + 1))
fi
echo ""

# 3. PII Scan
echo "3. PII & CUSTOMER DATA SCAN"
PII_FOUND=$(grep -r -i -E "[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}" --include="*.js" --include="*.py" --exclude-dir=node_modules --exclude-dir=.venv --exclude-dir=.git . 2>/dev/null | grep -v "example.com" | grep -v "your-email" | grep -v "@anthropic" | grep -v "THIRD_PARTY" | head -3)
if [ -z "$PII_FOUND" ]; then
    echo -e "${GREEN}✓ No PII detected in code files${NC}"
else
    echo -e "${YELLOW}⚠ Potential PII found (review needed):${NC}"
    echo "$PII_FOUND"
fi
echo ""

# 4. License Check
echo "4. LICENSE COMPLIANCE"
if [ -f "LICENSE" ]; then
    echo -e "${GREEN}✓ LICENSE file exists${NC}"
    head -1 LICENSE
else
    echo -e "${RED}✗ No LICENSE file found${NC}"
    ISSUES_FOUND=$((ISSUES_FOUND + 1))
fi
echo ""

# 5. Security Scan
echo "5. SECURITY SCAN"
SECRETS=$(grep -r -i -E "(password|api_key|secret_key|private_key|token)[\s]*[=:]\s*['\"][^'\"]{10,}" --include="*.js" --include="*.py" --include="*.json" --exclude-dir=node_modules --exclude-dir=.venv --exclude-dir=.git . 2>/dev/null | grep -v "your-api-key" | grep -v "example" | grep -v "placeholder" | head -3)
if [ -z "$SECRETS" ]; then
    echo -e "${GREEN}✓ No hardcoded secrets detected${NC}"
else
    echo -e "${RED}✗ Potential hardcoded secrets found:${NC}"
    echo "$SECRETS"
    ISSUES_FOUND=$((ISSUES_FOUND + 1))
fi
echo ""

# 6. Gitignore Check
echo "6. GITIGNORE CONFIGURATION"
if [ -f ".gitignore" ]; then
    if grep -q "\.pdf\|\.pptx\|\.docx" .gitignore; then
        echo -e "${GREEN}✓ .gitignore properly configured${NC}"
    else
        echo -e "${YELLOW}⚠ .gitignore missing document exclusions${NC}"
    fi
else
    echo -e "${RED}✗ No .gitignore file found${NC}"
    ISSUES_FOUND=$((ISSUES_FOUND + 1))
fi
echo ""

# Summary
echo "=========================================="
echo "VALIDATION SUMMARY"
echo "=========================================="
if [ $ISSUES_FOUND -eq 0 ]; then
    echo -e "${GREEN}✓ All checks passed! Ready to push.${NC}"
    exit 0
else
    echo -e "${RED}✗ Found $ISSUES_FOUND critical issue(s). Fix before pushing.${NC}"
    exit 1
fi

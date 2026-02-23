#!/bin/bash
# Git History Audit Script - Scan for secrets using truffleHog
# Task T074: Audit Git history for secrets, credentials, and sensitive files

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
REPORT_FILE="${REPO_ROOT}/git_secrets_audit_${TIMESTAMP}.txt"
LAST_RUN_FILE="${REPO_ROOT}/weekly_audit_last_run.txt"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Git History Secrets Audit${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo "Repository: ${REPO_ROOT}"
echo "Report will be saved to: ${REPORT_FILE}"
echo ""

# Check if truffleHog is installed
if ! command -v trufflehog &> /dev/null; then
    echo -e "${YELLOW}Warning: truffleHog is not installed.${NC}"
    echo ""
    echo "To install truffleHog, run one of the following:"
    echo "  - Using pip: pip install truffleHog"
    echo "  - Using brew (macOS): brew install trufflehog"
    echo "  - Using Docker: docker pull trufflesecurity/trufflehog:latest"
    echo ""
    echo -e "${RED}Falling back to manual git log scanning...${NC}"
    echo ""

    # Fallback: Manual scanning using git log
    {
        echo "========================================="
        echo "Git History Secrets Audit Report"
        echo "========================================="
        echo "Date: $(date)"
        echo "Repository: ${REPO_ROOT}"
        echo "Method: Manual git log scanning (truffleHog not available)"
        echo ""
        echo "========================================="
        echo "Scanning for sensitive patterns..."
        echo "========================================="
        echo ""

        # Check for .env files in history
        echo "--- Checking for .env files in Git history ---"
        git log --all --full-history --pretty=format:"%H %ai %an" -- "*.env" "*.env.*" ".env" || echo "No .env files found in history"
        echo ""
        echo ""

        # Check for credentials directory
        echo "--- Checking for credentials/ directory in Git history ---"
        git log --all --full-history --pretty=format:"%H %ai %an" -- "credentials/*" "**/credentials/*" || echo "No credentials/ directory found in history"
        echo ""
        echo ""

        # Check for common secret file patterns
        echo "--- Checking for common secret file patterns ---"
        git log --all --full-history --pretty=format:"%H %ai %an" -- "*.key" "*.pem" "*.token" "*.pickle" "*token.json" "*credentials.json" || echo "No common secret files found in history"
        echo ""
        echo ""

        # Search for potential API keys and tokens in commit diffs
        echo "--- Scanning commit diffs for potential secrets ---"
        echo "(Searching for patterns: API_KEY, SECRET, TOKEN, PASSWORD, PRIVATE_KEY)"
        echo ""

        git log --all --full-history -p | grep -iE "(api[_-]?key|secret[_-]?key|access[_-]?token|password|private[_-]?key|bearer|authorization)" | head -50 || echo "No obvious secret patterns found in diffs"
        echo ""
        echo ""

        # Check current .gitignore effectiveness
        echo "--- Checking .gitignore configuration ---"
        if [ -f "${REPO_ROOT}/.gitignore" ]; then
            echo "Current .gitignore rules for secrets:"
            grep -E "(\.env|credentials|token|key|pem|secret)" "${REPO_ROOT}/.gitignore" || echo "No secret-related patterns found in .gitignore"
        else
            echo "WARNING: No .gitignore file found!"
        fi
        echo ""
        echo ""

        # Summary
        echo "========================================="
        echo "Audit Summary"
        echo "========================================="
        echo "Scan completed at: $(date)"
        echo ""
        echo "RECOMMENDATIONS:"
        echo "1. Install truffleHog for more comprehensive scanning:"
        echo "   pip install truffleHog"
        echo "2. Review any findings above carefully"
        echo "3. If secrets were found, consider using git-filter-repo to remove them"
        echo "4. Ensure .gitignore includes all secret patterns"
        echo "5. Set up pre-commit hooks to prevent future secret commits"
        echo ""

    } > "${REPORT_FILE}"

else
    # TruffleHog is available - use it for comprehensive scanning
    echo -e "${GREEN}truffleHog found! Running comprehensive scan...${NC}"
    echo ""

    {
        echo "========================================="
        echo "Git History Secrets Audit Report"
        echo "========================================="
        echo "Date: $(date)"
        echo "Repository: ${REPO_ROOT}"
        echo "Method: truffleHog v3 scan"
        echo ""
        echo "========================================="
        echo "TruffleHog Scan Results"
        echo "========================================="
        echo ""

    } > "${REPORT_FILE}"

    # Run truffleHog scan
    cd "${REPO_ROOT}"

    # TruffleHog v3 command (scans entire git history)
    echo "Running: trufflehog git file://. --json --no-update"
    trufflehog git file://. --json --no-update >> "${REPORT_FILE}" 2>&1 || {
        echo "TruffleHog scan completed with warnings (this is normal if no secrets found)"
    }

    # Additional manual checks
    {
        echo ""
        echo ""
        echo "========================================="
        echo "Additional Manual Checks"
        echo "========================================="
        echo ""

        echo "--- Files matching secret patterns in history ---"
        git log --all --full-history --name-only --pretty=format: -- "*.env" "*.env.*" ".env" "credentials/*" "*.key" "*.pem" "*.token" "*.pickle" | sort -u | grep -v '^$' || echo "None found"
        echo ""
        echo ""

        echo "--- Current .gitignore rules for secrets ---"
        if [ -f "${REPO_ROOT}/.gitignore" ]; then
            grep -E "(\.env|credentials|token|key|pem|secret)" "${REPO_ROOT}/.gitignore" || echo "No secret-related patterns in .gitignore"
        else
            echo "WARNING: No .gitignore file found!"
        fi
        echo ""

    } >> "${REPORT_FILE}"
fi

# Record last run time
echo "$(date)" > "${LAST_RUN_FILE}"

# Display summary
echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Audit Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Report saved to: ${REPORT_FILE}"
echo ""

# Check if any secrets were found and display warning
if grep -qi "secret\|password\|api.key\|token" "${REPORT_FILE}"; then
    echo -e "${RED}⚠️  WARNING: Potential secrets detected in scan!${NC}"
    echo -e "${RED}Please review the report carefully.${NC}"
    echo ""
    echo "If secrets are found in Git history:"
    echo "1. Rotate/invalidate the exposed credentials immediately"
    echo "2. Use git-filter-repo to remove secrets from history"
    echo "3. Force push to remote (coordinate with team first)"
    echo "4. Update .gitignore and pre-commit hooks"
else
    echo -e "${GREEN}✓ No obvious secrets detected in initial scan${NC}"
    echo "Review the full report for details."
fi

echo ""
echo "Last audit run time recorded in: ${LAST_RUN_FILE}"
echo ""

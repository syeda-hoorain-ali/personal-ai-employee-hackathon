#!/bin/bash
# Weekly Audit Execution Script for Mac/Linux
# This script activates the virtual environment and runs the weekly audit

set -e  # Exit on error

echo "Starting Weekly CEO Briefing Audit..."
echo ""

# Get the script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Change to project root
cd "$PROJECT_ROOT"

# Activate virtual environment
if [ -f "app/.venv/bin/activate" ]; then
    source app/.venv/bin/activate
else
    echo "ERROR: Virtual environment not found at app/.venv"
    echo "Please run: cd app && uv venv"
    exit 1
fi

# Set vault path if not already set
if [ -z "$AI_EMPLOYEE_VAULT" ]; then
    export AI_EMPLOYEE_VAULT="AI_Employee_Vault"
fi

# Run the weekly audit
echo "Running audit from vault: $AI_EMPLOYEE_VAULT"
python -m app.src.app.weekly_audit.audit_orchestrator

# Check exit code
if [ $? -eq 0 ]; then
    echo ""
    echo "Weekly audit completed successfully!"
    exit 0
else
    echo ""
    echo "ERROR: Weekly audit failed with exit code $?"
    echo "Check logs for details."
    exit $?
fi

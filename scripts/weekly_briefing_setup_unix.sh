#!/bin/bash
# Setup cron job for Weekly CEO Briefing on Unix/Linux/Mac
# Runs every Monday at 8:00 AM

echo "========================================"
echo "Weekly CEO Briefing Cron Setup"
echo "========================================"
echo ""

# Get the script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
PYTHON_EXE="$PROJECT_DIR/app/.venv/bin/python"
TRIGGER_SCRIPT="$PROJECT_DIR/app/scripts/weekly_briefing_trigger.py"

echo "Project Directory: $PROJECT_DIR"
echo "Python Executable: $PYTHON_EXE"
echo "Trigger Script: $TRIGGER_SCRIPT"
echo ""

# Check if Python exists
if [ ! -f "$PYTHON_EXE" ]; then
    echo "ERROR: Python executable not found at $PYTHON_EXE"
    echo "Please ensure the virtual environment is set up correctly."
    exit 1
fi

# Check if trigger script exists
if [ ! -f "$TRIGGER_SCRIPT" ]; then
    echo "ERROR: Trigger script not found at $TRIGGER_SCRIPT"
    exit 1
fi

# Create cron job entry
CRON_JOB="0 8 * * 1 cd $PROJECT_DIR && $PYTHON_EXE $TRIGGER_SCRIPT >> $PROJECT_DIR/weekly_briefing.log 2>&1"

echo "Adding cron job..."
echo ""
echo "Cron entry:"
echo "$CRON_JOB"
echo ""

# Check if cron job already exists
if crontab -l 2>/dev/null | grep -q "weekly_briefing_trigger.py"; then
    echo "Cron job already exists. Removing old entry..."
    crontab -l 2>/dev/null | grep -v "weekly_briefing_trigger.py" | crontab -
fi

# Add new cron job
(crontab -l 2>/dev/null; echo "$CRON_JOB") | crontab -

if [ $? -eq 0 ]; then
    echo ""
    echo "========================================"
    echo "SUCCESS: Cron job created!"
    echo "========================================"
    echo ""
    echo "Schedule: Every Monday at 8:00 AM"
    echo "Action: Generate Weekly CEO Briefing"
    echo "Log file: $PROJECT_DIR/weekly_briefing.log"
    echo ""
    echo "To view all cron jobs:"
    echo "  crontab -l"
    echo ""
    echo "To remove this cron job:"
    echo "  crontab -e"
    echo "  (then delete the line containing 'weekly_briefing_trigger.py')"
    echo ""
else
    echo ""
    echo "ERROR: Failed to create cron job."
    echo ""
fi

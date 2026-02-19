# Quickstart Guide: Weekly CEO Briefing

**Feature**: 004-weekly-ceo-briefing
**Version**: 1.0
**Last Updated**: 2026-02-19

## Overview

This guide will help you set up and use the Weekly CEO Briefing feature, which automatically generates a comprehensive business performance report every Sunday night.

**What you'll get**:
- Automated weekly briefing every Monday morning
- Revenue tracking against your goals
- Completed task summaries
- Subscription cost optimization suggestions
- Task bottleneck identification
- Proactive business insights

**Time to setup**: 15-20 minutes

---

## Prerequisites

Before you begin, ensure you have:

- ✅ Python 3.12 or higher installed
- ✅ Claude Code installed and configured
- ✅ Obsidian vault set up at a known location
- ✅ Windows 10+ (or Mac/Linux with cron access)
- ✅ Basic familiarity with command line

**Check Python version**:
```bash
python --version
# Should show: Python 3.12.x or higher
```

**Check Claude Code**:
```bash
claude --version
# Should show Claude Code version
```

---

## Step 1: Install Dependencies

Navigate to your project directory and install required Python packages:

```bash
cd C:/Users/dell/Desktop/projects/class-project/personal-ai-employee

# Activate virtual environment
cd app
source .venv/Scripts/activate  # Windows Git Bash
# OR
.venv\Scripts\activate.bat     # Windows CMD
# OR
source .venv/bin/activate      # Mac/Linux

# Install dependencies
pip install schedule pyyaml python-dateutil

# Verify installation
pip list | grep -E "schedule|pyyaml|python-dateutil"
```

**Expected output**:
```
python-dateutil    2.8.2
PyYAML            6.0.1
schedule          1.2.0
```

---

## Step 2: Set Up Vault Structure

Create the required folders in your Obsidian vault:

```bash
# Navigate to your vault (adjust path as needed)
cd /path/to/your/vault

# Create required directories
mkdir -p Briefings
mkdir -p Accounting
mkdir -p Done

# Verify structure
ls -la
# Should show: Briefings/, Accounting/, Done/ folders
```

**Folder purposes**:
- `Briefings/` - Generated CEO briefings will be stored here
- `Accounting/` - Place your bank transaction CSV files here
- `Done/` - Move completed task files here

---

## Step 3: Create Business Goals File

Create `/Vault/Business_Goals.md` with your business metrics:

```bash
# Create the file
touch Business_Goals.md

# Open in your editor (or use Obsidian)
nano Business_Goals.md
```

**Template content**:
```markdown
---
last_updated: 2026-02-19
review_frequency: weekly
---

## Q1 2026 Objectives

### Revenue Target
- Monthly goal: $10,000
- Current MTD: $0

### Key Metrics to Track

| Metric | Target | Alert Threshold |
|--------|--------|-----------------|
| Client response time | < 24 hours | > 48 hours |
| Invoice payment rate | > 90% | < 80% |
| Software costs | < $500/month | > $600/month |

### Active Projects

1. **Personal AI Employee**
   - Due: Feb 28, 2026
   - Budget: $0
   - Status: In progress

### Subscription Audit Rules

Flag for review if:
- No activity in 30 days
- Cost increased > 20%
- Duplicate functionality with another tool
```

**Customize this template** with your actual business goals, metrics, and projects.

---

## Step 4: Prepare Transaction Data

Export your bank transactions to CSV format and place them in the `/Accounting` folder.

**Required CSV format**:
```csv
date,amount,description,category
2026-02-15,-49.99,Netflix Subscription,Entertainment
2026-02-14,1500.00,Client Payment - Project Alpha,Revenue
2026-02-13,-12.99,Spotify Premium,Entertainment
```

**Column definitions**:
- `date`: YYYY-MM-DD format
- `amount`: Negative for expenses, positive for revenue
- `description`: Transaction description (used for subscription detection)
- `category`: Optional categorization

**Tips**:
- Most banks allow CSV export from their web interface
- You can have multiple CSV files (e.g., one per month)
- Update files weekly or use automatic export if available

---

## Step 5: Set Up Task Tracking (Optional)

To enable bottleneck analysis, add metadata to your task files:

**Task file format** (`/Done/task-name.md`):
```markdown
---
expected_duration: 2h
actual_duration: 3.5h
priority: high
project: client-alpha
---

# Task: Create client proposal

## Description
Draft proposal for Client Alpha project...

## Completed
2026-02-15
```

**Duration formats**:
- Hours: `2h`, `1.5h`
- Minutes: `30m`, `45m`
- Days: `1d`, `0.5d`

**Note**: Metadata is optional. Tasks without metadata will still be counted as completed, but won't appear in bottleneck analysis.

---

## Step 6: Install Claude Code Skill

Create the weekly CEO briefing skill for Claude Code:

```bash
# Navigate to project root
cd C:/Users/dell/Desktop/projects/class-project/personal-ai-employee

# Create skill directory
mkdir -p .claude/skills/weekly-ceo-briefing

# Create skill file
touch .claude/skills/weekly-ceo-briefing/skill.md
```

**Skill content** (`.claude/skills/weekly-ceo-briefing/skill.md`):
```markdown
---
name: weekly-ceo-briefing
description: Generate weekly CEO briefing with business audit
trigger: Use when user requests weekly briefing or on Sunday night schedule
---

# Weekly CEO Briefing Generator

Generate a comprehensive Monday morning CEO briefing by analyzing:
1. Business goals and metrics from Business_Goals.md
2. Completed tasks from /Done folder (last 7 days)
3. Bank transactions from /Accounting folder
4. Subscription usage patterns

## Process

1. Read context file provided in the prompt
2. Parse business goals, tasks, transactions, and subscriptions
3. Calculate revenue progress toward monthly target
4. Identify task bottlenecks (tasks that took >50% longer than expected)
5. Generate proactive cost optimization suggestions
6. Format briefing using the standard template

## Output Format

Create briefing at `/Briefings/YYYY-MM-DD_Monday_Briefing.md` with:
- Executive summary (2-3 sentences)
- Revenue metrics with trend analysis
- Completed tasks list
- Bottlenecks table (if any)
- Proactive suggestions with actionable items
- Upcoming deadlines from Business_Goals.md

## Tone

Professional but friendly. Focus on insights and actionable recommendations, not just data reporting.
```

---

## Step 7: Test Manual Execution

Before setting up scheduling, test the audit manually:

```bash
# Navigate to project root
cd C:/Users/dell/Desktop/projects/class-project/personal-ai-employee

# Activate virtual environment
source app/.venv/Scripts/activate

# Run the audit module manually
python -m app.src.app.weekly_audit.audit_orchestrator

# Check for generated briefing
ls Vault/Briefings/
# Should show: YYYY-MM-DD_Monday_Briefing.md
```

**Expected output**:
```
[INFO] Starting weekly audit...
[INFO] Parsing Business_Goals.md...
[INFO] Analyzing completed tasks (last 7 days)...
[INFO] Found 12 completed tasks
[INFO] Analyzing transactions...
[INFO] Found 47 transactions, total revenue: $3,500.00
[INFO] Detecting subscriptions...
[INFO] Found 8 subscriptions, 2 flagged for review
[INFO] Invoking Claude Code skill...
[INFO] Briefing generated successfully: /Vault/Briefings/2026-02-16_Monday_Briefing.md
```

**Troubleshooting**:
- If "Claude Code not found": Ensure `claude` is in your PATH
- If "Vault not found": Check vault path in configuration
- If "No transactions": Verify CSV files are in `/Accounting` folder

---

## Step 8: Set Up Automated Scheduling

### Windows (Task Scheduler)

**Option A: Using PowerShell (Recommended)**

1. Create the trigger script:

```bash
# Create scripts directory
mkdir -p scripts

# Create the batch file
cat > scripts/run_weekly_audit.bat << 'EOF'
@echo off
cd /d "%~dp0.."
call app\.venv\Scripts\activate.bat
python -m app.src.app.weekly_audit.audit_orchestrator
if %ERRORLEVEL% NEQ 0 (
    echo Weekly audit failed with error code %ERRORLEVEL%
    exit /b %ERRORLEVEL%
)
EOF
```

2. Schedule the task:

```powershell
# Run PowerShell as Administrator
# Navigate to project directory
cd C:\Users\dell\Desktop\projects\class-project\personal-ai-employee

# Create scheduled task
$action = New-ScheduledTaskAction -Execute "C:\Users\dell\Desktop\projects\class-project\personal-ai-employee\scripts\run_weekly_audit.bat"
$trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Sunday -At 8:00PM
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -RunOnlyIfNetworkAvailable:$false
Register-ScheduledTask -TaskName "WeeklyCEOBriefing" -Action $action -Trigger $trigger -Settings $settings -Description "Generate weekly CEO briefing report"
```

3. Verify the task:

```powershell
Get-ScheduledTask -TaskName "WeeklyCEOBriefing"
```

**Option B: Using Task Scheduler GUI**

1. Open Task Scheduler (search in Start menu)
2. Click "Create Basic Task"
3. Name: "Weekly CEO Briefing"
4. Trigger: Weekly, Sunday, 8:00 PM
5. Action: Start a program
6. Program: `C:\Users\dell\Desktop\projects\class-project\personal-ai-employee\scripts\run_weekly_audit.bat`
7. Finish and test

### Mac/Linux (Cron)

1. Create the cron script:

```bash
# Create scripts directory
mkdir -p scripts

# Create the shell script
cat > scripts/run_weekly_audit.sh << 'EOF'
#!/bin/bash
cd "$(dirname "$0")/.."
source app/.venv/bin/activate
python -m app.src.app.weekly_audit.audit_orchestrator
EOF

# Make executable
chmod +x scripts/run_weekly_audit.sh
```

2. Add to crontab:

```bash
# Edit crontab
crontab -e

# Add this line (runs every Sunday at 8:00 PM)
0 20 * * 0 /path/to/personal-ai-employee/scripts/run_weekly_audit.sh >> /path/to/personal-ai-employee/logs/weekly_audit.log 2>&1
```

3. Verify cron job:

```bash
crontab -l
# Should show your weekly audit job
```

---

## Step 9: Verify Setup

**Checklist**:
- [ ] Dependencies installed (schedule, pyyaml, python-dateutil)
- [ ] Vault folders created (Briefings, Accounting, Done)
- [ ] Business_Goals.md created and customized
- [ ] Transaction CSV files in /Accounting folder
- [ ] Claude Code skill installed
- [ ] Manual test successful (briefing generated)
- [ ] Scheduled task created and verified

**Test the complete workflow**:
1. Add a few completed tasks to `/Done` folder
2. Add transaction CSV to `/Accounting` folder
3. Run manual audit: `python -m app.src.app.weekly_audit.audit_orchestrator`
4. Check `/Briefings` for generated report
5. Open briefing in Obsidian and review content

---

## Usage

### Viewing Briefings

Briefings are automatically generated every Sunday at 8:00 PM and saved to `/Briefings/` folder.

**Open in Obsidian**:
1. Navigate to Briefings folder
2. Open the latest briefing (sorted by date)
3. Review sections: Revenue, Completed Tasks, Bottlenecks, Suggestions

**Briefing naming**: `YYYY-MM-DD_Monday_Briefing.md` (date is the Monday following the reporting week)

### Updating Business Goals

Edit `Business_Goals.md` anytime to update:
- Revenue targets
- Key metrics
- Active projects
- Subscription audit rules

Changes take effect in the next weekly audit.

### Adding Transactions

Export new transactions from your bank and add CSV files to `/Accounting` folder. The audit will automatically include all transactions from the past 7 days.

### Managing Subscriptions

The system automatically detects subscriptions from transaction descriptions. To improve detection:

1. **Add custom patterns** (future enhancement)
2. **Categorize transactions** in CSV (helps with analysis)
3. **Review flagged subscriptions** in briefing and take action

---

## Troubleshooting

### Issue: "No briefing generated"

**Possible causes**:
- Scheduled task didn't run (check Task Scheduler/cron logs)
- Python environment not activated
- Claude Code not found in PATH
- Vault path incorrect

**Solution**:
```bash
# Check scheduled task status (Windows)
Get-ScheduledTask -TaskName "WeeklyCEOBriefing" | Get-ScheduledTaskInfo

# Check cron logs (Mac/Linux)
grep CRON /var/log/syslog

# Run manual test to identify issue
python -m app.src.app.weekly_audit.audit_orchestrator
```

### Issue: "No subscriptions detected"

**Possible causes**:
- Transaction descriptions don't match patterns
- Transactions not recurring (need 2+ occurrences)
- CSV format incorrect

**Solution**:
- Check transaction descriptions in CSV
- Verify at least 2 transactions for same subscription
- Review subscription patterns in code

### Issue: "Briefing missing sections"

**Possible causes**:
- No data available for that section
- Claude Code skill not generating correctly

**Solution**:
- Check if data exists (tasks in /Done, transactions in /Accounting)
- Review Claude Code skill logs
- Verify context file was created correctly

### Issue: "Task bottlenecks not showing"

**Possible causes**:
- Task files missing YAML frontmatter
- No tasks exceeded expected duration by 50%+

**Solution**:
- Add `expected_duration` and `actual_duration` to task files
- Ensure at least one task has significant delay

---

## Advanced Configuration

### Custom Subscription Patterns

Edit `app/src/app/weekly_audit/subscription_detector.py` to add custom patterns:

```python
SUBSCRIPTION_PATTERNS = {
    # Add your custom patterns
    'myservice.com': 'My Custom Service',
    'another-service': 'Another Service',
}
```

### Adjust Scheduling Time

**Windows**:
```powershell
# Change to different day/time
Set-ScheduledTask -TaskName "WeeklyCEOBriefing" -Trigger (New-ScheduledTaskTrigger -Weekly -DaysOfWeek Friday -At 6:00PM)
```

**Mac/Linux**:
```bash
# Edit crontab
crontab -e

# Change to Friday at 6:00 PM
0 18 * * 5 /path/to/scripts/run_weekly_audit.sh
```

### Change Reporting Period

By default, the audit analyzes the past 7 days. To change:

Edit `app/src/app/weekly_audit/audit_orchestrator.py`:
```python
# Change from 7 to desired number of days
tasks = task_analyzer.analyze_completed_tasks(done_folder, days=14)
transactions = transaction_analyzer.analyze_transactions(accounting_folder, days=14)
```

---

## Next Steps

Now that your Weekly CEO Briefing is set up:

1. **Wait for first briefing** (next Sunday at 8:00 PM)
2. **Review and customize** Business_Goals.md based on your needs
3. **Add task metadata** to enable bottleneck analysis
4. **Export transactions regularly** to keep data current
5. **Act on suggestions** in the briefing to optimize costs

**Pro tips**:
- Review briefings every Monday morning to start the week informed
- Update Business_Goals.md monthly to reflect new targets
- Use bottleneck insights to improve time estimates
- Track subscription savings from optimization suggestions

---

## Support

**Documentation**:
- [Feature Specification](./spec.md)
- [Implementation Plan](./plan.md)
- [Data Model](./data-model.md)
- [API Contracts](./contracts/claude-skill-interface.md)

**Common Resources**:
- [Claude Code Documentation](https://claude.com/claude-code)
- [Obsidian Help](https://help.obsidian.md)
- [Python Schedule Library](https://schedule.readthedocs.io)

**Getting Help**:
- Check troubleshooting section above
- Review logs in `logs/weekly_audit.log`
- Test manual execution to isolate issues
- Verify all prerequisites are met

---

## Changelog

### Version 1.0 (2026-02-19)
- Initial quickstart guide
- Setup instructions for Windows, Mac, Linux
- Troubleshooting section
- Advanced configuration options
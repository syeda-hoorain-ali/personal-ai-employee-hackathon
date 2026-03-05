# Weekly CEO Briefing - Testing Guide

## Overview

This guide explains how to test the Weekly CEO Briefing scheduler setup and execution.

**Important**: Since we're currently inside Claude Code, we cannot test the full execution (Claude Code cannot launch itself). This guide shows you how to test outside this session.

---

## Architecture

```
Windows Task Scheduler
    ↓
Trigger Script (app/scripts/weekly_briefing_trigger.py)
    ↓
Claude Code (new session via ccr code)
    ↓
    ├─→ Skill (.claude/skills/weekly-ceo-briefing/SKILL.md) [KNOWLEDGE]
    └─→ Odoo MCP Tools (mcp__odoo__search_records) [ACTIONS]
    ↓
Briefing File (Briefings/YYYY-MM-DD_Monday_Briefing.md)
```

---

## Step 1: Setup the Scheduled Task

**Run as Administrator**:
```bash
# Right-click and select "Run as administrator"
scripts\setup_weekly_briefing_task.bat
```

**What it does**:
1. Checks for admin privileges
2. Verifies Python and trigger script exist
3. Deletes any existing task
4. Creates new scheduled task: `WeeklyCEOBriefing`
5. Schedule: Every Monday at 8:00 AM

**Expected Output**:
```
============================================================
[SUCCESS] Scheduled task created successfully!
============================================================

Task Details:
  Name: WeeklyCEOBriefing
  Schedule: Every Monday at 8:00 AM
  Action: Run Python trigger script
```

---

## Step 2: Verify the Task

**Run**:
```bash
scripts\verify_weekly_briefing_task.bat
```

**What it checks**:
- Task exists in Task Scheduler
- Task configuration is correct
- Shows next run time

**Expected Output**:
```
[OK] Task 'WeeklyCEOBriefing' exists

[STEP 2] Task Details:
============================================================
TaskName: WeeklyCEOBriefing
Next Run Time: [Next Monday at 8:00 AM]
Status: Ready
...
```

---

## Step 3: View in Task Scheduler GUI

1. Press `Win + R`
2. Type: `taskschd.msc`
3. Press Enter
4. Look for `WeeklyCEOBriefing` in the task list

**Verify**:
- ✅ Task name: `WeeklyCEOBriefing`
- ✅ Trigger: Weekly, Monday, 8:00 AM
- ✅ Action: Run Python script
- ✅ Status: Ready

---

## Step 4: Manual Test (MUST be done outside Claude Code)

**CRITICAL**: Close this Claude Code session first!

**Then run**:
```bash
# Open a NEW Command Prompt (not inside Claude Code)
cd C:\Users\dell\Desktop\projects\class-project\personal-ai-employee
schtasks /run /tn "WeeklyCEOBriefing"
```

**What should happen**:
1. Task Scheduler runs the trigger script
2. Trigger script calls `ccr code` with the briefing prompt
3. Claude Code starts (new session)
4. Claude reads the weekly-ceo-briefing skill
5. Claude uses Odoo MCP tools to fetch data
6. Claude generates briefing file
7. File created at `Briefings/YYYY-MM-DD_Monday_Briefing.md`

---

## Step 5: Alternative Test (Direct Script Execution)

**Close Claude Code first, then**:
```bash
cd C:\Users\dell\Desktop\projects\class-project\personal-ai-employee
python app\scripts\weekly_briefing_trigger.py
```

**Expected**:
```
============================================================
Weekly CEO Briefing Trigger - Starting
============================================================
[2026-03-01 19:30:00] Triggering Claude Code...
[Claude Code starts and generates briefing]
[2026-03-01 19:32:15] Successfully generated briefing
============================================================
```

---

## Why Can't We Test Now?

**Current Situation**:
- We're inside Claude Code (this session)
- The trigger script tries to launch Claude Code with `ccr code`
- Claude Code detects nested session and refuses
- Error: "Claude Code cannot be launched inside another Claude Code session"

**Solution**:
- Close this Claude Code session
- Run the test from a regular Command Prompt
- The trigger script will successfully launch Claude Code

---

## Verification Checklist

After setup:

- [ ] Scheduled task exists: `schtasks /query /tn "WeeklyCEOBriefing"`
- [ ] Task shows in Task Scheduler GUI
- [ ] Task trigger is Monday at 8:00 AM
- [ ] Task action points to correct Python script
- [ ] Python executable path is correct
- [ ] Trigger script exists at `app/scripts/weekly_briefing_trigger.py`
- [ ] Odoo MCP server configured in `.mcp.json`
- [ ] Odoo credentials in `.env` file
- [ ] `Briefings/` directory exists (or will be created)

---

## Expected Briefing Output

**File**: `Briefings/YYYY-MM-DD_Monday_Briefing.md`

**Sections**:
1. Executive Summary (2-3 sentences)
2. Financial Performance (revenue, expenses, profit)
3. Outstanding Invoices (with overdue alerts)
4. Top Customers (by revenue)
5. Recurring Expenses (subscriptions)
6. Action Items (follow-ups, insights)

**Example**:
```markdown
# Weekly CEO Briefing

**Week of**: February 24, 2026 - March 2, 2026
**Generated**: 2026-03-03 08:00:15

---

## Executive Summary

Strong week with revenue of $12,450.00 and net profit of $9,250.00.
One overdue invoice requires follow-up.

---

## 💰 Financial Performance

| Metric | This Week |
|--------|-----------|
| Revenue | $12,450.00 |
| Expenses | $3,200.00 |
| Net Profit | $9,250.00 |

---

## 📋 Outstanding Invoices

**Total Outstanding**: $8,500.00 (3 invoices)

| Customer | Invoice | Amount | Due Date | Status |
|----------|---------|--------|----------|--------|
| Client A | INV/2026/0040 | $1,650.00 | Feb 15 | ⚠️ Overdue |
...
```

---

## Troubleshooting

### Issue: "Task not found"
**Fix**: Run setup script as Administrator

### Issue: "Python executable not found"
**Fix**: Check virtual environment path in setup script

### Issue: "Trigger script not found"
**Fix**: Verify file exists at `app/scripts/weekly_briefing_trigger.py`

### Issue: "Task runs but no briefing generated"
**Fix**:
1. Check Task Scheduler history for errors
2. Verify Odoo MCP server is running
3. Check `.env` has correct Odoo credentials
4. Test Odoo connection manually

### Issue: "Cannot launch Claude Code"
**Fix**: Make sure you're NOT inside an existing Claude Code session

---

## Next Steps

1. ✅ Run `scripts\setup_weekly_briefing_task.bat` (as Administrator)
2. ✅ Run `scripts\verify_weekly_briefing_task.bat` to confirm
3. ✅ View task in Task Scheduler GUI
4. ⏳ Close Claude Code and test manually
5. ⏳ Wait for Monday at 8 AM for automatic execution
6. ⏳ Check `Briefings/` directory for generated file

---

## Summary

**What Was Built**:
- ✅ Trigger script (`app/scripts/weekly_briefing_trigger.py`)
- ✅ Weekly CEO Briefing skill (`.claude/skills/weekly-ceo-briefing/`)
- ✅ Scheduler setup script (`scripts/setup_weekly_briefing_task.bat`)
- ✅ Verification script (`scripts/verify_weekly_briefing_task.bat`)
- ✅ Complete documentation

**What Works**:
- ✅ Scheduler setup and configuration
- ✅ Task creation and verification
- ✅ Trigger script (when run outside Claude Code)
- ✅ Odoo MCP integration
- ✅ Skills and documentation

**What to Test Next**:
- ⏳ Close Claude Code and run trigger script manually
- ⏳ Verify briefing file is generated
- ⏳ Check briefing contains Odoo data
- ⏳ Wait for Monday 8 AM automatic execution

---

**Status**: ✅ Setup Complete - Ready for Testing Outside Claude Code

# Research: Weekly CEO Briefing Technical Decisions

**Feature**: 004-weekly-ceo-briefing
**Date**: 2026-02-19
**Status**: Complete

## Overview

This document captures technical research and decisions made during the planning phase for the Weekly CEO Briefing feature. Each decision includes rationale, alternatives considered, and implementation guidance.

---

## Decision 1: Transaction File Format

### Question
What format should bank transactions use in the /Accounting folder?

### Decision
**CSV format** with standardized columns

### Rationale
- **Simplicity**: CSV is universally supported by banks and accounting software
- **No Dependencies**: Python's built-in `csv` module handles parsing
- **Human-Readable**: Can be viewed/edited in Excel or text editor
- **Extensibility**: Easy to add columns without breaking existing code

### Alternatives Considered

| Format | Pros | Cons | Rejected Because |
| ------ | ---- | ---- | ---------------- |
| JSON | Structured, flexible | Not bank-standard export format | Users unlikely to have JSON exports |
| Markdown Tables | Obsidian-native | Hard to parse reliably | Parsing complexity, no standard format |
| Excel (.xlsx) | Rich formatting | Requires openpyxl dependency | Adds dependency, overkill for simple data |

### Implementation

**Standard CSV Format**:
```csv
date,amount,description,category
2026-02-15,-49.99,Netflix Subscription,Entertainment
2026-02-14,1500.00,Client Payment - Project Alpha,Revenue
2026-02-13,-12.99,Spotify Premium,Entertainment
```

**Required Columns**:
- `date`: YYYY-MM-DD format
- `amount`: Decimal number (negative for expenses, positive for revenue)
- `description`: Transaction description text
- `category`: Optional categorization

**Parsing Strategy**:
```python
import csv
from datetime import datetime
from pathlib import Path

def parse_transactions(accounting_folder: Path, days: int = 7):
    transactions = []
    cutoff_date = datetime.now() - timedelta(days=days)

    for csv_file in accounting_folder.glob("*.csv"):
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                txn_date = datetime.strptime(row['date'], '%Y-%m-%d')
                if txn_date >= cutoff_date:
                    transactions.append({
                        'date': txn_date,
                        'amount': float(row['amount']),
                        'description': row['description'],
                        'category': row.get('category', 'Uncategorized')
                    })

    return transactions
```

**Test Cases**:
- Empty CSV file → returns empty list
- Malformed date → logs warning, skips row
- Missing required column → raises clear error
- Multiple CSV files → merges all transactions

---

## Decision 2: Scheduling Mechanism

### Question
How to reliably schedule Sunday 8 PM execution on Windows (primary platform)?

### Decision
**Hybrid approach**: Windows Task Scheduler triggers Python script

### Rationale
- **Reliability**: Task Scheduler is native, always-on, survives reboots
- **No Background Process**: Doesn't require Python process running 24/7
- **Cross-Platform**: Can provide cron instructions for Mac/Linux users
- **User Control**: Users can modify schedule via familiar OS tools

### Alternatives Considered

| Approach | Pros | Cons | Rejected Because |
| -------- | ---- | ---- | ---------------- |
| Python `schedule` library | Cross-platform code | Requires always-running process | Fragile, stops if process crashes |
| Pure Task Scheduler | Native, reliable | Windows-only | Need cross-platform support |
| Cloud scheduler (AWS EventBridge) | Always available | Requires cloud setup, costs | Adds complexity, not local-first |

### Implementation

**Windows Task Scheduler Setup**:

Create `scripts/run_weekly_audit.bat`:
```batch
@echo off
cd /d "%~dp0.."
call app\.venv\Scripts\activate.bat
python -m app.src.app.weekly_audit.audit_orchestrator
if %ERRORLEVEL% NEQ 0 (
    echo Weekly audit failed with error code %ERRORLEVEL%
    exit /b %ERRORLEVEL%
)
```

**Task Scheduler Configuration** (via PowerShell):
```powershell
$action = New-ScheduledTaskAction -Execute "C:\path\to\scripts\run_weekly_audit.bat"
$trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Sunday -At 8:00PM
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -RunOnlyIfNetworkAvailable:$false
Register-ScheduledTask -TaskName "WeeklyCEOBriefing" -Action $action -Trigger $trigger -Settings $settings -Description "Generate weekly CEO briefing report"
```

**Mac/Linux Cron Setup**:

Add to crontab:
```bash
# Run every Sunday at 8:00 PM
0 20 * * 0 cd /path/to/personal-ai-employee && source app/.venv/bin/activate && python -m app.src.app.weekly_audit.audit_orchestrator
```

**Scheduler Abstraction** (for future flexibility):
```python
# app/src/app/weekly_audit/schedulers/base_scheduler.py
from abc import ABC, abstractmethod

class BaseScheduler(ABC):
    @abstractmethod
    def schedule_weekly_audit(self, day: str, hour: int) -> bool:
        """Schedule the weekly audit. Returns True if successful."""
        pass

    @abstractmethod
    def is_scheduled(self) -> bool:
        """Check if audit is currently scheduled."""
        pass
```

**Test Strategy**:
- Manual trigger test: Run script directly to verify execution
- Schedule verification: Check Task Scheduler shows correct trigger
- Error handling: Test script behavior when vault is locked/inaccessible

---

## Decision 3: Claude Code Skill Invocation

### Question
How should the audit module trigger Claude Code to generate the briefing?

### Decision
**Subprocess call** to `claude --skill weekly-ceo-briefing` with context file

### Rationale
- **Simplicity**: Direct command-line invocation, no complex integration
- **Error Handling**: Can capture exit codes and stderr output
- **Flexibility**: Claude Code handles the actual briefing generation logic
- **Separation of Concerns**: Audit module prepares data, Claude generates prose

### Alternatives Considered

| Approach | Pros | Cons | Rejected Because |
| -------- | ---- | ---- | ---------------- |
| File-based trigger | Decoupled | Requires polling, timing issues | Adds complexity, less reliable |
| Direct API call | Programmatic | No public Claude Code API | Not available |
| Generate briefing in Python | No external dependency | Loses Claude's intelligence | Defeats purpose of AI Employee |

### Implementation

**Context File Preparation**:
```python
# app/src/app/weekly_audit/audit_orchestrator.py
import subprocess
import json
from pathlib import Path

def prepare_context_file(context_data: dict) -> Path:
    """Prepare context file for Claude Code skill."""
    context_file = Path("temp/weekly_audit_context.json")
    context_file.parent.mkdir(exist_ok=True)

    with open(context_file, 'w', encoding='utf-8') as f:
        json.dump(context_data, f, indent=2)

    return context_file

def invoke_claude_skill(week_start: str, week_end: str, context_file: Path) -> bool:
    """Invoke Claude Code skill to generate briefing."""
    try:
        result = subprocess.run(
            [
                'claude',
                '--skill', 'weekly-ceo-briefing',
                f'Generate weekly CEO briefing for {week_start} to {week_end}. Context: {context_file}'
            ],
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )

        if result.returncode == 0:
            logger.info(f"Briefing generated successfully: {result.stdout}")
            return True
        else:
            logger.error(f"Briefing generation failed: {result.stderr}")
            return False

    except subprocess.TimeoutExpired:
        logger.error("Briefing generation timed out after 5 minutes")
        return False
    except FileNotFoundError:
        logger.error("Claude Code not found. Is it installed and in PATH?")
        return False
```

**Context Data Structure**:
```json
{
  "week_start": "2026-02-10",
  "week_end": "2026-02-16",
  "business_goals": {
    "revenue_target": 10000,
    "current_revenue": 3500
  },
  "completed_tasks": [
    {"name": "Client proposal", "completed": "2026-02-15"},
    {"name": "Invoice processing", "completed": "2026-02-14"}
  ],
  "transactions": {
    "total_spent": 1250.50,
    "total_revenue": 3500.00,
    "subscription_count": 8
  },
  "subscriptions": [
    {
      "name": "Netflix",
      "amount": 49.99,
      "flags": ["no_activity_30_days"]
    }
  ]
}
```

**Error Handling Strategy**:
- Claude not installed → Log error, provide installation instructions
- Skill not found → Log error, provide skill setup instructions
- Timeout → Log warning, suggest manual generation
- Vault locked → Retry once after 30 seconds, then fail gracefully

**Test Cases**:
- Mock subprocess call to verify command construction
- Test timeout handling with slow mock
- Test error code handling (non-zero exit)
- Integration test with actual Claude Code (if available in CI)

---

## Decision 4: Task Metadata Format

### Question
How should expected task durations be stored for bottleneck analysis?

### Decision
**YAML frontmatter** (optional) with graceful degradation

### Rationale
- **Obsidian Compatible**: YAML frontmatter is standard in Obsidian
- **Easy Parsing**: Python's `pyyaml` library handles parsing
- **Optional**: Bottleneck analysis only runs when metadata exists
- **Extensible**: Can add other metadata fields in future

### Alternatives Considered

| Format | Pros | Cons | Rejected Because |
| ------ | ---- | ---- | ---------------- |
| Inline comments | Simple | Hard to parse reliably | Not structured |
| Separate metadata file | Clean separation | Extra file management | User friction |
| No metadata | Simplest | No bottleneck analysis | Loses valuable feature |

### Implementation

**Task File Format**:
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

**Parsing Strategy**:
```python
import yaml
from pathlib import Path
from datetime import datetime, timedelta

def parse_task_file(task_file: Path) -> dict:
    """Parse task file with optional YAML frontmatter."""
    content = task_file.read_text(encoding='utf-8')

    # Check for YAML frontmatter
    if content.startswith('---'):
        parts = content.split('---', 2)
        if len(parts) >= 3:
            try:
                metadata = yaml.safe_load(parts[1])
            except yaml.YAMLError:
                metadata = {}
        else:
            metadata = {}
    else:
        metadata = {}

    # Get completion date from file modification time
    completion_date = datetime.fromtimestamp(task_file.stat().st_mtime)

    return {
        'name': task_file.stem,
        'completion_date': completion_date,
        'expected_duration': metadata.get('expected_duration'),
        'actual_duration': metadata.get('actual_duration'),
        'priority': metadata.get('priority'),
        'project': metadata.get('project')
    }

def parse_duration(duration_str: str) -> timedelta:
    """Parse duration string like '2h', '30m', '1.5h' to timedelta."""
    if not duration_str:
        return None

    duration_str = duration_str.lower().strip()

    if duration_str.endswith('h'):
        hours = float(duration_str[:-1])
        return timedelta(hours=hours)
    elif duration_str.endswith('m'):
        minutes = float(duration_str[:-1])
        return timedelta(minutes=minutes)
    elif duration_str.endswith('d'):
        days = float(duration_str[:-1])
        return timedelta(days=days)
    else:
        # Assume hours if no unit
        return timedelta(hours=float(duration_str))
```

**Bottleneck Detection**:
```python
def identify_bottlenecks(tasks: list) -> list:
    """Identify tasks that took significantly longer than expected."""
    bottlenecks = []

    for task in tasks:
        if task['expected_duration'] and task['actual_duration']:
            expected = parse_duration(task['expected_duration'])
            actual = parse_duration(task['actual_duration'])

            if actual > expected * 1.5:  # 50% over expected
                delay_percent = ((actual - expected) / expected) * 100
                bottlenecks.append({
                    'task': task['name'],
                    'expected': str(expected),
                    'actual': str(actual),
                    'delay_percent': round(delay_percent, 1)
                })

    return sorted(bottlenecks, key=lambda x: x['delay_percent'], reverse=True)
```

**Graceful Degradation**:
- No frontmatter → Task still counted as completed, no bottleneck analysis
- Missing expected_duration → Skip bottleneck check for that task
- Invalid duration format → Log warning, skip bottleneck check

**Test Cases**:
- Task with complete metadata → Bottleneck detected correctly
- Task without frontmatter → Parsed successfully, no bottleneck
- Task with malformed YAML → Parsed without metadata
- Various duration formats (2h, 30m, 1.5h) → Parsed correctly

---

## Decision 5: Subscription Pattern Matching

### Question
How to reliably detect subscriptions from transaction descriptions?

### Decision
**Hybrid approach**: Domain matching + amount-based recurrence detection

### Rationale
- **High Accuracy**: Combining patterns catches more subscriptions
- **Maintainable**: Pattern list is simple to update
- **Low False Positives**: Amount recurrence confirms subscription
- **Extensible**: Can add ML-based detection later

### Alternatives Considered

| Approach | Pros | Cons | Rejected Because |
| -------- | ---- | ---- | ---------------- |
| Simple string matching | Fast, simple | Misses variations | Too many false negatives |
| Regex only | Flexible | Complex to maintain | Overkill for current needs |
| Amount-only detection | Language-agnostic | Many false positives | Unreliable alone |
| ML classification | Most accurate | Requires training data | Over-engineering |

### Implementation

**Subscription Patterns**:
```python
# app/src/app/weekly_audit/subscription_detector.py

SUBSCRIPTION_PATTERNS = {
    # Streaming services
    'netflix.com': 'Netflix',
    'netflix': 'Netflix',
    'spotify.com': 'Spotify',
    'spotify premium': 'Spotify',
    'disney+': 'Disney Plus',
    'hulu': 'Hulu',
    'amazon prime': 'Amazon Prime',
    'youtube premium': 'YouTube Premium',

    # Software/SaaS
    'adobe.com': 'Adobe Creative Cloud',
    'adobe': 'Adobe',
    'notion.so': 'Notion',
    'notion': 'Notion',
    'slack.com': 'Slack',
    'github.com': 'GitHub',
    'openai.com': 'OpenAI',
    'anthropic.com': 'Anthropic',
    'microsoft 365': 'Microsoft 365',
    'office 365': 'Microsoft 365',
    'google workspace': 'Google Workspace',
    'dropbox': 'Dropbox',

    # Development tools
    'jetbrains': 'JetBrains',
    'vercel': 'Vercel',
    'heroku': 'Heroku',
    'aws': 'Amazon Web Services',

    # Business services
    'quickbooks': 'QuickBooks',
    'xero': 'Xero',
    'mailchimp': 'Mailchimp',
    'zoom': 'Zoom',
}

def detect_subscriptions(transactions: list, lookback_months: int = 3) -> list:
    """Detect subscriptions using pattern matching and recurrence analysis."""
    subscriptions = {}

    # Phase 1: Pattern matching
    for txn in transactions:
        desc_lower = txn['description'].lower()

        for pattern, name in SUBSCRIPTION_PATTERNS.items():
            if pattern in desc_lower:
                if name not in subscriptions:
                    subscriptions[name] = {
                        'name': name,
                        'amounts': [],
                        'dates': [],
                        'pattern_matched': pattern
                    }

                subscriptions[name]['amounts'].append(txn['amount'])
                subscriptions[name]['dates'].append(txn['date'])

    # Phase 2: Recurrence confirmation
    confirmed_subscriptions = []

    for name, data in subscriptions.items():
        # Check if amounts are consistent (within 10% variance)
        if len(data['amounts']) >= 2:
            avg_amount = sum(data['amounts']) / len(data['amounts'])
            variance = max(abs(amt - avg_amount) / avg_amount for amt in data['amounts'])

            if variance < 0.10:  # Less than 10% variance
                # Check if dates are roughly monthly
                dates_sorted = sorted(data['dates'])
                if len(dates_sorted) >= 2:
                    intervals = [(dates_sorted[i+1] - dates_sorted[i]).days
                                for i in range(len(dates_sorted)-1)]
                    avg_interval = sum(intervals) / len(intervals)

                    # Monthly (25-35 days) or annual (350-380 days)
                    is_recurring = (25 <= avg_interval <= 35) or (350 <= avg_interval <= 380)

                    if is_recurring:
                        confirmed_subscriptions.append({
                            'name': name,
                            'amount': abs(avg_amount),
                            'last_seen': max(data['dates']),
                            'frequency': 'monthly' if avg_interval < 40 else 'annual',
                            'pattern': data['pattern_matched']
                        })

    return confirmed_subscriptions

def flag_subscriptions(subscriptions: list, transactions: list) -> list:
    """Add flags for subscriptions needing review."""
    flagged = []
    now = datetime.now()

    for sub in subscriptions:
        flags = []

        # Flag 1: No activity in 30+ days
        days_since_last = (now - sub['last_seen']).days
        if days_since_last > 30:
            flags.append(f"No activity in {days_since_last} days")

        # Flag 2: Cost increase >20%
        # (Would need historical data - implement in future iteration)

        # Flag 3: Duplicate functionality
        # (Would need service category mapping - implement in future iteration)

        if flags:
            sub['flags'] = flags
            flagged.append(sub)

    return flagged
```

**Test Cases**:
- Single transaction → Not detected as subscription
- Two transactions, same amount, ~30 days apart → Detected as monthly subscription
- Transactions with 15% amount variance → Not confirmed (too much variance)
- Netflix with various description formats → All matched to same subscription
- Non-subscription recurring payment (rent) → Not in pattern list, not detected

**Accuracy Target**: 90%+ detection rate for common subscriptions

**Future Enhancements**:
- User-defined patterns (custom subscription list)
- Cost increase tracking (requires historical data)
- Duplicate functionality detection (service categorization)
- ML-based pattern learning from user corrections

---

## Summary

All technical decisions have been made with clear rationale and implementation guidance. The feature is ready to proceed to Phase 1 (Design) with:

1. ✅ Transaction format: CSV with standard columns
2. ✅ Scheduling: Task Scheduler (Windows) / cron (Mac/Linux)
3. ✅ Claude invocation: Subprocess with context file
4. ✅ Task metadata: Optional YAML frontmatter
5. ✅ Subscription detection: Hybrid pattern + recurrence approach

**Next Phase**: Generate data-model.md, contracts/, and quickstart.md
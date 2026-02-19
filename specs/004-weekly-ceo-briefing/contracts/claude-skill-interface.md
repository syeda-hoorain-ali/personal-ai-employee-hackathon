# Claude Code Skill Interface Contract

**Feature**: 004-weekly-ceo-briefing
**Date**: 2026-02-19
**Version**: 1.0

## Overview

This document defines the interface contract between the Weekly Audit Python module and the Claude Code skill that generates the CEO briefing. The Python module prepares context data, and Claude Code uses its intelligence to generate the prose briefing.

---

## Skill Invocation

### Command Line Interface

```bash
claude --skill weekly-ceo-briefing "Generate weekly CEO briefing for [week_start] to [week_end]. Context: [context_file_path]"
```

**Parameters**:
- `week_start`: ISO date format (YYYY-MM-DD) for the start of the reporting week
- `week_end`: ISO date format (YYYY-MM-DD) for the end of the reporting week
- `context_file_path`: Absolute path to JSON context file

**Example**:
```bash
claude --skill weekly-ceo-briefing "Generate weekly CEO briefing for 2026-02-10 to 2026-02-16. Context: C:/Users/dell/Desktop/projects/class-project/personal-ai-employee/temp/weekly_audit_context.json"
```

---

## Input: Context File Format

### File Location
`temp/weekly_audit_context.json` (created by audit module, deleted after use)

### JSON Schema

```json
{
  "week_start": "YYYY-MM-DD",
  "week_end": "YYYY-MM-DD",
  "generated_at": "YYYY-MM-DDTHH:MM:SS",
  "vault_path": "/absolute/path/to/vault",

  "business_goals": {
    "revenue_target": 10000.00,
    "current_revenue": 3500.00,
    "key_metrics": [
      {
        "name": "Client response time",
        "target": "< 24 hours",
        "alert_threshold": "> 48 hours",
        "current_status": "On track"
      }
    ],
    "active_projects": [
      {
        "name": "Personal AI Employee",
        "deadline": "2026-02-28",
        "budget": 0,
        "days_remaining": 12
      }
    ]
  },

  "completed_tasks": [
    {
      "name": "Create client proposal",
      "completion_date": "2026-02-15",
      "priority": "high",
      "project": "client-alpha",
      "had_delay": true
    }
  ],

  "transactions": {
    "total_revenue": 3500.00,
    "total_expenses": 1250.50,
    "net_income": 2249.50,
    "transaction_count": 47,
    "top_expense_categories": [
      {"category": "Software", "amount": 450.00},
      {"category": "Entertainment", "amount": 150.00}
    ]
  },

  "subscriptions": [
    {
      "name": "Netflix",
      "amount": 49.99,
      "frequency": "monthly",
      "last_seen_date": "2026-02-15",
      "flags": ["No activity in 45 days"]
    }
  ],

  "bottlenecks": [
    {
      "task_name": "Create client proposal",
      "expected_duration": "2 hours",
      "actual_duration": "3.5 hours",
      "delay_percent": 75.0
    }
  ]
}
```

### Field Descriptions

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `week_start` | string (ISO date) | Yes | Start of reporting period |
| `week_end` | string (ISO date) | Yes | End of reporting period |
| `generated_at` | string (ISO datetime) | Yes | When context was generated |
| `vault_path` | string | Yes | Absolute path to Obsidian vault |
| `business_goals` | object | Yes | Business metrics and targets |
| `completed_tasks` | array | Yes | Tasks completed this week (can be empty) |
| `transactions` | object | Yes | Financial summary |
| `subscriptions` | array | Yes | Detected subscriptions (can be empty) |
| `bottlenecks` | array | Yes | Delayed tasks (can be empty) |

---

## Output: Briefing File

### File Location
`/Vault/Briefings/YYYY-MM-DD_Monday_Briefing.md`

**Naming Convention**: Date is the Monday following the reporting week (e.g., week ending 2026-02-16 → `2026-02-17_Monday_Briefing.md`)

### Markdown Structure

```markdown
---
generated: 2026-02-16T20:15:00
period: 2026-02-10 to 2026-02-16
---

# Monday Morning CEO Briefing

## Executive Summary

[2-3 sentence overview of the week's performance, highlighting key achievements and concerns]

## Revenue

- **This Week**: $3,500.00
- **MTD**: $3,500.00 (35% of $10,000 target)
- **Trend**: On track / Behind / Ahead

[Brief analysis of revenue performance]

## Completed Tasks

- **Create client proposal** (Feb 15) - High priority, Client Alpha project
- **Invoice processing** (Feb 14)
- **Email campaign setup** (Feb 13)

[Total: 12 tasks completed this week]

## Bottlenecks

| Task | Expected | Actual | Delay |
|------|----------|--------|-------|
| Create client proposal | 2 hours | 3.5 hours | 75% |

[Analysis of why delays occurred and suggestions for improvement]

## Proactive Suggestions

### Cost Optimization

1. **Netflix subscription** ($49.99/month)
   - No activity detected in 45 days
   - **Action**: Consider canceling to save $599.88/year

2. **Duplicate services detected**
   - Spotify Premium ($12.99) and YouTube Premium ($11.99) both provide music streaming
   - **Action**: Consider consolidating to save $155.88/year

### Process Improvements

[Suggestions based on bottleneck analysis and task patterns]

## Upcoming Deadlines

- **Personal AI Employee** - Due Feb 28 (12 days remaining)

---

*Generated by AI Employee v0.1*
```

### Section Requirements

| Section | Required | Can Be Empty | Empty Message |
|---------|----------|--------------|---------------|
| Executive Summary | Yes | No | Must always provide summary |
| Revenue | Yes | No | Show $0 if no transactions |
| Completed Tasks | Yes | Yes | "No tasks completed this week" |
| Bottlenecks | Yes | Yes | "No significant delays this week" |
| Proactive Suggestions | Yes | Yes | "No optimization opportunities identified" |
| Upcoming Deadlines | Yes | Yes | "No upcoming deadlines" |

---

## Exit Codes

| Code | Meaning | Action |
|------|---------|--------|
| 0 | Success | Briefing generated successfully |
| 1 | Context file not found | Check file path, verify audit module ran |
| 2 | Invalid context format | Validate JSON schema |
| 3 | Vault path inaccessible | Check vault path, ensure not locked |
| 4 | Briefing generation failed | Check Claude Code logs |
| 5 | Timeout | Increase timeout, check system resources |

---

## Error Handling

### Missing Data Scenarios

1. **No Business_Goals.md**
   - Use default template values
   - Show message: "Business goals not configured. Run setup to create Business_Goals.md"

2. **No completed tasks**
   - Show: "No tasks completed this week"
   - Suggest: "Consider reviewing task tracking process"

3. **No transaction data**
   - Show: "No transaction data available"
   - Suggest: "Ensure bank transactions are exported to /Accounting folder"

4. **No subscriptions detected**
   - Show: "No recurring subscriptions detected"
   - Note: "This is normal if you have few subscriptions or they're not in the pattern list"

### Error Recovery

```python
# Example error handling in audit module
try:
    result = subprocess.run(
        ['claude', '--skill', 'weekly-ceo-briefing', prompt],
        capture_output=True,
        text=True,
        timeout=300
    )

    if result.returncode == 0:
        logger.info("Briefing generated successfully")
        return True
    elif result.returncode == 3:
        logger.error("Vault inaccessible. Is Obsidian running?")
        return False
    else:
        logger.error(f"Briefing generation failed: {result.stderr}")
        return False

except subprocess.TimeoutExpired:
    logger.error("Briefing generation timed out after 5 minutes")
    return False
except FileNotFoundError:
    logger.error("Claude Code not found. Install from: https://claude.com/claude-code")
    return False
```

---

## Performance Requirements

| Metric | Target | Maximum |
|--------|--------|---------|
| Execution time | < 60 seconds | 120 seconds |
| Context file size | < 100 KB | 500 KB |
| Output file size | < 50 KB | 100 KB |
| Memory usage | < 100 MB | 200 MB |

---

## Skill Implementation Notes

The Claude Code skill should:

1. **Read context file** and parse JSON
2. **Validate data** against schema
3. **Generate executive summary** by analyzing all sections
4. **Calculate revenue metrics** and determine trend (on track/behind/ahead)
5. **Format completed tasks** with dates and priorities
6. **Analyze bottlenecks** and provide actionable suggestions
7. **Generate cost optimization suggestions** from flagged subscriptions
8. **Format upcoming deadlines** with days remaining
9. **Write briefing file** to /Briefings/ folder
10. **Return exit code** based on success/failure

### Skill Prompt Template

```markdown
You are generating a Monday Morning CEO Briefing for a small business owner.

**Context**: [JSON context data]

**Your task**:
1. Analyze the provided data (revenue, tasks, subscriptions, bottlenecks)
2. Generate a concise, actionable briefing in the specified markdown format
3. Focus on insights, not just data reporting
4. Provide specific, actionable suggestions
5. Keep tone professional but friendly

**Guidelines**:
- Executive summary: 2-3 sentences max
- Revenue trend: Compare to target and provide clear assessment
- Bottleneck analysis: Explain why delays matter and how to prevent them
- Cost optimization: Calculate annual savings for each suggestion
- Be proactive: Suggest improvements even if no obvious issues

**Output**: Write briefing to /Briefings/[date]_Monday_Briefing.md
```

---

## Testing Contract

### Unit Tests

```python
def test_skill_invocation_success():
    """Test successful skill invocation with valid context."""
    context = create_valid_context()
    result = invoke_claude_skill(context)
    assert result.returncode == 0
    assert briefing_file_exists()

def test_skill_invocation_missing_context():
    """Test skill invocation with missing context file."""
    result = invoke_claude_skill("nonexistent.json")
    assert result.returncode == 1

def test_skill_invocation_invalid_json():
    """Test skill invocation with malformed JSON."""
    context = create_invalid_json()
    result = invoke_claude_skill(context)
    assert result.returncode == 2
```

### Integration Tests

```python
def test_end_to_end_briefing_generation():
    """Test complete workflow from audit to briefing."""
    # Setup test data
    create_test_business_goals()
    create_test_completed_tasks()
    create_test_transactions()

    # Run audit
    orchestrator = WeeklyAuditOrchestrator(test_vault_path)
    result = orchestrator.run_weekly_audit()

    # Verify briefing
    assert result.success
    assert briefing_file_exists()
    assert briefing_has_all_sections()
    assert briefing_data_matches_context()
```

---

## Versioning

**Current Version**: 1.0

**Breaking Changes**:
- Changes to JSON schema structure
- Changes to output file format
- Changes to exit codes

**Non-Breaking Changes**:
- Adding optional fields to JSON schema
- Adding new sections to output (with backward compatibility)
- Performance improvements

**Deprecation Policy**:
- Deprecated features will be supported for 2 versions
- Deprecation warnings will be logged
- Migration guide will be provided

---

## Security Considerations

1. **Context File**: Contains business-sensitive data
   - Store in temp directory with restricted permissions
   - Delete immediately after use
   - Never commit to version control

2. **Vault Path**: Absolute paths may expose system structure
   - Validate path is within expected vault location
   - Sanitize paths in logs

3. **Error Messages**: May contain sensitive information
   - Sanitize error messages before logging
   - Don't expose full file paths in user-facing errors

---

## Future Enhancements

Potential additions to the contract (not in v1.0):

1. **Comparison Mode**: Compare current week to previous weeks
2. **Goal Progress Tracking**: Track progress toward quarterly/annual goals
3. **Predictive Analytics**: Forecast revenue based on trends
4. **Custom Sections**: User-defined sections in briefing
5. **Multi-Format Output**: PDF, HTML, email formats
6. **Notification Integration**: Email/Slack delivery of briefing

---

## Support and Troubleshooting

**Common Issues**:

1. **"Claude Code not found"**
   - Install Claude Code from https://claude.com/claude-code
   - Ensure `claude` command is in PATH

2. **"Context file not found"**
   - Check audit module logs for errors
   - Verify temp directory exists and is writable

3. **"Briefing generation timeout"**
   - Increase timeout in audit module
   - Check system resources (CPU, memory)
   - Reduce context data size if very large

4. **"Invalid JSON format"**
   - Validate context file with JSON linter
   - Check for encoding issues (use UTF-8)

**Debug Mode**:
```bash
# Run with verbose logging
claude --skill weekly-ceo-briefing --verbose "Generate weekly CEO briefing..."
```

---

## Changelog

### Version 1.0 (2026-02-19)
- Initial contract definition
- JSON schema for context file
- Markdown structure for briefing output
- Exit codes and error handling
- Performance requirements

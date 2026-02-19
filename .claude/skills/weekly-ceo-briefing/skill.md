# Weekly CEO Briefing Skill

## Purpose

Generate a comprehensive weekly business briefing for the CEO/business owner, including:
- Revenue progress and financial metrics
- Completed tasks and accomplishments
- Subscription cost optimization recommendations
- Task bottleneck identification
- Upcoming project deadlines

## Input

This skill expects a context file at `/tmp/weekly_audit_context.json` containing:

```json
{
  "business_goals": {
    "revenue_target": 10000.00,
    "current_revenue": 3500.00,
    "key_metrics": [...],
    "active_projects": [...],
    "subscription_rules": {...}
  },
  "transaction_summary": {
    "total_revenue": 3500.00,
    "total_expenses": 1250.50,
    "net_income": 2249.50,
    "transaction_count": 47,
    "subscription_count": 8,
    "top_expense_categories": [...],
    "period_start": "2026-02-10",
    "period_end": "2026-02-16"
  },
  "completed_tasks": [...],
  "subscriptions": [...],
  "bottlenecks": [...],
  "week_start": "2026-02-10",
  "week_end": "2026-02-16"
}
```

## Output

Generate a markdown briefing file at `/Briefings/YYYY-MM-DD_DayOfWeek_Briefing.md` with the following structure:

```markdown
# Weekly Business Briefing
**Week of**: [Week Start] - [Week End]
**Generated**: [Timestamp]

## Executive Summary
[2-3 sentence overview of the week's performance]

## Revenue & Financial Performance
- **Weekly Revenue**: $X,XXX.XX
- **Monthly Target**: $X,XXX.XX
- **Progress**: XX% of monthly target
- **Trend**: [On track / Behind / Ahead]
- **Net Income**: $X,XXX.XX (Revenue: $X,XXX.XX - Expenses: $X,XXX.XX)

### Top Expense Categories
1. Category Name: $XXX.XX
2. Category Name: $XXX.XX
3. Category Name: $XXX.XX

## Completed Tasks (XX tasks)
- [Task Name] - Completed on [Date]
- [Task Name] - Completed on [Date]

## Proactive Suggestions
### Cost Optimization
- [Subscription Name]: [Flag reason]. Consider [action] to save $XX.XX/month.
- [Subscription Name]: [Flag reason]. Consider [action].

### Process Improvements
- [Insight based on bottlenecks or patterns]

## Task Bottlenecks
| Task | Expected | Actual | Delay |
|------|----------|--------|-------|
| [Task Name] | Xh | Xh | XX% |

## Upcoming Deadlines
- **[Project Name]**: [Date] ([X days remaining])
- **[Project Name]**: [Date] ([X days remaining])

## Key Metrics Status
- [Metric Name]: [Current Status] (Target: [Target], Alert: [Threshold])
- [Metric Name]: [Current Status] (Target: [Target], Alert: [Threshold])
```

## Instructions

1. Read the context file from `/tmp/weekly_audit_context.json`
2. Parse the JSON data and extract all relevant information
3. Calculate derived metrics:
   - Revenue progress percentage: (current_revenue / revenue_target) * 100
   - Trend analysis: Compare to previous weeks if data available
   - Days remaining for project deadlines
4. Generate executive summary highlighting:
   - Most significant achievement or concern
   - Revenue performance
   - Key action items
5. Format all currency values with 2 decimal places
6. Sort completed tasks by completion date (most recent first)
7. Sort bottlenecks by delay percentage (highest first)
8. Sort upcoming deadlines by date (soonest first)
9. For subscriptions with flags, provide specific actionable recommendations
10. Write the complete briefing to the output file
11. Ensure all sections are present, even if empty (show "No items" messages)

## Error Handling

- If context file is missing: Log error and exit
- If business goals are missing: Use default values and add note to briefing
- If no completed tasks: Show "No tasks completed this week"
- If no subscriptions flagged: Show "All subscriptions appear active and optimized"
- If no bottlenecks: Show "No significant task delays detected"
- If no upcoming deadlines: Show "No project deadlines in the next 30 days"

## Example Usage

```bash
# Invoked by the audit orchestrator
claude --skill weekly-ceo-briefing
```

The skill will automatically read the context file, generate the briefing, and save it to the appropriate location.

## Notes

- This skill is designed to be invoked programmatically by the audit orchestrator
- The context file is prepared by the orchestrator before invoking this skill
- The output file path follows the naming convention: YYYY-MM-DD_DayOfWeek_Briefing.md
- All dates should be formatted as YYYY-MM-DD for consistency
- Currency values should include the $ symbol and 2 decimal places

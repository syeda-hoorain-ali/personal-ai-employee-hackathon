# Data Model: Weekly CEO Briefing

**Feature**: 004-weekly-ceo-briefing
**Date**: 2026-02-19
**Status**: Complete

## Overview

This document defines the core entities and their relationships for the Weekly CEO Briefing feature. All entities are designed to be technology-agnostic and focus on business concepts rather than implementation details.

---

## Entity Definitions

### 1. BusinessGoals

**Purpose**: Represents the business metrics, targets, and rules that guide the audit analysis.

**Attributes**:
- `revenue_target` (decimal): Monthly revenue goal in currency units
- `current_revenue` (decimal): Revenue accumulated in current month
- `key_metrics` (list): List of metric definitions with targets and alert thresholds
- `active_projects` (list): Current projects with deadlines and budgets
- `subscription_rules` (dict): Rules for flagging subscriptions (e.g., inactivity days, cost increase threshold)
- `last_updated` (date): When the goals were last modified
- `review_frequency` (string): How often goals should be reviewed (e.g., "weekly", "monthly")

**Source**: `/Vault/Business_Goals.md` (YAML frontmatter + markdown content)

**Validation Rules**:
- `revenue_target` must be positive number
- `last_updated` must be valid ISO date (YYYY-MM-DD)
- `key_metrics` must include: metric name, target value, alert threshold
- `active_projects` must include: name, deadline, budget (optional)

**Example**:
```python
BusinessGoals(
    revenue_target=10000.00,
    current_revenue=3500.00,
    key_metrics=[
        {
            'name': 'Client response time',
            'target': '< 24 hours',
            'alert_threshold': '> 48 hours'
        },
        {
            'name': 'Invoice payment rate',
            'target': '> 90%',
            'alert_threshold': '< 80%'
        }
    ],
    active_projects=[
        {
            'name': 'Personal AI Employee',
            'deadline': '2026-02-28',
            'budget': 0
        }
    ],
    subscription_rules={
        'inactivity_days': 30,
        'cost_increase_threshold': 0.20
    },
    last_updated='2026-02-19',
    review_frequency='weekly'
)
```

**Relationships**: None (standalone configuration entity)

---

### 2. CompletedTask

**Purpose**: Represents a task that was completed during the analysis period.

**Attributes**:
- `name` (string): Task name (derived from filename)
- `completion_date` (datetime): When the task was completed
- `expected_duration` (timedelta, optional): How long the task was expected to take
- `actual_duration` (timedelta, optional): How long the task actually took
- `priority` (string, optional): Task priority level (high, medium, low)
- `project` (string, optional): Associated project name
- `file_path` (Path): Location of the task file

**Source**: `/Done/*.md` files (file modification time for completion_date, YAML frontmatter for metadata)

**Validation Rules**:
- `name` must not be empty
- `completion_date` must be valid datetime
- `expected_duration` and `actual_duration` must be positive if present
- `priority` must be one of: "high", "medium", "low" (if present)

**Example**:
```python
CompletedTask(
    name='Create client proposal',
    completion_date=datetime(2026, 2, 15, 14, 30),
    expected_duration=timedelta(hours=2),
    actual_duration=timedelta(hours=3.5),
    priority='high',
    project='client-alpha',
    file_path=Path('/Vault/Done/create-client-proposal.md')
)
```

**Relationships**:
- May reference a project in `BusinessGoals.active_projects`
- Used to calculate bottlenecks when duration metadata exists

---

### 3. Transaction

**Purpose**: Represents a financial transaction (expense or revenue).

**Attributes**:
- `date` (date): Transaction date
- `amount` (decimal): Transaction amount (negative for expenses, positive for revenue)
- `description` (string): Transaction description text
- `category` (string, optional): Transaction category (e.g., "Entertainment", "Revenue", "Software")
- `source_file` (Path): CSV file containing this transaction

**Source**: `/Accounting/*.csv` files

**Validation Rules**:
- `date` must be valid date in YYYY-MM-DD format
- `amount` must be valid decimal number (can be negative)
- `description` must not be empty
- `category` defaults to "Uncategorized" if not provided

**Example**:
```python
Transaction(
    date=date(2026, 2, 15),
    amount=-49.99,
    description='Netflix Subscription',
    category='Entertainment',
    source_file=Path('/Vault/Accounting/february-2026.csv')
)
```

**Relationships**:
- Multiple transactions may be grouped into a `Subscription`
- Transactions contribute to revenue calculations in `TransactionSummary`

---

### 4. Subscription

**Purpose**: Represents a detected recurring subscription service.

**Attributes**:
- `name` (string): Subscription service name (e.g., "Netflix", "GitHub")
- `amount` (decimal): Average subscription cost
- `last_seen_date` (date): Most recent transaction date
- `frequency` (string): Recurrence frequency ("monthly" or "annual")
- `pattern_matched` (string): Pattern that identified this subscription
- `flags` (list): List of warning flags (e.g., "No activity in 45 days")
- `transaction_count` (int): Number of transactions detected for this subscription

**Source**: Derived from `Transaction` analysis via pattern matching and recurrence detection

**Validation Rules**:
- `name` must not be empty
- `amount` must be positive
- `frequency` must be "monthly" or "annual"
- `flags` must be list of strings (can be empty)

**Example**:
```python
Subscription(
    name='Netflix',
    amount=49.99,
    last_seen_date=date(2026, 2, 15),
    frequency='monthly',
    pattern_matched='netflix',
    flags=['No activity in 45 days'],
    transaction_count=3
)
```

**Relationships**:
- Derived from multiple `Transaction` entities
- Flags are evaluated against `BusinessGoals.subscription_rules`

---

### 5. TaskBottleneck

**Purpose**: Represents a task that took significantly longer than expected.

**Attributes**:
- `task_name` (string): Name of the delayed task
- `expected_duration` (timedelta): How long it was expected to take
- `actual_duration` (timedelta): How long it actually took
- `delay_percent` (float): Percentage over expected duration
- `completion_date` (date): When the task was completed

**Source**: Derived from `CompletedTask` entities with duration metadata

**Validation Rules**:
- `delay_percent` must be positive (only tasks that took longer are bottlenecks)
- `actual_duration` must be greater than `expected_duration`

**Example**:
```python
TaskBottleneck(
    task_name='Create client proposal',
    expected_duration=timedelta(hours=2),
    actual_duration=timedelta(hours=3.5),
    delay_percent=75.0,
    completion_date=date(2026, 2, 15)
)
```

**Relationships**:
- Derived from `CompletedTask` entities
- Included in `CEOBriefing.bottlenecks` section

---

### 6. TransactionSummary

**Purpose**: Aggregated financial metrics for the analysis period.

**Attributes**:
- `total_revenue` (decimal): Sum of all positive transactions
- `total_expenses` (decimal): Sum of all negative transactions (absolute value)
- `net_income` (decimal): Revenue minus expenses
- `transaction_count` (int): Total number of transactions
- `subscription_count` (int): Number of detected subscriptions
- `top_expense_categories` (list): Top 5 expense categories with amounts
- `period_start` (date): Start of analysis period
- `period_end` (date): End of analysis period

**Source**: Derived from aggregating `Transaction` entities

**Validation Rules**:
- All amounts must be non-negative (expenses are absolute values)
- `period_end` must be after `period_start`
- `transaction_count` must match actual transaction list length

**Example**:
```python
TransactionSummary(
    total_revenue=3500.00,
    total_expenses=1250.50,
    net_income=2249.50,
    transaction_count=47,
    subscription_count=8,
    top_expense_categories=[
        {'category': 'Software', 'amount': 450.00},
        {'category': 'Entertainment', 'amount': 150.00},
        {'category': 'Office Supplies', 'amount': 85.50}
    ],
    period_start=date(2026, 2, 10),
    period_end=date(2026, 2, 16)
)
```

**Relationships**:
- Aggregates multiple `Transaction` entities
- Used in `CEOBriefing.revenue_section`

---

### 7. CEOBriefing

**Purpose**: The complete generated briefing report.

**Attributes**:
- `week_start` (date): Start of the reporting week
- `week_end` (date): End of the reporting week
- `generated_date` (datetime): When the briefing was generated
- `executive_summary` (string): 2-3 sentence overview
- `revenue_section` (dict): Revenue metrics and progress
- `completed_tasks` (list): List of completed task summaries
- `bottlenecks` (list): List of task bottlenecks
- `proactive_suggestions` (list): Cost optimization and improvement suggestions
- `upcoming_deadlines` (list): Deadlines from active projects
- `output_path` (Path): Location of generated briefing file

**Source**: Generated by combining all analyzed data

**Validation Rules**:
- `week_end` must be after `week_start`
- `generated_date` must be after `week_end`
- All sections must be present (can be empty with appropriate messages)
- `output_path` must be in `/Briefings/` folder

**Example**:
```python
CEOBriefing(
    week_start=date(2026, 2, 10),
    week_end=date(2026, 2, 16),
    generated_date=datetime(2026, 2, 16, 20, 15),
    executive_summary='Strong week with $3,500 revenue. Completed 12 tasks. 8 subscriptions detected, 2 flagged for review.',
    revenue_section={
        'weekly_revenue': 3500.00,
        'monthly_target': 10000.00,
        'progress_percent': 35.0,
        'trend': 'On track'
    },
    completed_tasks=[
        {'name': 'Create client proposal', 'date': '2026-02-15'},
        {'name': 'Invoice processing', 'date': '2026-02-14'}
    ],
    bottlenecks=[
        {
            'task': 'Create client proposal',
            'expected': '2 hours',
            'actual': '3.5 hours',
            'delay': '75%'
        }
    ],
    proactive_suggestions=[
        'Netflix subscription: No activity in 45 days. Consider canceling to save $49.99/month.',
        'Spotify and YouTube Premium: Duplicate music streaming. Consider consolidating.'
    ],
    upcoming_deadlines=[
        {'project': 'Personal AI Employee', 'deadline': '2026-02-28', 'days_remaining': 12}
    ],
    output_path=Path('/Vault/Briefings/2026-02-16_Monday_Briefing.md')
)
```

**Relationships**:
- Aggregates data from all other entities
- Final output of the weekly audit process

---

## Entity Relationships Diagram

```
BusinessGoals (configuration)
    ↓ (provides targets and rules)
    ↓
TransactionSummary ← Transaction (many) → Subscription (detected from patterns)
    ↓                                           ↓
    ↓                                      (flagged against rules)
    ↓                                           ↓
CompletedTask (many) → TaskBottleneck (derived when duration metadata exists)
    ↓                        ↓
    ↓                        ↓
    └────────────────────────┴──────────→ CEOBriefing (final output)
```

---

## State Transitions

### Subscription Detection Flow

```
Transaction (raw data)
    ↓
[Pattern Matching] → Potential Subscription
    ↓
[Recurrence Analysis] → Confirmed Subscription
    ↓
[Flag Evaluation] → Flagged Subscription (if rules violated)
    ↓
Included in CEOBriefing
```

### Task Analysis Flow

```
Task File in /Done
    ↓
[File Modification Time] → CompletedTask (basic)
    ↓
[YAML Frontmatter Parsing] → CompletedTask (with metadata)
    ↓
[Duration Comparison] → TaskBottleneck (if delay > 50%)
    ↓
Included in CEOBriefing
```

---

## Data Validation Summary

| Entity | Required Fields | Optional Fields | Validation Rules |
|--------|----------------|-----------------|------------------|
| BusinessGoals | revenue_target, key_metrics | active_projects, subscription_rules | Positive numbers, valid dates |
| CompletedTask | name, completion_date | expected_duration, actual_duration, priority | Non-empty name, valid datetime |
| Transaction | date, amount, description | category | Valid date, numeric amount |
| Subscription | name, amount, last_seen_date, frequency | flags | Positive amount, valid frequency |
| TaskBottleneck | task_name, expected_duration, actual_duration, delay_percent | - | Positive delay, actual > expected |
| TransactionSummary | All fields required | - | Non-negative amounts, valid period |
| CEOBriefing | All fields required | - | Valid dates, all sections present |

---

## Implementation Notes

1. **Immutability**: All entities should be immutable after creation (use dataclasses with frozen=True)
2. **Validation**: Validate all entities at creation time, not during processing
3. **Error Handling**: Invalid data should log warnings and use sensible defaults, not crash
4. **Serialization**: All entities must be JSON-serializable for context file generation
5. **Testing**: Each entity should have unit tests for validation rules and edge cases

---

## Next Steps

- ✅ Data model complete
- ⏳ Create API contracts in `/contracts/` directory
- ⏳ Create quickstart guide
- ⏳ Update agent context
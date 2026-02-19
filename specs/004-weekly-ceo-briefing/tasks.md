# Implementation Tasks: Weekly Business and Accounting Audit with CEO Briefing

**Feature**: 004-weekly-ceo-briefing
**Branch**: `004-weekly-ceo-briefing`
**Generated**: 2026-02-19

## Overview

This document provides a complete, dependency-ordered task breakdown for implementing the Weekly CEO Briefing feature. Tasks are organized by user story to enable independent implementation and testing of each feature increment.

**Implementation Strategy**: MVP-first approach
- **MVP**: User Story 1 (Automated Weekly Business Review) - Delivers core value
- **Enhancement 1**: User Story 2 (Subscription Cost Optimization) - Adds cost insights
- **Enhancement 2**: User Story 3 (Task Bottleneck Identification) - Adds process insights

---

## Task Summary

| Phase     | User Story   | Task Count | Parallelizable | Independent Test                |
| --------- | ------------ | ---------- | -------------- | ------------------------------- |
| Phase 1   | Setup        | 6          | 4              | N/A (infrastructure)            |
| Phase 2   | Foundational | 5          | 3              | N/A (shared components)         |
| Phase 3   | US1 (P1)     | 12         | 7              | ✅ Complete briefing generation |
| Phase 4   | US2 (P2)     | 5          | 3              | ✅ Subscription detection       |
| Phase 5   | US3 (P3)     | 4          | 2              | ✅ Bottleneck analysis          |
| Phase 6   | Scheduling   | 4          | 2              | ✅ Automated execution          |
| Phase 7   | Polish       | 4          | 2              | N/A (cross-cutting)             |
| **Total** | -            | **40**     | **23**         | **4 stories**                   |

---

## Dependency Graph

```
Phase 1 (Setup)
    ↓
Phase 2 (Foundational)
    ↓
Phase 3 (US1 - MVP) ← Must complete before US2 or US3
    ↓
    ├─→ Phase 4 (US2) ← Independent of US3
    └─→ Phase 5 (US3) ← Independent of US2
    ↓
Phase 6 (Scheduling) ← Requires US1 complete
    ↓
Phase 7 (Polish)
```

**Key Dependencies**:
- US2 and US3 can be implemented in parallel after US1
- Scheduling requires US1 (core briefing) to be functional
- Each user story is independently testable

---

## Phase 1: Setup & Infrastructure

**Goal**: Initialize project structure, dependencies, and configuration files.

**Tasks**:

- [x] T001 Install Python dependencies in app/.venv: `uv add schedule pyyaml python-dateutil`
- [x] T002 [P] Create weekly_audit module directory at app/src/app/weekly_audit/ with __init__.py
- [x] T003 [P] Create schedulers subdirectory at app/src/app/weekly_audit/schedulers/ with __init__.py
- [x] T004 [P] Create Claude skill directory at .claude/skills/weekly-ceo-briefing/ with skill.md
- [x] T005 [P] Create Business_Goals.md template in project root (to be copied to vault by user)
- [x] T006 Create test directories: tests/unit/weekly_audit/ and tests/integration/

**Validation**: All directories exist, dependencies installed, skill file created

---

## Phase 2: Foundational Components

**Goal**: Create shared data structures and base components used by all user stories.

**Tasks**:

- [x] T007 [P] Create entity dataclasses in app/src/app/weekly_audit/entities.py (BusinessGoals, CompletedTask, Transaction, TransactionSummary, CEOBriefing)
- [x] T008 [P] Create base_scheduler.py abstract interface in app/src/app/weekly_audit/schedulers/
- [x] T009 [P] Create audit_orchestrator.py skeleton with run_weekly_audit() method in app/src/app/weekly_audit/
- [x] T010 Add weekly_audit logging configuration to app/src/app/logging_config.py
- [x] T011 Create test fixtures in tests/unit/weekly_audit/conftest.py (mock vault paths, sample data)

**Validation**: All base components importable, logging configured, test fixtures available

---

## Phase 3: User Story 1 - Automated Weekly Business Review (P1) 🎯 MVP

**Story Goal**: Generate automated weekly briefing with revenue, completed tasks, and business metrics.

**Independent Test**: Run audit manually and verify briefing file created in /Briefings/ with all sections populated from past 7 days of data.

**Acceptance Criteria**:
- ✅ Briefing file created at /Briefings/YYYY-MM-DD_Monday_Briefing.md
- ✅ Completed tasks listed with completion dates
- ✅ Revenue progress shown as percentage of monthly target

### US1 - Data Parsing Components

- [x] T012 [P] [US1] Implement BusinessGoalsParser.parse() in app/src/app/weekly_audit/business_goals_parser.py to read Business_Goals.md YAML frontmatter and extract revenue_target, key_metrics, active_projects
- [x] T013 [P] [US1] Implement TaskAnalyzer.analyze_completed_tasks() in app/src/app/weekly_audit/task_analyzer.py to scan /Done folder for files modified in last 7 days
- [x] T014 [P] [US1] Implement TransactionAnalyzer.parse_csv() in app/src/app/weekly_audit/transaction_analyzer.py to read CSV files from /Accounting folder with columns: date, amount, description, category
- [x] T015 [P] [US1] Implement TransactionAnalyzer.calculate_summary() in app/src/app/weekly_audit/transaction_analyzer.py to aggregate total_revenue, total_expenses, net_income

### US1 - Briefing Generation

- [x] T016 [P] [US1] Implement BriefingGenerator.generate_executive_summary() in app/src/app/weekly_audit/briefing_generator.py to create 2-3 sentence overview
- [x] T017 [P] [US1] Implement BriefingGenerator.generate_revenue_section() in app/src/app/weekly_audit/briefing_generator.py with weekly revenue, MTD, progress percentage, trend analysis
- [x] T018 [P] [US1] Implement BriefingGenerator.generate_completed_tasks_section() in app/src/app/weekly_audit/briefing_generator.py to format task list with dates
- [x] T019 [US1] Implement BriefingGenerator.write_briefing_file() in app/src/app/weekly_audit/briefing_generator.py to create markdown file at /Briefings/YYYY-MM-DD_Monday_Briefing.md

### US1 - Orchestration & Integration

- [x] T020 [US1] Implement AuditOrchestrator.prepare_context_data() in app/src/app/weekly_audit/audit_orchestrator.py to collect data from all parsers and create context dict
- [x] T021 [US1] Implement AuditOrchestrator.invoke_claude_skill() in app/src/app/weekly_audit/audit_orchestrator.py using subprocess to call 'claude --skill weekly-ceo-briefing' with context file
- [x] T022 [US1] Implement AuditOrchestrator.run_weekly_audit() in app/src/app/weekly_audit/audit_orchestrator.py to coordinate full workflow: parse → analyze → generate context → invoke Claude → verify output
- [x] T023 [US1] Create Claude skill prompt in .claude/skills/weekly-ceo-briefing/skill.md with instructions to read context file and generate briefing markdown

**US1 Validation**:
- Run: `python -m app.src.app.weekly_audit.audit_orchestrator`
- Verify: Briefing file exists with executive summary, revenue section, completed tasks
- Test with: Sample Business_Goals.md, 3 task files in /Done, 10 transactions in /Accounting

---

## Phase 4: User Story 2 - Subscription Cost Optimization (P2)

**Story Goal**: Automatically detect recurring subscriptions and flag unused or redundant services.

**Independent Test**: Add sample transactions with known subscription patterns (Netflix, Spotify) and verify they appear in briefing with appropriate flags.

**Acceptance Criteria**:
- ✅ Subscriptions detected from transaction patterns
- ✅ Subscriptions flagged when no activity in 30+ days
- ✅ Cost increase flags when subscription cost rises >20%

### US2 - Subscription Detection

- [x] T024 [P] [US2] Create SUBSCRIPTION_PATTERNS dictionary in app/src/app/weekly_audit/subscription_detector.py with common services (Netflix, Spotify, GitHub, Adobe, Notion, Slack, OpenAI, etc.)
- [x] T025 [P] [US2] Implement SubscriptionDetector.detect_subscriptions() in app/src/app/weekly_audit/subscription_detector.py using pattern matching + recurrence analysis (2+ transactions, <10% amount variance, 25-35 day intervals)
- [x] T026 [P] [US2] Implement SubscriptionDetector.flag_subscriptions() in app/src/app/weekly_audit/subscription_detector.py to add flags for: no activity in 30+ days, cost increase >20%
- [x] T027 [US2] Integrate SubscriptionDetector into AuditOrchestrator.prepare_context_data() in app/src/app/weekly_audit/audit_orchestrator.py
- [x] T028 [US2] Update BriefingGenerator to add proactive_suggestions section in app/src/app/weekly_audit/briefing_generator.py with cost optimization recommendations based on flagged subscriptions

**US2 Validation**:
- Run: `python -m app.src.app.weekly_audit.audit_orchestrator`
- Verify: Briefing includes "Proactive Suggestions" section with flagged subscriptions
- Test with: Transactions containing "Netflix" (2 occurrences, 30 days apart), "Spotify" (1 occurrence, 45 days ago)

---

## Phase 5: User Story 3 - Task Bottleneck Identification (P3)

**Story Goal**: Identify tasks that took longer than expected to help improve process efficiency.

**Independent Test**: Create task files with expected_duration and actual_duration metadata, verify bottlenecks table populated correctly.

**Acceptance Criteria**:
- ✅ Tasks with 50%+ delay appear in bottlenecks table
- ✅ Bottlenecks sorted by delay magnitude
- ✅ Shows "No significant delays" when no bottlenecks exist

### US3 - Bottleneck Analysis

- [x] T029 [P] [US3] Implement TaskAnalyzer.parse_task_metadata() in app/src/app/weekly_audit/task_analyzer.py to extract YAML frontmatter (expected_duration, actual_duration, priority, project)
- [x] T030 [P] [US3] Implement TaskAnalyzer.parse_duration() in app/src/app/weekly_audit/task_analyzer.py to convert duration strings (2h, 30m, 1.5h) to timedelta objects
- [x] T031 [US3] Implement TaskAnalyzer.identify_bottlenecks() in app/src/app/weekly_audit/task_analyzer.py to find tasks where actual > expected * 1.5, sorted by delay_percent descending
- [x] T032 [US3] Update BriefingGenerator to add bottlenecks section in app/src/app/weekly_audit/briefing_generator.py with table format: Task | Expected | Actual | Delay

**US3 Validation**:
- Run: `python -m app.src.app.weekly_audit.audit_orchestrator`
- Verify: Briefing includes "Bottlenecks" section with delayed tasks
- Test with: Task file with expected_duration: 2h, actual_duration: 3.5h (75% delay)

---

## Phase 6: Scheduling & Automation

**Goal**: Enable automated weekly execution every Sunday at 8:00 PM.

**Independent Test**: Verify scheduled task exists and triggers audit script successfully.

**Acceptance Criteria**:
- ✅ Scheduled task created for Sunday 8:00 PM
- ✅ Script executes without manual intervention
- ✅ Briefing generated automatically

### Scheduling Implementation

- [x] T033 [P] Create run_weekly_audit.bat script in scripts/ directory for Windows with: activate venv, run audit module, log errors
- [x] T034 [P] Create run_weekly_audit.sh script in scripts/ directory for Mac/Linux with: activate venv, run audit module, log errors
- [x] T035 Implement WindowsScheduler.schedule_weekly_audit() in app/src/app/weekly_audit/schedulers/windows_scheduler.py using PowerShell commands to create Task Scheduler entry
- [x] T036 Implement UnixScheduler.schedule_weekly_audit() in app/src/app/weekly_audit/schedulers/unix_scheduler.py to add crontab entry: 0 20 * * 0

**Validation**:
- Windows: Run PowerShell script to create task, verify in Task Scheduler GUI
- Mac/Linux: Run crontab setup, verify with `crontab -l`
- Test: Manually trigger scheduled task, verify briefing generated

---

## Phase 7: Polish & Cross-Cutting Concerns

**Goal**: Handle edge cases, improve error handling, and finalize documentation.

### Error Handling & Edge Cases

- [x] T037 [P] Add error handling in AuditOrchestrator for missing Business_Goals.md (use default template, log warning) in app/src/app/weekly_audit/audit_orchestrator.py
- [x] T038 [P] Add graceful degradation for empty data sources (no tasks, no transactions, no subscriptions) with appropriate messages in app/src/app/weekly_audit/briefing_generator.py
- [x] T039 Add duplicate briefing prevention in AuditOrchestrator.run_weekly_audit() to check if briefing already exists for current date in app/src/app/weekly_audit/audit_orchestrator.py
- [x] T040 Add comprehensive error logging for Claude Code invocation failures (not found, timeout, exit codes) in app/src/app/weekly_audit/audit_orchestrator.py

**Validation**:
- Test with missing Business_Goals.md → briefing generated with defaults
- Test with empty /Done folder → briefing shows "No tasks completed this week"
- Test running audit twice same day → second run skips generation
- Test with Claude Code not in PATH → clear error message logged

---

## Parallel Execution Opportunities

Tasks marked with [P] can be executed in parallel within their phase:

### Phase 1 (Setup) - 4 parallel tasks
```bash
# Can run simultaneously:
T002, T003, T004, T005
```

### Phase 2 (Foundational) - 3 parallel tasks
```bash
# Can run simultaneously:
T007, T008, T009
```

### Phase 3 (US1) - 7 parallel tasks
```bash
# Data parsing (can run simultaneously):
T012, T013, T014, T015

# Briefing generation (can run simultaneously after parsing):
T016, T017, T018
```

### Phase 4 (US2) - 3 parallel tasks
```bash
# Can run simultaneously:
T024, T025, T026
```

### Phase 5 (US3) - 2 parallel tasks
```bash
# Can run simultaneously:
T029, T030
```

### Phase 6 (Scheduling) - 2 parallel tasks
```bash
# Can run simultaneously:
T033, T034
```

### Phase 7 (Polish) - 2 parallel tasks
```bash
# Can run simultaneously:
T037, T038
```

---

## Testing Strategy

**Note**: Tests are not included in this task breakdown as they were not explicitly requested in the specification. If TDD approach is desired, add test tasks before each implementation task.

**Manual Testing Approach**:
1. After each user story phase, run manual validation
2. Use sample data provided in validation sections
3. Verify output matches acceptance criteria

**Integration Testing**:
- End-to-end test after US1 complete
- Regression test after US2 and US3 to ensure US1 still works
- Scheduling test after Phase 6

---

## Implementation Checklist

### MVP Delivery (US1 Only)
- [ ] Phase 1: Setup complete (T001-T006)
- [ ] Phase 2: Foundational complete (T007-T011)
- [ ] Phase 3: US1 complete (T012-T023)
- [ ] Manual validation: Briefing generated with revenue, tasks, metrics
- [ ] **MVP READY** - Can deliver value to user

### Enhancement 1 (Add US2)
- [ ] Phase 4: US2 complete (T024-T028)
- [ ] Manual validation: Subscriptions detected and flagged
- [ ] Regression test: US1 still works

### Enhancement 2 (Add US3)
- [ ] Phase 5: US3 complete (T029-T032)
- [ ] Manual validation: Bottlenecks identified
- [ ] Regression test: US1 and US2 still work

### Automation (Scheduling)
- [ ] Phase 6: Scheduling complete (T033-T036)
- [ ] Manual validation: Scheduled task triggers successfully
- [ ] End-to-end test: Wait for Sunday 8 PM or manually trigger

### Production Ready
- [ ] Phase 7: Polish complete (T037-T040)
- [ ] All edge cases handled
- [ ] Error logging comprehensive
- [ ] Documentation updated

---

## File Paths Reference

**New Files Created**:
```
app/src/app/weekly_audit/
├── __init__.py
├── entities.py
├── audit_orchestrator.py
├── business_goals_parser.py
├── task_analyzer.py
├── transaction_analyzer.py
├── subscription_detector.py
├── briefing_generator.py
└── schedulers/
    ├── __init__.py
    ├── base_scheduler.py
    ├── windows_scheduler.py
    └── unix_scheduler.py

.claude/skills/weekly-ceo-briefing/
└── skill.md

scripts/
├── run_weekly_audit.bat
└── run_weekly_audit.sh

app/tests/
├──integration
│   └── test_weekly_audit_e2e.py
└── unit/weekly_audit/
    └── conftest.py

AI_Employee_Vault/
└──Business_Goals.md (template in project root)
```

**Modified Files**:
```
app/src/app/logging_config.py (add weekly_audit logger)
```

---

## Next Steps

1. **Start with MVP**: Implement Phase 1-3 (US1) first
2. **Validate MVP**: Test briefing generation manually
3. **Iterate**: Add US2 and US3 incrementally
4. **Automate**: Set up scheduling after core features work
5. **Polish**: Handle edge cases and improve error handling

**Estimated Effort**:
- MVP (US1): ~8-10 hours
- US2: ~2-3 hours
- US3: ~2-3 hours
- Scheduling: ~2 hours
- Polish: ~2 hours
- **Total**: ~16-20 hours

---

## Support

**Documentation References**:
- [Feature Specification](./spec.md)
- [Implementation Plan](./plan.md)
- [Data Model](./data-model.md)
- [API Contracts](./contracts/claude-skill-interface.md)
- [Quickstart Guide](./quickstart.md)
- [Research Decisions](./research.md)

**Key Design Decisions**:
- Transaction format: CSV (see research.md)
- Scheduling: Task Scheduler/cron (see research.md)
- Claude invocation: Subprocess (see research.md)
- Task metadata: Optional YAML frontmatter (see research.md)
- Subscription detection: Hybrid pattern + recurrence (see research.md)

# Implementation Plan: Weekly Business and Accounting Audit with CEO Briefing

**Branch**: `004-weekly-ceo-briefing` | **Date**: 2026-02-19 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/004-weekly-ceo-briefing/spec.md`

## Summary

Implement an autonomous weekly audit system that analyzes business performance data (completed tasks, bank transactions, business goals) and generates a comprehensive "Monday Morning CEO Briefing" report every Sunday at 8:00 PM. The system will integrate with the existing Orchestrator architecture, adding a scheduled component that triggers Claude Code to generate briefings with proactive insights on revenue, subscriptions, and task bottlenecks.

## Technical Context

**Language/Version**: Python 3.12 (matching existing project)
**Primary Dependencies**:
- Existing: pathlib, threading, logging (from orchestrator)
- New: schedule (for time-based triggers), pyyaml (for Business_Goals.md parsing), python-dateutil (for date calculations)

**Storage**: File-based (Obsidian vault structure)
- `/Vault/Business_Goals.md` - Business metrics and targets
- `/Done/*.md` - Completed task files
- `/Accounting/*.csv` or `*.md` - Bank transaction data [NEEDS CLARIFICATION: transaction file format]
- `/Briefings/YYYY-MM-DD_Monday_Briefing.md` - Generated briefings

**Testing**: pytest (matching existing project structure)
- Unit tests for each analyzer component
- Integration tests for end-to-end briefing generation
- Mock data for transaction and task analysis

**Target Platform**: Windows 10+ (primary), Mac/Linux (secondary via cron)
**Project Type**: Single project (extends existing app/src/app structure)

**Performance Goals**:
- Briefing generation completes within 2 minutes
- Handles up to 1000 transactions per week
- Processes up to 100 completed tasks per week

**Constraints**:
- Must not block other orchestrator operations
- Vault must be accessible (not locked) during scheduled execution
- No external API dependencies (uses local vault data only)

**Scale/Scope**:
- Single-user system (one business owner)
- Weekly execution (52 briefings per year)
- Designed for small business scale (< 1000 transactions/week)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**Note**: Constitution file contains template placeholders. Applying general software engineering principles:

### Pre-Research Gates

- ✅ **Simplicity**: Feature adds new capability without modifying existing watchers
- ✅ **Testability**: Each component (parser, analyzer, generator) is independently testable
- ✅ **Integration**: Extends existing Orchestrator pattern rather than creating parallel system
- ⚠️ **Clarity Needed**: Transaction file format must be determined before implementation

### Post-Design Gates (to be validated after Phase 1)

- [ ] **Data Model**: Business entities clearly defined
- [ ] **Contracts**: Claude Code skill interface documented
- [ ] **Testing Strategy**: Test cases cover all user scenarios from spec

## Project Structure

### Documentation (this feature)

```text
specs/004-weekly-ceo-briefing/
├── plan.md              # This file
├── research.md          # Phase 0: Technical decisions and patterns
├── data-model.md        # Phase 1: Entity definitions
├── quickstart.md        # Phase 1: Setup and usage guide
├── contracts/           # Phase 1: Skill interface and data formats
│   └── claude-skill-interface.md
└── tasks.md             # Phase 2: Implementation tasks (created by /sp.tasks)
```

### Source Code (repository root)

```text
app/src/app/
├── weekly_audit/                    # NEW: Weekly audit module
│   ├── __init__.py
│   ├── audit_orchestrator.py       # Coordinates audit execution
│   ├── business_goals_parser.py    # Parses Business_Goals.md
│   ├── task_analyzer.py            # Analyzes completed tasks
│   ├── transaction_analyzer.py     # Analyzes bank transactions
│   ├── subscription_detector.py    # Detects recurring subscriptions
│   ├── briefing_generator.py       # Generates briefing markdown
│   └── schedulers/
│       ├── __init__.py
│       ├── base_scheduler.py       # Abstract scheduler interface
│       ├── windows_scheduler.py    # Task Scheduler integration
│       └── unix_scheduler.py       # Cron integration
│
├── orchestrator.py                  # MODIFIED: Add weekly audit component
├── file_processor.py                # EXISTING: No changes
├── vault_reader.py                  # EXISTING: Used by audit module
└── vault_writer.py                  # EXISTING: Used by briefing generator

.claude/skills/
└── weekly-ceo-briefing/             # NEW: Claude Code skill
    └── skill.md                     # Skill definition and prompt

tests/
├── unit/
│   └── weekly_audit/                # NEW: Unit tests
│       ├── test_business_goals_parser.py
│       ├── test_task_analyzer.py
│       ├── test_transaction_analyzer.py
│       ├── test_subscription_detector.py
│       └── test_briefing_generator.py
│
└── integration/
    └── test_weekly_audit_e2e.py     # NEW: End-to-end test

Vault/                               # NEW: Vault structure additions
├── Business_Goals.md                # NEW: Business metrics template
└── Briefings/                       # NEW: Generated briefings folder
```

**Structure Decision**: Extends existing single-project structure with a new `weekly_audit` module under `app/src/app/`. This maintains consistency with the current architecture (orchestrator + specialized components) and allows the weekly audit to be managed as another orchestrator component alongside existing watchers.

## Complexity Tracking

No constitution violations requiring justification. The design follows existing patterns and adds a new component without introducing architectural complexity.

## Phase 0: Research & Technical Decisions

### Research Tasks

1. **Transaction File Format Investigation**
   - **Question**: What format are bank transactions stored in the /Accounting folder?
   - **Options**: CSV (most common), JSON, Markdown tables, Excel
   - **Decision Criteria**: Must be parseable without external dependencies, human-readable
   - **Output**: Document chosen format and parsing strategy in research.md

2. **Scheduling Mechanism Selection**
   - **Question**: How to reliably schedule Sunday 8 PM execution on Windows?
   - **Options**:
     - Python `schedule` library (requires always-running process)
     - Windows Task Scheduler (native, reliable)
     - Hybrid approach (Task Scheduler triggers Python script)
   - **Decision Criteria**: Reliability, user setup complexity, cross-platform support
   - **Output**: Document chosen approach with setup instructions

3. **Claude Code Skill Invocation Pattern**
   - **Question**: How does the audit module trigger Claude Code with the skill?
   - **Options**:
     - Subprocess call to `claude --skill weekly-ceo-briefing`
     - File-based trigger (create file that Claude monitors)
     - Direct integration with Claude Code API (if available)
   - **Decision Criteria**: Reliability, error handling, user experience
   - **Output**: Document invocation pattern and error handling strategy

4. **Task Metadata Format**
   - **Question**: How are expected durations stored in task files?
   - **Options**:
     - YAML frontmatter (e.g., `expected_duration: 2h`)
     - Inline metadata (e.g., `<!-- duration: 2h -->`)
     - Separate metadata file
     - No metadata (bottleneck analysis optional)
   - **Decision Criteria**: Obsidian compatibility, ease of parsing, user convenience
   - **Output**: Document metadata format or mark bottleneck analysis as optional

5. **Subscription Pattern Matching Strategy**
   - **Question**: How to reliably detect subscriptions from transaction descriptions?
   - **Research**: Common subscription patterns, false positive handling
   - **Options**:
     - Simple string matching (fast, may miss variations)
     - Regex patterns (flexible, more complex)
     - Amount-based detection (recurring same amounts)
     - Hybrid approach
   - **Decision Criteria**: Accuracy (90%+ detection rate), maintainability
   - **Output**: Document pattern matching rules and test cases

### Research Deliverable

Create `research.md` with:
- Decision for each research task
- Rationale and alternatives considered
- Code examples or configuration snippets
- Test strategy for each decision

## Phase 1: Design & Contracts

### Data Model (`data-model.md`)

Define entities and their relationships:

1. **BusinessGoals**
   - Attributes: revenue_target, key_metrics, active_projects, subscription_rules
   - Source: `/Vault/Business_Goals.md`
   - Validation: Required fields, date formats, numeric ranges

2. **CompletedTask**
   - Attributes: name, completion_date, expected_duration (optional), actual_duration (optional)
   - Source: `/Done/*.md` (file modification time)
   - Relationships: None (standalone)

3. **Transaction**
   - Attributes: date, amount, description, category (optional)
   - Source: `/Accounting/*.csv` or other format
   - Validation: Date format, numeric amount

4. **Subscription**
   - Attributes: name, amount, last_seen_date, pattern_matched
   - Derived from: Transaction analysis
   - Flags: no_activity_days, cost_increase_percent

5. **CEOBriefing**
   - Attributes: week_start, week_end, generated_date, sections
   - Sections: executive_summary, revenue, completed_tasks, bottlenecks, suggestions, deadlines
   - Output: `/Briefings/YYYY-MM-DD_Monday_Briefing.md`

### API Contracts (`contracts/`)

#### Claude Code Skill Interface

Document the skill invocation contract:

```markdown
# Weekly CEO Briefing Skill Contract

## Invocation
```bash
claude --skill weekly-ceo-briefing "Generate weekly CEO briefing for [week_start] to [week_end]"
```

## Input Context
- Business_Goals.md content
- List of completed tasks (from /Done folder)
- Transaction summary (from audit module)
- Detected subscriptions with flags

## Output
- Briefing file at /Briefings/YYYY-MM-DD_Monday_Briefing.md
- Exit code 0 on success, non-zero on failure
- Logs to stdout/stderr for debugging

## Error Handling
- Missing Business_Goals.md: Use default template
- No completed tasks: Show "No completed tasks this week"
- No transactions: Show "No transaction data available"
```

#### Audit Module Interface

Document the Python module interfaces:

```python
# audit_orchestrator.py
class WeeklyAuditOrchestrator:
    def run_weekly_audit() -> BriefingResult

# business_goals_parser.py
class BusinessGoalsParser:
    def parse(file_path: Path) -> BusinessGoals

# task_analyzer.py
class TaskAnalyzer:
    def analyze_completed_tasks(done_folder: Path, days: int = 7) -> List[CompletedTask]

# transaction_analyzer.py
class TransactionAnalyzer:
    def analyze_transactions(accounting_folder: Path, days: int = 7) -> TransactionSummary

# subscription_detector.py
class SubscriptionDetector:
    def detect_subscriptions(transactions: List[Transaction]) -> List[Subscription]

# briefing_generator.py
class BriefingGenerator:
    def generate(context: BriefingContext) -> Path
```

### Quickstart Guide (`quickstart.md`)

Create user-facing setup and usage documentation:

1. **Prerequisites**: Python 3.12, Claude Code installed
2. **Installation**: Dependencies, vault structure setup
3. **Configuration**: Business_Goals.md template, scheduling setup
4. **First Run**: Manual test execution
5. **Scheduling**: Platform-specific instructions (Windows Task Scheduler, cron)
6. **Troubleshooting**: Common issues and solutions

### Agent Context Update

After Phase 1 completion, run:

```bash
.specify/scripts/bash/update-agent-context.sh claude
```

This will update `.claude/settings.local.json` or similar with:
- New dependencies: schedule, pyyaml, python-dateutil
- New modules: weekly_audit
- Technology additions: Task Scheduler integration, cron support

## Phase 2: Task Generation

**Note**: Phase 2 (task generation) is handled by the `/sp.tasks` command, not `/sp.plan`.

After completing Phase 0 (research) and Phase 1 (design), the next step is:

```bash
/sp.tasks
```

This will generate `tasks.md` with:
- Dependency-ordered implementation tasks
- Test cases for each task
- Acceptance criteria
- Estimated complexity

## Next Steps

1. ✅ Specification complete (`spec.md`)
2. ✅ Implementation plan complete (this file)
3. ⏳ **Next**: Run Phase 0 research to resolve NEEDS CLARIFICATION items
4. ⏳ **Then**: Generate Phase 1 design artifacts (data-model.md, contracts/, quickstart.md)
5. ⏳ **Then**: Run `/sp.tasks` to generate implementation tasks
6. ⏳ **Finally**: Execute tasks with `/sp.implement`

## Architectural Decision Points

The following decisions will be documented as ADRs if they meet significance criteria:

1. **Scheduling Architecture** (Phase 0)
   - Impact: Long-term reliability and user experience
   - Alternatives: Python schedule vs Task Scheduler vs hybrid
   - Scope: Cross-cutting (affects deployment and maintenance)
   - **ADR Candidate**: Yes (if multiple viable options with significant tradeoffs)

2. **Transaction Data Format** (Phase 0)
   - Impact: Parsing complexity and extensibility
   - Alternatives: CSV vs JSON vs Markdown
   - Scope: Affects data ingestion and future integrations
   - **ADR Candidate**: Maybe (if format choice has long-term implications)

3. **Claude Code Integration Pattern** (Phase 0)
   - Impact: Reliability and error handling
   - Alternatives: Subprocess vs file-based vs API
   - Scope: Core feature functionality
   - **ADR Candidate**: Yes (critical integration point)

**Note**: ADR suggestions will be made after research phase when decisions are finalized.
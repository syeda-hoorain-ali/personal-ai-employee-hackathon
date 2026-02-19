# Feature Specification: Weekly Business and Accounting Audit with CEO Briefing

**Feature Branch**: `004-weekly-ceo-briefing`
**Created**: 2026-02-19
**Status**: Draft
**Input**: Implement an autonomous weekly audit system that analyzes business performance and generates a "Monday Morning CEO Briefing" report.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Automated Weekly Business Review (Priority: P1)

As a business owner, I want to receive an automated weekly briefing every Monday morning that summarizes my business performance, so I can start the week with clear visibility into revenue, completed work, and areas needing attention.

**Why this priority**: This is the core value proposition - transforming the AI from reactive to proactive. Without this, the feature doesn't exist.

**Independent Test**: Can be fully tested by running the audit script manually on Sunday night and verifying a briefing file is created in /Briefings/ with all required sections populated with data from the past 7 days.

**Acceptance Scenarios**:

1. **Given** it's Sunday at 8:00 PM, **When** the scheduled audit runs, **Then** a new briefing file is created at `/Briefings/YYYY-MM-DD_Monday_Briefing.md` with the current date
2. **Given** there are completed tasks in /Done folder from the past week, **When** the audit runs, **Then** the briefing lists all completed tasks with their completion dates
3. **Given** Business_Goals.md contains revenue targets, **When** the audit runs, **Then** the briefing shows current revenue progress as a percentage of the monthly target

---

### User Story 2 - Subscription Cost Optimization (Priority: P2)

As a business owner, I want the system to automatically detect recurring subscriptions and flag unused or redundant services, so I can reduce unnecessary expenses without manual tracking.

**Why this priority**: Provides immediate cost savings and demonstrates proactive intelligence, but the briefing is still valuable without this feature.

**Independent Test**: Can be tested by adding sample bank transactions with known subscription patterns (Netflix, Spotify, etc.) and verifying they appear in the "Cost Optimization" section with appropriate flags.

**Acceptance Scenarios**:

1. **Given** bank transactions contain recurring charges matching subscription patterns, **When** the audit runs, **Then** the briefing lists all detected subscriptions with amounts
2. **Given** a subscription hasn't been used in 30+ days, **When** the audit runs, **Then** the briefing flags it for review with "No activity in X days"
3. **Given** a subscription cost increased by more than 20%, **When** the audit runs, **Then** the briefing flags it with "Cost increased by X%"

---

### User Story 3 - Task Bottleneck Identification (Priority: P3)

As a business owner, I want the system to identify tasks that took longer than expected, so I can understand where my processes are slowing down and make improvements.

**Why this priority**: Provides valuable insights but requires more complex analysis. The briefing is useful without this feature.

**Independent Test**: Can be tested by creating task files in /Done with metadata showing expected vs actual completion times, then verifying the bottlenecks table is populated correctly.

**Acceptance Scenarios**:

1. **Given** a task file contains expected duration metadata, **When** actual completion time exceeds expected by 50%+, **Then** the task appears in the bottlenecks table
2. **Given** multiple delayed tasks exist, **When** the audit runs, **Then** bottlenecks are sorted by delay magnitude (largest delays first)
3. **Given** no tasks exceeded expected duration, **When** the audit runs, **Then** the bottlenecks section shows "No significant delays this week"

---

### Edge Cases

- What happens when /Done folder is empty (no completed tasks this week)?
- What happens when Business_Goals.md doesn't exist or is malformed?
- What happens when /Accounting folder has no transaction data?
- How does the system handle duplicate briefing generation (script runs twice on same day)?
- What happens when a subscription pattern matches multiple times in one transaction description?
- How does the system handle tasks without expected duration metadata?
- What happens when the scheduled script runs but the vault is locked or inaccessible?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST read Business_Goals.md to extract revenue targets, key metrics, active projects, and subscription audit rules
- **FR-002**: System MUST scan /Done folder for files modified within the last 7 days to identify completed tasks
- **FR-003**: System MUST read bank transaction data from /Accounting folder to analyze spending patterns
- **FR-004**: System MUST detect subscriptions by pattern matching transaction descriptions against a predefined list (Netflix, Spotify, GitHub, Adobe, Notion, Slack, OpenAI, etc.)
- **FR-005**: System MUST flag subscriptions that meet any of these criteria: no activity in 30+ days, cost increase >20%, or duplicate functionality with another detected subscription
- **FR-006**: System MUST calculate total revenue for the week and compare it to monthly targets from Business_Goals.md
- **FR-007**: System MUST identify task bottlenecks by comparing expected vs actual completion times (when metadata is available)
- **FR-008**: System MUST generate a briefing file at `/Briefings/YYYY-MM-DD_Monday_Briefing.md` with all required sections populated
- **FR-009**: System MUST execute automatically every Sunday at 8:00 PM via scheduled task (cron on Mac/Linux, Task Scheduler on Windows)
- **FR-010**: System MUST integrate with existing Orchestrator.py to trigger Claude Code with the weekly-ceo-briefing skill
- **FR-011**: System MUST handle missing or incomplete data gracefully by showing appropriate messages (e.g., "No completed tasks this week" instead of errors)
- **FR-012**: System MUST prevent duplicate briefings by checking if a briefing already exists for the current date before generating

### Key Entities

- **Business Goals**: Contains revenue targets, key metrics thresholds, active projects with deadlines, and subscription audit rules. Stored in `/Vault/Business_Goals.md`
- **Completed Task**: Represents work finished during the week. Stored as markdown files in `/Done` folder with file modification time indicating completion date
- **Bank Transaction**: Financial transaction record containing date, amount, description, and category. Stored in `/Accounting` folder (format to be determined by existing accounting setup)
- **Subscription**: Recurring service charge detected via pattern matching. Contains name, amount, date, and usage status
- **CEO Briefing**: Generated report containing executive summary, revenue metrics, completed tasks, bottlenecks, proactive suggestions, and upcoming deadlines. Stored in `/Briefings` folder

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A new briefing file is automatically created every Sunday night without manual intervention
- **SC-002**: All briefing sections are populated with accurate data from the past 7 days (no empty sections when data exists)
- **SC-003**: Subscription detection correctly identifies at least 90% of known recurring charges from the predefined pattern list
- **SC-004**: Revenue calculations match the targets defined in Business_Goals.md with 100% accuracy
- **SC-005**: The briefing generation completes within 2 minutes of scheduled execution time
- **SC-006**: Business owner can review the briefing and understand business status in under 5 minutes
- **SC-007**: Proactive suggestions are actionable (each suggestion includes specific action items, not just observations)
- **SC-008**: System handles missing data gracefully without crashes or incomplete briefings (shows appropriate "no data" messages)

## Assumptions *(include if making informed guesses)*

- Bank transaction data is available in a parseable format (CSV or structured markdown) in the /Accounting folder
- Task files in /Done folder use standard markdown format with YAML frontmatter for metadata
- Business_Goals.md follows the template structure defined in the Hackathon Document
- The Obsidian vault is accessible and not locked when the scheduled script runs
- Expected task duration metadata is optional - bottleneck analysis only runs when this data is available
- Subscription usage tracking is based on transaction frequency, not actual login/usage data (which would require API integrations)
- The system runs on a machine that is powered on Sunday nights at 8:00 PM (or uses a cloud VM for always-on operation)

## Dependencies *(include if feature relies on external systems)*

- **Obsidian Vault**: Must be accessible at the configured vault path
- **Business_Goals.md**: Must exist and follow the expected template structure
- **Orchestrator.py**: Must be running or callable to trigger Claude Code
- **Claude Code**: Must be installed and configured with the weekly-ceo-briefing skill
- **Task Scheduler/Cron**: System scheduling service must be available and configured
- **/Done folder**: Must exist for task tracking
- **/Accounting folder**: Must exist and contain transaction data
- **/Briefings folder**: Will be created if it doesn't exist

## Out of Scope *(include to clarify boundaries)*

- Real-time subscription usage tracking (requires API integrations with each service)
- Automatic subscription cancellation (requires payment system integrations)
- Predictive analytics or forecasting (only historical analysis)
- Integration with external accounting software (uses local vault data only)
- Multi-user or team briefings (designed for single business owner)
- Mobile app or web dashboard (briefing is markdown file in Obsidian)
- Email delivery of briefings (user reads in Obsidian)
- Customizable briefing templates (uses fixed template structure)

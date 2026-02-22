# Implementation Plan: Error Recovery and Graceful Degradation

**Branch**: `005-error-recovery` | **Date**: 2026-02-19 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/005-error-recovery/spec.md`

**Note**: This template is filled in by the `/sp.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Implement comprehensive error recovery system for Personal AI Employee with centralized logging, automatic retry with exponential backoff, circuit breaker pattern, watchdog process for auto-restart, operation queuing, and file quarantine. This Gold Tier hackathon feature ensures system resilience and autonomous operation by handling transient errors (90% auto-recovery), preventing cascading failures (pause after 4 consecutive failures), and maintaining visibility through daily error logs and dashboard integration.

**Technical Approach**: File-based error logging to daily JSON files, Python decorators for retry logic, circuit breaker state machine, separate watchdog process using psutil, file-based operation queue, and atomic dashboard updates using temp file + rename pattern.

## Technical Context

**Language/Version**: Python 3.13 (existing project requirement)
**Primary Dependencies**:
- psutil (process monitoring, already available)
- filelock (cross-platform file locking, NEW)
- tenacity (retry logic with exponential backoff, NEW)
- Standard library: json, logging, pathlib, subprocess, traceback, datetime, uuid

**Storage**: File-based (JSON files in AI_Employee_Vault)
- Error logs: `AI_Employee_Vault/Logs/Errors/YYYY-MM-DD-DayName.json`
- Component health: `AI_Employee_Vault/.system/health_status.json`
- Operation queue: `AI_Employee_Vault/Queue/[ServiceName]/pending/`
- Quarantine: `AI_Employee_Vault/Quarantine/YYYY-MM-DD/`

**Testing**: pytest (existing project standard)
- Unit tests for each error handler
- Integration tests for error propagation
- Chaos tests for failure simulation
- End-to-end tests for dashboard updates

**Target Platform**: Windows 10+ (primary), Linux/macOS (secondary)
**Project Type**: Single project (library + CLI integration)
**Performance Goals**:
- Error logging: <50ms per error
- Retry overhead: Max 7 seconds per operation (3 attempts with exponential backoff)
- Watchdog check interval: 60 seconds
- Queue processing: 1 operation per second

**Constraints**:
- No external dependencies (database, message broker)
- Must work with existing vault-based architecture
- File operations must be atomic (no corruption during concurrent access)
- Dashboard updates must not block Obsidian
- Error logs must not contain sensitive data (credentials, tokens)

**Scale/Scope**:
- 5-10 components to monitor
- Expected 10-50 errors per day
- Queue size: <100 pending operations
- Log retention: 90 days
- Quarantine: <10 files per day

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**Note**: Constitution file is a template and not yet populated for this project. Proceeding with standard best practices:

✅ **Library-First**: Error recovery implemented as reusable library (`app/src/app/error_recovery/`)
✅ **Test-First**: TDD approach with tests written before implementation
✅ **Simplicity**: File-based storage, no external dependencies, standard patterns
✅ **Observability**: All errors logged with full context, human-readable logs
✅ **No Violations**: No complexity justification needed

## Project Structure

### Documentation (this feature)

```text
specs/005-error-recovery/
├── spec.md              # Feature specification (completed)
├── plan.md              # This file (implementation plan)
├── research.md          # Technical decisions and research (completed)
├── data-model.md        # Data structures and entities (completed)
├── quickstart.md        # Quick start guide (completed)
├── contracts/           # API contracts (completed)
│   ├── error_logger.md
│   ├── retry_handler.md
│   ├── circuit_breaker.md
│   ├── watchdog.md
│   ├── operation_queue.md
│   └── quarantine_handler.md
├── checklists/
│   └── requirements.md  # Spec quality checklist (completed)
└── tasks.md             # Implementation tasks (/sp.tasks command - NOT YET CREATED)
```

### Source Code (repository root)

```text
app/src/app/error_recovery/          # NEW: Error recovery library
├── __init__.py                      # Public API exports
├── error_logger.py                  # Centralized error logging
├── retry_handler.py                 # Retry with exponential backoff
├── circuit_breaker.py               # Circuit breaker pattern
├── watchdog.py                      # Process monitoring and restart
├── operation_queue.py               # Operation queuing for service outages
├── quarantine_handler.py            # File quarantine for corrupted data
├── entities.py                      # Data classes (ErrorLogEntry, etc.)
├── exceptions.py                    # Custom exception classes
└── utils.py                         # Shared utilities (file locking, etc.)

app/src/app/watchers/                # MODIFY: Add error recovery to watchers
├── gmail_watcher.py                 # Add retry, circuit breaker, error logging
└── file_system_watcher.py           # Add error recovery wrapper

app/src/app/weekly_audit/            # MODIFY: Add error recovery
└── audit_orchestrator.py            # Add error logging and retry

app/src/app/                         # MODIFY: Add error recovery
├── file_processor.py                # Add quarantine handler
└── linkedin_poster.py               # Add operation queue

scripts/                             # NEW: Watchdog startup script
└── start_watchdog.py                # Entry point for watchdog process

app/tests/unit/error_recovery/       # NEW: Unit tests
├── test_error_logger.py
├── test_retry_handler.py
├── test_circuit_breaker.py
├── test_watchdog.py
├── test_operation_queue.py
└── test_quarantine_handler.py

app/tests/integration/               # NEW: Integration tests
├── test_error_propagation.py        # Test error flow across components
└── test_dashboard_updates.py        # Test dashboard integration

app/tests/                           # NEW: End-to-end tests
└── test_error_recovery_e2e.py       # Full system error recovery tests

AI_Employee_Vault/                   # NEW: Directory structure
├── Logs/
│   └── Errors/                      # Daily error logs (YYYY-MM-DD-DayName.json)
├── Queue/                           # Operation queues
│   ├── gmail_api/
│   │   ├── pending/
│   │   ├── completed/
│   │   └── failed/
│   └── linkedin_api/
│       ├── pending/
│       ├── completed/
│       └── failed/
├── Quarantine/                      # Quarantined files by date
│   └── YYYY-MM-DD/
└── .system/                         # System state
    └── health_status.json           # Component health tracking
```

**Structure Decision**: Single project structure with new error_recovery library under app/src/app/. This aligns with existing codebase organization where all application code lives under app/src/app/. The error recovery system is implemented as a reusable library that can be imported by any component. Tests follow existing pattern with unit/, integration/, and root-level e2e tests.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No violations. All design decisions follow standard patterns and best practices.

## Architecture Decisions

### 1. File-Based Storage vs. Database

**Decision**: Use file-based storage (JSON files)

**Rationale**:
- Consistent with existing vault-based architecture
- No additional dependencies or setup required
- Easy to inspect and debug manually
- Survives system restarts
- Sufficient for expected scale (10-50 errors/day)

**Trade-offs**:
- Limited query capabilities (no SQL)
- Manual cleanup required for old logs
- Concurrent access requires file locking

### 2. Separate Watchdog Process vs. Built-in Monitoring

**Decision**: Separate Python process for watchdog

**Rationale**:
- Survives component crashes (can restart crashed components)
- Independent lifecycle (can be started/stopped separately)
- Simpler to test and debug
- Can be scheduled via OS task scheduler

**Trade-offs**:
- Additional process to manage
- Requires OS task scheduler setup
- Inter-process communication via file system

### 3. Decorator Pattern for Retry Logic

**Decision**: Use Python decorators (@with_retry)

**Rationale**:
- Clean, non-invasive integration
- Easy to add to existing functions
- Configurable per function
- Standard Python pattern

**Trade-offs**:
- Requires function-level granularity
- May not work with all function types (generators, async)

### 4. Circuit Breaker State Persistence

**Decision**: Persist circuit breaker state to health_status.json

**Rationale**:
- State survives process restarts
- Prevents immediate re-failure after restart
- Enables manual inspection and reset
- Centralized component health tracking

**Trade-offs**:
- File I/O overhead on every state change
- Requires file locking for concurrent access

### 5. Dashboard Update Strategy

**Decision**: Atomic write using temp file + rename

**Rationale**:
- Prevents corruption during concurrent access
- Works even if Obsidian is reading the file
- Standard pattern for atomic file updates
- No file locking required

**Trade-offs**:
- Slightly more complex than direct write
- Requires cleanup of temp files on failure

## Integration Points

### Existing Components to Modify

1. **gmail_watcher.py**
   - Add: ErrorLogger, CircuitBreaker, @with_retry decorator
   - Wrap: fetch_emails() with retry logic
   - Add: Circuit breaker around main loop

2. **file_processor.py**
   - Add: ErrorLogger, QuarantineHandler
   - Wrap: parse_file() with try/except and quarantine on parse errors
   - Add: Error logging for all exceptions

3. **weekly_audit/audit_orchestrator.py**
   - Add: ErrorLogger, @with_retry decorator
   - Wrap: All external API calls with retry logic
   - Add: Error logging for audit failures

4. **linkedin_poster.py**
   - Add: ErrorLogger, OperationQueue
   - Wrap: post_to_linkedin() with queue on service unavailable
   - Add: Queue processing on startup

### New Components to Create

1. **watchdog.py**
   - Monitor: All watcher processes and scheduled tasks
   - Restart: Crashed processes automatically
   - Pause: Components after 3 crashes in 5 minutes

2. **scripts/start_watchdog.py**
   - Entry point for watchdog process
   - Load component configurations
   - Start monitoring loop

3. **scripts/setup_watchdog_scheduler.py**
   - Create OS scheduled task for watchdog
   - Configure to start on boot
   - Set restart policy

## Testing Strategy

### Unit Tests (app/tests/unit/error_recovery/)

- Test each error recovery component in isolation
- Mock file system operations
- Test all error paths and edge cases
- Verify state transitions (circuit breaker, queue)

### Integration Tests (app/tests/integration/)

- Test error propagation across components
- Test dashboard updates with real file system
- Test concurrent error logging
- Test watchdog restart behavior

### End-to-End Tests (app/tests/)

- Simulate real failure scenarios
- Test complete error recovery workflows
- Verify dashboard reflects system state
- Test queue processing after service recovery

### Chaos Tests

- Simulate network failures (disconnect during API call)
- Simulate disk full (fill disk during error logging)
- Simulate process crashes (kill -9 on watcher)
- Simulate corrupted files (invalid JSON, YAML)

## Deployment Plan

### Phase 1: Core Error Logging (P1 - Foundation)

1. Create error_recovery library structure
2. Implement ErrorLogger with daily JSON logs
3. Implement dashboard update logic
4. Add error logging to one component (file_processor)
5. Test and verify logs are created correctly

**Deliverable**: Centralized error logging working for one component

### Phase 2: Retry Logic (P2 - Reliability)

1. Implement RetryHandler with exponential backoff
2. Add @with_retry decorator
3. Integrate with gmail_watcher
4. Test retry behavior with simulated failures

**Deliverable**: Automatic retry working for transient errors

### Phase 3: Circuit Breaker (P3 - Stability)

1. Implement CircuitBreaker with state machine
2. Persist state to health_status.json
3. Integrate with all watchers
4. Test circuit breaker opens after 4 failures

**Deliverable**: Components pause after repeated failures

### Phase 4: Watchdog (P5 - Availability)

1. Implement Watchdog process monitor
2. Create start_watchdog.py script
3. Set up OS scheduled task
4. Test auto-restart behavior

**Deliverable**: Crashed components restart automatically

### Phase 5: Operation Queue (P6 - Data Integrity)

1. Implement OperationQueue
2. Integrate with linkedin_poster
3. Add queue processing to watchdog
4. Test queue during service outage

**Deliverable**: Operations queued when services unavailable

### Phase 6: File Quarantine (P7 - Robustness)

1. Implement QuarantineHandler
2. Integrate with file_processor
3. Add quarantine section to dashboard
4. Test with corrupted files

**Deliverable**: Corrupted files quarantined automatically

## Rollback Plan

Each phase is independently deployable and can be rolled back:

- **Phase 1**: Remove error logging calls, delete error_recovery library
- **Phase 2**: Remove @with_retry decorators, revert to original code
- **Phase 3**: Remove CircuitBreaker, revert to original code
- **Phase 4**: Stop watchdog process, remove scheduled task
- **Phase 5**: Remove OperationQueue, revert to direct API calls
- **Phase 6**: Remove QuarantineHandler, revert to original error handling

## Success Metrics

- **Error Visibility**: 100% of errors logged to daily files
- **Auto-Recovery**: 90% of transient errors resolved without human intervention
- **Diagnosis Time**: Users can identify errors within 2 minutes
- **Crash Recovery**: Components restart within 60 seconds
- **Data Loss**: Zero operations lost during service outages
- **Cascading Failures**: Zero cascading failures (circuit breaker prevents)

## Open Questions

None. All technical decisions have been made and documented in research.md.

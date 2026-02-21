# Research: Error Recovery and Graceful Degradation

**Feature**: 005-error-recovery
**Date**: 2026-02-19
**Purpose**: Document technical decisions and research findings for error recovery system

## Technical Decisions

### 1. Error Logging Format

**Decision**: Use JSON format for error logs with daily rotation

**Rationale**:
- JSON is machine-readable and human-readable
- Easy to parse for future analytics or monitoring tools
- Daily rotation prevents log files from growing too large
- Append mode ensures no data loss during concurrent writes

**Alternatives Considered**:
- Plain text logs: Harder to parse programmatically
- Database storage: Adds complexity and dependency
- Single log file: Would grow indefinitely

**Implementation Details**:
- File path: `AI_Employee_Vault/Logs/Errors/YYYY-MM-DD-DayName.json`
- Format: JSON array with one object per error
- Fields: timestamp, component, error_type, message, stack_trace, retry_count, context

### 2. Retry Strategy

**Decision**: Exponential backoff with 3 attempts (1s, 2s, 4s delays)

**Rationale**:
- Exponential backoff is industry standard for transient errors
- 3 attempts balances reliability vs. latency
- Total retry time: 7 seconds (acceptable for background operations)
- Prevents overwhelming failing services

**Alternatives Considered**:
- Fixed delay: Doesn't adapt to service recovery time
- More attempts: Increases latency unnecessarily
- Immediate retry: Can overwhelm recovering services

**Implementation Details**:
- Base delay: 1 second
- Multiplier: 2x
- Max attempts: 3
- Jitter: Add ±10% randomness to prevent thundering herd

### 3. Circuit Breaker Threshold

**Decision**: Open circuit after 4 consecutive failures

**Rationale**:
- 4 failures indicates systemic issue, not transient glitch
- Prevents resource waste on broken components
- User requirement explicitly specified 4 failures
- Aligns with industry patterns (Netflix Hystrix uses 5)

**Alternatives Considered**:
- 3 failures: Too sensitive, may trigger on transient issues
- 5+ failures: Wastes more resources before pausing
- Time-based: Harder to reason about and test

**Implementation Details**:
- Counter resets to 0 on any successful operation
- Circuit remains open until manual restart
- Log "CIRCUIT_BREAKER_OPEN" event when triggered

### 4. Watchdog Implementation

**Decision**: Separate Python process checking health every 60 seconds

**Rationale**:
- Separate process ensures watchdog survives component crashes
- 60-second interval balances responsiveness vs. overhead
- Python allows code reuse with existing components
- Can be scheduled via OS task scheduler for boot persistence

**Alternatives Considered**:
- Built-in to each component: Doesn't survive process crashes
- External monitoring service: Adds complexity and dependencies
- Shorter interval: Unnecessary overhead for background tasks

**Implementation Details**:
- Check process PIDs via psutil library
- Restart crashed processes using subprocess
- Log all restart events
- Pause component after 3 crashes in 5 minutes

### 5. Operation Queue Storage

**Decision**: File-based queue using JSON files in AI_Employee_Vault/Queue/

**Rationale**:
- Consistent with existing vault-based architecture
- No additional dependencies (database, message broker)
- Survives system restarts
- Easy to inspect and debug manually

**Alternatives Considered**:
- In-memory queue: Lost on restart
- Database queue: Adds complexity
- Redis/RabbitMQ: Overkill for single-machine system

**Implementation Details**:
- Directory structure: Queue/[ServiceName]/pending/, completed/, failed/
- File naming: [timestamp]_[operation_id].json
- Processing: Chronological order (oldest first)
- Cleanup: Move to completed/ or failed/ after processing

### 6. Dashboard Update Strategy

**Decision**: Atomic file write with temp file + rename

**Rationale**:
- Prevents corruption if Obsidian is reading file
- Atomic rename ensures consistency
- No file locking issues
- Standard pattern for concurrent file access

**Alternatives Considered**:
- Direct write: Risk of corruption during concurrent access
- File locking: Complex on Windows, may block Obsidian
- Separate error file: Fragments information

**Implementation Details**:
- Write to Dashboard.md.tmp
- Rename to Dashboard.md (atomic operation)
- Retry with exponential backoff if rename fails

### 7. Error Categorization

**Decision**: 5 error types (TRANSIENT, AUTHENTICATION, LOGIC, DATA, SYSTEM)

**Rationale**:
- Each type requires different handling strategy
- Clear mapping from error to recovery action
- Aligns with user requirements
- Covers all common failure modes

**Error Type Mapping**:
- **TRANSIENT**: Network timeouts, API rate limits → Retry with backoff
- **AUTHENTICATION**: 401, 403, invalid_grant → Pause immediately
- **LOGIC**: Unexpected responses, business rule violations → Human review
- **DATA**: Corrupted files, invalid formats → Quarantine
- **SYSTEM**: Process crashes, disk full → Watchdog restart

### 8. Concurrency Control

**Decision**: File-based locking using fcntl (Unix) / msvcrt (Windows)

**Rationale**:
- Prevents race conditions during concurrent error logging
- Native OS support, no additional dependencies
- Works across processes
- Timeout mechanism prevents deadlocks

**Alternatives Considered**:
- No locking: Risk of corrupted JSON
- Database transactions: Adds complexity
- Distributed locks: Overkill for single machine

**Implementation Details**:
- Acquire exclusive lock before writing
- Timeout: 5 seconds
- Fallback: Write to temporary file if lock fails

## Best Practices Applied

### Error Handling Patterns

1. **Fail Fast**: Authentication errors pause immediately
2. **Graceful Degradation**: Continue processing valid items when one fails
3. **Idempotency**: Retry logic handles duplicate operations safely
4. **Observability**: All errors logged with full context
5. **Circuit Breaker**: Prevent cascading failures

### Python-Specific Patterns

1. **Context Managers**: Use `with` statements for file operations
2. **Logging Module**: Use Python's built-in logging with structured output
3. **Exception Hierarchy**: Define custom exception classes for each error type
4. **Type Hints**: Use typing module for better IDE support and validation
5. **Dataclasses**: Use for error log entries and component health status

### Testing Strategy

1. **Unit Tests**: Test each error handler in isolation
2. **Integration Tests**: Test error propagation across components
3. **Chaos Testing**: Simulate failures (network, disk, process crashes)
4. **End-to-End Tests**: Verify dashboard updates and log file creation

## Dependencies

### Required Python Libraries

- **psutil**: Process monitoring for watchdog (already available)
- **filelock**: Cross-platform file locking (add to pyproject.toml)
- **tenacity**: Retry logic with exponential backoff (add to pyproject.toml)

### Existing Components to Integrate

- **file_processor.py**: Add error recovery wrapper
- **weekly_audit/audit_orchestrator.py**: Add error logging
- **Gmail watcher**: Add retry and circuit breaker
- **LinkedIn poster**: Add operation queuing

## Performance Considerations

- **Log File Size**: Daily rotation keeps files manageable (<10MB/day expected)
- **Retry Overhead**: Max 7 seconds per operation (acceptable for background tasks)
- **Watchdog Overhead**: 60-second interval, minimal CPU usage
- **Queue Processing**: Process 1 operation per second to avoid overwhelming services

## Security Considerations

- **Error Messages**: Sanitize sensitive data (credentials, tokens) before logging
- **Log Access**: Error logs contain debugging info, restrict file permissions
- **Stack Traces**: May reveal code structure, acceptable for local-only system

## Migration Strategy

1. **Phase 1**: Add error logging to existing components (non-breaking)
2. **Phase 2**: Add retry logic (non-breaking, improves reliability)
3. **Phase 3**: Add circuit breaker (may pause components, document behavior)
4. **Phase 4**: Add watchdog (new process, requires OS task scheduler setup)
5. **Phase 5**: Add operation queuing (new feature, opt-in initially)

## Open Questions (Resolved)

All technical unknowns have been resolved through research and alignment with existing codebase patterns.

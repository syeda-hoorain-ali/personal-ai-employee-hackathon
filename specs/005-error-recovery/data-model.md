# Data Model: Error Recovery System

**Feature**: 005-error-recovery
**Date**: 2026-02-19
**Purpose**: Define data structures for error recovery and graceful degradation

## Core Entities

### 1. Error Log Entry

Represents a single error occurrence in the system.

**Fields**:
- `id` (string): Unique identifier (UUID)
- `timestamp` (ISO 8601 string): When the error occurred
- `component` (string): Name of the component that failed (e.g., "gmail_watcher", "weekly_audit", "file_processor")
- `error_type` (enum): Category of error - TRANSIENT | AUTHENTICATION | LOGIC | DATA | SYSTEM
- `error_code` (string, optional): Specific error code if available (e.g., "ECONNREFUSED", "401", "INVALID_JSON")
- `message` (string): Human-readable error description
- `stack_trace` (string, optional): Full stack trace for debugging
- `retry_count` (integer): Number of retry attempts made (0 for first attempt)
- `context` (object): Additional context specific to the error
  - `operation` (string): What operation was being performed
  - `input_data` (object, sanitized): Relevant input data (sensitive data removed)
  - `service` (string, optional): External service involved (e.g., "gmail_api", "linkedin_api")
- `resolution_status` (enum): UNRESOLVED | AUTO_RECOVERED | MANUAL_INTERVENTION_REQUIRED | IGNORED
- `resolved_at` (ISO 8601 string, optional): When the error was resolved

**Validation Rules**:
- `timestamp` must be valid ISO 8601 format
- `component` must not be empty
- `error_type` must be one of the 5 defined types
- `retry_count` must be >= 0
- `message` must not contain sensitive data (credentials, tokens, API keys)
- `stack_trace` should be truncated if > 5000 characters

**State Transitions**:
- Created → UNRESOLVED (initial state)
- UNRESOLVED → AUTO_RECOVERED (after successful retry)
- UNRESOLVED → MANUAL_INTERVENTION_REQUIRED (after circuit breaker opens)
- UNRESOLVED → IGNORED (after manual review)

**Example**:
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "timestamp": "2026-02-19T14:30:45.123Z",
  "component": "gmail_watcher",
  "error_type": "TRANSIENT",
  "error_code": "ECONNREFUSED",
  "message": "Failed to connect to Gmail API: Connection refused",
  "stack_trace": "Traceback (most recent call last):\n  File \"gmail_watcher.py\", line 42...",
  "retry_count": 2,
  "context": {
    "operation": "fetch_unread_emails",
    "input_data": {"query": "is:unread is:important"},
    "service": "gmail_api"
  },
  "resolution_status": "AUTO_RECOVERED",
  "resolved_at": "2026-02-19T14:30:52.456Z"
}
```

---

### 2. Component Health Status

Represents the operational state of a system component.

**Fields**:
- `component_name` (string): Unique identifier for the component
- `status` (enum): RUNNING | PAUSED | CRASHED | STARTING
- `failure_count` (integer): Number of consecutive failures
- `last_success_at` (ISO 8601 string, optional): Timestamp of last successful operation
- `last_failure_at` (ISO 8601 string, optional): Timestamp of last failure
- `last_error_id` (string, optional): Reference to the most recent error log entry
- `circuit_breaker_state` (enum): CLOSED | OPEN | HALF_OPEN
- `circuit_opened_at` (ISO 8601 string, optional): When circuit breaker opened
- `restart_count` (integer): Number of times watchdog has restarted this component
- `process_id` (integer, optional): OS process ID if component is a separate process
- `health_check_last_run` (ISO 8601 string): When health check last ran
- `metadata` (object): Component-specific metadata
  - `version` (string): Component version
  - `config` (object): Relevant configuration

**Validation Rules**:
- `component_name` must be unique across all components
- `failure_count` must be >= 0
- `circuit_breaker_state` must be OPEN when `failure_count` >= 4
- `restart_count` must be >= 0
- If `status` is CRASHED, `process_id` should be null

**State Transitions**:
- RUNNING → PAUSED (after 4 consecutive failures or authentication error)
- RUNNING → CRASHED (after unexpected process termination)
- CRASHED → STARTING (watchdog initiates restart)
- STARTING → RUNNING (successful restart)
- PAUSED → RUNNING (manual restart by user)

**Relationships**:
- Has many Error Log Entries (via `component_name`)
- Referenced by Dashboard Error Summary

**Example**:
```json
{
  "component_name": "gmail_watcher",
  "status": "PAUSED",
  "failure_count": 4,
  "last_success_at": "2026-02-19T10:15:30.000Z",
  "last_failure_at": "2026-02-19T14:30:45.123Z",
  "last_error_id": "550e8400-e29b-41d4-a716-446655440000",
  "circuit_breaker_state": "OPEN",
  "circuit_opened_at": "2026-02-19T14:30:45.123Z",
  "restart_count": 0,
  "process_id": null,
  "health_check_last_run": "2026-02-19T14:31:00.000Z",
  "metadata": {
    "version": "1.0.0",
    "config": {
      "check_interval": 120,
      "credentials_path": "~/.gmail-mcp/"
    }
  }
}
```

---

### 3. Queued Operation

Represents a pending operation that couldn't be executed due to service unavailability.

**Fields**:
- `id` (string): Unique identifier (UUID)
- `operation_type` (string): Type of operation (e.g., "send_email", "post_linkedin", "update_dashboard")
- `service` (string): Target service (e.g., "gmail_api", "linkedin_api")
- `payload` (object): Operation-specific data
- `created_at` (ISO 8601 string): When operation was queued
- `scheduled_for` (ISO 8601 string, optional): When to attempt execution (for delayed retry)
- `retry_count` (integer): Number of execution attempts
- `max_retries` (integer): Maximum retry attempts before moving to failed
- `status` (enum): PENDING | PROCESSING | COMPLETED | FAILED
- `last_attempt_at` (ISO 8601 string, optional): When last execution was attempted
- `error_message` (string, optional): Error from last failed attempt
- `priority` (integer): Execution priority (1=highest, 10=lowest)

**Validation Rules**:
- `operation_type` must not be empty
- `service` must not be empty
- `retry_count` must be >= 0 and <= `max_retries`
- `priority` must be between 1 and 10
- `payload` must not contain sensitive data in plain text

**State Transitions**:
- Created → PENDING (initial state)
- PENDING → PROCESSING (when execution starts)
- PROCESSING → COMPLETED (successful execution)
- PROCESSING → PENDING (failed execution, retry scheduled)
- PROCESSING → FAILED (max retries exhausted)

**Relationships**:
- May reference Error Log Entry (if execution failed)
- Grouped by service in queue directories

**Example**:
```json
{
  "id": "660e8400-e29b-41d4-a716-446655440001",
  "operation_type": "send_email",
  "service": "gmail_api",
  "payload": {
    "to": "client@example.com",
    "subject": "Invoice #1234",
    "body": "Please find attached...",
    "attachment_path": "/vault/Invoices/2026-01_Client_A.pdf"
  },
  "created_at": "2026-02-19T14:00:00.000Z",
  "scheduled_for": "2026-02-19T14:05:00.000Z",
  "retry_count": 1,
  "max_retries": 3,
  "status": "PENDING",
  "last_attempt_at": "2026-02-19T14:00:05.000Z",
  "error_message": "Gmail API unavailable: 503 Service Unavailable",
  "priority": 5
}
```

---

### 4. Quarantined File

Represents a corrupted or invalid file that was moved to quarantine.

**Fields**:
- `id` (string): Unique identifier (UUID)
- `original_path` (string): Original file location before quarantine
- `quarantine_path` (string): Current location in quarantine directory
- `quarantined_at` (ISO 8601 string): When file was quarantined
- `file_size` (integer): File size in bytes
- `file_hash` (string): SHA-256 hash for integrity verification
- `error_type` (enum): DATA (always DATA for quarantined files)
- `error_reason` (string): Why file was quarantined (e.g., "Invalid YAML frontmatter", "Corrupted JSON")
- `parsing_error` (string): Detailed parsing error message
- `component` (string): Component that quarantined the file
- `reviewed` (boolean): Whether user has reviewed the file
- `action_taken` (enum, optional): RESTORED | DELETED | IGNORED

**Validation Rules**:
- `original_path` must be absolute path
- `quarantine_path` must be under AI_Employee_Vault/Quarantine/
- `file_size` must be >= 0
- `file_hash` must be valid SHA-256 (64 hex characters)
- `error_reason` must not be empty

**State Transitions**:
- Created → Quarantined (initial state, `reviewed` = false)
- Quarantined → Reviewed (`reviewed` = true, `action_taken` set)

**Relationships**:
- May reference Error Log Entry
- Grouped by date in quarantine directories

**Example**:
```json
{
  "id": "770e8400-e29b-41d4-a716-446655440002",
  "original_path": "C:/Users/dell/Desktop/projects/class-project/personal-ai-employee/AI_Employee_Vault/Needs_Action/EMAIL_12345.md",
  "quarantine_path": "C:/Users/dell/Desktop/projects/class-project/personal-ai-employee/AI_Employee_Vault/Quarantine/2026-02-19/EMAIL_12345.md",
  "quarantined_at": "2026-02-19T15:00:00.000Z",
  "file_size": 2048,
  "file_hash": "a3b2c1d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6a7b8c9d0e1f2",
  "error_type": "DATA",
  "error_reason": "Invalid YAML frontmatter",
  "parsing_error": "yaml.scanner.ScannerError: mapping values are not allowed here\n  in \"<unicode string>\", line 3, column 10",
  "component": "file_processor",
  "reviewed": false,
  "action_taken": null
}
```

---

## Supporting Data Structures

### Dashboard Error Summary

Embedded in Dashboard.md, not a separate entity.

**Fields**:
- `total_errors_today` (integer): Count of errors in today's log
- `paused_components` (array of strings): List of component names currently paused
- `quarantined_files_count` (integer): Number of files in quarantine
- `log_file_path` (string): Relative path to today's error log
- `last_updated` (ISO 8601 string): When summary was last updated

**Example (Markdown)**:
```markdown
## Error Summary

**Last Updated**: 2026-02-19 15:30:00

- **Errors Today**: 12 ([View Log](Logs/Errors/2026-02-19-Wednesday.json))
- **Paused Components**: gmail_watcher (authentication error)
- **Quarantined Files**: 1 ([View Quarantine](Quarantine/2026-02-19/))

**Action Required**: gmail_watcher authentication failed. Please refresh credentials.
```

---

## Data Relationships

```
Component Health Status (1) ──< (many) Error Log Entries
                         │
                         └──> (references) Latest Error Log Entry

Queued Operation (1) ──> (0..1) Error Log Entry (if failed)

Quarantined File (1) ──> (0..1) Error Log Entry

Dashboard Error Summary ──> (aggregates) Error Log Entries
                        ──> (references) Component Health Status
                        ──> (references) Quarantined Files
```

---

## Storage Locations

- **Error Log Entries**: `AI_Employee_Vault/Logs/Errors/YYYY-MM-DD-DayName.json` (JSON array)
- **Component Health Status**: `AI_Employee_Vault/.system/health_status.json` (JSON object, keyed by component name)
- **Queued Operations**: `AI_Employee_Vault/Queue/[ServiceName]/pending/[timestamp]_[id].json` (individual JSON files)
- **Quarantined Files**: `AI_Employee_Vault/Quarantine/YYYY-MM-DD/[original_filename]` (original file) + `.meta.json` (metadata)
- **Dashboard Error Summary**: Embedded in `AI_Employee_Vault/Dashboard.md` (Markdown section)

---

## Data Retention

- **Error Logs**: Keep for 90 days, then archive or delete
- **Component Health Status**: Keep indefinitely, reset counters on manual restart
- **Queued Operations**: Delete after completion or failure (move to completed/failed directories)
- **Quarantined Files**: Keep until user reviews and takes action
- **Dashboard Error Summary**: Update in real-time, no historical retention

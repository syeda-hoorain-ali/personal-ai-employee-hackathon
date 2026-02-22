# Error Logger Interface

**Purpose**: Centralized error logging for all components

## Interface Definition

### `log_error(error_entry: ErrorLogEntry) -> str`

Logs an error to the daily error log file and updates dashboard.

**Parameters**:
- `error_entry` (ErrorLogEntry): Complete error information

**Returns**:
- `error_id` (str): UUID of the logged error

**Behavior**:
1. Validate error_entry fields
2. Sanitize sensitive data from message and context
3. Acquire file lock on daily log file
4. Append error to JSON array
5. Release file lock
6. Update Dashboard.md with error summary
7. Return error_id

**Error Handling**:
- If log file is locked: Retry with exponential backoff (max 3 attempts)
- If disk full: Log to stderr and return None
- If dashboard update fails: Log warning but don't fail the operation

**Example Usage**:
```python
from error_recovery import ErrorLogger, ErrorLogEntry, ErrorType

logger = ErrorLogger(vault_path="AI_Employee_Vault")

error = ErrorLogEntry(
    component="gmail_watcher",
    error_type=ErrorType.TRANSIENT,
    message="Connection timeout",
    stack_trace=traceback.format_exc(),
    retry_count=0,
    context={"operation": "fetch_emails"}
)

error_id = logger.log_error(error)
print(f"Error logged: {error_id}")
```

---

### `get_errors_today() -> List[ErrorLogEntry]`

Retrieves all errors from today's log file.

**Returns**:
- List of ErrorLogEntry objects

**Behavior**:
1. Read today's log file
2. Parse JSON array
3. Return list of error entries

**Error Handling**:
- If log file doesn't exist: Return empty list
- If JSON is corrupted: Log warning and return partial results

---

### `update_error_status(error_id: str, status: ResolutionStatus) -> bool`

Updates the resolution status of an error.

**Parameters**:
- `error_id` (str): UUID of the error
- `status` (ResolutionStatus): New status

**Returns**:
- `success` (bool): Whether update succeeded

**Behavior**:
1. Find error in today's log file
2. Update resolution_status and resolved_at
3. Write back to file

---

## Configuration

```python
class ErrorLoggerConfig:
    vault_path: str = "AI_Employee_Vault"
    log_retention_days: int = 90
    max_log_file_size_mb: int = 10
    enable_dashboard_updates: bool = True
    sanitize_patterns: List[str] = [
        r"password=\w+",
        r"token=[\w-]+",
        r"api_key=[\w-]+"
    ]
```

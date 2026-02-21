# Quickstart: Error Recovery System

**Feature**: 005-error-recovery
**Date**: 2026-02-19
**Purpose**: Quick guide to implementing and using the error recovery system

## Overview

The error recovery system provides comprehensive error handling across all Personal AI Employee components with:
- Centralized error logging to daily JSON files
- Automatic retry with exponential backoff
- Circuit breaker pattern (pause after 4 failures)
- Watchdog process for auto-restart
- Operation queuing for service outages
- File quarantine for corrupted data

## Quick Setup (5 minutes)

### 1. Install Dependencies

```bash
cd app
uv add filelock tenacity
```

### 2. Create Directory Structure

```bash
mkdir -p AI_Employee_Vault/Logs/Errors
mkdir -p AI_Employee_Vault/Queue
mkdir -p AI_Employee_Vault/Quarantine
mkdir -p AI_Employee_Vault/.system
```

### 3. Initialize Error Logger

```python
# In your component (e.g., gmail_watcher.py)
from app.src.app.error_recovery import ErrorLogger, ErrorType

logger = ErrorLogger(vault_path="AI_Employee_Vault")

try:
    # Your code here
    fetch_emails()
except Exception as e:
    logger.log_error(
        component="gmail_watcher",
        error_type=ErrorType.TRANSIENT,
        message=str(e),
        stack_trace=traceback.format_exc()
    )
```

### 4. Add Retry Logic

```python
from app.src.app.error_recovery import with_retry, ErrorType

@with_retry(max_attempts=3, error_types=[ErrorType.TRANSIENT])
def fetch_emails():
    # This will automatically retry on transient errors
    return gmail_api.fetch_unread()
```

### 5. Add Circuit Breaker

```python
from app.src.app.error_recovery import CircuitBreaker

breaker = CircuitBreaker("gmail_watcher", failure_threshold=4)

try:
    result = breaker.call(fetch_emails)
except CircuitBreakerOpenError:
    logger.error("Component paused due to repeated failures")
```

## Common Use Cases

### Use Case 1: Wrap Existing Component with Error Recovery

**Before**:
```python
def process_file(file_path):
    data = parse_file(file_path)
    result = process_data(data)
    return result
```

**After**:
```python
from app.src.app.error_recovery import (
    ErrorLogger, with_retry, QuarantineHandler, ErrorType
)

logger = ErrorLogger("AI_Employee_Vault")
quarantine = QuarantineHandler("AI_Employee_Vault")

@with_retry(max_attempts=3)
def process_file(file_path):
    try:
        data = parse_file(file_path)
        result = process_data(data)
        return result
    except ParseError as e:
        # Quarantine corrupted files
        quarantine.quarantine_file(
            file_path=file_path,
            error_reason="Parse error",
            parsing_error=str(e),
            component="file_processor"
        )
        raise
    except Exception as e:
        # Log all other errors
        logger.log_error(
            component="file_processor",
            error_type=ErrorType.DATA,
            message=f"Failed to process {file_path}: {e}",
            context={"file_path": file_path}
        )
        raise
```

### Use Case 2: Queue Operations When Service is Down

```python
from app.src.app.error_recovery import OperationQueue

queue = OperationQueue("gmail_api", "AI_Employee_Vault")

try:
    send_email(to="client@example.com", subject="Invoice", body="...")
except ServiceUnavailableError:
    # Queue for later processing
    queue.enqueue(
        operation_type="send_email",
        payload={
            "to": "client@example.com",
            "subject": "Invoice",
            "body": "..."
        },
        priority=5
    )
```

### Use Case 3: Start Watchdog for Auto-Restart

```python
# watchdog_main.py
from app.src.app.error_recovery import Watchdog, ComponentConfig

components = [
    ComponentConfig(
        name="gmail_watcher",
        command="python app/src/app/watchers/gmail_watcher.py",
        restart_policy="always"
    ),
    ComponentConfig(
        name="file_processor",
        command="python app/src/app/file_processor.py",
        restart_policy="on-failure"
    )
]

watchdog = Watchdog(components)
watchdog.start()  # Runs indefinitely
```

## Testing

### Test Error Logging

```python
# test_error_logging.py
from app.src.app.error_recovery import ErrorLogger, ErrorType

logger = ErrorLogger("AI_Employee_Vault")

# Log a test error
error_id = logger.log_error(
    component="test_component",
    error_type=ErrorType.TRANSIENT,
    message="Test error",
    context={"test": True}
)

# Verify error was logged
errors = logger.get_errors_today()
assert len(errors) > 0
assert errors[-1].component == "test_component"

# Verify dashboard was updated
with open("AI_Employee_Vault/Dashboard.md") as f:
    content = f.read()
    assert "Error Summary" in content
```

### Test Retry Logic

```python
# test_retry.py
from app.src.app.error_recovery import with_retry, ErrorType

call_count = 0

@with_retry(max_attempts=3)
def flaky_function():
    global call_count
    call_count += 1
    if call_count < 3:
        raise ConnectionError("Transient error")
    return "success"

result = flaky_function()
assert result == "success"
assert call_count == 3  # Failed twice, succeeded on third attempt
```

### Test Circuit Breaker

```python
# test_circuit_breaker.py
from app.src.app.error_recovery import CircuitBreaker, CircuitBreakerOpenError

breaker = CircuitBreaker("test_component", failure_threshold=4)

# Simulate 4 failures
for i in range(4):
    try:
        breaker.call(lambda: 1/0)  # Always fails
    except ZeroDivisionError:
        pass

# Circuit should now be open
try:
    breaker.call(lambda: "success")
    assert False, "Should have raised CircuitBreakerOpenError"
except CircuitBreakerOpenError:
    pass  # Expected
```

## Monitoring

### Check Error Logs

```bash
# View today's errors
cat AI_Employee_Vault/Logs/Errors/$(date +%Y-%m-%d-%A).json | jq '.'

# Count errors by component
cat AI_Employee_Vault/Logs/Errors/$(date +%Y-%m-%d-%A).json | jq '[.[] | .component] | group_by(.) | map({component: .[0], count: length})'
```

### Check Component Health

```bash
# View component health status
cat AI_Employee_Vault/.system/health_status.json | jq '.'

# Check for paused components
cat AI_Employee_Vault/.system/health_status.json | jq '[.[] | select(.status == "PAUSED")]'
```

### Check Queue Status

```bash
# Count pending operations
ls AI_Employee_Vault/Queue/*/pending/ | wc -l

# View pending operations
find AI_Employee_Vault/Queue/*/pending/ -name "*.json" -exec cat {} \;
```

### Check Quarantined Files

```bash
# List quarantined files
ls -lh AI_Employee_Vault/Quarantine/$(date +%Y-%m-%d)/

# View quarantine metadata
cat AI_Employee_Vault/Quarantine/$(date +%Y-%m-%d)/*.meta.json | jq '.'
```

## Troubleshooting

### Problem: Errors not being logged

**Solution**: Check that Logs/Errors directory exists and is writable
```bash
mkdir -p AI_Employee_Vault/Logs/Errors
chmod 755 AI_Employee_Vault/Logs/Errors
```

### Problem: Dashboard not updating

**Solution**: Check for file lock issues
```bash
# Check if Dashboard.md is locked
lsof AI_Employee_Vault/Dashboard.md  # Unix
# Or check in Task Manager (Windows)
```

### Problem: Circuit breaker stuck open

**Solution**: Manually reset the circuit breaker
```python
from app.src.app.error_recovery import CircuitBreaker

breaker = CircuitBreaker("gmail_watcher")
breaker.reset()
```

### Problem: Watchdog not restarting components

**Solution**: Check watchdog logs and process status
```bash
# View watchdog logs
tail -f watchdog.log

# Check if watchdog is running
ps aux | grep watchdog  # Unix
# Or check in Task Manager (Windows)
```

## Next Steps

1. **Integrate with existing components**: Add error recovery to gmail_watcher, file_processor, weekly_audit
2. **Set up watchdog**: Create scheduled task to start watchdog on boot
3. **Configure monitoring**: Set up daily review of error logs
4. **Test failure scenarios**: Simulate network failures, disk full, process crashes
5. **Tune thresholds**: Adjust retry attempts, circuit breaker threshold based on real-world usage

## Reference

- **Specification**: `specs/005-error-recovery/spec.md`
- **Architecture**: `specs/005-error-recovery/plan.md`
- **Data Model**: `specs/005-error-recovery/data-model.md`
- **API Contracts**: `specs/005-error-recovery/contracts/`

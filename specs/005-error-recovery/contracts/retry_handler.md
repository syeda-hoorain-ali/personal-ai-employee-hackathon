# Retry Handler Interface

**Purpose**: Automatic retry with exponential backoff for transient errors

## Interface Definition

### `@with_retry(max_attempts=3, error_types=[ErrorType.TRANSIENT])`

Decorator that wraps a function with retry logic.

**Parameters**:
- `max_attempts` (int): Maximum number of attempts (default: 3)
- `error_types` (List[ErrorType]): Which error types to retry (default: [TRANSIENT])
- `base_delay` (float): Initial delay in seconds (default: 1.0)
- `max_delay` (float): Maximum delay in seconds (default: 60.0)
- `jitter` (bool): Add randomness to delays (default: True)

**Behavior**:
1. Execute wrapped function
2. If succeeds: Return result
3. If fails with retryable error:
   - Log error with retry_count
   - Wait for delay (exponential backoff)
   - Retry up to max_attempts
4. If all attempts fail: Raise final exception

**Example Usage**:
```python
from error_recovery import with_retry, ErrorType

@with_retry(max_attempts=3, error_types=[ErrorType.TRANSIENT])
def fetch_emails():
    # This will retry up to 3 times with exponential backoff
    return gmail_api.fetch_unread()

try:
    emails = fetch_emails()
except Exception as e:
    # All retries exhausted
    logger.log_error(...)
```

---

### `retry_with_backoff(func, *args, **kwargs) -> Any`

Programmatic retry without decorator.

**Parameters**:
- `func` (Callable): Function to retry
- `*args, **kwargs`: Arguments to pass to function
- `max_attempts` (int, kwarg): Maximum attempts
- `error_types` (List[ErrorType], kwarg): Error types to retry

**Returns**:
- Result of successful function call

**Raises**:
- Final exception if all retries fail

---

## Configuration

```python
class RetryConfig:
    max_attempts: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    multiplier: float = 2.0
    jitter_range: Tuple[float, float] = (0.9, 1.1)
    retryable_error_types: List[ErrorType] = [ErrorType.TRANSIENT]
```

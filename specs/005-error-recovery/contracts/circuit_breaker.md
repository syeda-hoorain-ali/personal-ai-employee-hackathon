# Circuit Breaker Interface

**Purpose**: Prevent cascading failures by pausing components after repeated failures

## Interface Definition

### `CircuitBreaker(component_name: str, failure_threshold: int = 4)`

Circuit breaker that tracks failures and opens after threshold is reached.

**Parameters**:
- `component_name` (str): Unique identifier for the component
- `failure_threshold` (int): Number of consecutive failures before opening (default: 4)

**Methods**:

#### `call(func: Callable, *args, **kwargs) -> Any`

Execute function through circuit breaker.

**Behavior**:
1. Check circuit state
2. If OPEN: Raise CircuitBreakerOpenError
3. If CLOSED or HALF_OPEN: Execute function
4. If succeeds: Reset failure counter, close circuit
5. If fails: Increment failure counter
6. If failure_count >= threshold: Open circuit, log event

**Example Usage**:
```python
from error_recovery import CircuitBreaker, CircuitBreakerOpenError

breaker = CircuitBreaker("gmail_watcher", failure_threshold=4)

try:
    result = breaker.call(fetch_emails)
except CircuitBreakerOpenError:
    logger.error("Circuit breaker open, component paused")
    # Update dashboard with paused status
```

---

#### `reset() -> None`

Manually reset circuit breaker (close circuit, reset counter).

**Behavior**:
1. Set state to CLOSED
2. Reset failure_count to 0
3. Update component health status
4. Log reset event

---

#### `get_state() -> CircuitBreakerState`

Get current circuit breaker state.

**Returns**:
- CircuitBreakerState: CLOSED | OPEN | HALF_OPEN

---

## State Machine

```
CLOSED (normal operation)
  ├─> failure_count < threshold: Stay CLOSED
  └─> failure_count >= threshold: Open circuit → OPEN

OPEN (component paused)
  └─> Manual reset only → CLOSED

HALF_OPEN (testing recovery)
  ├─> Success: Reset counter → CLOSED
  └─> Failure: Increment counter → OPEN if threshold reached
```

---

## Configuration

```python
class CircuitBreakerConfig:
    failure_threshold: int = 4
    reset_timeout: Optional[int] = None  # Auto-reset after N seconds (None = manual only)
    half_open_max_calls: int = 1  # Number of test calls in HALF_OPEN state
```

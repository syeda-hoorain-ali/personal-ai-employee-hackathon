"""
Circuit breaker pattern implementation for error recovery.

This module provides a circuit breaker that monitors component health and prevents
cascading failures by temporarily disabling failing components.
"""

import time
from datetime import datetime, UTC
from pathlib import Path
from typing import Callable, Optional, Any, Dict
from functools import wraps

from .entities import CircuitBreakerState, ComponentHealthStatus, ErrorType
from .exceptions import CircuitBreakerOpenError, AuthenticationError
from .error_logger import ErrorLogger
from .utils import read_json_file, write_json_file, file_lock


class CircuitBreaker:
    """
    Circuit breaker that monitors component health and prevents cascading failures.

    The circuit breaker has three states:
    - CLOSED: Normal operation, requests pass through
    - OPEN: Component is failing, requests are blocked
    - HALF_OPEN: Testing if component has recovered

    State transitions:
    - CLOSED -> OPEN: After failure_threshold consecutive failures
    - OPEN -> HALF_OPEN: After timeout_seconds have passed
    - HALF_OPEN -> CLOSED: After a successful request
    - HALF_OPEN -> OPEN: After any failure
    """

    def __init__(
        self,
        component: str,
        failure_threshold: int = 4,
        timeout_seconds: int = 60,
        health_status_path: Optional[Path] = None,
        error_logger: Optional[ErrorLogger] = None
    ):
        """
        Initialize circuit breaker.

        Args:
            component: Name of the component being monitored
            failure_threshold: Number of consecutive failures before opening circuit
            timeout_seconds: Seconds to wait before attempting recovery (half-open)
            health_status_path: Path to health status JSON file for persistence
            error_logger: Optional ErrorLogger for logging state changes
        """
        self.component = component
        self.failure_threshold = failure_threshold
        self.timeout_seconds = timeout_seconds
        self.health_status_path = health_status_path
        self.error_logger = error_logger

        # Load persisted state or initialize
        self._load_state()

    def _load_state(self):
        """Load circuit breaker state from persistence or initialize."""
        if self.health_status_path and self.health_status_path.exists():
            try:
                with file_lock(self.health_status_path):
                    data = read_json_file(self.health_status_path, default={})
                    component_data = data.get(self.component, {})

                    self.state = CircuitBreakerState(
                        component_data.get("state", CircuitBreakerState.CLOSED.value)
                    )
                    self.failure_count = component_data.get("failure_count", 0)
                    self.last_failure_time = component_data.get("last_failure_time")
                    self.last_success_time = component_data.get("last_success_time")
                    return
            except Exception:
                pass  # Fall through to default initialization

        # Default initialization
        self.state = CircuitBreakerState.CLOSED
        self.failure_count = 0
        self.last_failure_time: Optional[str] = None
        self.last_success_time: Optional[str] = None

    def _save_state(self):
        """Persist circuit breaker state to file."""
        if not self.health_status_path:
            return

        try:
            with file_lock(self.health_status_path):
                # Read existing data
                data = read_json_file(self.health_status_path, default={})

                # Update component data
                data[self.component] = {
                    "state": self.state.value,
                    "failure_count": self.failure_count,
                    "last_failure_time": self.last_failure_time,
                    "last_success_time": self.last_success_time,
                    "updated_at": datetime.now(UTC).isoformat().replace('+00:00', 'Z')
                }

                # Write back
                write_json_file(self.health_status_path, data)
        except Exception as e:
            if self.error_logger:
                self.error_logger.log_error(
                    component="CircuitBreaker",
                    error_type=ErrorType.SYSTEM,
                    message=f"Failed to persist circuit breaker state for {self.component}",
                    error=e
                )

    def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute a function through the circuit breaker.

        Args:
            func: Function to execute
            *args: Positional arguments for the function
            **kwargs: Keyword arguments for the function

        Returns:
            Result of the function call

        Raises:
            CircuitBreakerOpenError: If circuit is open
            Exception: Any exception raised by the function
        """
        # Check if circuit is open
        if self.state == CircuitBreakerState.OPEN:
            # Check if timeout has passed to transition to half-open
            if self._should_attempt_reset():
                self._transition_to_half_open()
            else:
                raise CircuitBreakerOpenError(
                    self.component,
                    f"Circuit breaker is OPEN for {self.component}. "
                    f"Last failure: {self.last_failure_time}"
                )

        # Attempt to call the function
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure(e)
            raise

    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset."""
        if not self.last_failure_time:
            return True

        try:
            last_failure = datetime.fromisoformat(self.last_failure_time.replace('Z', '+00:00'))
            elapsed = (datetime.now(UTC) - last_failure).total_seconds()
            return elapsed >= self.timeout_seconds
        except Exception:
            return True

    def _transition_to_half_open(self):
        """Transition circuit from OPEN to HALF_OPEN."""
        self.state = CircuitBreakerState.HALF_OPEN
        self._save_state()

        if self.error_logger:
            self.error_logger.log_error(
                component=self.component,
                error_type=ErrorType.SYSTEM,
                message=f"Circuit breaker transitioning to HALF_OPEN - attempting recovery",
                context={
                    "previous_state": "OPEN",
                    "failure_count": self.failure_count
                }
            )
            # Update dashboard - still paused but attempting recovery
            self.error_logger.update_paused_component(
                component=self.component,
                is_paused=True,
                reason="Attempting recovery (HALF_OPEN state)",
                failure_count=self.failure_count
            )

    def _on_success(self):
        """Handle successful function execution."""
        previous_state = self.state

        # Reset failure count and close circuit
        self.failure_count = 0
        self.state = CircuitBreakerState.CLOSED
        self.last_success_time = datetime.now(UTC).isoformat().replace('+00:00', 'Z')
        self._save_state()

        # Log recovery if we were in a failed state
        if previous_state != CircuitBreakerState.CLOSED and self.error_logger:
            self.error_logger.log_error(
                component=self.component,
                error_type=ErrorType.SYSTEM,
                message=f"Circuit breaker CLOSED - component recovered",
                context={
                    "previous_state": previous_state.value,
                    "recovery_time": self.last_success_time
                }
            )
            # Update dashboard - component is no longer paused
            self.error_logger.update_paused_component(
                component=self.component,
                is_paused=False
            )

    def _on_failure(self, exception: Exception):
        """Handle failed function execution."""
        self.failure_count += 1
        self.last_failure_time = datetime.now(UTC).isoformat().replace('+00:00', 'Z')

        previous_state = self.state

        # Determine if we should open the circuit
        if isinstance(exception, AuthenticationError):
            # Authentication errors open circuit immediately
            self.state = CircuitBreakerState.OPEN
        elif self.state == CircuitBreakerState.HALF_OPEN:
            # Any failure in half-open state opens the circuit
            self.state = CircuitBreakerState.OPEN
        elif self.failure_count >= self.failure_threshold:
            # Threshold reached, open the circuit
            self.state = CircuitBreakerState.OPEN

        self._save_state()

        # Log state change
        if self.state == CircuitBreakerState.OPEN and previous_state != CircuitBreakerState.OPEN:
            if self.error_logger:
                # Determine error type and message based on exception
                if isinstance(exception, AuthenticationError):
                    error_type = ErrorType.AUTHENTICATION
                    message = f"Circuit breaker OPENED - authentication error requires immediate action"
                    reason = "Authentication error - credentials may be expired or invalid"
                else:
                    error_type = ErrorType.SYSTEM
                    message = f"Circuit breaker OPENED - component paused after {self.failure_count} failures"
                    reason = f"Circuit breaker opened after {self.failure_count} consecutive failures"

                self.error_logger.log_error(
                    component=self.component,
                    error_type=error_type,
                    message=message,
                    error=exception,
                    context={
                        "failure_threshold": self.failure_threshold,
                        "consecutive_failures": self.failure_count,
                        "last_failure_time": self.last_failure_time,
                        "action_required": isinstance(exception, AuthenticationError)
                    }
                )
                # Update dashboard - component is now paused
                self.error_logger.update_paused_component(
                    component=self.component,
                    is_paused=True,
                    reason=reason,
                    failure_count=self.failure_count
                )

    def reset(self):
        """Manually reset the circuit breaker to CLOSED state."""
        previous_state = self.state

        self.state = CircuitBreakerState.CLOSED
        self.failure_count = 0
        self.last_success_time = datetime.now(UTC).isoformat().replace('+00:00', 'Z')
        self._save_state()

        if self.error_logger and previous_state != CircuitBreakerState.CLOSED:
            self.error_logger.log_error(
                component=self.component,
                error_type=ErrorType.SYSTEM,
                message=f"Circuit breaker manually reset to CLOSED",
                context={
                    "previous_state": previous_state.value,
                    "reset_time": self.last_success_time
                }
            )

    def get_status(self) -> ComponentHealthStatus:
        """
        Get current health status of the component.

        Returns:
            ComponentHealthStatus with current state information
        """
        from .entities import ComponentStatus

        # Map circuit breaker state to component status
        if self.state == CircuitBreakerState.CLOSED:
            status = ComponentStatus.RUNNING
        elif self.state == CircuitBreakerState.HALF_OPEN:
            status = ComponentStatus.STARTING
        else:  # OPEN
            status = ComponentStatus.PAUSED

        return ComponentHealthStatus(
            component=self.component,
            status=status,
            failure_count=self.failure_count,
            last_success_at=self.last_success_time,
            last_failure_at=self.last_failure_time,
            circuit_breaker_state=self.state,
            circuit_opened_at=self.last_failure_time if self.state == CircuitBreakerState.OPEN else None,
            health_check_last_run=datetime.now(UTC).isoformat().replace('+00:00', 'Z')
        )


def with_circuit_breaker(
    component: str,
    failure_threshold: int = 4,
    timeout_seconds: int = 60,
    health_status_path: Optional[Path] = None,
    error_logger: Optional[ErrorLogger] = None
):
    """
    Decorator to wrap a function with circuit breaker protection.

    Args:
        component: Name of the component
        failure_threshold: Number of failures before opening circuit
        timeout_seconds: Seconds to wait before attempting recovery
        health_status_path: Path to health status file
        error_logger: Optional ErrorLogger instance

    Returns:
        Decorated function with circuit breaker protection

    Example:
        @with_circuit_breaker("EmailService", failure_threshold=4)
        def send_email(to, subject, body):
            # This will be protected by circuit breaker
            ...
    """
    circuit_breaker = CircuitBreaker(
        component=component,
        failure_threshold=failure_threshold,
        timeout_seconds=timeout_seconds,
        health_status_path=health_status_path,
        error_logger=error_logger
    )

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            return circuit_breaker.call(func, *args, **kwargs)
        return wrapper
    return decorator

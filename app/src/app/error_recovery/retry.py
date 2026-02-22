"""
Retry mechanism with exponential backoff for transient errors.

This module provides decorators and utilities for automatically retrying operations
that fail due to transient errors, with configurable exponential backoff.
"""

from functools import wraps
from typing import Callable, Optional, Type, Tuple
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    wait_random_exponential,
    retry_if_exception_type,
    before_sleep_log,
    after_log
)
import logging

from .entities import ErrorType
from .exceptions import TransientError, ErrorRecoveryException, AuthenticationError
from .error_logger import ErrorLogger


logger = logging.getLogger(__name__)


def with_retry(
    max_attempts: int = 3,
    initial_wait: float = 1.0,
    max_wait: float = 10.0,
    multiplier: float = 2.0,
    jitter: bool = True,
    exception_types: Tuple[Type[Exception], ...] = (TransientError,),
    error_logger: Optional[ErrorLogger] = None,
    component: str = "Unknown"
):
    """
    Decorator to retry a function with exponential backoff on transient errors.

    Args:
        max_attempts: Maximum number of retry attempts (default: 3)
        initial_wait: Initial wait time in seconds (default: 1.0)
        max_wait: Maximum wait time in seconds (default: 10.0)
        multiplier: Exponential backoff multiplier (default: 2.0)
        jitter: Add random jitter to retry delays to avoid thundering herd (default: True)
        exception_types: Tuple of exception types to retry on (default: (TransientError,))
        error_logger: Optional ErrorLogger instance for logging retry attempts
        component: Name of the component for error logging

    Returns:
        Decorated function with retry logic

    Example:
        @with_retry(max_attempts=3, component="EmailService")
        def send_email(to, subject, body):
            # This will retry up to 3 times on TransientError
            ...
    """
    def decorator(func: Callable) -> Callable:
        # Track retry attempts for logging
        retry_count = {"count": 0}

        def log_retry_attempt(retry_state_obj):
            """Log retry attempts."""
            retry_count["count"] = retry_state_obj.attempt_number

            if error_logger:
                attempt_number = retry_state_obj.attempt_number
                outcome = retry_state_obj.outcome

                if outcome and outcome.failed:
                    error_logger.log_error(
                        component=component,
                        error_type=ErrorType.TRANSIENT,
                        message=f"Transient error on attempt {attempt_number}/{max_attempts}",
                        error=outcome.exception(),
                        retry_count=attempt_number,
                        context={
                            "function": func.__name__,
                            "max_attempts": max_attempts
                        }
                    )

        # Choose wait strategy based on jitter setting
        if jitter:
            wait_strategy = wait_random_exponential(
                multiplier=multiplier,
                min=initial_wait,
                max=max_wait
            )
        else:
            wait_strategy = wait_exponential(
                multiplier=multiplier,
                min=initial_wait,
                max=max_wait
            )

        def should_retry_exception(retry_state):
            """Check if exception should be retried."""
            # Extract exception from retry state
            if not retry_state.outcome or not retry_state.outcome.failed:
                return False

            exception = retry_state.outcome.exception()

            # Never retry authentication errors
            if isinstance(exception, AuthenticationError):
                if error_logger:
                    error_logger.log_error(
                        component=component,
                        error_type=ErrorType.AUTHENTICATION,
                        message=f"Authentication error - immediate pause required",
                        error=exception,
                        context={
                            "function": func.__name__,
                            "action_required": True
                        }
                    )
                return False

            # Check if exception matches configured retry types
            return isinstance(exception, exception_types)

        @retry(
            stop=stop_after_attempt(max_attempts),
            wait=wait_strategy,
            retry=should_retry_exception,
            before_sleep=log_retry_attempt,
            reraise=True  # Re-raise the original exception, not RetryError
        )
        @wraps(func)
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)

            # Log successful retry if this wasn't the first attempt
            if retry_count["count"] > 0 and error_logger:
                error_logger.log_error(
                    component=component,
                    error_type=ErrorType.TRANSIENT,
                    message=f"Operation succeeded after {retry_count['count']} retries",
                    context={
                        "function": func.__name__,
                        "retry_count": retry_count["count"],
                        "resolution": "auto_recovered"
                    }
                )

            # Reset counter for next call
            retry_count["count"] = 0

            return result

        return wrapper
    return decorator


class RetryableOperation:
    """
    Context manager for retryable operations with manual retry control.

    This provides more fine-grained control than the decorator for cases where
    you need to handle retries within a larger operation.

    Example:
        retry_op = RetryableOperation(
            max_attempts=3,
            error_logger=logger,
            component="DataProcessor"
        )

        with retry_op:
            # Your operation here
            result = process_data()

        if retry_op.succeeded:
            print(f"Succeeded after {retry_op.attempt_count} attempts")
    """

    def __init__(
        self,
        max_attempts: int = 3,
        initial_wait: float = 1.0,
        max_wait: float = 10.0,
        multiplier: float = 2.0,
        error_logger: Optional[ErrorLogger] = None,
        component: str = "Unknown"
    ):
        """
        Initialize retryable operation.

        Args:
            max_attempts: Maximum number of retry attempts
            initial_wait: Initial wait time in seconds
            max_wait: Maximum wait time in seconds
            multiplier: Exponential backoff multiplier
            error_logger: Optional ErrorLogger instance
            component: Name of the component for error logging
        """
        self.max_attempts = max_attempts
        self.initial_wait = initial_wait
        self.max_wait = max_wait
        self.multiplier = multiplier
        self.error_logger = error_logger
        self.component = component

        self.attempt_count = 0
        self.succeeded = False
        self.last_error: Optional[Exception] = None

    def __enter__(self):
        """Enter the retry context."""
        self.attempt_count += 1
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit the retry context and handle exceptions."""
        if exc_type is None:
            # Success
            self.succeeded = True

            # Log successful retry if this wasn't the first attempt
            if self.attempt_count > 1 and self.error_logger:
                self.error_logger.log_error(
                    component=self.component,
                    error_type=ErrorType.TRANSIENT,
                    message=f"Operation succeeded after {self.attempt_count - 1} retries",
                    context={
                        "attempt_count": self.attempt_count,
                        "resolution": "auto_recovered"
                    }
                )

            return True

        # Exception occurred
        self.last_error = exc_val

        # Log the error
        if self.error_logger:
            self.error_logger.log_error(
                component=self.component,
                error_type=ErrorType.TRANSIENT,
                message=f"Transient error on attempt {self.attempt_count}/{self.max_attempts}",
                error=exc_val,
                retry_count=self.attempt_count,
                context={
                    "max_attempts": self.max_attempts
                }
            )

        # Don't suppress the exception - let it propagate
        return False

    def should_retry(self) -> bool:
        """
        Check if another retry attempt should be made.

        Returns:
            True if should retry, False otherwise
        """
        return not self.succeeded and self.attempt_count < self.max_attempts

    def get_wait_time(self) -> float:
        """
        Calculate wait time for next retry using exponential backoff.

        Returns:
            Wait time in seconds
        """
        wait = self.initial_wait * (self.multiplier ** (self.attempt_count - 1))
        return min(wait, self.max_wait)

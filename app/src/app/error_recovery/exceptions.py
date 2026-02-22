"""
Custom exception classes for error recovery system.

This module defines specialized exceptions used throughout the error recovery
system to distinguish between different types of failures and enable appropriate
handling strategies.
"""

from typing import Optional


class ErrorRecoveryException(Exception):
    """Base exception for all error recovery system errors."""
    pass


class CircuitBreakerOpenError(ErrorRecoveryException):
    """Raised when attempting to call a function through an open circuit breaker."""

    def __init__(self, component: str, message: Optional[str] = None):
        self.component = component
        if message is None:
            message = f"Circuit breaker is OPEN for component '{component}'. Component is paused."
        super().__init__(message)


class AuthenticationError(ErrorRecoveryException):
    """Raised when authentication fails (expired token, invalid credentials)."""

    def __init__(self, service: str, message: Optional[str] = None):
        self.service = service
        if message is None:
            message = f"Authentication failed for service '{service}'"
        super().__init__(message)


class TransientError(ErrorRecoveryException):
    """Raised for temporary failures that should be retried (network timeouts, rate limits)."""

    def __init__(self, message: str, retry_count: int = 0):
        self.retry_count = retry_count
        super().__init__(message)


class DataError(ErrorRecoveryException):
    """Raised when data is corrupted or invalid (parsing errors, schema violations)."""

    def __init__(self, file_path: str, message: str):
        self.file_path = file_path
        super().__init__(f"Data error in '{file_path}': {message}")


class SystemError(ErrorRecoveryException):
    """Raised for system-level failures (disk full, process crashes)."""
    pass


class QueueFullError(ErrorRecoveryException):
    """Raised when operation queue exceeds maximum size."""
    pass


class QuarantineError(ErrorRecoveryException):
    """Raised when file quarantine operation fails."""
    pass


class HealthStatusError(ErrorRecoveryException):
    """Raised when component health status operations fail."""
    pass


class WatchdogError(ErrorRecoveryException):
    """Raised when watchdog operations fail."""
    pass

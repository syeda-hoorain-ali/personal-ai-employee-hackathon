"""
Error recovery system for Personal AI Employee.

This package provides centralized error logging, retry mechanisms, circuit breakers,
and other error recovery capabilities.
"""

from .error_logger import ErrorLogger
from .retry import with_retry, RetryableOperation
from .circuit_breaker import CircuitBreaker, with_circuit_breaker
from .watchdog import Watchdog, ComponentConfig
from .operation_queue import OperationQueue, OperationQueueConfig
from .file_quarantine import FileQuarantine
from .entities import (
    ErrorType,
    ResolutionStatus,
    CircuitBreakerState,
    ComponentStatus,
    OperationStatus,
    ErrorLogEntry,
    ComponentHealthStatus,
    QueuedOperation,
    QuarantinedFile
)
from .exceptions import (
    ErrorRecoveryException,
    CircuitBreakerOpenError,
    AuthenticationError,
    TransientError,
    DataError,
    SystemError,
    QueueFullError,
    QuarantineError,
    HealthStatusError,
    WatchdogError
)

__all__ = [
    # Main classes
    "ErrorLogger",
    "with_retry",
    "RetryableOperation",
    "CircuitBreaker",
    "with_circuit_breaker",
    "Watchdog",
    "ComponentConfig",
    "OperationQueue",
    "OperationQueueConfig",
    "FileQuarantine",

    # Enums
    "ErrorType",
    "ResolutionStatus",
    "CircuitBreakerState",
    "ComponentStatus",
    "OperationStatus",

    # Data classes
    "ErrorLogEntry",
    "ComponentHealthStatus",
    "QueuedOperation",
    "QuarantinedFile",

    # Exceptions
    "ErrorRecoveryException",
    "CircuitBreakerOpenError",
    "AuthenticationError",
    "TransientError",
    "DataError",
    "SystemError",
    "QueueFullError",
    "QuarantineError",
    "HealthStatusError",
    "WatchdogError",
]

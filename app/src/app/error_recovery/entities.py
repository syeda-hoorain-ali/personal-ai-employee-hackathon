"""
Core entities and data structures for error recovery system.

This module defines the data classes used throughout the error recovery system,
including error log entries, component health status, queued operations, and
quarantined files.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any, List


class ErrorType(Enum):
    """Categories of errors for different handling strategies."""
    TRANSIENT = "TRANSIENT"  # Network timeouts, API rate limits - retry with backoff
    AUTHENTICATION = "AUTHENTICATION"  # 401, 403, invalid_grant - pause immediately
    LOGIC = "LOGIC"  # Unexpected responses, business rule violations - human review
    DATA = "DATA"  # Corrupted files, invalid formats - quarantine
    SYSTEM = "SYSTEM"  # Process crashes, disk full - watchdog restart


class ResolutionStatus(Enum):
    """Status of error resolution."""
    UNRESOLVED = "UNRESOLVED"
    AUTO_RECOVERED = "AUTO_RECOVERED"
    MANUAL_INTERVENTION_REQUIRED = "MANUAL_INTERVENTION_REQUIRED"
    IGNORED = "IGNORED"


class CircuitBreakerState(Enum):
    """Circuit breaker states."""
    CLOSED = "CLOSED"  # Normal operation
    OPEN = "OPEN"  # Component paused
    HALF_OPEN = "HALF_OPEN"  # Testing recovery


class ComponentStatus(Enum):
    """Operational state of a component."""
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    CRASHED = "CRASHED"
    STARTING = "STARTING"


class OperationStatus(Enum):
    """Status of queued operations."""
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


@dataclass
class ErrorLogEntry:
    """Represents a single error occurrence in the system."""

    id: str
    timestamp: str  # ISO 8601 format
    component: str
    error_type: ErrorType
    message: str
    stack_trace: Optional[str] = None
    retry_count: int = 0
    error_code: Optional[str] = None
    context: Dict[str, Any] = field(default_factory=dict)
    resolution_status: ResolutionStatus = ResolutionStatus.UNRESOLVED
    resolved_at: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "timestamp": self.timestamp,
            "component": self.component,
            "error_type": self.error_type.value,
            "error_code": self.error_code,
            "message": self.message,
            "stack_trace": self.stack_trace,
            "retry_count": self.retry_count,
            "context": self.context,
            "resolution_status": self.resolution_status.value,
            "resolved_at": self.resolved_at
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ErrorLogEntry':
        """Create from dictionary."""
        return cls(
            id=data["id"],
            timestamp=data["timestamp"],
            component=data["component"],
            error_type=ErrorType(data["error_type"]),
            message=data["message"],
            stack_trace=data.get("stack_trace"),
            retry_count=data.get("retry_count", 0),
            error_code=data.get("error_code"),
            context=data.get("context", {}),
            resolution_status=ResolutionStatus(data.get("resolution_status", "UNRESOLVED")),
            resolved_at=data.get("resolved_at")
        )


@dataclass
class ComponentHealthStatus:
    """Represents the operational state of a component."""

    component: str
    status: ComponentStatus
    failure_count: int = 0
    last_success_at: Optional[str] = None
    last_failure_at: Optional[str] = None
    last_error_id: Optional[str] = None
    circuit_breaker_state: CircuitBreakerState = CircuitBreakerState.CLOSED
    circuit_opened_at: Optional[str] = None
    restart_count: int = 0
    process_id: Optional[int] = None
    health_check_last_run: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "component": self.component,
            "status": self.status.value,
            "failure_count": self.failure_count,
            "last_success_at": self.last_success_at,
            "last_failure_at": self.last_failure_at,
            "last_error_id": self.last_error_id,
            "circuit_breaker_state": self.circuit_breaker_state.value,
            "circuit_opened_at": self.circuit_opened_at,
            "restart_count": self.restart_count,
            "process_id": self.process_id,
            "health_check_last_run": self.health_check_last_run,
            "metadata": self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ComponentHealthStatus':
        """Create from dictionary."""
        return cls(
            component=data.get("component") or data.get("component_name"),  # Support both for backward compatibility
            status=ComponentStatus(data["status"]),
            failure_count=data.get("failure_count", 0),
            last_success_at=data.get("last_success_at"),
            last_failure_at=data.get("last_failure_at"),
            last_error_id=data.get("last_error_id"),
            circuit_breaker_state=CircuitBreakerState(data.get("circuit_breaker_state", "CLOSED")),
            circuit_opened_at=data.get("circuit_opened_at"),
            restart_count=data.get("restart_count", 0),
            process_id=data.get("process_id"),
            health_check_last_run=data.get("health_check_last_run"),
            metadata=data.get("metadata", {})
        )


@dataclass
class QueuedOperation:
    """Represents a pending operation that couldn't be executed."""

    id: str
    operation_type: str
    operation_data: Dict[str, Any]
    status: OperationStatus
    priority: int
    component: str
    queued_at: str  # ISO 8601 format
    retry_count: int = 0
    max_retries: int = 3
    last_retry_at: Optional[str] = None
    completed_at: Optional[str] = None
    failed_at: Optional[str] = None
    cancelled_at: Optional[str] = None
    error_message: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "operation_type": self.operation_type,
            "operation_data": self.operation_data,
            "status": self.status.value,
            "priority": self.priority,
            "component": self.component,
            "queued_at": self.queued_at,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
            "last_retry_at": self.last_retry_at,
            "completed_at": self.completed_at,
            "failed_at": self.failed_at,
            "cancelled_at": self.cancelled_at,
            "error_message": self.error_message
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'QueuedOperation':
        """Create from dictionary."""
        return cls(
            id=data["id"],
            operation_type=data["operation_type"],
            operation_data=data["operation_data"],
            status=OperationStatus(data["status"]),
            priority=data["priority"],
            component=data["component"],
            queued_at=data["queued_at"],
            retry_count=data.get("retry_count", 0),
            max_retries=data.get("max_retries", 3),
            last_retry_at=data.get("last_retry_at"),
            completed_at=data.get("completed_at"),
            failed_at=data.get("failed_at"),
            cancelled_at=data.get("cancelled_at"),
            error_message=data.get("error_message")
        )


@dataclass
class QuarantinedFile:
    """Represents a corrupted file that was moved to quarantine."""

    id: str
    original_path: str
    quarantine_path: str
    quarantined_at: str  # ISO 8601 format
    reason: str
    error_type: ErrorType
    component: str
    file_size_bytes: int
    file_hash: str  # SHA-256
    metadata: Optional[Dict[str, Any]] = None
    restored_at: Optional[str] = None
    restored_to: Optional[str] = None

    def __post_init__(self):
        """Initialize metadata if None."""
        if self.metadata is None:
            self.metadata = {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "original_path": self.original_path,
            "quarantine_path": self.quarantine_path,
            "quarantined_at": self.quarantined_at,
            "reason": self.reason,
            "error_type": self.error_type.value,
            "component": self.component,
            "file_size_bytes": self.file_size_bytes,
            "file_hash": self.file_hash,
            "metadata": self.metadata,
            "restored_at": self.restored_at,
            "restored_to": self.restored_to
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'QuarantinedFile':
        """Create from dictionary."""
        return cls(
            id=data["id"],
            original_path=data["original_path"],
            quarantine_path=data["quarantine_path"],
            quarantined_at=data["quarantined_at"],
            reason=data["reason"],
            error_type=ErrorType(data["error_type"]),
            component=data["component"],
            file_size_bytes=data["file_size_bytes"],
            file_hash=data["file_hash"],
            metadata=data.get("metadata", {}),
            restored_at=data.get("restored_at"),
            restored_to=data.get("restored_to")
        )

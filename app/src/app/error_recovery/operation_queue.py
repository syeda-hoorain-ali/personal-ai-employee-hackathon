"""
Operation queue for handling failed operations and retrying them later.

This module provides the OperationQueue class for queuing operations when
external services are unavailable, with priority handling and persistence.
"""

import uuid
from datetime import datetime, UTC
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, asdict

from .entities import QueuedOperation, OperationStatus, ErrorType
from .exceptions import QueueFullError
from .error_logger import ErrorLogger
from .utils import read_json_file, write_json_file, file_lock, ensure_directory


@dataclass
class OperationQueueConfig:
    """Configuration for operation queue."""

    max_queue_size: int = 1000
    max_retries: int = 3
    retry_delay_seconds: int = 60
    priority_levels: int = 3  # 1=high, 2=medium, 3=low


class OperationQueue:
    """
    Queue for operations that failed due to external service unavailability.

    Features:
    - Priority-based queuing
    - Persistence to disk
    - Automatic retry with backoff
    - Queue size limits
    """

    def __init__(
        self,
        queue_dir: Path,
        config: Optional[OperationQueueConfig] = None,
        error_logger: Optional[ErrorLogger] = None
    ):
        """
        Initialize operation queue.

        Args:
            queue_dir: Directory for queue persistence
            config: Queue configuration
            error_logger: Optional ErrorLogger instance
        """
        self.queue_dir = Path(queue_dir)
        self.config = config or OperationQueueConfig()
        self.error_logger = error_logger

        # Ensure queue directories exist
        ensure_directory(self.queue_dir / "pending")
        ensure_directory(self.queue_dir / "completed")
        ensure_directory(self.queue_dir / "failed")

        # In-memory queue (loaded from disk)
        self.pending_operations: Dict[str, QueuedOperation] = {}
        self._load_pending_operations()

    def enqueue(
        self,
        operation_type: str,
        operation_data: Dict[str, Any],
        priority: int = 2,
        component: str = "Unknown"
    ) -> str:
        """
        Add an operation to the queue.

        Args:
            operation_type: Type of operation (e.g., "send_email", "post_linkedin")
            operation_data: Operation data/payload
            priority: Priority level (1=high, 2=medium, 3=low)
            component: Component that queued the operation

        Returns:
            Operation ID

        Raises:
            QueueFullError: If queue is at capacity
        """
        # Check queue size
        if len(self.pending_operations) >= self.config.max_queue_size:
            raise QueueFullError(
                f"Queue is full ({self.config.max_queue_size} operations)"
            )

        # Create operation
        operation_id = str(uuid.uuid4())
        operation = QueuedOperation(
            id=operation_id,
            operation_type=operation_type,
            operation_data=operation_data,
            status=OperationStatus.PENDING,
            priority=priority,
            component=component,
            queued_at=datetime.now(UTC).isoformat().replace('+00:00', 'Z'),
            retry_count=0,
            max_retries=self.config.max_retries
        )

        # Add to in-memory queue
        self.pending_operations[operation_id] = operation

        # Persist to disk
        self._save_operation(operation, "pending")

        # Log
        if self.error_logger:
            self.error_logger.log_error(
                component=component,
                error_type=ErrorType.TRANSIENT,
                message=f"Operation queued: {operation_type}",
                context={
                    "operation_id": operation_id,
                    "operation_type": operation_type,
                    "priority": priority,
                    "queue_size": len(self.pending_operations)
                }
            )

        return operation_id

    def process_queue(
        self,
        operation_handlers: Dict[str, Callable[[Dict[str, Any]], bool]]
    ) -> Dict[str, int]:
        """
        Process pending operations in priority order.

        Args:
            operation_handlers: Dictionary mapping operation types to handler functions
                               Handler should return True on success, False on failure

        Returns:
            Dictionary with counts: {"processed": N, "succeeded": N, "failed": N}
        """
        stats = {"processed": 0, "succeeded": 0, "failed": 0}

        # Sort operations by priority (1=highest)
        sorted_ops = sorted(
            self.pending_operations.values(),
            key=lambda op: (op.priority, op.queued_at)
        )

        for operation in sorted_ops:
            # Check if handler exists
            if operation.operation_type not in operation_handlers:
                continue

            # Get handler
            handler = operation_handlers[operation.operation_type]

            # Process operation
            try:
                success = handler(operation.operation_data)
                stats["processed"] += 1

                if success:
                    # Mark as completed
                    operation.status = OperationStatus.COMPLETED
                    operation.completed_at = datetime.now(UTC).isoformat().replace('+00:00', 'Z')

                    # Move to completed
                    self._move_operation(operation, "pending", "completed")
                    del self.pending_operations[operation.id]

                    stats["succeeded"] += 1

                    if self.error_logger:
                        self.error_logger.log_error(
                            component=operation.component,
                            error_type=ErrorType.TRANSIENT,
                            message=f"Queued operation completed: {operation.operation_type}",
                            context={
                                "operation_id": operation.id,
                                "retry_count": operation.retry_count
                            }
                        )
                else:
                    # Increment retry count
                    operation.retry_count += 1
                    operation.last_retry_at = datetime.now(UTC).isoformat().replace('+00:00', 'Z')

                    # Check if max retries exceeded
                    if operation.retry_count >= operation.max_retries:
                        operation.status = OperationStatus.FAILED
                        operation.failed_at = datetime.now(UTC).isoformat().replace('+00:00', 'Z')

                        # Move to failed
                        self._move_operation(operation, "pending", "failed")
                        del self.pending_operations[operation.id]

                        stats["failed"] += 1

                        if self.error_logger:
                            self.error_logger.log_error(
                                component=operation.component,
                                error_type=ErrorType.SYSTEM,
                                message=f"Queued operation failed after {operation.retry_count} retries",
                                context={
                                    "operation_id": operation.id,
                                    "operation_type": operation.operation_type
                                }
                            )
                    else:
                        # Save updated operation
                        self._save_operation(operation, "pending")

            except Exception as e:
                # Log error but continue processing
                if self.error_logger:
                    self.error_logger.log_error(
                        component=operation.component,
                        error_type=ErrorType.SYSTEM,
                        message=f"Error processing queued operation",
                        error=e,
                        context={
                            "operation_id": operation.id,
                            "operation_type": operation.operation_type
                        }
                    )

        return stats

    def get_queue_size(self, priority: Optional[int] = None) -> int:
        """
        Get number of pending operations.

        Args:
            priority: Optional priority filter

        Returns:
            Number of pending operations
        """
        if priority is None:
            return len(self.pending_operations)

        return sum(
            1 for op in self.pending_operations.values()
            if op.priority == priority
        )

    def cancel_operation(self, operation_id: str) -> bool:
        """
        Cancel a pending operation.

        Args:
            operation_id: Operation ID to cancel

        Returns:
            True if cancelled, False if not found
        """
        if operation_id not in self.pending_operations:
            return False

        operation = self.pending_operations[operation_id]
        operation.status = OperationStatus.CANCELLED
        operation.cancelled_at = datetime.now(UTC).isoformat().replace('+00:00', 'Z')

        # Move to failed directory
        self._move_operation(operation, "pending", "failed")
        del self.pending_operations[operation_id]

        return True

    def get_operation(self, operation_id: str) -> Optional[QueuedOperation]:
        """
        Get operation by ID.

        Args:
            operation_id: Operation ID

        Returns:
            QueuedOperation or None if not found
        """
        return self.pending_operations.get(operation_id)

    def get_all_pending(self) -> List[QueuedOperation]:
        """
        Get all pending operations.

        Returns:
            List of pending operations sorted by priority
        """
        return sorted(
            self.pending_operations.values(),
            key=lambda op: (op.priority, op.queued_at)
        )

    def _load_pending_operations(self):
        """Load pending operations from disk."""
        pending_dir = self.queue_dir / "pending"

        if not pending_dir.exists():
            return

        for file_path in pending_dir.glob("*.json"):
            try:
                data = read_json_file(file_path)
                operation = QueuedOperation.from_dict(data)
                self.pending_operations[operation.id] = operation
            except Exception as e:
                if self.error_logger:
                    self.error_logger.log_error(
                        component="OperationQueue",
                        error_type=ErrorType.DATA,
                        message=f"Failed to load queued operation",
                        error=e,
                        context={"file": str(file_path)}
                    )

    def _save_operation(self, operation: QueuedOperation, subdir: str):
        """Save operation to disk."""
        file_path = self.queue_dir / subdir / f"{operation.id}.json"

        try:
            write_json_file(file_path, operation.to_dict())
        except Exception as e:
            if self.error_logger:
                self.error_logger.log_error(
                    component="OperationQueue",
                    error_type=ErrorType.SYSTEM,
                    message=f"Failed to save queued operation",
                    error=e,
                    context={"operation_id": operation.id}
                )

    def _move_operation(self, operation: QueuedOperation, from_dir: str, to_dir: str):
        """Move operation file between directories."""
        from_path = self.queue_dir / from_dir / f"{operation.id}.json"
        to_path = self.queue_dir / to_dir / f"{operation.id}.json"

        try:
            # Save to new location
            write_json_file(to_path, operation.to_dict())

            # Remove from old location
            if from_path.exists():
                from_path.unlink()
        except Exception as e:
            if self.error_logger:
                self.error_logger.log_error(
                    component="OperationQueue",
                    error_type=ErrorType.SYSTEM,
                    message=f"Failed to move queued operation",
                    error=e,
                    context={
                        "operation_id": operation.id,
                        "from": from_dir,
                        "to": to_dir
                    }
                )

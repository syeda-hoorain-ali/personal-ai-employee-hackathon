"""
Unit tests for OperationQueue class.

Tests cover:
- T090: Test enqueue() adds operation to queue
- T091: Test process_queue() executes operations in priority order
- T092: Test queue respects max_queue_size limit
- T093: Test operations retry on failure with backoff
- T094: Test operations marked as failed after max retries
"""

import pytest
from pathlib import Path
from datetime import datetime, UTC
from typing import Dict, Any
import tempfile
import shutil
import json

from app.error_recovery.operation_queue import OperationQueue, OperationQueueConfig
from app.error_recovery.error_logger import ErrorLogger
from app.error_recovery.entities import OperationStatus, ErrorType
from app.error_recovery.exceptions import QueueFullError


@pytest.fixture
def temp_dirs():
    """Create temporary directories for testing."""
    temp_dir = Path(tempfile.mkdtemp())
    queue_dir = temp_dir / "queue"
    logs_dir = temp_dir / "logs"

    queue_dir.mkdir(parents=True)
    logs_dir.mkdir(parents=True)

    yield {
        "temp_dir": temp_dir,
        "queue_dir": queue_dir,
        "logs_dir": logs_dir
    }

    # Cleanup
    shutil.rmtree(temp_dir)


@pytest.fixture
def error_logger(temp_dirs):
    """Create ErrorLogger instance for testing."""
    dashboard_path = temp_dirs["temp_dir"] / "dashboard.json"
    return ErrorLogger(temp_dirs["logs_dir"], dashboard_path)


@pytest.fixture
def operation_queue(temp_dirs, error_logger):
    """Create OperationQueue instance for testing."""
    config = OperationQueueConfig(
        max_queue_size=10,
        max_retries=3,
        retry_delay_seconds=0,  # No delay for testing
        priority_levels=3
    )
    return OperationQueue(
        queue_dir=temp_dirs["queue_dir"],
        config=config,
        error_logger=error_logger
    )


# T090: Test enqueue() adds operation to queue
def test_enqueue_adds_operation(operation_queue):
    """Test that enqueue() adds an operation to the queue."""
    operation_data = {"email": "test@example.com", "subject": "Test"}

    # Enqueue operation
    operation_id = operation_queue.enqueue(
        operation_type="send_email",
        operation_data=operation_data,
        priority=1,
        component="EmailService"
    )

    # Verify operation was added
    assert operation_id is not None
    assert len(operation_id) > 0

    # Verify operation is in queue
    operation = operation_queue.get_operation(operation_id)
    assert operation is not None
    assert operation.id == operation_id
    assert operation.operation_type == "send_email"
    assert operation.operation_data == operation_data
    assert operation.priority == 1
    assert operation.component == "EmailService"
    assert operation.status == OperationStatus.PENDING
    assert operation.retry_count == 0


def test_enqueue_creates_persistence_file(operation_queue, temp_dirs):
    """Test that enqueue() creates a persistence file."""
    operation_data = {"test": "data"}

    # Enqueue operation
    operation_id = operation_queue.enqueue(
        operation_type="test_operation",
        operation_data=operation_data,
        priority=2,
        component="TestComponent"
    )

    # Verify persistence file exists
    persistence_file = temp_dirs["queue_dir"] / "pending" / f"{operation_id}.json"
    assert persistence_file.exists()

    # Verify file content
    with open(persistence_file, 'r') as f:
        data = json.load(f)
        assert data["id"] == operation_id
        assert data["operation_type"] == "test_operation"
        assert data["operation_data"] == operation_data


def test_enqueue_multiple_operations(operation_queue):
    """Test enqueueing multiple operations."""
    operation_ids = []

    for i in range(5):
        operation_id = operation_queue.enqueue(
            operation_type=f"operation_{i}",
            operation_data={"index": i},
            priority=i % 3 + 1,  # Mix of priorities
            component="TestComponent"
        )
        operation_ids.append(operation_id)

    # Verify all operations are in queue
    assert operation_queue.get_queue_size() == 5

    # Verify each operation
    for operation_id in operation_ids:
        operation = operation_queue.get_operation(operation_id)
        assert operation is not None
        assert operation.status == OperationStatus.PENDING


# T091: Test process_queue() executes operations in priority order
def test_process_queue_priority_order(operation_queue):
    """Test that operations are processed in priority order (1=highest)."""
    processed_order = []

    def handler(data: Dict[str, Any]) -> bool:
        processed_order.append(data["priority"])
        return True

    # Enqueue operations with different priorities
    operation_queue.enqueue("test_op", {"priority": 3}, priority=3, component="Test")
    operation_queue.enqueue("test_op", {"priority": 1}, priority=1, component="Test")
    operation_queue.enqueue("test_op", {"priority": 2}, priority=2, component="Test")

    # Process queue
    handlers = {"test_op": handler}
    stats = operation_queue.process_queue(handlers)

    # Verify processing order (1, 2, 3)
    assert processed_order == [1, 2, 3]
    assert stats["processed"] == 3
    assert stats["succeeded"] == 3
    assert stats["failed"] == 0


def test_process_queue_successful_operations(operation_queue):
    """Test that successful operations are marked as completed."""
    success_count = 0

    def successful_handler(data: Dict[str, Any]) -> bool:
        nonlocal success_count
        success_count += 1
        return True

    # Enqueue operations
    op_id1 = operation_queue.enqueue("test_op", {"data": "1"}, priority=1, component="Test")
    op_id2 = operation_queue.enqueue("test_op", {"data": "2"}, priority=1, component="Test")

    # Process queue
    handlers = {"test_op": successful_handler}
    stats = operation_queue.process_queue(handlers)

    # Verify statistics
    assert stats["processed"] == 2
    assert stats["succeeded"] == 2
    assert stats["failed"] == 0
    assert success_count == 2

    # Verify operations are no longer in pending queue
    assert operation_queue.get_operation(op_id1) is None
    assert operation_queue.get_operation(op_id2) is None
    assert operation_queue.get_queue_size() == 0


def test_process_queue_skips_unknown_operation_types(operation_queue):
    """Test that operations without handlers are skipped."""
    def handler(data: Dict[str, Any]) -> bool:
        return True

    # Enqueue operations with different types
    operation_queue.enqueue("known_op", {"data": "1"}, priority=1, component="Test")
    operation_queue.enqueue("unknown_op", {"data": "2"}, priority=1, component="Test")

    # Process queue with handler only for known_op
    handlers = {"known_op": handler}
    stats = operation_queue.process_queue(handlers)

    # Verify only known operation was processed
    assert stats["processed"] == 1
    assert stats["succeeded"] == 1

    # Verify unknown operation is still in queue
    assert operation_queue.get_queue_size() == 1


# T092: Test queue respects max_queue_size limit
def test_queue_respects_max_size(temp_dirs, error_logger):
    """Test that queue respects max_queue_size limit."""
    config = OperationQueueConfig(max_queue_size=3)
    queue = OperationQueue(
        queue_dir=temp_dirs["queue_dir"],
        config=config,
        error_logger=error_logger
    )

    # Enqueue up to max size
    queue.enqueue("op1", {"data": "1"}, priority=1, component="Test")
    queue.enqueue("op2", {"data": "2"}, priority=1, component="Test")
    queue.enqueue("op3", {"data": "3"}, priority=1, component="Test")

    # Verify queue is at capacity
    assert queue.get_queue_size() == 3

    # Try to enqueue one more - should raise QueueFullError
    with pytest.raises(QueueFullError, match="Queue is full"):
        queue.enqueue("op4", {"data": "4"}, priority=1, component="Test")


def test_get_queue_size_by_priority(operation_queue):
    """Test getting queue size filtered by priority."""
    # Enqueue operations with different priorities
    operation_queue.enqueue("op", {"data": "1"}, priority=1, component="Test")
    operation_queue.enqueue("op", {"data": "2"}, priority=1, component="Test")
    operation_queue.enqueue("op", {"data": "3"}, priority=2, component="Test")
    operation_queue.enqueue("op", {"data": "4"}, priority=3, component="Test")

    # Verify total size
    assert operation_queue.get_queue_size() == 4

    # Verify size by priority
    assert operation_queue.get_queue_size(priority=1) == 2
    assert operation_queue.get_queue_size(priority=2) == 1
    assert operation_queue.get_queue_size(priority=3) == 1


# T093: Test operations retry on failure with backoff
def test_operations_retry_on_failure(operation_queue):
    """Test that failed operations are retried."""
    attempt_count = 0

    def failing_handler(data: Dict[str, Any]) -> bool:
        nonlocal attempt_count
        attempt_count += 1
        return False  # Always fail

    # Enqueue operation
    op_id = operation_queue.enqueue("test_op", {"data": "1"}, priority=1, component="Test")

    # Process queue multiple times (simulating retry attempts)
    handlers = {"test_op": failing_handler}

    # First attempt
    stats1 = operation_queue.process_queue(handlers)
    assert stats1["processed"] == 1
    assert stats1["succeeded"] == 0

    # Verify operation is still in queue with incremented retry count
    operation = operation_queue.get_operation(op_id)
    assert operation is not None
    assert operation.retry_count == 1
    assert operation.status == OperationStatus.PENDING

    # Second attempt
    stats2 = operation_queue.process_queue(handlers)
    assert stats2["processed"] == 1

    operation = operation_queue.get_operation(op_id)
    assert operation.retry_count == 2


def test_retry_count_increments(operation_queue):
    """Test that retry count increments on each failure."""
    def failing_handler(data: Dict[str, Any]) -> bool:
        return False

    # Enqueue operation
    op_id = operation_queue.enqueue("test_op", {"data": "1"}, priority=1, component="Test")

    handlers = {"test_op": failing_handler}

    # Process multiple times
    for expected_retry_count in range(1, 4):
        operation_queue.process_queue(handlers)
        operation = operation_queue.get_operation(op_id)

        if operation:  # Operation might be removed after max retries
            assert operation.retry_count == expected_retry_count


# T094: Test operations marked as failed after max retries
def test_operations_fail_after_max_retries(operation_queue):
    """Test that operations are marked as failed after max retries."""
    def failing_handler(data: Dict[str, Any]) -> bool:
        return False  # Always fail

    # Enqueue operation
    op_id = operation_queue.enqueue("test_op", {"data": "1"}, priority=1, component="Test")

    handlers = {"test_op": failing_handler}

    # Process queue until max retries exceeded (config has max_retries=3)
    for _ in range(4):  # Process 4 times to exceed max_retries
        stats = operation_queue.process_queue(handlers)

    # Verify operation was marked as failed and removed from pending
    assert operation_queue.get_operation(op_id) is None
    assert operation_queue.get_queue_size() == 0

    # Verify operation was moved to failed directory
    failed_file = operation_queue.queue_dir / "failed" / f"{op_id}.json"
    assert failed_file.exists()

    # Verify operation status in failed file
    with open(failed_file, 'r') as f:
        data = json.load(f)
        assert data["status"] == OperationStatus.FAILED.value
        assert data["retry_count"] >= 3


def test_mixed_success_and_failure(operation_queue):
    """Test processing queue with mix of successful and failing operations."""
    results = {"op1": True, "op2": False, "op3": True}

    def mixed_handler(data: Dict[str, Any]) -> bool:
        return results.get(data["id"], False)

    # Enqueue operations
    op_id1 = operation_queue.enqueue("test_op", {"id": "op1"}, priority=1, component="Test")
    op_id2 = operation_queue.enqueue("test_op", {"id": "op2"}, priority=1, component="Test")
    op_id3 = operation_queue.enqueue("test_op", {"id": "op3"}, priority=1, component="Test")

    handlers = {"test_op": mixed_handler}
    stats = operation_queue.process_queue(handlers)

    # Verify statistics
    assert stats["processed"] == 3
    assert stats["succeeded"] == 2  # op1 and op3
    assert stats["failed"] == 0  # op2 is retrying, not failed yet

    # Verify successful operations are removed
    assert operation_queue.get_operation(op_id1) is None
    assert operation_queue.get_operation(op_id3) is None

    # Verify failed operation is still in queue for retry
    assert operation_queue.get_operation(op_id2) is not None


def test_cancel_operation(operation_queue):
    """Test cancelling a pending operation."""
    # Enqueue operation
    op_id = operation_queue.enqueue("test_op", {"data": "1"}, priority=1, component="Test")

    # Verify operation is in queue
    assert operation_queue.get_operation(op_id) is not None

    # Cancel operation
    result = operation_queue.cancel_operation(op_id)
    assert result is True

    # Verify operation is no longer in pending queue
    assert operation_queue.get_operation(op_id) is None
    assert operation_queue.get_queue_size() == 0


def test_cancel_nonexistent_operation(operation_queue):
    """Test cancelling a non-existent operation returns False."""
    result = operation_queue.cancel_operation("nonexistent_id")
    assert result is False


def test_get_all_pending(operation_queue):
    """Test getting all pending operations sorted by priority."""
    # Enqueue operations with different priorities
    op_id1 = operation_queue.enqueue("op", {"data": "1"}, priority=3, component="Test")
    op_id2 = operation_queue.enqueue("op", {"data": "2"}, priority=1, component="Test")
    op_id3 = operation_queue.enqueue("op", {"data": "3"}, priority=2, component="Test")

    # Get all pending operations
    pending = operation_queue.get_all_pending()

    # Verify operations are sorted by priority (1, 2, 3)
    assert len(pending) == 3
    assert pending[0].id == op_id2  # Priority 1
    assert pending[1].id == op_id3  # Priority 2
    assert pending[2].id == op_id1  # Priority 3


def test_queue_persistence_across_instances(temp_dirs, error_logger):
    """Test that queue state persists across instances."""
    config = OperationQueueConfig(max_retries=3)

    # Create first queue instance and enqueue operations
    queue1 = OperationQueue(
        queue_dir=temp_dirs["queue_dir"],
        config=config,
        error_logger=error_logger
    )

    op_id1 = queue1.enqueue("op1", {"data": "1"}, priority=1, component="Test")
    op_id2 = queue1.enqueue("op2", {"data": "2"}, priority=2, component="Test")

    # Create second queue instance (should load persisted operations)
    queue2 = OperationQueue(
        queue_dir=temp_dirs["queue_dir"],
        config=config,
        error_logger=error_logger
    )

    # Verify operations were loaded
    assert queue2.get_queue_size() == 2
    assert queue2.get_operation(op_id1) is not None
    assert queue2.get_operation(op_id2) is not None

"""
Unit tests for Watchdog queue processing functionality.

Tests cover:
- T088: Test watchdog processes operation queues during monitoring loop
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from typing import Dict, Any

from app.error_recovery.watchdog import Watchdog
from app.error_recovery.operation_queue import OperationQueue
from app.error_recovery.error_logger import ErrorLogger


@pytest.fixture
def temp_vault():
    """Create temporary vault directory for testing."""
    temp_dir = Path(tempfile.mkdtemp())
    logs_dir = temp_dir / "Logs" / "Errors"
    system_dir = temp_dir / ".system"
    queue_dir = temp_dir / "Queue" / "test_service"

    logs_dir.mkdir(parents=True)
    system_dir.mkdir(parents=True)
    queue_dir.mkdir(parents=True)

    yield temp_dir

    # Cleanup
    shutil.rmtree(temp_dir)


@pytest.fixture
def error_logger(temp_vault):
    """Create ErrorLogger instance for testing."""
    logs_dir = temp_vault / "Logs" / "Errors"
    dashboard_path = temp_vault / ".system" / "error_dashboard.json"
    return ErrorLogger(logs_dir, dashboard_path)


@pytest.fixture
def watchdog(temp_vault, error_logger):
    """Create Watchdog instance for testing."""
    return Watchdog(
        vault_path=temp_vault,
        check_interval_seconds=1,
        error_logger=error_logger
    )


@pytest.fixture
def operation_queue(temp_vault, error_logger):
    """Create OperationQueue instance for testing."""
    queue_dir = temp_vault / "Queue" / "test_service"
    return OperationQueue(
        queue_dir=queue_dir,
        error_logger=error_logger
    )


# T088: Test watchdog processes operation queues
def test_watchdog_registers_operation_queue(watchdog, operation_queue):
    """Test that watchdog can register an operation queue."""
    # Create mock handler
    def mock_handler(operation_data: Dict[str, Any]) -> bool:
        return True

    handlers = {
        "test_operation": mock_handler
    }

    # Register queue
    watchdog.register_operation_queue(
        queue_name="test_service",
        operation_queue=operation_queue,
        handlers=handlers
    )

    # Verify registration
    assert "test_service" in watchdog.operation_queues
    assert watchdog.operation_queues["test_service"] == operation_queue
    assert "test_service" in watchdog.operation_handlers
    assert watchdog.operation_handlers["test_service"] == handlers


def test_watchdog_processes_queued_operations(watchdog, operation_queue):
    """Test that watchdog processes operations from registered queues."""
    # Track processed operations
    processed_operations = []

    def mock_handler(operation_data: Dict[str, Any]) -> bool:
        processed_operations.append(operation_data)
        return True

    handlers = {
        "test_operation": mock_handler
    }

    # Register queue
    watchdog.register_operation_queue(
        queue_name="test_service",
        operation_queue=operation_queue,
        handlers=handlers
    )

    # Enqueue some operations
    op1_id = operation_queue.enqueue(
        operation_type="test_operation",
        operation_data={"message": "Operation 1"},
        priority=1,
        component="TestComponent"
    )

    op2_id = operation_queue.enqueue(
        operation_type="test_operation",
        operation_data={"message": "Operation 2"},
        priority=2,
        component="TestComponent"
    )

    # Process queues
    watchdog._process_operation_queues()

    # Verify operations were processed
    assert len(processed_operations) == 2
    assert processed_operations[0]["message"] == "Operation 1"  # Higher priority first
    assert processed_operations[1]["message"] == "Operation 2"


def test_watchdog_handles_queue_processing_errors(watchdog, operation_queue):
    """Test that watchdog handles errors during queue processing gracefully."""
    # Create handler that raises exception
    def failing_handler(operation_data: Dict[str, Any]) -> bool:
        raise RuntimeError("Handler failed")

    handlers = {
        "test_operation": failing_handler
    }

    # Register queue
    watchdog.register_operation_queue(
        queue_name="test_service",
        operation_queue=operation_queue,
        handlers=handlers
    )

    # Enqueue operation
    operation_queue.enqueue(
        operation_type="test_operation",
        operation_data={"message": "Test"},
        priority=1,
        component="TestComponent"
    )

    # Process queues - should not crash
    try:
        watchdog._process_operation_queues()
        # Should complete without raising exception
        assert True
    except Exception as e:
        pytest.fail(f"Queue processing should handle errors gracefully: {e}")


def test_watchdog_processes_multiple_queues(watchdog, temp_vault, error_logger):
    """Test that watchdog can process multiple operation queues."""
    # Create two queues
    queue1_dir = temp_vault / "Queue" / "service1"
    queue2_dir = temp_vault / "Queue" / "service2"
    queue1_dir.mkdir(parents=True)
    queue2_dir.mkdir(parents=True)

    queue1 = OperationQueue(queue_dir=queue1_dir, error_logger=error_logger)
    queue2 = OperationQueue(queue_dir=queue2_dir, error_logger=error_logger)

    # Track processed operations
    processed_ops = {"service1": [], "service2": []}

    def handler1(operation_data: Dict[str, Any]) -> bool:
        processed_ops["service1"].append(operation_data)
        return True

    def handler2(operation_data: Dict[str, Any]) -> bool:
        processed_ops["service2"].append(operation_data)
        return True

    # Register both queues
    watchdog.register_operation_queue(
        queue_name="service1",
        operation_queue=queue1,
        handlers={"op_type": handler1}
    )

    watchdog.register_operation_queue(
        queue_name="service2",
        operation_queue=queue2,
        handlers={"op_type": handler2}
    )

    # Enqueue operations in both queues
    queue1.enqueue("op_type", {"service": "1"}, priority=1, component="Test")
    queue2.enqueue("op_type", {"service": "2"}, priority=1, component="Test")

    # Process all queues
    watchdog._process_operation_queues()

    # Verify both queues were processed
    assert len(processed_ops["service1"]) == 1
    assert len(processed_ops["service2"]) == 1
    assert processed_ops["service1"][0]["service"] == "1"
    assert processed_ops["service2"][0]["service"] == "2"


def test_watchdog_skips_queue_with_no_handlers(watchdog, operation_queue):
    """Test that watchdog skips processing queues with no handlers."""
    # Register queue with empty handlers
    watchdog.register_operation_queue(
        queue_name="test_service",
        operation_queue=operation_queue,
        handlers={}
    )

    # Enqueue operation
    operation_queue.enqueue(
        operation_type="test_operation",
        operation_data={"message": "Test"},
        priority=1,
        component="TestComponent"
    )

    # Process queues - should not crash and should skip this queue
    watchdog._process_operation_queues()

    # Operation should still be pending (not processed)
    assert operation_queue.get_queue_size() == 1


def test_watchdog_logs_queue_processing_stats(watchdog, operation_queue, error_logger):
    """Test that watchdog logs statistics after processing queues."""
    # Create handler
    def mock_handler(operation_data: Dict[str, Any]) -> bool:
        return True

    handlers = {"test_operation": mock_handler}

    # Register queue
    watchdog.register_operation_queue(
        queue_name="test_service",
        operation_queue=operation_queue,
        handlers=handlers
    )

    # Enqueue operations
    operation_queue.enqueue("test_operation", {"msg": "1"}, priority=1, component="Test")
    operation_queue.enqueue("test_operation", {"msg": "2"}, priority=1, component="Test")

    # Process queues
    watchdog._process_operation_queues()

    # Verify error logger was called (logs are created)
    # Check that today's log file exists
    from datetime import datetime, UTC
    today = datetime.now(UTC).strftime("%Y-%m-%d")
    log_file = error_logger.logs_dir / f"{today}.json"

    assert log_file.exists(), "Log file should be created after queue processing"

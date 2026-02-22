"""
End-to-end tests for error recovery system.

Tests cover:
- T109: Full system tests
- T110: Complete error recovery workflow (error → log → retry → circuit breaker)
- T111: Watchdog restart workflow (crash → detect → restart)
- T112: Queue workflow (service down → queue → service up → process)
"""

import os
import pytest
import shutil
import tempfile
from pathlib import Path
from typing import Any, Dict
from datetime import datetime, UTC

from app.error_recovery import (
    ErrorLogger,
    CircuitBreaker,
    with_retry,
    Watchdog,
    ComponentConfig,
    OperationQueue,
    OperationQueueConfig,
    FileQuarantine,
    ErrorType,
    CircuitBreakerOpenError,
)

@pytest.fixture
def temp_vault():
    """Create temporary vault directory for testing."""
    temp_dir = Path(tempfile.mkdtemp())
    logs_dir = temp_dir / "Logs" / "Errors"
    system_dir = temp_dir / ".system"
    quarantine_dir = system_dir / "quarantine"
    queue_dir = system_dir / "queue"

    logs_dir.mkdir(parents=True)
    system_dir.mkdir(parents=True)
    quarantine_dir.mkdir(parents=True)
    queue_dir.mkdir(parents=True)

    yield temp_dir

    # Cleanup
    shutil.rmtree(temp_dir)


@pytest.fixture
def error_logger(temp_vault):
    """Create ErrorLogger instance."""
    logs_dir = temp_vault / "Logs" / "Errors"
    dashboard_path = temp_vault / ".system" / "error_dashboard.json"
    return ErrorLogger(logs_dir, dashboard_path)


# T110: Test complete error recovery workflow (error → log → retry → circuit breaker)
def test_complete_error_recovery_workflow(error_logger, temp_vault):
    """Test complete error recovery workflow from error to circuit breaker."""
    health_status_path = temp_vault / ".system" / "health_status.json"

    # Setup circuit breaker
    circuit_breaker = CircuitBreaker(
        component="EmailService",
        failure_threshold=3,
        timeout_seconds=60,
        health_status_path=health_status_path,
        error_logger=error_logger
    )

    attempt_count = 0
    max_attempts = 3

    # Define operation with retry
    @with_retry(
        max_attempts=max_attempts,
        initial_wait=0.01,
        exception_types=(Exception,),
        error_logger=error_logger,
        component="EmailService"
    )
    def send_email():
        nonlocal attempt_count
        attempt_count += 1
        raise Exception("Email service unavailable")

    # Execute operation through circuit breaker multiple times to trigger opening
    for i in range(4):
        attempt_count = 0
        try:
            circuit_breaker.call(send_email)
        except Exception:
            pass

    # Verify workflow:
    # 1. Errors were logged
    errors = error_logger.get_errors_by_date(datetime.now(UTC))
    email_errors = [e for e in errors if e.component == "EmailService"]
    assert len(email_errors) > 0

    # 2. Retry attempts occurred
    retry_errors = [e for e in email_errors if "Transient error" in e.message or "attempt" in e.message.lower()]
    assert len(retry_errors) > 0

    # 3. Circuit breaker opened after threshold
    assert circuit_breaker.state.name == "OPEN"

    # 4. Dashboard was updated
    import json
    dashboard_path = temp_vault / ".system" / "error_dashboard.json"
    with open(dashboard_path, 'r') as f:
        dashboard = json.load(f)
    assert "EmailService" in dashboard["error_summary"]["by_component"]

    # 5. Further calls are blocked by circuit breaker
    with pytest.raises(CircuitBreakerOpenError):
        circuit_breaker.call(send_email)


def test_error_recovery_with_eventual_success(error_logger, temp_vault):
    """Test error recovery workflow that eventually succeeds."""
    health_status_path = temp_vault / ".system" / "health_status.json"

    circuit_breaker = CircuitBreaker(
        component="TransientService",
        failure_threshold=5,
        timeout_seconds=60,
        health_status_path=health_status_path,
        error_logger=error_logger
    )

    attempt_count = 0

    @with_retry(
        max_attempts=3,
        initial_wait=0.01,
        exception_types=(Exception,),
        error_logger=error_logger,
        component="TransientService"
    )
    def transient_operation():
        nonlocal attempt_count
        attempt_count += 1
        if attempt_count < 2:
            raise Exception("Transient failure")
        return "Success"

    # Execute operation - should succeed after retry
    result = circuit_breaker.call(transient_operation)

    # Verify success
    assert result == "Success"
    assert attempt_count == 2

    # Verify circuit breaker remained closed
    assert circuit_breaker.state.name == "CLOSED"

    # Verify errors were logged but operation succeeded
    errors = error_logger.get_errors_by_date(datetime.now(UTC))
    transient_errors = [e for e in errors if e.component == "TransientService"]
    assert len(transient_errors) > 0  # Retry attempts logged


# T111: Test watchdog restart workflow (crash → detect → restart)
def test_watchdog_restart_workflow(error_logger, temp_vault):
    """Test watchdog detects crash and restarts component."""

    class MockComponent:
        def __init__(self):
            self.start_count = 0
            self.is_healthy = True
            self.pid = None

        def start(self):
            self.start_count += 1
            self.pid = os.getpid() + self.start_count
            return self.pid

        def health_check(self):
            return self.is_healthy

    mock_component = MockComponent()

    # Setup watchdog
    watchdog = Watchdog(
        vault_path=temp_vault,
        check_interval_seconds=1,
        error_logger=error_logger
    )

    config = ComponentConfig(
        name="TestService",
        start_command=mock_component.start,
        health_check=mock_component.health_check,
        restart_on_failure=True,
        max_restart_attempts=3,
        restart_backoff_seconds=0
    )

    watchdog.register_component(config)

    # 1. Start component
    watchdog._start_component("TestService")
    assert mock_component.start_count == 1

    # 2. Simulate crash (component becomes unhealthy)
    mock_component.is_healthy = False

    # 3. Watchdog detects crash and restarts
    success = watchdog.restart_component("TestService")
    assert success is True
    assert mock_component.start_count == 2

    # 4. Verify errors were logged
    errors = error_logger.get_errors_today()
    restart_errors = [e for e in errors if "restarted" in e.message.lower()]
    assert len(restart_errors) > 0

    # 5. Verify component is running again
    status = watchdog.get_component_status("TestService")
    assert status is not None


def test_watchdog_crash_loop_detection(error_logger, temp_vault):
    """Test watchdog detects crash loop and pauses component."""
    from datetime import timedelta

    class MockComponent:
        def __init__(self):
            self.start_count = 0
            self.pid = None

        def start(self):
            self.start_count += 1
            self.pid = os.getpid() + self.start_count
            return self.pid

    mock_component = MockComponent()

    watchdog = Watchdog(
        vault_path=temp_vault,
        check_interval_seconds=1,
        error_logger=error_logger
    )

    config = ComponentConfig(
        name="CrashLoopService",
        start_command=mock_component.start,
        restart_on_failure=True,
        max_restart_attempts=10,
        restart_backoff_seconds=0,
        crash_detection_window_minutes=5,
        crash_threshold=3
    )

    watchdog.register_component(config)
    watchdog._start_component("CrashLoopService")

    # Simulate crash loop (3 crashes in 5 minutes)
    now = datetime.now(UTC)
    watchdog.crash_history["CrashLoopService"] = [
        (now - timedelta(minutes=4)).isoformat().replace('+00:00', 'Z'),
        (now - timedelta(minutes=2)).isoformat().replace('+00:00', 'Z'),
        (now - timedelta(minutes=1)).isoformat().replace('+00:00', 'Z')
    ]

    # Try to restart - should be paused
    success = watchdog.restart_component("CrashLoopService")
    assert success is False

    # Verify component was paused
    status = watchdog.get_component_status("CrashLoopService")
    assert status is not None
    assert status.status.name == "PAUSED"

    # Verify pause was logged
    errors = error_logger.get_errors_today()
    pause_errors = [e for e in errors if "paused" in e.message.lower()]
    assert len(pause_errors) > 0


# T112: Test queue workflow (service down → queue → service up → process)
def test_queue_workflow_service_recovery(error_logger, temp_vault):
    """Test operation queuing when service is down and processing when recovered."""
    queue_dir = temp_vault / ".system" / "queue"

    config = OperationQueueConfig(
        max_queue_size=100,
        max_retries=3,
        retry_delay_seconds=0
    )

    operation_queue = OperationQueue(
        queue_dir=queue_dir,
        config=config,
        error_logger=error_logger
    )

    # Simulate service being down - queue operations
    operations_data = []
    for i in range(5):
        op_data = {"email": f"user{i}@example.com", "subject": f"Test {i}"}
        operations_data.append(op_data)

        op_id = operation_queue.enqueue(
            operation_type="send_email",
            operation_data=op_data,
            priority=1,
            component="EmailService"
        )
        assert op_id is not None

    # Verify operations are queued
    assert operation_queue.get_queue_size() == 5

    # Simulate service recovery - process queue
    processed_operations = []

    def email_handler(data: Dict[str, Any]) -> bool:
        processed_operations.append(data)
        return True  # Success

    handlers = {"send_email": email_handler}
    stats = operation_queue.process_queue(handlers)

    # Verify all operations were processed
    assert stats["processed"] == 5
    assert stats["succeeded"] == 5
    assert stats["failed"] == 0
    assert len(processed_operations) == 5

    # Verify queue is empty
    assert operation_queue.get_queue_size() == 0

    # Verify operations were logged
    errors = error_logger.get_errors_today()
    queue_errors = [e for e in errors if "queued" in e.message.lower() or "completed" in e.message.lower()]
    assert len(queue_errors) > 0


def test_queue_workflow_with_priority(error_logger, temp_vault):
    """Test that queued operations are processed by priority."""
    queue_dir = temp_vault / ".system" / "queue"

    operation_queue = OperationQueue(
        queue_dir=queue_dir,
        config=OperationQueueConfig(max_retries=3, retry_delay_seconds=0),
        error_logger=error_logger
    )

    # Queue operations with different priorities
    operation_queue.enqueue("op", {"priority": 3}, priority=3, component="Test")
    operation_queue.enqueue("op", {"priority": 1}, priority=1, component="Test")
    operation_queue.enqueue("op", {"priority": 2}, priority=2, component="Test")

    # Process queue
    processed_order = []

    def handler(data: Dict[str, Any]) -> bool:
        processed_order.append(data["priority"])
        return True

    handlers = {"op": handler}
    operation_queue.process_queue(handlers)

    # Verify processing order (1, 2, 3)
    assert processed_order == [1, 2, 3]


def test_full_system_integration(error_logger, temp_vault):
    """Test full system integration with all components."""
    # Setup all components
    health_status_path = temp_vault / ".system" / "health_status.json"
    quarantine_dir = temp_vault / ".system" / "quarantine"
    queue_dir = temp_vault / ".system" / "queue"

    circuit_breaker = CircuitBreaker(
        component="IntegratedService",
        failure_threshold=3,
        timeout_seconds=60,
        health_status_path=health_status_path,
        error_logger=error_logger
    )

    file_quarantine = FileQuarantine(
        quarantine_dir=quarantine_dir,
        error_logger=error_logger
    )

    operation_queue = OperationQueue(
        queue_dir=queue_dir,
        config=OperationQueueConfig(max_retries=3, retry_delay_seconds=0),
        error_logger=error_logger
    )

    # Scenario: Process file, encounter error, quarantine, queue operation

    # 1. Create corrupted file
    test_file = temp_vault / "corrupted.txt"
    test_file.write_text("Corrupted data")

    # 2. Quarantine corrupted file
    quarantine_id = file_quarantine.quarantine_file(
        file_path=test_file,
        reason="File validation failed",
        error_type=ErrorType.DATA,
        component="FileProcessor"
    )

    # 3. Queue operation to notify about quarantine
    op_id = operation_queue.enqueue(
        operation_type="notify_admin",
        operation_data={"quarantine_id": quarantine_id, "reason": "File validation failed"},
        priority=1,
        component="FileProcessor"
    )

    # 4. Log error through circuit breaker
    def log_quarantine_error():
        error_logger.log_error(
            component="FileProcessor",
            error_type=ErrorType.DATA,
            message="File quarantined due to validation failure",
            context={"quarantine_id": quarantine_id}
        )

    circuit_breaker.call(log_quarantine_error)

    # Verify all components worked together

    # Verify file was quarantined
    quarantined_file = file_quarantine.get_quarantined_file(quarantine_id)
    assert quarantined_file is not None

    # Verify operation was queued
    operation = operation_queue.get_operation(op_id)
    assert operation is not None

    # Verify error was logged
    errors = error_logger.get_errors_today()
    quarantine_errors = [e for e in errors if "quarantined" in e.message.lower()]
    assert len(quarantine_errors) > 0

    # Verify dashboard was updated
    import json
    dashboard_path = temp_vault / ".system" / "error_dashboard.json"
    with open(dashboard_path, 'r') as f:
        dashboard = json.load(f)
    assert "FileProcessor" in dashboard["error_summary"]["by_component"]

    # Process queued operation
    notifications_sent = []

    def notify_handler(data: Dict[str, Any]) -> bool:
        notifications_sent.append(data)
        return True

    handlers = {"notify_admin": notify_handler}
    stats = operation_queue.process_queue(handlers)

    # Verify notification was sent
    assert stats["succeeded"] == 1
    assert len(notifications_sent) == 1
    assert notifications_sent[0]["quarantine_id"] == quarantine_id


def test_system_resilience_under_load(error_logger, temp_vault):
    """Test system resilience under high error load."""
    # Generate many errors rapidly
    for i in range(50):
        error_logger.log_error(
            component=f"Component{i % 5}",
            error_type=ErrorType.TRANSIENT,
            message=f"Error {i}"
        )

    # Verify all errors were logged
    errors = error_logger.get_errors_today()
    assert len(errors) >= 50

    # Verify dashboard is still functional
    import json
    dashboard_path = temp_vault / ".system" / "error_dashboard.json"
    with open(dashboard_path, 'r') as f:
        dashboard = json.load(f)

    assert "error_summary" in dashboard
    assert len(dashboard["error_summary"]["by_component"]) >= 5

"""
Integration tests for error propagation across components.

Tests cover:
- T108: Error flow across components
- Error propagation from file processor to error logger
- Circuit breaker integration with error logging
- Quarantine integration with error logging
"""

import pytest
from pathlib import Path
from datetime import datetime, UTC
import tempfile
import shutil

from app.error_recovery.error_logger import ErrorLogger
from app.error_recovery.circuit_breaker import CircuitBreaker
from app.error_recovery.file_quarantine import FileQuarantine
from app.error_recovery.retry import with_retry
from app.error_recovery.entities import ErrorType
from app.error_recovery.exceptions import CircuitBreakerOpenError


@pytest.fixture
def temp_vault():
    """Create temporary vault directory for testing."""
    temp_dir = Path(tempfile.mkdtemp())
    logs_dir = temp_dir / "Logs" / "Errors"
    system_dir = temp_dir / ".system"
    quarantine_dir = system_dir / "quarantine"

    logs_dir.mkdir(parents=True)
    system_dir.mkdir(parents=True)
    quarantine_dir.mkdir(parents=True)

    yield temp_dir

    # Cleanup
    shutil.rmtree(temp_dir)


@pytest.fixture
def error_logger(temp_vault):
    """Create ErrorLogger instance."""
    logs_dir = temp_vault / "Logs" / "Errors"
    dashboard_path = temp_vault / ".system" / "error_dashboard.json"
    return ErrorLogger(logs_dir, dashboard_path)


def test_error_propagation_from_retry_to_logger(error_logger):
    """Test that errors from retry mechanism are logged."""
    attempt_count = 0

    @with_retry(max_attempts=3, initial_wait=0.01, error_logger=error_logger, component="TestComponent")
    def failing_operation():
        nonlocal attempt_count
        attempt_count += 1
        raise Exception("Test failure")

    # Execute failing operation
    with pytest.raises(Exception):
        failing_operation()

    # Verify retries occurred
    assert attempt_count == 3

    # Verify errors were logged
    errors = error_logger.get_errors_by_date(datetime.now(UTC))
    retry_errors = [e for e in errors if "Retry attempt" in e.message]
    assert len(retry_errors) >= 2  # At least 2 retry attempts logged


def test_error_propagation_from_circuit_breaker_to_logger(error_logger, temp_vault):
    """Test that circuit breaker errors are logged."""
    health_status_path = temp_vault / ".system" / "health_status.json"

    circuit_breaker = CircuitBreaker(
        component="TestService",
        failure_threshold=2,
        timeout_seconds=60,
        health_status_path=health_status_path,
        error_logger=error_logger
    )

    def failing_operation():
        raise Exception("Test failure")

    # Trigger failures to open circuit breaker
    for _ in range(3):
        try:
            circuit_breaker.call(failing_operation)
        except:
            pass

    # Verify circuit breaker opened
    assert circuit_breaker.state.name == "OPEN"

    # Verify errors were logged
    errors = error_logger.get_errors_by_date(datetime.now(UTC))
    cb_errors = [e for e in errors if e.component == "TestService"]
    assert len(cb_errors) >= 2  # At least failure threshold errors


def test_error_propagation_from_quarantine_to_logger(error_logger, temp_vault):
    """Test that quarantine operations are logged."""
    quarantine_dir = temp_vault / ".system" / "quarantine"
    file_quarantine = FileQuarantine(
        quarantine_dir=quarantine_dir,
        error_logger=error_logger
    )

    # Create test file
    test_file = temp_vault / "test.txt"
    test_file.write_text("Test content")

    # Quarantine file
    quarantine_id = file_quarantine.quarantine_file(
        file_path=test_file,
        reason="Test quarantine",
        error_type=ErrorType.DATA,
        component="FileProcessor"
    )

    # Verify quarantine was logged
    errors = error_logger.get_errors_by_date(datetime.now(UTC))
    quarantine_errors = [e for e in errors if "quarantined" in e.message.lower()]
    assert len(quarantine_errors) >= 1


def test_cross_component_error_tracking(error_logger, temp_vault):
    """Test that errors from multiple components are tracked separately."""
    # Log errors from different components
    error_logger.log_error(
        component="EmailService",
        error_type=ErrorType.TRANSIENT,
        message="Email send failed"
    )

    error_logger.log_error(
        component="FileProcessor",
        error_type=ErrorType.DATA,
        message="File parsing failed"
    )

    error_logger.log_error(
        component="LinkedInService",
        error_type=ErrorType.AUTHENTICATION,
        message="Authentication failed"
    )

    # Get errors
    errors = error_logger.get_errors_by_date(datetime.now(UTC))

    # Verify errors from each component
    email_errors = [e for e in errors if e.component == "EmailService"]
    file_errors = [e for e in errors if e.component == "FileProcessor"]
    linkedin_errors = [e for e in errors if e.component == "LinkedInService"]

    assert len(email_errors) >= 1
    assert len(file_errors) >= 1
    assert len(linkedin_errors) >= 1

    # Verify error types
    assert email_errors[0].error_type == ErrorType.TRANSIENT
    assert file_errors[0].error_type == ErrorType.DATA
    assert linkedin_errors[0].error_type == ErrorType.AUTHENTICATION


def test_error_context_preservation(error_logger):
    """Test that error context is preserved across components."""
    context = {
        "file_path": "/path/to/file.txt",
        "user_id": "user123",
        "operation": "process_file"
    }

    # Log error with context
    error_logger.log_error(
        component="FileProcessor",
        error_type=ErrorType.DATA,
        message="File processing failed",
        context=context
    )

    # Retrieve error
    errors = error_logger.get_errors_by_date(datetime.now(UTC))
    assert len(errors) >= 1

    # Verify context was preserved
    logged_error = errors[-1]
    assert logged_error.context["file_path"] == "/path/to/file.txt"
    assert logged_error.context["user_id"] == "user123"
    assert logged_error.context["operation"] == "process_file"


def test_error_chain_with_retry_and_circuit_breaker(error_logger, temp_vault):
    """Test error propagation through retry and circuit breaker."""
    health_status_path = temp_vault / ".system" / "health_status.json"

    circuit_breaker = CircuitBreaker(
        component="ChainedService",
        failure_threshold=2,
        timeout_seconds=60,
        health_status_path=health_status_path,
        error_logger=error_logger
    )

    @with_retry(max_attempts=2, initial_wait=0.01, error_logger=error_logger, component="ChainedService")
    def failing_operation():
        raise Exception("Test failure")

    # Execute through circuit breaker with retry
    for _ in range(3):
        try:
            circuit_breaker.call(failing_operation)
        except:
            pass

    # Verify both retry and circuit breaker errors were logged
    errors = error_logger.get_errors_by_date(datetime.now(UTC))
    chained_errors = [e for e in errors if e.component == "ChainedService"]

    # Should have errors from both retry attempts and circuit breaker
    assert len(chained_errors) >= 4  # Multiple retry attempts + circuit breaker errors


def test_error_aggregation_in_dashboard(error_logger, temp_vault):
    """Test that errors are properly aggregated in dashboard."""
    # Generate multiple errors
    for i in range(5):
        error_logger.log_error(
            component="TestComponent",
            error_type=ErrorType.TRANSIENT,
            message=f"Error {i}"
        )

    # Read dashboard
    dashboard_path = temp_vault / ".system" / "error_dashboard.json"
    import json
    with open(dashboard_path, 'r') as f:
        dashboard = json.load(f)

    # Verify aggregation
    assert "error_summary" in dashboard
    assert "TestComponent" in dashboard["error_summary"]["by_component"]
    assert dashboard["error_summary"]["by_component"]["TestComponent"] >= 5


def test_error_recovery_state_persistence(error_logger, temp_vault):
    """Test that error recovery state persists across restarts."""
    # Log errors
    error_logger.log_error(
        component="PersistentComponent",
        error_type=ErrorType.DATA,
        message="Test error"
    )

    # Create new error logger instance (simulating restart)
    logs_dir = temp_vault / "Logs" / "Errors"
    dashboard_path = temp_vault / ".system" / "error_dashboard.json"
    new_error_logger = ErrorLogger(logs_dir, dashboard_path)

    # Verify errors are still accessible
    errors = new_error_logger.get_errors_by_date(datetime.now(UTC))
    persistent_errors = [e for e in errors if e.component == "PersistentComponent"]
    assert len(persistent_errors) >= 1

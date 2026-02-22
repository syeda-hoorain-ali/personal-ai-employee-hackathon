"""
Integration test for dashboard updates.

Tests cover:
- T036: Dashboard updates with error statistics and component health
"""

import pytest
from pathlib import Path
from datetime import datetime, UTC
import tempfile
import shutil
import json

from app.error_recovery.error_logger import ErrorLogger
from app.error_recovery.circuit_breaker import CircuitBreaker
from app.error_recovery.file_quarantine import FileQuarantine
from app.error_recovery.entities import ErrorType, ResolutionStatus


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
def dashboard_path(temp_vault):
    """Get dashboard path."""
    return temp_vault / ".system" / "error_dashboard.json"


@pytest.fixture
def error_logger(temp_vault, dashboard_path):
    """Create ErrorLogger instance."""
    logs_dir = temp_vault / "Logs" / "Errors"
    return ErrorLogger(logs_dir, dashboard_path)


def test_dashboard_updates_with_errors(error_logger, dashboard_path):
    """Test that dashboard is updated when errors are logged."""
    # Log some errors
    error_logger.log_error(
        component="TestComponent",
        error_type=ErrorType.DATA,
        message="Test data error"
    )

    error_logger.log_error(
        component="TestComponent",
        error_type=ErrorType.TRANSIENT,
        message="Test transient error"
    )

    # Read dashboard
    with open(dashboard_path, 'r') as f:
        dashboard = json.load(f)

    # Verify dashboard structure
    assert "errors_by_component" in dashboard
    assert "TestComponent" in dashboard["errors_by_component"]
    assert "by_type" in dashboard["errors_by_component"]
    assert "last_updated" in dashboard

    # Verify error counts
    assert dashboard["errors_by_component"]["TestComponent"] >= 2
    assert dashboard["errors_by_type"]["DATA"] >= 1
    assert dashboard["errors_by_type"]["TRANSIENT"] >= 1


def test_dashboard_updates_with_circuit_breaker(error_logger, dashboard_path, temp_vault):
    """Test that dashboard is updated when circuit breaker opens."""
    health_status_path = temp_vault / ".system" / "health_status.json"

    circuit_breaker = CircuitBreaker(
        component="TestService",
        failure_threshold=2,
        timeout_seconds=60,
        health_status_path=health_status_path,
        error_logger=error_logger
    )

    # Simulate failures to open circuit breaker
    def failing_operation():
        raise Exception("Test failure")

    for _ in range(3):
        try:
            circuit_breaker.call(failing_operation)
        except:
            pass

    # Update dashboard with paused component
    error_logger.update_paused_component(
        component="TestService",
        is_paused=True,
        reason="Circuit breaker opened",
        failure_count=3
    )

    # Read dashboard
    with open(dashboard_path, 'r') as f:
        dashboard = json.load(f)

    # Verify paused components section
    assert "paused_components" in dashboard
    assert "TestService" in dashboard["paused_components"]
    assert dashboard["paused_components"]["TestService"]["reason"] == "Circuit breaker opened"
    assert dashboard["paused_components"]["TestService"]["failure_count"] == 3


def test_dashboard_updates_with_quarantined_files(error_logger, dashboard_path, temp_vault):
    """Test that dashboard is updated with quarantined files statistics."""
    quarantine_dir = temp_vault / ".system" / "quarantine"
    file_quarantine = FileQuarantine(
        quarantine_dir=quarantine_dir,
        error_logger=error_logger
    )

    # Create test files and quarantine them
    test_files_dir = temp_vault / "test_files"
    test_files_dir.mkdir()

    for i in range(3):
        test_file = test_files_dir / f"test_{i}.txt"
        test_file.write_text(f"Test content {i}")

        file_quarantine.quarantine_file(
            file_path=test_file,
            reason=f"Test quarantine {i}",
            error_type=ErrorType.DATA,
            component="FileProcessor"
        )

    # Update dashboard with quarantine stats
    stats = file_quarantine.get_quarantine_stats()
    error_logger.update_quarantined_files(stats)

    # Read dashboard
    with open(dashboard_path, 'r') as f:
        dashboard = json.load(f)

    # Verify quarantined files section
    assert "quarantined_files" in dashboard
    assert dashboard["quarantined_files"]["total_files"] == 3
    assert "FileProcessor" in dashboard["quarantined_files"]["by_component"]
    assert dashboard["quarantined_files"]["by_component"]["FileProcessor"] == 3
    assert "DATA" in dashboard["quarantined_files"]["by_error_type"]
    assert dashboard["quarantined_files"]["total_size_mb"] > 0


def test_dashboard_comprehensive_update(error_logger, dashboard_path, temp_vault):
    """Test comprehensive dashboard update with multiple components."""
    # Log errors from multiple components
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

    # Update paused components
    error_logger.update_paused_component(
        component="EmailService",
        is_paused=True,
        reason="Too many failures",
        failure_count=5
    )

    # Setup and update quarantine stats
    quarantine_dir = temp_vault / ".system" / "quarantine"
    file_quarantine = FileQuarantine(
        quarantine_dir=quarantine_dir,
        error_logger=error_logger
    )

    test_file = temp_vault / "corrupted.txt"
    test_file.write_text("Corrupted data")
    file_quarantine.quarantine_file(
        file_path=test_file,
        reason="Corrupted file",
        error_type=ErrorType.DATA,
        component="FileProcessor"
    )

    stats = file_quarantine.get_quarantine_stats()
    error_logger.update_quarantined_files(stats)

    # Read dashboard
    with open(dashboard_path, 'r') as f:
        dashboard = json.load(f)

    # Verify all sections are present and populated
    assert "errors_by_component" in dashboard
    assert "paused_components" in dashboard
    assert "quarantined_files" in dashboard
    assert "last_updated" in dashboard

    # Verify error summary
    assert len(dashboard["errors_by_component"]) >= 3
    assert "EmailService" in dashboard["errors_by_component"]
    assert "FileProcessor" in dashboard["errors_by_component"]
    assert "LinkedInService" in dashboard["errors_by_component"]

    # Verify error types
    assert "TRANSIENT" in dashboard["errors_by_type"]
    assert "DATA" in dashboard["errors_by_type"]
    assert "AUTHENTICATION" in dashboard["errors_by_type"]

    # Verify paused components
    assert "EmailService" in dashboard["paused_components"]

    # Verify quarantined files
    assert dashboard["quarantined_files"]["total_files"] >= 1


def test_dashboard_timestamp_updates(error_logger, dashboard_path):
    """Test that dashboard timestamp is updated on each change."""
    # Log first error
    error_logger.log_error(
        component="TestComponent",
        error_type=ErrorType.DATA,
        message="First error"
    )

    # Read first timestamp
    with open(dashboard_path, 'r') as f:
        dashboard1 = json.load(f)
    timestamp1 = dashboard1["last_updated"]

    # Small delay to ensure different timestamp
    import time
    time.sleep(0.1)

    # Log second error
    error_logger.log_error(
        component="TestComponent",
        error_type=ErrorType.DATA,
        message="Second error"
    )

    # Read second timestamp
    with open(dashboard_path, 'r') as f:
        dashboard2 = json.load(f)
    timestamp2 = dashboard2["last_updated"]

    # Verify timestamp was updated
    assert timestamp2 > timestamp1


def test_dashboard_paused_component_removal(error_logger, dashboard_path):
    """Test that paused components can be removed from dashboard."""
    # Add paused component
    error_logger.update_paused_component(
        component="TestService",
        is_paused=True,
        reason="Test pause"
    )

    # Verify component is paused
    with open(dashboard_path, 'r') as f:
        dashboard = json.load(f)
    assert "TestService" in dashboard["paused_components"]

    # Remove paused component
    error_logger.update_paused_component(
        component="TestService",
        is_paused=False
    )

    # Verify component is removed
    with open(dashboard_path, 'r') as f:
        dashboard = json.load(f)
    assert "TestService" not in dashboard["paused_components"]

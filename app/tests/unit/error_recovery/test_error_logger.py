"""
Unit tests for ErrorLogger class.

Tests error logging functionality including:
- Daily log file creation
- Sensitive data sanitization
- Dashboard updates
- Error retrieval and resolution
"""

import pytest
import json
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, patch, mock_open
import tempfile
import shutil

from app.error_recovery.error_logger import ErrorLogger
from app.error_recovery.entities import ErrorType, ResolutionStatus, ErrorLogEntry


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    # Cleanup
    shutil.rmtree(temp_path, ignore_errors=True)


@pytest.fixture
def error_logger(temp_dir):
    """Create an ErrorLogger instance with temporary directories."""
    logs_dir = temp_dir / "logs"
    dashboard_path = temp_dir / "dashboard.json"
    return ErrorLogger(logs_dir, dashboard_path)


class TestErrorLoggerInitialization:
    """Test ErrorLogger initialization."""

    def test_init_creates_logs_directory(self, temp_dir):
        """Test that initialization creates the logs directory."""
        logs_dir = temp_dir / "logs"
        dashboard_path = temp_dir / "dashboard.json"

        logger = ErrorLogger(logs_dir, dashboard_path)

        assert logs_dir.exists()
        assert logs_dir.is_dir()

    def test_init_creates_dashboard_parent_directory(self, temp_dir):
        """Test that initialization creates the dashboard parent directory."""
        logs_dir = temp_dir / "logs"
        dashboard_path = temp_dir / "system" / "dashboard.json"

        logger = ErrorLogger(logs_dir, dashboard_path)

        assert dashboard_path.parent.exists()
        assert dashboard_path.parent.is_dir()

    def test_init_without_dashboard(self, temp_dir):
        """Test initialization without dashboard path."""
        logs_dir = temp_dir / "logs"

        logger = ErrorLogger(logs_dir, dashboard_path=None)

        assert logger.dashboard_path is None


class TestLogError:
    """Test error logging functionality."""

    def test_log_error_creates_daily_file(self, error_logger, temp_dir):
        """Test that log_error creates a daily log file."""
        error_id = error_logger.log_error(
            component="TestComponent",
            error_type=ErrorType.TRANSIENT,
            message="Test error message"
        )

        # Check that error ID is returned
        assert error_id is not None
        assert len(error_id) == 36  # UUID format

        # Check that daily log file was created
        date_str = datetime.utcnow().strftime("%Y-%m-%d")
        log_file = temp_dir / "logs" / f"{date_str}.json"
        assert log_file.exists()

    def test_log_error_writes_correct_structure(self, error_logger, temp_dir):
        """Test that log_error writes correct JSON structure."""
        error_id = error_logger.log_error(
            component="TestComponent",
            error_type=ErrorType.AUTHENTICATION,
            message="Auth failed",
            error_code="401",
            context={"user": "test_user"}
        )

        # Read the log file
        date_str = datetime.utcnow().strftime("%Y-%m-%d")
        log_file = temp_dir / "logs" / f"{date_str}.json"

        with open(log_file, 'r') as f:
            data = json.load(f)

        assert len(data) == 1
        entry = data[0]

        assert entry["id"] == error_id
        assert entry["component"] == "TestComponent"
        assert entry["error_type"] == "AUTHENTICATION"
        assert entry["message"] == "Auth failed"
        assert entry["error_code"] == "401"
        assert entry["context"]["user"] == "test_user"
        assert entry["resolution_status"] == "UNRESOLVED"

    def test_log_error_sanitizes_message(self, error_logger, temp_dir):
        """Test that log_error sanitizes sensitive data in message."""
        error_logger.log_error(
            component="TestComponent",
            error_type=ErrorType.TRANSIENT,
            message="Failed to connect with password=secret123 and token=abc456"
        )

        # Read the log file
        date_str = datetime.utcnow().strftime("%Y-%m-%d")
        log_file = temp_dir / "logs" / f"{date_str}.json"

        with open(log_file, 'r') as f:
            data = json.load(f)

        entry = data[0]
        assert "secret123" not in entry["message"]
        assert "abc456" not in entry["message"]
        assert "password=***" in entry["message"]
        assert "token=***" in entry["message"]

    def test_log_error_sanitizes_context(self, error_logger, temp_dir):
        """Test that log_error sanitizes sensitive data in context."""
        error_logger.log_error(
            component="TestComponent",
            error_type=ErrorType.TRANSIENT,
            message="Test error",
            context={
                "password": "secret123",
                "api_key": "key456",
                "user": "john@example.com"
            }
        )

        # Read the log file
        date_str = datetime.utcnow().strftime("%Y-%m-%d")
        log_file = temp_dir / "logs" / f"{date_str}.json"

        with open(log_file, 'r') as f:
            data = json.load(f)

        entry = data[0]
        assert entry["context"]["password"] == "***"
        assert entry["context"]["api_key"] == "***"
        assert "john@example.com" not in str(entry["context"])

    def test_log_error_with_exception(self, error_logger, temp_dir):
        """Test that log_error captures stack trace from exception."""
        try:
            raise ValueError("Test exception")
        except ValueError as e:
            error_logger.log_error(
                component="TestComponent",
                error_type=ErrorType.LOGIC,
                message="Exception occurred",
                error=e
            )

        # Read the log file
        date_str = datetime.utcnow().strftime("%Y-%m-%d")
        log_file = temp_dir / "logs" / f"{date_str}.json"

        with open(log_file, 'r') as f:
            data = json.load(f)

        entry = data[0]
        assert entry["stack_trace"] is not None
        assert "ValueError" in entry["stack_trace"]
        assert "Test exception" in entry["stack_trace"]

    def test_log_error_with_retry_count(self, error_logger, temp_dir):
        """Test that log_error records retry count."""
        error_logger.log_error(
            component="TestComponent",
            error_type=ErrorType.TRANSIENT,
            message="Retry attempt",
            retry_count=3
        )

        # Read the log file
        date_str = datetime.utcnow().strftime("%Y-%m-%d")
        log_file = temp_dir / "logs" / f"{date_str}.json"

        with open(log_file, 'r') as f:
            data = json.load(f)

        entry = data[0]
        assert entry["retry_count"] == 3

    def test_log_error_appends_to_existing_file(self, error_logger, temp_dir):
        """Test that multiple errors are appended to the same daily file."""
        error_logger.log_error(
            component="Component1",
            error_type=ErrorType.TRANSIENT,
            message="First error"
        )

        error_logger.log_error(
            component="Component2",
            error_type=ErrorType.DATA,
            message="Second error"
        )

        # Read the log file
        date_str = datetime.utcnow().strftime("%Y-%m-%d")
        log_file = temp_dir / "logs" / f"{date_str}.json"

        with open(log_file, 'r') as f:
            data = json.load(f)

        assert len(data) == 2
        assert data[0]["message"] == "First error"
        assert data[1]["message"] == "Second error"


class TestDashboardUpdate:
    """Test dashboard update functionality."""

    def test_dashboard_created_on_first_error(self, error_logger, temp_dir):
        """Test that dashboard is created on first error."""
        error_logger.log_error(
            component="TestComponent",
            error_type=ErrorType.TRANSIENT,
            message="Test error"
        )

        dashboard_path = temp_dir / "dashboard.json"
        assert dashboard_path.exists()

    def test_dashboard_structure(self, error_logger, temp_dir):
        """Test that dashboard has correct structure."""
        error_logger.log_error(
            component="TestComponent",
            error_type=ErrorType.AUTHENTICATION,
            message="Test error"
        )

        dashboard_path = temp_dir / "dashboard.json"
        with open(dashboard_path, 'r') as f:
            dashboard = json.load(f)

        assert "last_updated" in dashboard
        assert "total_errors" in dashboard
        assert "errors_by_type" in dashboard
        assert "errors_by_component" in dashboard
        assert "recent_errors" in dashboard

    def test_dashboard_counts_errors(self, error_logger, temp_dir):
        """Test that dashboard correctly counts errors."""
        error_logger.log_error(
            component="Component1",
            error_type=ErrorType.TRANSIENT,
            message="Error 1"
        )

        error_logger.log_error(
            component="Component2",
            error_type=ErrorType.TRANSIENT,
            message="Error 2"
        )

        dashboard_path = temp_dir / "dashboard.json"
        with open(dashboard_path, 'r') as f:
            dashboard = json.load(f)

        assert dashboard["total_errors"] == 2

    def test_dashboard_groups_by_type(self, error_logger, temp_dir):
        """Test that dashboard groups errors by type."""
        error_logger.log_error(
            component="Component1",
            error_type=ErrorType.TRANSIENT,
            message="Error 1"
        )

        error_logger.log_error(
            component="Component2",
            error_type=ErrorType.TRANSIENT,
            message="Error 2"
        )

        error_logger.log_error(
            component="Component3",
            error_type=ErrorType.AUTHENTICATION,
            message="Error 3"
        )

        dashboard_path = temp_dir / "dashboard.json"
        with open(dashboard_path, 'r') as f:
            dashboard = json.load(f)

        assert dashboard["errors_by_type"]["TRANSIENT"] == 2
        assert dashboard["errors_by_type"]["AUTHENTICATION"] == 1

    def test_dashboard_groups_by_component(self, error_logger, temp_dir):
        """Test that dashboard groups errors by component."""
        error_logger.log_error(
            component="Component1",
            error_type=ErrorType.TRANSIENT,
            message="Error 1"
        )

        error_logger.log_error(
            component="Component1",
            error_type=ErrorType.DATA,
            message="Error 2"
        )

        error_logger.log_error(
            component="Component2",
            error_type=ErrorType.TRANSIENT,
            message="Error 3"
        )

        dashboard_path = temp_dir / "dashboard.json"
        with open(dashboard_path, 'r') as f:
            dashboard = json.load(f)

        # Verify nested structure with by_type
        assert "Component1" in dashboard["errors_by_component"]
        assert "by_type" in dashboard["errors_by_component"]["Component1"]
        assert dashboard["errors_by_component"]["Component1"]["by_type"]["TRANSIENT"] == 1
        assert dashboard["errors_by_component"]["Component1"]["by_type"]["DATA"] == 1

        assert "Component2" in dashboard["errors_by_component"]
        assert "by_type" in dashboard["errors_by_component"]["Component2"]
        assert dashboard["errors_by_component"]["Component2"]["by_type"]["TRANSIENT"] == 1

    def test_dashboard_recent_errors_limit(self, error_logger, temp_dir):
        """Test that dashboard keeps only last 50 recent errors."""
        # Log 60 errors
        for i in range(60):
            error_logger.log_error(
                component=f"Component{i}",
                error_type=ErrorType.TRANSIENT,
                message=f"Error {i}"
            )

        dashboard_path = temp_dir / "dashboard.json"
        with open(dashboard_path, 'r') as f:
            dashboard = json.load(f)

        assert len(dashboard["recent_errors"]) == 50
        # Most recent error should be first
        assert dashboard["recent_errors"][0]["message"] == "Error 59"


class TestErrorRetrieval:
    """Test error retrieval functionality."""

    def test_get_errors_by_date(self, error_logger, temp_dir):
        """Test retrieving errors by date."""
        # Log some errors
        error_logger.log_error(
            component="Component1",
            error_type=ErrorType.TRANSIENT,
            message="Error 1"
        )

        error_logger.log_error(
            component="Component2",
            error_type=ErrorType.DATA,
            message="Error 2"
        )

        # Retrieve errors
        today = datetime.utcnow()
        errors = error_logger.get_errors_by_date(today)

        assert len(errors) == 2
        assert all(isinstance(e, ErrorLogEntry) for e in errors)
        assert errors[0].message == "Error 1"
        assert errors[1].message == "Error 2"

    def test_get_errors_by_date_no_file(self, error_logger, temp_dir):
        """Test retrieving errors when no log file exists."""
        from datetime import timedelta
        yesterday = datetime.utcnow() - timedelta(days=1)

        errors = error_logger.get_errors_by_date(yesterday)

        assert errors == []

    def test_get_error_by_id(self, error_logger, temp_dir):
        """Test retrieving a specific error by ID."""
        error_id = error_logger.log_error(
            component="TestComponent",
            error_type=ErrorType.AUTHENTICATION,
            message="Test error"
        )

        # Retrieve the error
        error = error_logger.get_error_by_id(error_id)

        assert error is not None
        assert error.id == error_id
        assert error.message == "Test error"

    def test_get_error_by_id_not_found(self, error_logger, temp_dir):
        """Test retrieving a non-existent error."""
        error = error_logger.get_error_by_id("non-existent-id")

        assert error is None


class TestErrorResolution:
    """Test error resolution functionality."""

    def test_mark_error_resolved(self, error_logger, temp_dir):
        """Test marking an error as resolved."""
        error_id = error_logger.log_error(
            component="TestComponent",
            error_type=ErrorType.TRANSIENT,
            message="Test error"
        )

        # Mark as resolved
        success = error_logger.mark_error_resolved(
            error_id,
            ResolutionStatus.AUTO_RECOVERED
        )

        assert success is True

        # Verify resolution status
        error = error_logger.get_error_by_id(error_id)
        assert error.resolution_status == ResolutionStatus.AUTO_RECOVERED
        assert error.resolved_at is not None

    def test_mark_error_resolved_not_found(self, error_logger, temp_dir):
        """Test marking a non-existent error as resolved."""
        success = error_logger.mark_error_resolved(
            "non-existent-id",
            ResolutionStatus.AUTO_RECOVERED
        )

        assert success is False

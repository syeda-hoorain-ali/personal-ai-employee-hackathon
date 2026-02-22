"""
Unit tests for FileProcessor integration with ErrorLogger.

Tests error logging integration in file processing workflows.
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import tempfile
import shutil

from app.file_processor import FileProcessor
from app.error_recovery.entities import ErrorType


@pytest.fixture
def temp_vault():
    """Create a temporary vault directory for testing."""
    temp_path = Path(tempfile.mkdtemp())

    # Create required subdirectories
    (temp_path / "Logs" / "Errors").mkdir(parents=True)
    (temp_path / ".system").mkdir(parents=True)
    (temp_path / "Needs_Action").mkdir(parents=True)

    # Create a test Company_Handbook.md
    handbook_content = """# Company Handbook

## Communication Guidelines
Always be professional and courteous in communications.

## Financial Guidelines
Require approval for payments over $100.

## Task Management
Process tasks in priority order.
"""
    (temp_path / "Company_Handbook.md").write_text(handbook_content, encoding='utf-8')

    yield temp_path

    # Cleanup
    shutil.rmtree(temp_path, ignore_errors=True)


@pytest.fixture
def file_processor(temp_vault):
    """Create a FileProcessor instance with temporary vault."""
    return FileProcessor(str(temp_vault))


class TestFileProcessorErrorLogging:
    """Test error logging in FileProcessor."""

    def test_error_logger_initialized(self, file_processor):
        """Test that ErrorLogger is initialized in FileProcessor."""
        assert hasattr(file_processor, 'error_logger')
        assert file_processor.error_logger is not None

    def test_error_logged_on_missing_handbook(self, temp_vault):
        """Test that error is logged when handbook is missing."""
        # Remove handbook
        (temp_vault / "Company_Handbook.md").unlink()

        # Create processor (should log error)
        processor = FileProcessor(str(temp_vault))

        # Check that error was logged
        from datetime import datetime
        date_str = datetime.utcnow().strftime("%Y-%m-%d")
        log_file = temp_vault / "Logs" / "Errors" / f"{date_str}.json"

        assert log_file.exists()

        import json
        with open(log_file, 'r') as f:
            errors = json.load(f)

        assert len(errors) >= 1
        error = errors[0]
        assert error["component"] == "FileProcessor"
        assert error["error_type"] == "DATA"
        assert "Company_Handbook.md" in error["message"]

    def test_error_logged_on_file_read_failure(self, file_processor, temp_vault):
        """Test that error is logged when file cannot be read."""
        # Try to process non-existent file
        success, message = file_processor.process_file("Needs_Action/nonexistent.md")

        assert success is False

        # Check that error was logged
        from datetime import datetime
        date_str = datetime.utcnow().strftime("%Y-%m-%d")
        log_file = temp_vault / "Logs" / "Errors" / f"{date_str}.json"

        assert log_file.exists()

        import json
        with open(log_file, 'r') as f:
            errors = json.load(f)

        # Find the file read error
        file_read_errors = [e for e in errors if "Could not read file" in e["message"]]
        assert len(file_read_errors) >= 1

        error = file_read_errors[0]
        assert error["component"] == "FileProcessor"
        assert error["error_type"] == "DATA"
        assert "nonexistent.md" in error["context"]["file_path"]

    @patch('subprocess.run')
    def test_error_logged_on_claude_timeout(self, mock_run, file_processor, temp_vault):
        """Test that error is logged when Claude Code times out."""
        import subprocess

        # Create a test file
        test_file = temp_vault / "Needs_Action" / "test.md"
        test_file.write_text("Test content", encoding='utf-8')

        # Mock subprocess to raise TimeoutExpired
        mock_run.side_effect = subprocess.TimeoutExpired(cmd="ccr", timeout=600)

        # Try to process file
        success, message = file_processor.process_file("Needs_Action/test.md")

        assert success is False

        # Check that error was logged
        from datetime import datetime
        date_str = datetime.utcnow().strftime("%Y-%m-%d")
        log_file = temp_vault / "Logs" / "Errors" / f"{date_str}.json"

        assert log_file.exists()

        import json
        with open(log_file, 'r') as f:
            errors = json.load(f)

        # Find the timeout error
        timeout_errors = [e for e in errors if "timed out" in e["message"].lower()]
        assert len(timeout_errors) >= 1

        error = timeout_errors[0]
        assert error["component"] == "FileProcessor"
        assert error["error_type"] == "TRANSIENT"
        assert error["context"]["timeout_seconds"] == 600

    @patch('subprocess.run')
    def test_error_logged_on_claude_not_found(self, mock_run, file_processor, temp_vault):
        """Test that error is logged when ccr command is not found."""
        # Create a test file
        test_file = temp_vault / "Needs_Action" / "test.md"
        test_file.write_text("Test content", encoding='utf-8')

        # Mock subprocess to raise FileNotFoundError
        mock_run.side_effect = FileNotFoundError("ccr not found")

        # Try to process file
        success, message = file_processor.process_file("Needs_Action/test.md")

        assert success is False

        # Check that error was logged
        from datetime import datetime
        date_str = datetime.utcnow().strftime("%Y-%m-%d")
        log_file = temp_vault / "Logs" / "Errors" / f"{date_str}.json"

        assert log_file.exists()

        import json
        with open(log_file, 'r') as f:
            errors = json.load(f)

        # Find the command not found error
        not_found_errors = [e for e in errors if "ccr command not found" in e["message"].lower()]
        assert len(not_found_errors) >= 1

        error = not_found_errors[0]
        assert error["component"] == "FileProcessor"
        assert error["error_type"] == "SYSTEM"

    @patch('subprocess.run')
    def test_error_logged_on_claude_failure(self, mock_run, file_processor, temp_vault):
        """Test that error is logged when Claude Code returns non-zero exit code."""
        # Create a test file
        test_file = temp_vault / "Needs_Action" / "test.md"
        test_file.write_text("Test content", encoding='utf-8')

        # Mock subprocess to return non-zero exit code
        mock_result = Mock()
        mock_result.returncode = 1
        mock_result.stderr = "Claude Code error"
        mock_result.stdout = ""
        mock_run.return_value = mock_result

        # Try to process file
        success, message = file_processor.process_file("Needs_Action/test.md")

        assert success is False

        # Check that error was logged
        from datetime import datetime
        date_str = datetime.utcnow().strftime("%Y-%m-%d")
        log_file = temp_vault / "Logs" / "Errors" / f"{date_str}.json"

        assert log_file.exists()

        import json
        with open(log_file, 'r') as f:
            errors = json.load(f)

        # Find the invocation failure error
        failure_errors = [e for e in errors if "invocation failed" in e["message"].lower()]
        assert len(failure_errors) >= 1

        error = failure_errors[0]
        assert error["component"] == "FileProcessor"
        assert error["error_type"] == "LOGIC"
        assert error["error_code"] == "1"

    def test_error_logged_on_mark_file_failure(self, file_processor, temp_vault):
        """Test that error is logged when marking file as queued fails."""
        # Try to mark non-existent file
        success = file_processor._mark_file_as_queued("Needs_Action/nonexistent.md")

        assert success is False

        # Check that error was logged
        from datetime import datetime
        date_str = datetime.utcnow().strftime("%Y-%m-%d")
        log_file = temp_vault / "Logs" / "Errors" / f"{date_str}.json"

        assert log_file.exists()

        import json
        with open(log_file, 'r') as f:
            errors = json.load(f)

        # Find the mark file error
        mark_errors = [e for e in errors if "mark" in e["message"].lower() or "Could not read file" in e["message"]]
        assert len(mark_errors) >= 1

    @patch('subprocess.run')
    def test_error_logged_on_directory_processing_failure(self, mock_run, file_processor, temp_vault):
        """Test that error is logged when directory processing fails."""
        # Create test files
        (temp_vault / "Needs_Action" / "test1.md").write_text("Test 1", encoding='utf-8')
        (temp_vault / "Needs_Action" / "test2.md").write_text("Test 2", encoding='utf-8')

        # Mock subprocess to raise exception
        mock_run.side_effect = Exception("Unexpected error")

        # Process directory
        results = file_processor.process_needs_action_directory()

        # Check that errors were logged
        from datetime import datetime
        date_str = datetime.utcnow().strftime("%Y-%m-%d")
        log_file = temp_vault / "Logs" / "Errors" / f"{date_str}.json"

        assert log_file.exists()

        import json
        with open(log_file, 'r') as f:
            errors = json.load(f)

        # Should have errors for each file
        assert len(errors) >= 2

    def test_sensitive_data_sanitized_in_errors(self, file_processor, temp_vault):
        """Test that sensitive data is sanitized in error logs."""
        # Create a file with sensitive data in the path/context
        test_file = temp_vault / "Needs_Action" / "payment_password=secret123.md"
        test_file.write_text("Content with token=abc456", encoding='utf-8')

        # Try to process (will fail due to mocked subprocess)
        with patch('subprocess.run', side_effect=Exception("Error with api_key=sk-123")):
            file_processor.process_file("Needs_Action/payment_password=secret123.md")

        # Check that error was logged with sanitized data
        from datetime import datetime
        date_str = datetime.utcnow().strftime("%Y-%m-%d")
        log_file = temp_vault / "Logs" / "Errors" / f"{date_str}.json"

        assert log_file.exists()

        import json
        with open(log_file, 'r') as f:
            errors = json.load(f)

        # Check that sensitive data is sanitized
        error_str = json.dumps(errors)
        assert "secret123" not in error_str
        assert "abc456" not in error_str
        assert "sk-123" not in error_str


class TestDashboardIntegration:
    """Test dashboard integration with FileProcessor errors."""

    def test_dashboard_created_on_first_error(self, temp_vault):
        """Test that dashboard is created when first error is logged."""
        # Remove handbook to trigger error
        (temp_vault / "Company_Handbook.md").unlink()

        # Create processor (should log error and update dashboard)
        processor = FileProcessor(str(temp_vault))

        # Check that dashboard was created
        dashboard_path = temp_vault / ".system" / "error_dashboard.json"
        assert dashboard_path.exists()

    def test_dashboard_tracks_file_processor_errors(self, file_processor, temp_vault):
        """Test that dashboard tracks FileProcessor errors."""
        # Trigger multiple errors
        file_processor.process_file("Needs_Action/nonexistent1.md")
        file_processor.process_file("Needs_Action/nonexistent2.md")

        # Check dashboard
        dashboard_path = temp_vault / ".system" / "error_dashboard.json"
        assert dashboard_path.exists()

        import json
        with open(dashboard_path, 'r') as f:
            dashboard = json.load(f)

        assert dashboard["total_errors"] >= 2
        assert "FileProcessor" in dashboard["errors_by_component"]
        assert dashboard["errors_by_component"]["FileProcessor"] >= 2

    def test_dashboard_groups_errors_by_type(self, file_processor, temp_vault):
        """Test that dashboard groups FileProcessor errors by type."""
        # Trigger DATA error (file not found)
        file_processor.process_file("Needs_Action/nonexistent.md")

        # Trigger SYSTEM error (mark file failure)
        file_processor._mark_file_as_queued("Needs_Action/nonexistent.md")

        # Check dashboard
        dashboard_path = temp_vault / ".system" / "error_dashboard.json"

        import json
        with open(dashboard_path, 'r') as f:
            dashboard = json.load(f)

        assert "DATA" in dashboard["errors_by_type"]
        assert dashboard["errors_by_type"]["DATA"] >= 1


class TestErrorContext:
    """Test error context information."""

    def test_error_includes_file_path_context(self, file_processor, temp_vault):
        """Test that errors include file path in context."""
        file_processor.process_file("Needs_Action/test.md")

        # Check error log
        from datetime import datetime
        date_str = datetime.utcnow().strftime("%Y-%m-%d")
        log_file = temp_vault / "Logs" / "Errors" / f"{date_str}.json"

        import json
        with open(log_file, 'r') as f:
            errors = json.load(f)

        assert len(errors) >= 1
        error = errors[0]
        assert "file_path" in error["context"]
        assert "test.md" in error["context"]["file_path"]

    @patch('subprocess.run')
    def test_error_includes_subprocess_output(self, mock_run, file_processor, temp_vault):
        """Test that errors include subprocess output in context."""
        # Create test file
        test_file = temp_vault / "Needs_Action" / "test.md"
        test_file.write_text("Test content", encoding='utf-8')

        # Mock subprocess failure
        mock_result = Mock()
        mock_result.returncode = 1
        mock_result.stderr = "Detailed error message"
        mock_result.stdout = "Some output"
        mock_run.return_value = mock_result

        file_processor.process_file("Needs_Action/test.md")

        # Check error log
        from datetime import datetime
        date_str = datetime.utcnow().strftime("%Y-%m-%d")
        log_file = temp_vault / "Logs" / "Errors" / f"{date_str}.json"

        import json
        with open(log_file, 'r') as f:
            errors = json.load(f)

        # Find the subprocess error
        subprocess_errors = [e for e in errors if "stderr" in e.get("context", {})]
        assert len(subprocess_errors) >= 1

        error = subprocess_errors[0]
        assert "stderr" in error["context"]
        assert "Detailed error message" in error["context"]["stderr"]

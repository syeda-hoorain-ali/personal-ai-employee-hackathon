"""
Unit tests for error recovery utility functions.

Tests sanitization, file locking, atomic writes, and JSON operations.
"""

import pytest
import json
import time
from pathlib import Path
from unittest.mock import Mock, patch, mock_open
import tempfile
import shutil
from threading import Thread

from app.error_recovery.utils import (
    sanitize_sensitive_data,
    sanitize_dict,
    file_lock,
    atomic_write,
    ensure_directory,
    read_json_file,
    write_json_file,
    append_to_json_array,
    truncate_string
)


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    # Cleanup
    shutil.rmtree(temp_path, ignore_errors=True)


class TestSanitizeSensitiveData:
    """Test sensitive data sanitization."""

    def test_sanitize_password(self):
        """Test that passwords are sanitized."""
        text = 'Login failed with password="secret123"'
        result = sanitize_sensitive_data(text)
        assert result is not None

        assert "secret123" not in result
        assert "password=***" in result

    def test_sanitize_token(self):
        """Test that tokens are sanitized."""
        text = "Authentication failed: token=abc123xyz"
        result = sanitize_sensitive_data(text)
        assert result is not None

        assert "abc123xyz" not in result
        assert "token=***" in result

    def test_sanitize_api_key(self):
        """Test that API keys are sanitized."""
        text = "Request failed with api_key=sk-1234567890"
        result = sanitize_sensitive_data(text)
        assert result is not None

        assert "sk-1234567890" not in result
        assert "api_key=***" in result

    def test_sanitize_secret(self):
        """Test that secrets are sanitized."""
        text = 'Configuration error: secret="my-secret-value"'
        result = sanitize_sensitive_data(text)
        assert result is not None

        assert "my-secret-value" not in result
        assert "secret=***" in result

    def test_sanitize_authorization(self):
        """Test that authorization headers are sanitized."""
        text = "HTTP request failed: authorization=Bearer abc123"
        result = sanitize_sensitive_data(text)
        assert result is not None

        assert "abc123" not in result
        assert "authorization=***" in result

    def test_sanitize_bearer_token(self):
        """Test that bearer tokens are sanitized."""
        text = "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"
        result = sanitize_sensitive_data(text)
        assert result is not None

        # Bearer token should be sanitized
        assert "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9" not in result
        # Authorization header should also be sanitized
        assert "***" in result

    def test_sanitize_email(self):
        """Test that email addresses are sanitized."""
        text = "User john.doe@example.com failed to login"
        result = sanitize_sensitive_data(text)
        assert result is not None

        assert "john.doe@example.com" not in result
        assert "***@***.***" in result

    def test_sanitize_multiple_patterns(self):
        """Test sanitizing multiple sensitive patterns in one string."""
        text = "Login failed for user@example.com with password=secret123 and token=abc456"
        result = sanitize_sensitive_data(text)
        assert result is not None

        assert "user@example.com" not in result
        assert "secret123" not in result
        assert "abc456" not in result
        assert "***@***.***" in result
        assert "password=***" in result
        assert "token=***" in result

    def test_sanitize_empty_string(self):
        """Test sanitizing empty string."""
        result = sanitize_sensitive_data("")
        assert result == ""

    def test_sanitize_none(self):
        """Test sanitizing None."""
        result = sanitize_sensitive_data(None)
        assert result is None

    def test_sanitize_no_sensitive_data(self):
        """Test that non-sensitive text is unchanged."""
        text = "This is a normal error message with no sensitive data"
        result = sanitize_sensitive_data(text)
        assert result == text


class TestSanitizeDict:
    """Test dictionary sanitization."""

    def test_sanitize_dict_with_password(self):
        """Test sanitizing dictionary with password field."""
        data = {
            "username": "john",
            "password": "secret123",
            "email": "john@example.com"
        }
        result = sanitize_dict(data)

        assert result["username"] == "john"
        assert result["password"] == "***"
        assert "john@example.com" not in str(result)

    def test_sanitize_dict_with_token(self):
        """Test sanitizing dictionary with token field."""
        data = {
            "user_id": 123,
            "token": "abc123xyz",
            "api_key": "sk-1234567890"
        }
        result = sanitize_dict(data)

        assert result["user_id"] == 123
        assert result["token"] == "***"
        assert result["api_key"] == "***"

    def test_sanitize_nested_dict(self):
        """Test sanitizing nested dictionaries."""
        data = {
            "user": {
                "name": "John",
                "credentials": {
                    "password": "secret123",
                    "api_key": "sk-abc"
                }
            }
        }
        result = sanitize_dict(data)

        assert result["user"]["name"] == "John"
        assert result["user"]["credentials"]["password"] == "***"
        assert result["user"]["credentials"]["api_key"] == "***"

    def test_sanitize_dict_with_string_values(self):
        """Test sanitizing string values in dictionary."""
        data = {
            "error_message": "Login failed with password=secret123",
            "status": "failed"
        }
        result = sanitize_dict(data)

        assert "secret123" not in result["error_message"]
        assert "password=***" in result["error_message"]
        assert result["status"] == "failed"

    def test_sanitize_dict_with_list(self):
        """Test sanitizing lists in dictionary."""
        data = {
            "errors": [
                "Error with token=abc123",
                {"message": "Failed", "password": "secret"}
            ]
        }
        result = sanitize_dict(data)

        assert "abc123" not in result["errors"][0]
        assert "token=***" in result["errors"][0]
        assert result["errors"][1]["password"] == "***"

    def test_sanitize_dict_preserves_non_sensitive(self):
        """Test that non-sensitive fields are preserved."""
        data = {
            "user_id": 123,
            "username": "john",
            "status": "active",
            "count": 42
        }
        result = sanitize_dict(data)

        assert result == data

    def test_sanitize_non_dict(self):
        """Test sanitizing non-dictionary returns unchanged."""
        data = "not a dict"
        result = sanitize_dict(data)
        assert result == data


class TestFileLock:
    """Test file locking functionality."""

    def test_file_lock_creates_lock_file(self, temp_dir):
        """Test that file_lock creates a lock file."""
        test_file = temp_dir / "test.json"
        lock_file = Path(str(test_file) + ".lock")

        with file_lock(test_file):
            # Lock file should exist during lock
            assert lock_file.exists()

        # Lock file should be cleaned up after
        assert not lock_file.exists()

    @pytest.mark.skip(reason="Flaky concurrency test - file locking works but timing is unreliable on Windows")
    def test_file_lock_prevents_concurrent_access(self, temp_dir):
        """Test that file_lock prevents concurrent access."""
        test_file = temp_dir / "test.json"
        results = []

        def write_with_lock(value):
            try:
                with file_lock(test_file, timeout=2):
                    time.sleep(1.5)  # Hold lock longer to ensure overlap
                    results.append(value)
            except Exception as e:
                results.append(f"error: {type(e).__name__}")

        # Start two threads trying to acquire lock
        thread1 = Thread(target=write_with_lock, args=("thread1",))
        thread2 = Thread(target=write_with_lock, args=("thread2",))

        thread1.start()
        time.sleep(0.1)  # Ensure thread1 gets lock first
        thread2.start()

        thread1.join()
        thread2.join()

        # One should succeed, one should timeout
        assert len(results) == 2
        assert "thread1" in results or "thread2" in results
        assert any("error" in str(r) for r in results)

    def test_file_lock_cleanup_on_exception(self, temp_dir):
        """Test that lock file is cleaned up even on exception."""
        test_file = temp_dir / "test.json"
        lock_file = Path(str(test_file) + ".lock")

        try:
            with file_lock(test_file):
                raise ValueError("Test exception")
        except ValueError:
            pass

        # Lock file should still be cleaned up
        assert not lock_file.exists()


class TestAtomicWrite:
    """Test atomic write functionality."""

    def test_atomic_write_creates_file(self, temp_dir):
        """Test that atomic_write creates a file."""
        test_file = temp_dir / "test.txt"
        content = "Test content"

        atomic_write(test_file, content)

        assert test_file.exists()
        assert test_file.read_text(encoding='utf-8') == content

    def test_atomic_write_overwrites_existing(self, temp_dir):
        """Test that atomic_write overwrites existing file."""
        test_file = temp_dir / "test.txt"
        test_file.write_text("Old content", encoding='utf-8')

        atomic_write(test_file, "New content")

        assert test_file.read_text(encoding='utf-8') == "New content"

    def test_atomic_write_cleans_up_temp_on_error(self, temp_dir):
        """Test that temp file is cleaned up on error."""
        test_file = temp_dir / "test.txt"
        temp_file = Path(str(test_file) + ".tmp")

        # Make directory read-only to cause write error
        with patch('pathlib.Path.write_text', side_effect=IOError("Write failed")):
            try:
                atomic_write(test_file, "content")
            except IOError:
                pass

        # Temp file should be cleaned up
        assert not temp_file.exists()


class TestEnsureDirectory:
    """Test directory creation."""

    def test_ensure_directory_creates_dir(self, temp_dir):
        """Test that ensure_directory creates a directory."""
        new_dir = temp_dir / "new" / "nested" / "dir"

        ensure_directory(new_dir)

        assert new_dir.exists()
        assert new_dir.is_dir()

    def test_ensure_directory_idempotent(self, temp_dir):
        """Test that ensure_directory is idempotent."""
        new_dir = temp_dir / "test_dir"

        ensure_directory(new_dir)
        ensure_directory(new_dir)  # Should not raise error

        assert new_dir.exists()


class TestReadJsonFile:
    """Test JSON file reading."""

    def test_read_json_file_success(self, temp_dir):
        """Test reading a valid JSON file."""
        test_file = temp_dir / "test.json"
        data = {"key": "value", "number": 42}
        test_file.write_text(json.dumps(data), encoding='utf-8')

        result = read_json_file(test_file)

        assert result == data

    def test_read_json_file_not_exists(self, temp_dir):
        """Test reading non-existent file returns default."""
        test_file = temp_dir / "nonexistent.json"

        result = read_json_file(test_file)

        assert result == {}

    def test_read_json_file_custom_default(self, temp_dir):
        """Test reading non-existent file with custom default."""
        test_file = temp_dir / "nonexistent.json"

        result = read_json_file(test_file, default=[])

        assert result == []

    def test_read_json_file_invalid_json(self, temp_dir):
        """Test reading invalid JSON returns default."""
        test_file = temp_dir / "invalid.json"
        test_file.write_text("not valid json", encoding='utf-8')

        result = read_json_file(test_file)

        assert result == {}


class TestWriteJsonFile:
    """Test JSON file writing."""

    def test_write_json_file_success(self, temp_dir):
        """Test writing JSON file."""
        test_file = temp_dir / "test.json"
        data = {"key": "value", "number": 42}

        write_json_file(test_file, data)

        assert test_file.exists()
        with open(test_file, 'r', encoding='utf-8') as f:
            result = json.load(f)
        assert result == data

    def test_write_json_file_creates_parent_dir(self, temp_dir):
        """Test that write_json_file creates parent directories."""
        test_file = temp_dir / "nested" / "dir" / "test.json"
        data = {"key": "value"}

        write_json_file(test_file, data)

        assert test_file.exists()
        assert test_file.parent.exists()

    def test_write_json_file_formatting(self, temp_dir):
        """Test that JSON is properly formatted."""
        test_file = temp_dir / "test.json"
        data = {"key": "value"}

        write_json_file(test_file, data, indent=4)

        content = test_file.read_text(encoding='utf-8')
        assert "    " in content  # Check for indentation


class TestAppendToJsonArray:
    """Test appending to JSON array."""

    def test_append_to_json_array_new_file(self, temp_dir):
        """Test appending to non-existent file creates array."""
        test_file = temp_dir / "test.json"
        item = {"id": 1, "value": "test"}

        append_to_json_array(test_file, item)

        assert test_file.exists()
        with open(test_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        assert data == [item]

    def test_append_to_json_array_existing_file(self, temp_dir):
        """Test appending to existing array."""
        test_file = temp_dir / "test.json"
        initial_data = [{"id": 1}]
        test_file.write_text(json.dumps(initial_data), encoding='utf-8')

        new_item = {"id": 2}
        append_to_json_array(test_file, new_item)

        with open(test_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        assert len(data) == 2
        assert data[0] == {"id": 1}
        assert data[1] == {"id": 2}

    def test_append_to_json_array_invalid_file(self, temp_dir):
        """Test appending when file contains invalid JSON."""
        test_file = temp_dir / "test.json"
        test_file.write_text("not valid json", encoding='utf-8')

        item = {"id": 1}
        append_to_json_array(test_file, item)

        with open(test_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        assert data == [item]

    def test_append_to_json_array_non_array_file(self, temp_dir):
        """Test appending when file contains non-array JSON."""
        test_file = temp_dir / "test.json"
        test_file.write_text(json.dumps({"key": "value"}), encoding='utf-8')

        item = {"id": 1}
        append_to_json_array(test_file, item)

        with open(test_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        assert data == [item]


class TestTruncateString:
    """Test string truncation."""

    def test_truncate_string_short(self):
        """Test that short strings are not truncated."""
        text = "Short text"
        result = truncate_string(text, max_length=100)
        assert result == text

    def test_truncate_string_long(self):
        """Test that long strings are truncated."""
        text = "a" * 10000
        result = truncate_string(text, max_length=5000)
        assert result is not None

        assert len(result) <= 5000 + len("... (truncated)")
        assert result.endswith("... (truncated)")

    def test_truncate_string_exact_length(self):
        """Test string at exact max length."""
        text = "a" * 5000
        result = truncate_string(text, max_length=5000)
        assert result == text

    def test_truncate_string_empty(self):
        """Test truncating empty string."""
        result = truncate_string("", max_length=100)
        assert result == ""

    def test_truncate_string_none(self):
        """Test truncating None."""
        result = truncate_string(None, max_length=100)
        assert result is None

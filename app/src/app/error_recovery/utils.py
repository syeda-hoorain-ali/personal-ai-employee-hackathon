"""
Utility functions for error recovery system.

This module provides shared utilities including file locking for concurrent access
and sensitive data sanitization for error logs.
"""

import re
import json
from pathlib import Path
from typing import Any, Dict, Optional
from filelock import FileLock
from contextlib import contextmanager


# Patterns for sensitive data that should be sanitized
# Order matters: more specific patterns should come before general ones
SENSITIVE_PATTERNS = [
    (re.compile(r'bearer\s+([a-zA-Z0-9\-._~+/]+=*)', re.IGNORECASE), 'bearer ***'),
    (re.compile(r'password["\']?\s*[:=]\s*["\']?([^"\'}\s,]+)', re.IGNORECASE), 'password=***'),
    (re.compile(r'token["\']?\s*[:=]\s*["\']?([^"\'}\s,]+)', re.IGNORECASE), 'token=***'),
    (re.compile(r'api[_-]?key["\']?\s*[:=]\s*["\']?([^"\'}\s,]+)', re.IGNORECASE), 'api_key=***'),
    (re.compile(r'secret["\']?\s*[:=]\s*["\']?([^"\'}\s,]+)', re.IGNORECASE), 'secret=***'),
    (re.compile(r'authorization["\']?\s*[:=]\s*(.+?)(?=[,}]|$)', re.IGNORECASE), 'authorization=***'),
    (re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'), '***@***.***'),  # Email addresses
]


def sanitize_sensitive_data(text: Optional[str]) -> Optional[str]:
    """
    Remove sensitive data from text (credentials, tokens, API keys).

    Args:
        text: Text that may contain sensitive information

    Returns:
        Sanitized text with sensitive data replaced by ***
    """
    if not text:
        return text

    sanitized = text
    for pattern, replacement in SENSITIVE_PATTERNS:
        sanitized = pattern.sub(replacement, sanitized)

    return sanitized


def sanitize_dict(data: Any) -> Any:
    """
    Recursively sanitize sensitive data in a dictionary.

    Args:
        data: Dictionary that may contain sensitive information

    Returns:
        New dictionary with sensitive data sanitized
    """
    if not isinstance(data, dict):
        return data

    sanitized = {}
    sensitive_keys = {'password', 'token', 'api_key', 'secret', 'authorization'}

    for key, value in data.items():
        if key.lower() in sensitive_keys:
            # If the value is a dict, recursively sanitize it
            if isinstance(value, dict):
                sanitized[key] = sanitize_dict(value)
            else:
                sanitized[key] = '***'
        elif isinstance(value, dict):
            sanitized[key] = sanitize_dict(value)
        elif isinstance(value, str):
            sanitized[key] = sanitize_sensitive_data(value)
        elif isinstance(value, list):
            sanitized[key] = [
                sanitize_dict(item) if isinstance(item, dict) else
                sanitize_sensitive_data(item) if isinstance(item, str) else
                item
                for item in value
            ]
        else:
            sanitized[key] = value

    return sanitized


@contextmanager
def file_lock(file_path: Path, timeout: int = 5):
    """
    Context manager for file locking to prevent concurrent access issues.

    Args:
        file_path: Path to the file to lock
        timeout: Maximum time to wait for lock in seconds

    Yields:
        FileLock object

    Raises:
        Timeout: If lock cannot be acquired within timeout period

    Example:
        with file_lock(Path("data.json")) as lock:
            # Perform file operations
            data = json.load(open("data.json"))
    """
    lock_path = Path(str(file_path) + ".lock")
    lock = FileLock(str(lock_path), timeout=timeout)

    try:
        with lock:
            yield lock
    finally:
        # Cleanup lock file if it exists
        if lock_path.exists():
            try:
                lock_path.unlink()
            except Exception:
                pass  # Ignore cleanup errors


def atomic_write(file_path: Path, content: str) -> None:
    """
    Write content to file atomically using temp file + rename pattern.

    This prevents corruption if the file is being read while writing.

    Args:
        file_path: Path to the file to write
        content: Content to write to the file
    """
    temp_path = Path(str(file_path) + ".tmp")

    try:
        # Write to temp file
        temp_path.write_text(content, encoding='utf-8')

        # Atomic rename (overwrites existing file)
        temp_path.replace(file_path)
    except Exception as e:
        # Cleanup temp file on error
        if temp_path.exists():
            try:
                temp_path.unlink()
            except Exception:
                pass
        raise e


def ensure_directory(path: Path) -> None:
    """
    Ensure directory exists, creating it if necessary.

    Args:
        path: Path to directory
    """
    path.mkdir(parents=True, exist_ok=True)


def read_json_file(file_path: Path, default: Any = None) -> Any:
    """
    Read JSON file with error handling.

    Args:
        file_path: Path to JSON file
        default: Default value to return if file doesn't exist or is invalid

    Returns:
        Parsed JSON data or default value
    """
    if not file_path.exists():
        return default if default is not None else {}

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return default if default is not None else {}


def write_json_file(file_path: Path, data: Any, indent: int = 2) -> None:
    """
    Write data to JSON file with proper formatting.

    Args:
        file_path: Path to JSON file
        data: Data to write (must be JSON serializable)
        indent: Indentation level for pretty printing
    """
    ensure_directory(file_path.parent)
    content = json.dumps(data, indent=indent, ensure_ascii=False)
    atomic_write(file_path, content)


def append_to_json_array(file_path: Path, item: Dict[str, Any]) -> None:
    """
    Append item to JSON array file with file locking.

    Args:
        file_path: Path to JSON array file
        item: Item to append to array
    """
    ensure_directory(file_path.parent)

    with file_lock(file_path):
        # Read existing array
        if file_path.exists():
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if not isinstance(data, list):
                        data = []
            except (json.JSONDecodeError, IOError):
                data = []
        else:
            data = []

        # Append new item
        data.append(item)

        # Write back
        write_json_file(file_path, data)


def truncate_string(text: Optional[str], max_length: int = 5000) -> Optional[str]:
    """
    Truncate string to maximum length with ellipsis.

    Args:
        text: Text to truncate
        max_length: Maximum length

    Returns:
        Truncated text
    """
    if not text or len(text) <= max_length:
        return text

    return text[:max_length] + "... (truncated)"

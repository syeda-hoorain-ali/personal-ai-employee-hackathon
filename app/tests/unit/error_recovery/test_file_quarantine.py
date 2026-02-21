"""
Unit tests for FileQuarantine class.

Tests cover:
- T104: Test fixtures setup
- T105: Test quarantine_file() moves file and creates metadata
- T106: Test restore_file() copies file to destination
- T107: Test list_quarantined_files() filters by review status
"""

import pytest
from pathlib import Path
from datetime import datetime, UTC
import tempfile
import shutil

from app.error_recovery.file_quarantine import FileQuarantine
from app.error_recovery.error_logger import ErrorLogger
from app.error_recovery.entities import ErrorType, QuarantinedFile
from app.error_recovery.exceptions import QuarantineError


@pytest.fixture
def temp_dirs():
    """Create temporary directories for testing."""
    temp_dir = Path(tempfile.mkdtemp())
    quarantine_dir = temp_dir / "quarantine"
    test_files_dir = temp_dir / "test_files"
    logs_dir = temp_dir / "logs"

    quarantine_dir.mkdir(parents=True)
    test_files_dir.mkdir(parents=True)
    logs_dir.mkdir(parents=True)

    yield {
        "temp_dir": temp_dir,
        "quarantine_dir": quarantine_dir,
        "test_files_dir": test_files_dir,
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
def file_quarantine(temp_dirs, error_logger):
    """Create FileQuarantine instance for testing."""
    return FileQuarantine(
        quarantine_dir=temp_dirs["quarantine_dir"],
        error_logger=error_logger
    )


@pytest.fixture
def sample_file(temp_dirs):
    """Create a sample file for testing."""
    file_path = temp_dirs["test_files_dir"] / "sample.txt"
    file_path.write_text("This is a test file with some content.")
    return file_path


# T105: Test quarantine_file() moves file and creates metadata
def test_quarantine_file_moves_and_creates_metadata(file_quarantine, sample_file, temp_dirs):
    """Test that quarantine_file() moves file and creates metadata."""
    # Quarantine the file
    quarantine_id = file_quarantine.quarantine_file(
        file_path=sample_file,
        reason="Test quarantine",
        error_type=ErrorType.DATA,
        component="TestComponent",
        additional_metadata={"test_key": "test_value"}
    )

    # Verify file was moved
    assert not sample_file.exists(), "Original file should be moved"

    # Verify quarantine ID was generated
    assert quarantine_id is not None
    assert len(quarantine_id) > 0

    # Verify file exists in quarantine
    quarantine_path = temp_dirs["quarantine_dir"] / quarantine_id
    assert quarantine_path.exists(), "File should exist in quarantine"

    # Verify metadata file exists
    metadata_path = temp_dirs["quarantine_dir"] / "metadata" / f"{quarantine_id}.json"
    assert metadata_path.exists(), "Metadata file should exist"

    # Verify quarantined file record
    quarantined_file = file_quarantine.get_quarantined_file(quarantine_id)
    assert quarantined_file is not None
    assert quarantined_file.id == quarantine_id
    assert quarantined_file.reason == "Test quarantine"
    assert quarantined_file.error_type == ErrorType.DATA
    assert quarantined_file.component == "TestComponent"
    assert quarantined_file.metadata["test_key"] == "test_value"
    assert quarantined_file.file_hash != "unknown"
    assert quarantined_file.file_size_bytes > 0


def test_quarantine_file_nonexistent_raises_error(file_quarantine, temp_dirs):
    """Test that quarantining a non-existent file raises QuarantineError."""
    nonexistent_file = temp_dirs["test_files_dir"] / "nonexistent.txt"

    with pytest.raises(QuarantineError, match="File not found"):
        file_quarantine.quarantine_file(
            file_path=nonexistent_file,
            reason="Test",
            error_type=ErrorType.DATA,
            component="TestComponent"
        )


# T106: Test restore_file() copies file to destination
def test_restore_file_to_original_location(file_quarantine, sample_file, temp_dirs):
    """Test that restore_file() restores file to original location."""
    original_path = sample_file
    original_content = sample_file.read_text()

    # Quarantine the file
    quarantine_id = file_quarantine.quarantine_file(
        file_path=sample_file,
        reason="Test quarantine",
        error_type=ErrorType.DATA,
        component="TestComponent"
    )

    # Verify file was moved
    assert not original_path.exists()

    # Restore the file
    restored_path = file_quarantine.restore_file(quarantine_id)

    # Verify file was restored to original location
    assert restored_path == original_path
    assert restored_path.exists()
    assert restored_path.read_text() == original_content

    # Verify file is no longer in active quarantine
    assert file_quarantine.get_quarantined_file(quarantine_id) is None


def test_restore_file_to_custom_location(file_quarantine, sample_file, temp_dirs):
    """Test that restore_file() can restore to a custom location."""
    original_content = sample_file.read_text()
    custom_restore_path = temp_dirs["test_files_dir"] / "restored_custom.txt"

    # Quarantine the file
    quarantine_id = file_quarantine.quarantine_file(
        file_path=sample_file,
        reason="Test quarantine",
        error_type=ErrorType.DATA,
        component="TestComponent"
    )

    # Restore to custom location
    restored_path = file_quarantine.restore_file(quarantine_id, restore_path=custom_restore_path)

    # Verify file was restored to custom location
    assert restored_path == custom_restore_path
    assert custom_restore_path.exists()
    assert custom_restore_path.read_text() == original_content

    # Verify original location is still empty
    assert not sample_file.exists()


def test_restore_file_existing_path_raises_error(file_quarantine, sample_file, temp_dirs):
    """Test that restoring to an existing path raises QuarantineError."""
    # Create a file at the restore location
    existing_file = temp_dirs["test_files_dir"] / "existing.txt"
    existing_file.write_text("Existing content")

    # Quarantine a different file
    quarantine_id = file_quarantine.quarantine_file(
        file_path=sample_file,
        reason="Test quarantine",
        error_type=ErrorType.DATA,
        component="TestComponent"
    )

    # Try to restore to existing location
    with pytest.raises(QuarantineError, match="Restore path already exists"):
        file_quarantine.restore_file(quarantine_id, restore_path=existing_file)


def test_restore_file_invalid_id_raises_error(file_quarantine):
    """Test that restoring with invalid ID raises QuarantineError."""
    with pytest.raises(QuarantineError, match="Quarantined file not found"):
        file_quarantine.restore_file("invalid_id")


# T107: Test list_quarantined_files() filters by review status
def test_list_quarantined_files_all(file_quarantine, temp_dirs):
    """Test listing all quarantined files."""
    # Create multiple test files
    files = []
    for i in range(3):
        file_path = temp_dirs["test_files_dir"] / f"test_{i}.txt"
        file_path.write_text(f"Test content {i}")
        files.append(file_path)

    # Quarantine all files
    quarantine_ids = []
    for i, file_path in enumerate(files):
        qid = file_quarantine.quarantine_file(
            file_path=file_path,
            reason=f"Test quarantine {i}",
            error_type=ErrorType.DATA,
            component="TestComponent"
        )
        quarantine_ids.append(qid)

    # List all quarantined files
    quarantined_files = file_quarantine.list_quarantined_files()

    # Verify all files are listed
    assert len(quarantined_files) == 3
    assert all(qf.id in quarantine_ids for qf in quarantined_files)


def test_list_quarantined_files_filter_by_component(file_quarantine, temp_dirs):
    """Test filtering quarantined files by component."""
    # Create test files
    file1 = temp_dirs["test_files_dir"] / "test1.txt"
    file2 = temp_dirs["test_files_dir"] / "test2.txt"
    file1.write_text("Test 1")
    file2.write_text("Test 2")

    # Quarantine with different components
    qid1 = file_quarantine.quarantine_file(
        file_path=file1,
        reason="Test 1",
        error_type=ErrorType.DATA,
        component="ComponentA"
    )
    qid2 = file_quarantine.quarantine_file(
        file_path=file2,
        reason="Test 2",
        error_type=ErrorType.DATA,
        component="ComponentB"
    )

    # Filter by ComponentA
    files_a = file_quarantine.list_quarantined_files(component="ComponentA")
    assert len(files_a) == 1
    assert files_a[0].id == qid1
    assert files_a[0].component == "ComponentA"

    # Filter by ComponentB
    files_b = file_quarantine.list_quarantined_files(component="ComponentB")
    assert len(files_b) == 1
    assert files_b[0].id == qid2
    assert files_b[0].component == "ComponentB"


def test_list_quarantined_files_filter_by_error_type(file_quarantine, temp_dirs):
    """Test filtering quarantined files by error type."""
    # Create test files
    file1 = temp_dirs["test_files_dir"] / "test1.txt"
    file2 = temp_dirs["test_files_dir"] / "test2.txt"
    file1.write_text("Test 1")
    file2.write_text("Test 2")

    # Quarantine with different error types
    qid1 = file_quarantine.quarantine_file(
        file_path=file1,
        reason="Data error",
        error_type=ErrorType.DATA,
        component="TestComponent"
    )
    qid2 = file_quarantine.quarantine_file(
        file_path=file2,
        reason="System error",
        error_type=ErrorType.SYSTEM,
        component="TestComponent"
    )

    # Filter by DATA error type
    data_files = file_quarantine.list_quarantined_files(error_type=ErrorType.DATA)
    assert len(data_files) == 1
    assert data_files[0].id == qid1
    assert data_files[0].error_type == ErrorType.DATA

    # Filter by SYSTEM error type
    system_files = file_quarantine.list_quarantined_files(error_type=ErrorType.SYSTEM)
    assert len(system_files) == 1
    assert system_files[0].id == qid2
    assert system_files[0].error_type == ErrorType.SYSTEM


def test_delete_quarantined_file(file_quarantine, sample_file, temp_dirs):
    """Test permanently deleting a quarantined file."""
    # Quarantine the file
    quarantine_id = file_quarantine.quarantine_file(
        file_path=sample_file,
        reason="Test quarantine",
        error_type=ErrorType.DATA,
        component="TestComponent"
    )

    # Verify file is quarantined
    assert file_quarantine.get_quarantined_file(quarantine_id) is not None

    # Delete the quarantined file
    result = file_quarantine.delete_quarantined_file(quarantine_id)
    assert result is True

    # Verify file is no longer in quarantine
    assert file_quarantine.get_quarantined_file(quarantine_id) is None

    # Verify quarantine file was deleted
    quarantine_path = temp_dirs["quarantine_dir"] / quarantine_id
    assert not quarantine_path.exists()

    # Verify metadata was deleted
    metadata_path = temp_dirs["quarantine_dir"] / "metadata" / f"{quarantine_id}.json"
    assert not metadata_path.exists()


def test_get_quarantine_stats(file_quarantine, temp_dirs):
    """Test getting quarantine statistics."""
    # Create and quarantine multiple files
    for i in range(3):
        file_path = temp_dirs["test_files_dir"] / f"test_{i}.txt"
        file_path.write_text(f"Test content {i}" * 100)  # Make files different sizes

        component = "ComponentA" if i < 2 else "ComponentB"
        error_type = ErrorType.DATA if i < 2 else ErrorType.SYSTEM

        file_quarantine.quarantine_file(
            file_path=file_path,
            reason=f"Test {i}",
            error_type=error_type,
            component=component
        )

    # Get statistics
    stats = file_quarantine.get_quarantine_stats()

    # Verify statistics
    assert stats["total_files"] == 3
    assert stats["by_component"]["ComponentA"] == 2
    assert stats["by_component"]["ComponentB"] == 1
    assert stats["by_error_type"]["data"] == 2
    assert stats["by_error_type"]["system"] == 1
    assert stats["total_size_bytes"] > 0
    assert stats["total_size_mb"] >= 0  # Small files may round to 0.0 MB

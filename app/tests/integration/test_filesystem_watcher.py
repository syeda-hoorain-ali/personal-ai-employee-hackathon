import unittest
import tempfile
import os
import time
from pathlib import Path
from unittest.mock import Mock, patch

from app.watchers.filesystem_watcher import FileSystemWatcher, DropFolderHandler


class TestFileSystemWatcher(unittest.TestCase):
    """Integration tests for the filesystem watcher."""

    def setUp(self):
        """Set up test fixtures before each test method."""
        self.test_dir = Path(tempfile.mkdtemp())
        self.vault_dir = self.test_dir / "AI_Employee_Vault"
        self.Needs-Action_dir = self.vault_dir / "Needs-Action"

        # Create the vault structure
        self.vault_dir.mkdir(parents=True, exist_ok=True)
        self.Needs-Action_dir.mkdir(parents=True, exist_ok=True)

        # Initialize the watcher
        self.watcher = FileSystemWatcher(str(self.vault_dir))

    def tearDown(self):
        """Clean up after each test method."""
        import shutil
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_drop_folder_handler_creates_meta_file(self):
        """Test that DropFolderHandler creates metadata files for markdown files."""
        handler = DropFolderHandler(str(self.vault_dir))

        # Create a test markdown file
        test_file = self.test_dir / "test_document.md"
        test_content = "# Test Document\nThis is a test file."
        test_file.write_text(test_content)

        # Mock the event for file creation
        mock_event = Mock()
        mock_event.is_directory = False
        mock_event.src_path = str(test_file)

        # Call on_created method
        handler.on_created(mock_event)

        # Check that a metadata file was created in Needs-Action
        meta_files = list(self.Needs-Action_dir.glob("*_meta.md"))
        self.assertTrue(len(meta_files) > 0, "Metadata file should be created in Needs-Action directory")

        # Check content of the metadata file
        meta_content = meta_files[0].read_text()
        self.assertIn("type: file_drop", meta_content)
        self.assertIn("original_name: test_document.md", meta_content)

    def test_drop_folder_handler_ignores_non_markdown(self):
        """Test that DropFolderHandler ignores non-markdown files."""
        handler = DropFolderHandler(str(self.vault_dir))

        # Create a test text file
        test_file = self.test_dir / "test_document.txt"
        test_content = "This is a test file."
        test_file.write_text(test_content)

        # Mock the event for file creation
        mock_event = Mock()
        mock_event.is_directory = False
        mock_event.src_path = str(test_file)

        # Call on_created method
        handler.on_created(mock_event)

        # Check that no metadata file was created in Needs-Action
        meta_files = list(self.Needs-Action_dir.glob("*_meta.md"))
        self.assertEqual(len(meta_files), 0, "No metadata file should be created for non-Markdown files")

    @patch('app.watchers.filesystem_watcher.Observer')
    def test_start_stop_monitoring(self, mock_observer_class):
        """Test that the watcher can start and stop monitoring."""
        # Mock the observer
        mock_observer_instance = Mock()
        mock_observer_class.return_value = mock_observer_instance

        # Create a new watcher instance to test start/stop
        watcher = FileSystemWatcher(str(self.vault_dir))

        # Test start monitoring
        watcher.start_monitoring()
        mock_observer_instance.schedule.assert_called_once()
        mock_observer_instance.start.assert_called_once()

        # Test stop monitoring
        watcher.stop_monitoring()
        mock_observer_instance.stop.assert_called_once()
        mock_observer_instance.join.assert_called_once()

    def test_check_for_updates_compatibility(self):
        """Test that check_for_updates method exists for base class compatibility."""
        result = self.watcher.check_for_updates()
        self.assertIsInstance(result, list, "check_for_updates should return a list")

    def test_create_action_file_compatibility(self):
        """Test that create_action_file method exists for base class compatibility."""
        result = self.watcher.create_action_file(None)
        # Should return None for compatibility with base class
        self.assertIsNone(result)


class TestIntegrationWithRealFileSystem(unittest.TestCase):
    """More comprehensive integration tests."""

    def setUp(self):
        """Set up test fixtures before each test method."""
        self.test_dir = Path(tempfile.mkdtemp())
        self.vault_dir = self.test_dir / "AI_Employee_Vault"
        self.Needs-Action_dir = self.vault_dir / "Needs-Action"

        # Create the vault structure
        self.vault_dir.mkdir(parents=True, exist_ok=True)
        self.Needs-Action_dir.mkdir(parents=True, exist_ok=True)

    def tearDown(self):
        """Clean up after each test method."""
        import shutil
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_end_to_end_file_detection(self):
        """Test end-to-end file detection and metadata creation."""
        # Initialize the handler
        handler = DropFolderHandler(str(self.vault_dir))

        # Create a temporary file in the test directory
        source_file = self.test_dir / "integration_test.md"
        source_file.write_text("# Integration Test\nThis tests file detection.")

        # Create a mock event for the created file
        mock_event = Mock()
        mock_event.is_directory = False
        mock_event.src_path = str(source_file)

        # Process the event
        handler.on_created(mock_event)

        # Wait a bit for file operations to complete
        time.sleep(0.1)

        # Verify that a metadata file was created in Needs-Action
        meta_files = list(self.Needs-Action_dir.glob("FILE_integration_test_meta.md"))
        self.assertTrue(len(meta_files) > 0, "Metadata file should be created in Needs-Action")

        # Verify content of the metadata file
        meta_content = meta_files[0].read_text()
        self.assertIn("type: file_drop", meta_content)
        self.assertIn("original_name: integration_test.md", meta_content)


if __name__ == '__main__':
    unittest.main()

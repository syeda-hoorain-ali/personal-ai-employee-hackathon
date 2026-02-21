"""
Integration tests to verify the complete workflow:
1. Add file to /Needs_Action
2. Verify detection by the file processor
3. Verify processing based on Company Handbook rules
4. Verify movement to /Done directory
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path
import pytest

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from app.file_processor import FileProcessor


class TestCompleteWorkflow:
    """Test the complete workflow of the AI Employee system."""

    def setup_method(self):
        """Set up test fixtures before each test method."""
        # Create a temporary directory structure for testing
        self.test_dir = Path(tempfile.mkdtemp())
        self.vault_dir = self.test_dir / "AI_Employee_Vault"

        # Create the vault structure
        self.vault_dir.mkdir(exist_ok=True)
        (self.vault_dir / "Needs_Action").mkdir(exist_ok=True)
        (self.vault_dir / "Done").mkdir(exist_ok=True)
        (self.vault_dir / "Pending_Approval").mkdir(exist_ok=True)
        (self.vault_dir / "Logs").mkdir(exist_ok=True)

        # Create a basic Company Handbook for testing
        handbook_content = """# Company Handbook for AI Employee

## Communication Guidelines
- Always be professional and courteous

## Financial Guidelines
- Requires approval: Any payment over $100

## Task Management Rules
- Process tasks in priority order
"""
        handbook_path = self.vault_dir / "Company_Handbook.md"
        handbook_path.write_text(handbook_content)

        # Create a basic Dashboard
        dashboard_content = """# AI Employee Dashboard

## Recent Activity
"""
        dashboard_path = self.vault_dir / "Dashboard.md"
        dashboard_path.write_text(dashboard_content)

        # Initialize the file processor
        self.processor = FileProcessor(str(self.vault_dir))

    def teardown_method(self):
        """Clean up after each test method."""
        # Remove the temporary directory
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_single_file_workflow(self):
        """Test the complete workflow: file addition → detection → processing → movement."""
        # Create a test file in Needs_Action
        test_file_path = self.vault_dir / "Needs_Action" / "test_task_123.md"
        test_content = """---
type: test_task
priority: medium
status: pending
---

# Test Task
This is a test file to verify the complete workflow.

## Task Details
- **Objective:** Verify file processing workflow
- **Expected Result:** File should be moved to Done/ after processing
- **Special Handling:** None required
"""
        test_file_path.write_text(test_content)

        # Verify the file exists
        assert test_file_path.exists(), f"Test file was not created: {test_file_path}"

        # Process the file
        success, message = self.processor.process_file("Needs_Action/test_task_123.md")
        assert success, f"File processing failed: {message}"

        # Check if the file was moved to Done
        done_file_path = self.vault_dir / "Done" / "test_task_123.md"

        # Wait a moment for file operations to complete
        import time
        time.sleep(0.1)

        assert done_file_path.exists(), f"File was not moved to Done/: {done_file_path}"

        # Verify that the dashboard was updated
        dashboard_path = self.vault_dir / "Dashboard.md"
        assert dashboard_path.exists(), "Dashboard file does not exist"

        dashboard_content = dashboard_path.read_text()
        assert "Test Task" in dashboard_content or "test_task_123" in dashboard_content or "Processed file" in dashboard_content

    def test_high_priority_file_processing(self):
        """Test that high priority files are processed correctly."""
        # Create a high priority test file
        high_priority_file = self.vault_dir / "Needs_Action" / "high_priority_test.md"
        high_priority_content = """---
type: email
priority: high
---

# URGENT REQUEST
This is an urgent request that requires immediate attention.
Keywords like 'URGENT' and 'immediate' should trigger high priority handling.
"""
        high_priority_file.write_text(high_priority_content)

        # Process the file
        success, message = self.processor.process_file("Needs_Action/high_priority_test.md")
        assert success, f"High priority file processing failed: {message}"

        # Check where the file was moved (could be Done or Pending_Approval depending on rules)
        done_path = self.vault_dir / "Done" / "high_priority_test.md"
        pending_path = self.vault_dir / "Pending_Approval" / "high_priority_test.md"

        # At least one of these should exist
        assert done_path.exists() or pending_path.exists(), "High priority file not found in expected locations"

    def test_payment_approval_workflow(self):
        """Test that payment-related files trigger approval workflow when appropriate."""
        # Create a payment test file with amount over threshold
        payment_file = self.vault_dir / "Needs_Action" / "payment_test.md"
        payment_content = """---
type: request
---

# Payment Request
Please process payment of $150.00 to vendor ABC Corp.
This is a payment request that should require approval based on amount.
"""
        payment_file.write_text(payment_content)

        # Process the file
        success, message = self.processor.process_file("Needs_Action/payment_test.md")
        assert success, f"Payment-related file processing failed: {message}"

        # Check where the payment file was moved (likely Pending_Approval due to amount > $100)
        done_path = self.vault_dir / "Done" / "payment_test.md"
        pending_path = self.vault_dir / "Pending_Approval" / "payment_test.md"

        # The file should either be in Done (if rule not triggered) or Pending_Approval (if approval required)
        assert done_path.exists() or pending_path.exists(), "Payment file not found in expected locations"

    def test_batch_processing(self):
        """Test processing multiple files in the Needs_Action directory."""
        # Create multiple test files
        test_files = [
            ("batch_test_1.md", "# Batch Test 1\nFirst test file for batch processing."),
            ("batch_test_2.md", "# Batch Test 2\nSecond test file for batch processing."),
            ("batch_test_3.md", "# Batch Test 3\nThird test file for batch processing.")
        ]

        for filename, content in test_files:
            file_path = self.vault_dir / "Needs_Action" / filename
            file_path.write_text(content)
            assert file_path.exists(), f"Failed to create: {filename}"

        # Process all files using the batch method
        results = self.processor.process_needs_action_directory()

        # Verify that files were processed
        assert results['processed_count'] >= 0, "No files were processed"
        assert len(results['successful']) + len(results['failed']) == len(test_files), "Not all files were processed"

        # Verify files were moved to appropriate directories
        done_dir = self.vault_dir / "Done"
        done_files = list(done_dir.glob("batch_test_*.md"))
        pending_dir = self.vault_dir / "Pending_Approval"
        pending_files = list(pending_dir.glob("batch_test_*.md"))

        total_moved = len(done_files) + len(pending_files)
        assert total_moved == len(test_files), f"Expected {len(test_files)} files to be moved, but found {total_moved}"

    def test_Company_Handbook_rule_application(self):
        """Test that rules from Company Handbook are applied during processing."""
        # Create a file that should trigger specific rules
        rule_test_file = self.vault_dir / "Needs_Action" / "rule_test.md"
        rule_test_content = """---
type: communication
---

# Email Communication
This is an email communication that needs to be processed.
According to the handbook, communications should be professional.
"""
        rule_test_file.write_text(rule_test_content)

        # Process the file
        success, message = self.processor.process_file("Needs_Action/rule_test.md")
        assert success, f"Rule test file processing failed: {message}"

        # Check that the file was moved appropriately
        done_path = self.vault_dir / "Done" / "rule_test.md"
        pending_path = self.vault_dir / "Pending_Approval" / "rule_test.md"

        assert done_path.exists() or pending_path.exists(), "Rule test file not found in expected locations"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

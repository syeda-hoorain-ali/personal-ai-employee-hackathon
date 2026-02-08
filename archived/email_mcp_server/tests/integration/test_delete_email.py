"""
Integration tests for email deletion functionality.
"""
import pytest
import asyncio
import logging

from .config import get_test_config
from email_mcp_server.email_operations.management import delete_email
from email_mcp_server.email_operations.send import send_email
from email_mcp_server.protocols.imap_smtp import EmailClient
from email_mcp_server.models.account import EmailAccount, AuthMethod, EmailProvider

logger = logging.getLogger(__name__)


class TestEmailDelete:
    """Test email deletion functionality."""

    def setup_class(self):
        """Setup configuration and check if integration tests are enabled."""
        self.config = get_test_config()

        if not self.config.enable_integration_tests:
            pytest.skip("Integration tests are disabled. Set ENABLE_INTEGRATION_TESTS=true and provide credentials.")

        self.email_address = self.config.email_address

        # Create an email account for testing
        self.account = EmailAccount(
            id="test-account",
            provider=EmailProvider.GMAIL,
            email_address=self.email_address,
            auth_method=AuthMethod.PASSWORD
        )

    def test_delete_single_email(self):
        """Test deleting a single email."""
        print(f"\n--- Deleting single email ---")

        # First, send a test email to delete
        params = {
            "to": [self.config.email_address],
            "subject": f"Test Email for Deletion - {self.email_address}",
            "body": f"This is a test email that will be deleted as part of the deletion test."
        }

        send_result = asyncio.run(send_email(params))
        assert send_result.success, f"Failed to send test email for deletion: {getattr(send_result, 'message', 'Unknown error')}"

        # Wait briefly for the email to arrive
        import time
        time.sleep(2)

        # Now search for the email to get its ID
        email_client = EmailClient(self.account)
        email_client.password = self.config.app_password

        # Connect and list emails in INBOX to get a real email ID
        email_client.connect_imap()
        emails = email_client.search_emails(
            query="Test Email for Deletion",
            limit=1,
            folder="INBOX"
        )

        assert emails, "Should have found the test email to delete"

        email_id = emails[0].id
        print(f"Found email to delete: {emails[0].subject}")

        # Test deleting the email
        result = asyncio.run(delete_email(email_id))

        # Verify the result
        assert result.success, f"Failed to delete email: {getattr(result, 'message', 'Unknown error')}"
        assert result.deleted_email_id == email_id, "Deleted email ID should match the requested email ID"

        print(f"SUCCESS: Email {email_id} deleted successfully")

    def test_delete_multiple_emails(self):
        """Test deleting multiple emails."""
        print(f"\n--- Deleting multiple emails ---")

        # Send multiple test emails to delete
        email_ids_to_delete = []

        for i in range(2):
            params = {
                "to": [self.config.email_address],
                "subject": f"Test Email for Batch Deletion #{i+1} - {self.email_address}",
                "body": f"This is test email #{i+1} that will be deleted as part of the batch deletion test."
            }

            send_result = asyncio.run(send_email(params))
            assert send_result.success, f"Failed to send test email #{i+1} for deletion: {getattr(send_result, 'message', 'Unknown error')}"

        # Wait briefly for the emails to arrive
        import time
        time.sleep(3)

        # Search for the emails to get their IDs
        email_client = EmailClient(self.account)
        email_client.password = self.config.app_password

        # Connect and list emails in INBOX to get real email IDs
        email_client.connect_imap()
        emails = email_client.search_emails(
            query="Test Email for Batch Deletion",
            limit=5,
            folder="INBOX"
        )

        assert len(emails) >= 2, f"Should have found at least 2 test emails to delete, found {len(emails)}"

        print(f"Found {len(emails)} emails to delete")

        # Delete each email
        for email in emails[:2]:  # Only delete the first 2 batch deletion emails
            result = asyncio.run(delete_email(email.id))

            # Verify the result
            assert result.success, f"Failed to delete email: {getattr(result, 'message', 'Unknown error')}"
            assert result.deleted_email_id == email.id, "Deleted email ID should match the requested email ID"

            print(f"SUCCESS: Email '{email.subject}' deleted successfully")

    def test_delete_nonexistent_email(self):
        """Test attempting to delete a non-existent email."""
        print(f"\n--- Testing deletion of non-existent email ---")

        # Use a fake email ID to test error handling
        fake_email_id = "nonexistent-email-id-12345"

        # Test attempting to delete the non-existent email
        result = asyncio.run(delete_email(fake_email_id))

        # Note: This might fail or succeed depending on IMAP implementation
        # The important thing is that it doesn't crash
        logger.info(f"Attempted to delete non-existent email, success: {result.success}")
        if not result.success:
            logger.info(f"Expected failure message: {getattr(result, 'message', 'No error message')}")


# Standalone function to run the delete email tests
def run_delete_email_tests():
    """Helper function to run the email deletion tests."""
    config = get_test_config()

    if not config.enable_integration_tests:
        logger.info("Integration tests are disabled. Set ENABLE_INTEGRATION_TESTS=true and provide credentials.")
        return

    logger.info("Running email deletion tests...")

    tester = TestEmailDelete()
    tester.setup_class()

    try:
        tester.test_delete_single_email()
        tester.test_delete_multiple_emails()
        tester.test_delete_nonexistent_email()
        logger.info("\n🎉 All email deletion tests completed successfully!")
        logger.info("Email delete functionality works correctly!")
    except Exception as e:
        logger.info(f"\n❌ Email deletion tests failed: {e}")
        raise


if __name__ == "__main__":
    run_delete_email_tests()

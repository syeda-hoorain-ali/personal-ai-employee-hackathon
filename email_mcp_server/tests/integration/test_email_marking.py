"""
Integration tests for email marking functionality (read/unread, importance).
"""
import sys
import pytest
import asyncio
import logging

from .config import get_test_config
from email_mcp_server.email_operations.management import mark_email
from email_mcp_server.models.account import EmailAccount, AuthMethod, EmailProvider

logger = logging.getLogger(__name__)


class TestEmailMarking:
    """Integration tests for email marking functionality (read/unread, importance)."""

    def setup_class(self):
        """Setup configuration and check if integration tests are enabled."""
        self.config = get_test_config()

        if not self.config.enable_integration_tests:
            pytest.skip("Integration tests are disabled. Set ENABLE_INTEGRATION_TESTS=true and provide credentials.")

        # Create an email account for testing
        self.account = EmailAccount(
            id="test-account",
            provider=EmailProvider.GMAIL,
            email_address=self.config.email_address,
            auth_method=AuthMethod.PASSWORD
        )

    def test_mark_email_as_read(self):
        """Test marking an email as read."""
        # First, search for an existing email to mark
        from email_mcp_server.protocols.imap_smtp import EmailClient

        # Create email client to search for an email
        account = EmailAccount(
            id="test-account",
            provider=EmailProvider.GMAIL,
            email_address=self.config.email_address,
            auth_method=AuthMethod.PASSWORD
        )

        email_client = EmailClient(account)
        email_client.password = self.config.app_password

        # Connect and list emails in INBOX to get a real email ID
        email_client.connect_imap()
        emails = email_client.search_emails(limit=1, folder="INBOX")

        if not emails:
            # If no emails exist, send a test email first
            from email_mcp_server.email_operations.send import send_email

            params = {
                "to": [self.config.email_address],
                "subject": "Test Email for Marking Test",
                "body": "This is a test email sent to facilitate email marking tests."
            }

            send_result = asyncio.run(send_email(params))
            assert send_result.success, "Failed to send test email"

            # Wait briefly for the email to arrive
            import time
            time.sleep(2)

            # Search again
            emails = email_client.search_emails(limit=1, folder="INBOX")
            assert emails, "Should have at least one email after sending test email"

        # Use the ID of the first email found
        email_id = emails[0].id

        # Test marking email as read
        result = asyncio.run(mark_email(email_id, read=True))

        # Verify the result
        assert result.success, f"Failed to mark email as read: {getattr(result, 'message', 'Unknown error')}"
        assert "read_status" in result.updated_fields, "Read status should be in updated fields"

        print(f"✓ Email {email_id} marked as read successfully")

    def test_mark_email_as_unread(self):
        """Test marking an email as unread."""
        # First, search for an existing email to mark
        from email_mcp_server.protocols.imap_smtp import EmailClient

        # Create email client to search for an email
        account = EmailAccount(
            id="test-account",
            provider=EmailProvider.GMAIL,
            email_address=self.config.email_address,
            auth_method=AuthMethod.PASSWORD
        )

        email_client = EmailClient(account)
        email_client.password = self.config.app_password

        # Connect and list emails in INBOX to get a real email ID
        email_client.connect_imap()
        emails = email_client.search_emails(limit=1, folder="INBOX")

        if not emails:
            # If no emails exist, send a test email first
            from email_mcp_server.email_operations.send import send_email

            params = {
                "to": [self.config.email_address],
                "subject": "Test Email for Marking Test",
                "body": "This is a test email sent to facilitate email marking tests."
            }

            send_result = asyncio.run(send_email(params))
            assert send_result.success, "Failed to send test email"

            # Wait briefly for the email to arrive
            import time
            time.sleep(2)

            # Search again
            emails = email_client.search_emails(limit=1, folder="INBOX")
            assert emails, "Should have at least one email after sending test email"

        # Use the ID of the first email found
        email_id = emails[0].id

        # Test marking email as unread
        result = asyncio.run(mark_email(email_id, read=False))

        # Verify the result
        assert result.success, f"Failed to mark email as unread: {getattr(result, 'message', 'Unknown error')}"
        assert "read_status" in result.updated_fields, "Read status should be in updated fields"

        print(f"✓ Email {email_id} marked as unread successfully")

    def test_mark_email_importance_low(self):
        """Test marking an email with low importance."""
        # First, search for an existing email to mark
        from email_mcp_server.protocols.imap_smtp import EmailClient

        # Create email client to search for an email
        account = EmailAccount(
            id="test-account",
            provider=EmailProvider.GMAIL,
            email_address=self.config.email_address,
            auth_method=AuthMethod.PASSWORD
        )

        email_client = EmailClient(account)
        email_client.password = self.config.app_password

        # Connect and list emails in INBOX to get a real email ID
        email_client.connect_imap()
        emails = email_client.search_emails(limit=1, folder="INBOX")

        if not emails:
            # If no emails exist, send a test email first
            from email_mcp_server.email_operations.send import send_email

            params = {
                "to": [self.config.email_address],
                "subject": "Test Email for Marking Test",
                "body": "This is a test email sent to facilitate email marking tests."
            }

            send_result = asyncio.run(send_email(params))
            assert send_result.success, "Failed to send test email"

            # Wait briefly for the email to arrive
            import time
            time.sleep(2)

            # Search again
            emails = email_client.search_emails(limit=1, folder="INBOX")
            assert emails, "Should have at least one email after sending test email"

        # Use the ID of the first email found
        email_id = emails[0].id

        # Test marking email with low importance
        result = asyncio.run(mark_email(email_id, importance="low"))

        # Verify the result
        assert result.success, f"Failed to mark email importance as low: {getattr(result, 'message', 'Unknown error')}"
        assert "importance" in result.updated_fields, "Importance should be in updated fields"

        print(f"✓ Email {email_id} marked with low importance successfully")

    def test_mark_email_importance_normal(self):
        """Test marking an email with normal importance."""
        # First, search for an existing email to mark
        from email_mcp_server.protocols.imap_smtp import EmailClient

        # Create email client to search for an email
        account = EmailAccount(
            id="test-account",
            provider=EmailProvider.GMAIL,
            email_address=self.config.email_address,
            auth_method=AuthMethod.PASSWORD
        )

        email_client = EmailClient(account)
        email_client.password = self.config.app_password

        # Connect and list emails in INBOX to get a real email ID
        email_client.connect_imap()
        emails = email_client.search_emails(limit=1, folder="INBOX")

        if not emails:
            # If no emails exist, send a test email first
            from email_mcp_server.email_operations.send import send_email

            params = {
                "to": [self.config.email_address],
                "subject": "Test Email for Marking Test",
                "body": "This is a test email sent to facilitate email marking tests."
            }

            send_result = asyncio.run(send_email(params))
            assert send_result.success, "Failed to send test email"

            # Wait briefly for the email to arrive
            import time
            time.sleep(2)

            # Search again
            emails = email_client.search_emails(limit=1, folder="INBOX")
            assert emails, "Should have at least one email after sending test email"

        # Use the ID of the first email found
        email_id = emails[0].id

        # Test marking email with normal importance
        result = asyncio.run(mark_email(email_id, importance="normal"))

        # Verify the result
        assert result.success, f"Failed to mark email importance as normal: {getattr(result, 'message', 'Unknown error')}"
        assert "importance" in result.updated_fields, "Importance should be in updated fields"

        print(f"✓ Email {email_id} marked with normal importance successfully")

    def test_mark_email_importance_high(self):
        """Test marking an email with high importance."""
        # First, search for an existing email to mark
        from email_mcp_server.protocols.imap_smtp import EmailClient

        # Create email client to search for an email
        account = EmailAccount(
            id="test-account",
            provider=EmailProvider.GMAIL,
            email_address=self.config.email_address,
            auth_method=AuthMethod.PASSWORD
        )

        email_client = EmailClient(account)
        email_client.password = self.config.app_password

        # Connect and list emails in INBOX to get a real email ID
        email_client.connect_imap()
        emails = email_client.search_emails(limit=1, folder="INBOX")

        if not emails:
            # If no emails exist, send a test email first
            from email_mcp_server.email_operations.send import send_email

            params = {
                "to": [self.config.email_address],
                "subject": "Test Email for Marking Test",
                "body": "This is a test email sent to facilitate email marking tests."
            }

            send_result = asyncio.run(send_email(params))
            assert send_result.success, "Failed to send test email"

            # Wait briefly for the email to arrive
            import time
            time.sleep(2)

            # Search again
            emails = email_client.search_emails(limit=1, folder="INBOX")
            assert emails, "Should have at least one email after sending test email"

        # Use the ID of the first email found
        email_id = emails[0].id

        # Test marking email with high importance
        result = asyncio.run(mark_email(email_id, importance="high"))

        # Verify the result
        assert result.success, f"Failed to mark email importance as high: {getattr(result, 'message', 'Unknown error')}"
        assert "importance" in result.updated_fields, "Importance should be in updated fields"

        print(f"✓ Email {email_id} marked with high importance successfully")

    def test_mark_email_both_read_and_importance(self):
        """Test marking an email with both read status and importance."""
        # First, search for an existing email to mark
        from email_mcp_server.protocols.imap_smtp import EmailClient

        # Create email client to search for an email
        account = EmailAccount(
            id="test-account",
            provider=EmailProvider.GMAIL,
            email_address=self.config.email_address,
            auth_method=AuthMethod.PASSWORD
        )

        email_client = EmailClient(account)
        email_client.password = self.config.app_password

        # Connect and list emails in INBOX to get a real email ID
        email_client.connect_imap()
        emails = email_client.search_emails(limit=1, folder="INBOX")

        if not emails:
            # If no emails exist, send a test email first
            from email_mcp_server.email_operations.send import send_email

            params = {
                "to": [self.config.email_address],
                "subject": "Test Email for Marking Test",
                "body": "This is a test email sent to facilitate email marking tests."
            }

            send_result = asyncio.run(send_email(params))
            assert send_result.success, "Failed to send test email"

            # Wait briefly for the email to arrive
            import time
            time.sleep(2)

            # Search again
            emails = email_client.search_emails(limit=1, folder="INBOX")
            assert emails, "Should have at least one email after sending test email"

        # Use the ID of the first email found
        email_id = emails[0].id

        # Test marking email with both read status and importance
        result = asyncio.run(mark_email(email_id, read=True, importance="high"))

        # Verify the result
        assert result.success, f"Failed to mark email with read status and importance: {getattr(result, 'message', 'Unknown error')}"
        assert "read_status" in result.updated_fields, "Read status should be in updated fields"
        assert "importance" in result.updated_fields, "Importance should be in updated fields"

        print(f"✓ Email {email_id} marked with read status and high importance successfully")

    def test_invalid_importance_level(self):
        """Test that invalid importance levels are rejected."""
        email_id = "test-message-id-12345"

        # Test with invalid importance level
        result = asyncio.run(mark_email(email_id, importance="invalid_level"))

        # Verify the result
        assert not result.success, "Should fail with invalid importance level"
        assert "Invalid importance level" in result.message, "Should return error for invalid importance level"

        print(f"✓ Invalid importance level correctly rejected")


# Standalone function to run the email marking tests
def run_email_marking_tests():
    """Helper function to run the email marking tests."""
    config = get_test_config()

    if not config.enable_integration_tests:
        print("Integration tests are disabled. Set ENABLE_INTEGRATION_TESTS=true and provide credentials.")
        return

    print("Running email marking tests...")

    tester = TestEmailMarking()
    tester.setup_class()

    try:
        tester.test_mark_email_as_read()
        tester.test_mark_email_as_unread()
        tester.test_mark_email_importance_low()
        tester.test_mark_email_importance_normal()
        tester.test_mark_email_importance_high()
        tester.test_mark_email_both_read_and_importance()
        tester.test_invalid_importance_level()
        logger.info("All email marking tests completed successfully!")
    except Exception as e:
        logger.info(f"Email marking tests failed: {e}")
        raise


if __name__ == "__main__":
    run_email_marking_tests()

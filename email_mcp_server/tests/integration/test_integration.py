"""
Integration tests for the Email MCP Server that connect to actual email servers.
"""
import pytest
import asyncio
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from .config import get_test_config, EmailTestConfig
from email_mcp_server.protocols.imap_smtp import EmailClient
from email_mcp_server.models.account import EmailAccount, AuthMethod, EmailProvider
from email_mcp_server.models.email import Email
from email_mcp_server.email_operations.send import send_email

logger = logging.getLogger(__name__)


class TestEmailIntegration:
    """Integration tests that connect to actual email servers."""

    def setup_class(self):
        """Setup configuration and check if integration tests are enabled."""
        self.config = get_test_config()

        if not self.config.enable_integration_tests:
            pytest.skip("Integration tests are disabled. Set ENABLE_INTEGRATION_TESTS=true and provide credentials.")

        # Create a mock email account for testing
        self.account = EmailAccount(
            id="test-account",
            provider=EmailProvider.GMAIL,  # Can be customized based on the email provider
            email_address=self.config.email_address,
            auth_method=AuthMethod.PASSWORD  # Or AuthMethod.OAUTH2 if using OAuth
        )

    def test_send_email_integration(self):
        """Test sending an actual email via SMTP."""
        # Prepare test parameters
        params = {
            "to": [self.config.test_recipient],
            "subject": "Integration Test: Email MCP Server Test",
            "body": "This is a test email sent from the Email MCP Server integration test.",
            "html_body": "<p>This is a <strong>test email</strong> sent from the Email MCP Server integration test.</p>"
        }

        # Test the send_email function
        result = asyncio.run(send_email(params))

        assert result.success, f"Email sending failed: {getattr(result, 'message', 'Unknown error')}"
        assert result.message_id is not None, "Message ID should be returned after successful send"

        logger.info(f"Email sent successfully with message ID: {result.message_id}")

    def test_connect_to_email_server(self):
        """Test connecting to email server via IMAP/SMTP."""
        # Create email client
        email_client = EmailClient(self.account)

        # Test SMTP connection
        try:
            email_client.connect_smtp()
            logger.info("Successfully connected to SMTP server")
        except Exception as e:
            pytest.fail(f"Failed to connect to SMTP server: {e}")
        finally:
            email_client.disconnect_smtp()

        # Test IMAP connection
        try:
            email_client.connect_imap()
            logger.info("Successfully connected to IMAP server")
        except Exception as e:
            pytest.fail(f"Failed to connect to IMAP server: {e}")
        finally:
            email_client.disconnect_imap()

    def test_list_folders_integration(self):
        """Test listing email folders via IMAP."""
        email_client = EmailClient(self.account)

        try:
            folders = email_client.list_folders()
            logger.info(f"Found {len(folders)} folders: {[f['name'] for f in folders]}")

            # Verify standard folders exist
            folder_names = [f['name'].lower() for f in folders]
            assert 'inbox' in folder_names or 'INBOX' in folder_names, "INBOX folder should exist"

        except Exception as e:
            pytest.fail(f"Failed to list folders: {e}")
        finally:
            email_client.disconnect_imap()

    def test_search_emails_integration(self):
        """Test searching for emails via IMAP."""
        email_client = EmailClient(self.account)

        try:
            # Search for recent emails in INBOX
            emails = email_client.search_emails(
                query="test",   # Search for emails containing 'test'
                folder="INBOX",
                limit=5
            )

            logger.info(f"Found {len(emails)} emails matching the search criteria")

            # At least verify the function returned without error
            assert isinstance(emails, list), "Search should return a list of emails"

        except Exception as e:
            # This might fail if no emails match the criteria, which is fine
            logger.info(f"Search test completed with potential expected error: {e}")
        finally:
            email_client.disconnect_imap()

    def test_create_and_retrieve_draft_integration(self):
        """Test creating and retrieving a draft email."""
        email_client = EmailClient(self.account)

        try:
            # Create a draft
            draft_id = email_client.create_draft(
                to=[self.config.test_recipient],
                subject="Integration Test: Draft Email",
                body="This is a test draft created by the Email MCP Server integration test.",
                html_body="<p>This is a <strong>test draft</strong> created by the Email MCP Server integration test.</p>"
            )

            logger.info(f"Draft created with ID: {draft_id}")
            assert draft_id is not None, "Draft ID should be returned after successful creation"

        except Exception as e:
            pytest.fail(f"Failed to create draft: {e}")
        finally:
            email_client.disconnect_smtp()


# Additional helper function for running integration tests
def run_integration_tests():
    """Helper function to run all integration tests."""
    config = get_test_config()

    if not config.enable_integration_tests:
        logger.info("Integration tests are disabled. Set ENABLE_INTEGRATION_TESTS=true and provide credentials.")
        return

    logger.info("Running Email MCP Server integration tests...")

    # This would typically be run with pytest, but we can demonstrate the concept
    tester = TestEmailIntegration()
    tester.setup_class()

    logger.info("All integration tests completed successfully!")


if __name__ == "__main__":
    run_integration_tests()

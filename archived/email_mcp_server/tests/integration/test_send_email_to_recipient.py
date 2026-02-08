"""
Generic integration test for sending an email to recipient.
"""
import pytest
import asyncio
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from .config import get_test_config
from email_mcp_server.models.account import EmailAccount, AuthMethod, EmailProvider
from email_mcp_server.email_operations.send import send_email
from .config import test_config

class TestSendEmailToRecipient:
    """Integration test for sending an email to recipient."""

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

    def test_send_email_to_configurable_recipient(self):
        """Test sending an email to recipient."""
        # Prepare test parameters for sending email to recipient
        test_recipient = test_config.test_recipient
        params = {
            "to": [test_recipient],  # The specific recipient from environment
            "subject": "Integration Test: Email to Recipient",
            "body": f"This is a test email sent to {test_recipient} from the Email MCP Server integration test.",
            "html_body": f"<p>This is a <strong>test email</strong> sent to {test_recipient} from the Email MCP Server integration test.</p>"
        }

        # Test the send_email function
        result = asyncio.run(send_email(params))

        # Verify the result
        assert result.success, f"Email sending to {test_recipient} failed: {getattr(result, 'message', 'Unknown error')}"
        assert result.message_id is not None, "Message ID should be returned after successful send"

        print(f"Email sent successfully to {test_recipient} with message ID: {result.message_id}")
        print(f"Test completed: Sent email from {self.config.email_address} to {test_recipient}")

    def test_send_email_with_cc_bcc_to_recipient(self):
        """Test sending an email to a configurable recipient with CC and BCC."""
        # Prepare test parameters for sending email to configurable recipient with CC/BCC
        test_recipient = test_config.test_recipient
        params = {
            "to": [test_recipient],  # Primary recipient from environment
            "cc": [self.config.test_recipient],  # CC to test recipient
            "bcc": [self.config.email_address],  # BCC to sender
            "subject": "Integration Test: Email to Configurable Recipient with CC/BCC",
            "body": f"This is a test email with CC and BCC sent to {test_recipient} from the Email MCP Server integration test.",
            "html_body": f"<p>This is a <strong>test email</strong> with CC and BCC sent to {test_recipient} from the Email MCP Server integration test.</p>"
        }

        # Test the send_email function
        result = asyncio.run(send_email(params))

        # Verify the result
        assert result.success, f"Email sending to {test_recipient} with CC/BCC failed: {getattr(result, 'message', 'Unknown error')}"
        assert result.message_id is not None, "Message ID should be returned after successful send"

        print(f"Email with CC/BCC sent successfully to {test_recipient} with message ID: {result.message_id}")


# Standalone function to run just this test
def run_send_email_to_recipient_test():
    """Helper function to run the specific send email test to recipient."""
    config = get_test_config()

    if not config.enable_integration_tests:
        print("Integration test is disabled. Set ENABLE_INTEGRATION_TESTS=true and provide credentials.")
        return

    test_recipient = test_config.test_recipient
    print(f"Running email send test to recipient {test_recipient}...")

    tester = TestSendEmailToRecipient()
    tester.setup_class()

    try:
        tester.test_send_email_to_configurable_recipient()
        tester.test_send_email_with_cc_bcc_to_recipient()
        print(f"Email send test to {test_recipient} completed successfully!")
    except Exception as e:
        print(f"Email send test to {test_recipient} failed: {e}")
        raise


if __name__ == "__main__":
    run_send_email_to_recipient_test()
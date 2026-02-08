"""
Integration test for sending an email to the same account (self).
"""
import pytest
import asyncio
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from .config import get_test_config

from email_mcp_server.models.account import EmailAccount, EmailProvider, AuthMethod
from email_mcp_server.email_operations.send import send_email


class TestSendEmailToSelf:
    """Integration test for sending an email to the same account (self)."""

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

    def test_send_email_to_same_account(self):
        """Test sending an email to the same account (self)."""
        # Prepare test parameters for sending email to the same account
        same_account = self.config.email_address
        params = {
            "to": [same_account],  # Send to the same account
            "subject": "Integration Test: Email to Same Account",
            "body": f"This is a test email sent to {same_account} from the Email MCP Server integration test.",
            "html_body": f"<p>This is a <strong>test email</strong> sent to {same_account} from the Email MCP Server integration test.</p>"
        }

        # Test the send_email function
        result = asyncio.run(send_email(params))

        # Verify the result
        assert result.success, f"Email sending to same account {same_account} failed: {getattr(result, 'message', 'Unknown error')}"
        assert result.message_id is not None, "Message ID should be returned after successful send"

        print(f"Email sent successfully to same account {same_account} with message ID: {result.message_id}")
        print(f"Test completed: Sent email from {self.config.email_address} to {same_account}")

    def test_send_email_with_cc_bcc_to_same_account(self):
        """Test sending an email to the same account with CC and BCC."""
        # Prepare test parameters for sending email to same account with CC/BCC
        same_account = self.config.email_address
        params = {
            "to": [same_account],  # Send to the same account
            "cc": [self.config.test_recipient],  # CC to test recipient
            "bcc": [self.config.email_address],  # BCC to sender
            "subject": "Integration Test: Email to Same Account with CC/BCC",
            "body": f"This is a test email with CC and BCC sent to {same_account} from the Email MCP Server integration test.",
            "html_body": f"<p>This is a <strong>test email</strong> with CC and BCC sent to {same_account} from the Email MCP Server integration test.</p>"
        }

        # Test the send_email function
        result = asyncio.run(send_email(params))

        # Verify the result
        assert result.success, f"Email sending to same account {same_account} with CC/BCC failed: {getattr(result, 'message', 'Unknown error')}"
        assert result.message_id is not None, "Message ID should be returned after successful send"

        print(f"Email with CC/BCC sent successfully to same account {same_account} with message ID: {result.message_id}")


# Standalone function to run just this test
def run_send_email_to_self_test():
    """Helper function to run the send email to self test."""
    config = get_test_config()

    if not config.enable_integration_tests:
        print("Integration test is disabled. Set ENABLE_INTEGRATION_TESTS=true and provide credentials.")
        return

    print("Running email send test to same account...")

    tester = TestSendEmailToSelf()
    tester.setup_class()

    try:
        tester.test_send_email_to_same_account()
        tester.test_send_email_with_cc_bcc_to_same_account()
        print("Email send test to same account completed successfully!")
    except Exception as e:
        print(f"Email send test to same account failed: {e}")
        raise


if __name__ == "__main__":
    run_send_email_to_self_test()

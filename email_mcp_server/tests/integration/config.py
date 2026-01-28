"""
Configuration for integration tests that connect to actual email servers.
"""
from dataclasses import dataclass
from dotenv import load_dotenv
from email_mcp_server.config.settings import settings

# Load environment variables from .env file
load_dotenv()


@dataclass
class EmailTestConfig:
    """Configuration for email integration tests."""
    # Email account settings
    email_address: str = ""
    email_password: str = ""
    app_password: str = ""  # For Gmail and other providers

    # Server settings
    smtp_server: str = ""
    smtp_port: int = 587
    imap_server: str = ""
    imap_port: int = 993

    # Test settings
    test_recipient: str = ""
    enable_integration_tests: bool = False

    def __post_init__(self):
        """Initialize values from settings if not provided."""
        if not self.email_address:
            self.email_address = settings.test_email_address or settings.email_address or ""
        if not self.email_password:
            self.email_password = settings.test_email_password or settings.email_password or ""
        if not self.app_password:
            self.app_password = settings.test_email_app_password or settings.email_password or ""
        if not self.smtp_server:
            self.smtp_server = settings.test_smtp_server or ""
        if self.smtp_port == 587:  # Default value
            self.smtp_port = settings.test_smtp_port or 587
        if not self.imap_server:
            self.imap_server = settings.test_imap_server or ""
        if self.imap_port == 993:  # Default value
            self.imap_port = settings.test_imap_port or 993
        if not self.test_recipient:
            self.test_recipient = settings.test_recipient or settings.email_address or ""
        if self.enable_integration_tests is False:  # Default value
            self.enable_integration_tests = settings.enable_integration_tests or False

    def validate(self) -> 'EmailTestConfig':
        """Validate that all required configuration is present."""
        if not self.enable_integration_tests:
            return self

        if not self.email_address:
            raise ValueError("TEST_EMAIL_ADDRESS or EMAIL_ADDRESS setting is required")

        if not (self.email_password or self.app_password):
            raise ValueError("Either TEST_EMAIL_PASSWORD, EMAIL_PASSWORD, or TEST_EMAIL_APP_PASSWORD setting is required")

        if not self.test_recipient:
            raise ValueError("TEST_RECIPIENT or EMAIL_ADDRESS setting is required")

        return self


# Global config instance
test_config = EmailTestConfig()


def get_test_config() -> EmailTestConfig:
    """Get the test configuration."""
    return test_config

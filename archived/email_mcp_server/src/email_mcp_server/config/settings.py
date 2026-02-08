"""
Configuration settings for the Email MCP Server using Pydantic BaseSettings.
"""
from pydantic_settings import BaseSettings
from typing import Optional


class EmailSettings(BaseSettings):
    """Email configuration settings."""

    # Email account settings
    email_address: Optional[str] = None
    email_password: Optional[str] = None
    test_email_address: Optional[str] = None
    test_email_app_password: Optional[str] = None

    # Gmail specific settings
    gmail_client_id: Optional[str] = None
    gmail_client_secret: Optional[str] = None

    # SMTP settings
    smtp_timeout: int = 30
    smtp_max_retries: int = 3

    # IMAP settings
    imap_timeout: int = 30
    imap_max_retries: int = 3

    # Security settings
    max_attachment_size_mb: int = 25
    max_total_attachment_size_mb: int = 35

    # Generic SMTP/IMAP server settings
    smtp_server: str = "localhost"
    smtp_port: int = 587
    imap_server: str = "localhost"
    imap_port: int = 993
    use_tls: bool = True
    oauth_support: bool = False

    # JWT and authentication settings
    jwt_secret_key: Optional[str] = None
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    # OAuth provider settings
    gmail_client_id: Optional[str] = None
    gmail_client_secret: Optional[str] = None
    gmail_redirect_uri: str = "http://localhost:8080/callback"
    outlook_client_id: Optional[str] = None
    outlook_client_secret: Optional[str] = None
    outlook_redirect_uri: str = "http://localhost:8080/callback"
    yahoo_client_id: Optional[str] = None
    yahoo_client_secret: Optional[str] = None
    yahoo_redirect_uri: str = "http://localhost:8080/callback"

    # Test settings
    test_email_password: Optional[str] = None
    test_smtp_server: str = "smtp.gmail.com"
    test_smtp_port: int = 587
    test_imap_server: str = "imap.gmail.com"
    test_imap_port: int = 993
    test_recipient: Optional[str] = None
    enable_integration_tests: bool = False

    class Config:
        case_sensitive = False
        # Load from .env file if it exists
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"  # ignore extra fields that are not explicitly defined


# Global instance of settings
settings = EmailSettings()

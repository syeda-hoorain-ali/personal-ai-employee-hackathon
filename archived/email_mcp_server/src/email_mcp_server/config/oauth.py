"""
Configuration templates and OAuth settings for email providers.
"""
from typing import Dict, Optional
from pydantic import BaseModel
from .settings import settings


class OAuthConfig(BaseModel):
    """Configuration for OAuth 2.0 authentication."""
    client_id: str
    client_secret: str
    redirect_uri: str
    scopes: list[str]
    authorization_url: str
    token_url: str


class ProviderConfigTemplate(BaseModel):
    """Configuration template for an email provider."""
    provider_name: str
    display_name: str
    smtp_server: str
    smtp_port: int
    imap_server: str
    imap_port: int
    oauth_config: Optional[OAuthConfig] = None
    default: bool = False


class ConfigProvider:
    """Provides configuration templates for different email providers."""

    def __init__(self):
        self.templates: Dict[str, ProviderConfigTemplate] = {}
        self._load_default_templates()

    def _load_default_templates(self):
        """Load default configuration templates for common providers."""

        # Gmail configuration template
        gmail_oauth = OAuthConfig(
            client_id=settings.gmail_client_id or '',
            client_secret=settings.gmail_client_secret or '',
            redirect_uri=settings.gmail_redirect_uri,
            scopes=['https://www.googleapis.com/auth/gmail.send',
                    'https://www.googleapis.com/auth/gmail.readonly'],
            authorization_url='https://accounts.google.com/o/oauth2/auth',
            token_url='https://oauth2.googleapis.com/token'
        )

        self.templates['gmail'] = ProviderConfigTemplate(
            provider_name='gmail',
            display_name='Gmail',
            smtp_server='smtp.gmail.com',
            smtp_port=587,
            imap_server='imap.gmail.com',
            imap_port=993,
            oauth_config=gmail_oauth,
            default=True
        )

        # Outlook configuration template
        outlook_oauth = OAuthConfig(
            client_id=settings.outlook_client_id or '',
            client_secret=settings.outlook_client_secret or '',
            redirect_uri=settings.outlook_redirect_uri,
            scopes=['https://graph.microsoft.com/Mail.Send',
                    'https://graph.microsoft.com/Mail.Read'],
            authorization_url='https://login.microsoftonline.com/common/oauth2/v2.0/authorize',
            token_url='https://login.microsoftonline.com/common/oauth2/v2.0/token'
        )

        self.templates['outlook'] = ProviderConfigTemplate(
            provider_name='outlook',
            display_name='Outlook/Exchange',
            smtp_server='smtp-mail.outlook.com',
            smtp_port=587,
            imap_server='outlook.office365.com',
            imap_port=993,
            oauth_config=outlook_oauth,
            default=True
        )

        # Yahoo configuration template
        yahoo_oauth = OAuthConfig(
            client_id=settings.yahoo_client_id or '',
            client_secret=settings.yahoo_client_secret or '',
            redirect_uri=settings.yahoo_redirect_uri,
            scopes=['mail-w'],
            authorization_url='https://api.login.yahoo.com/oauth2/request_auth',
            token_url='https://api.login.yahoo.com/oauth2/get_token'
        )

        self.templates['yahoo'] = ProviderConfigTemplate(
            provider_name='yahoo',
            display_name='Yahoo Mail',
            smtp_server='smtp.mail.yahoo.com',
            smtp_port=587,
            imap_server='imap.mail.yahoo.com',
            imap_port=993,
            oauth_config=yahoo_oauth,
            default=True
        )

        # Generic configuration template
        self.templates['generic'] = ProviderConfigTemplate(
            provider_name='generic',
            display_name='Generic IMAP/SMTP',
            smtp_server=settings.smtp_server or 'smtp.example.com',
            smtp_port=settings.smtp_port or 587,
            imap_server=settings.imap_server or 'imap.example.com',
            imap_port=settings.imap_port or 993,
            oauth_config=None,
            default=False
        )

    def get_template(self, provider_name: str) -> Optional[ProviderConfigTemplate]:
        """
        Get a configuration template for a provider.

        Args:
            provider_name: Name of the email provider

        Returns:
            Provider configuration template if found, None otherwise
        """
        return self.templates.get(provider_name.lower())

    def get_all_templates(self) -> Dict[str, ProviderConfigTemplate]:
        """
        Get all available configuration templates.

        Returns:
            Dictionary of all provider configuration templates
        """
        return self.templates

    def get_default_templates(self) -> Dict[str, ProviderConfigTemplate]:
        """
        Get only the default configuration templates.

        Returns:
            Dictionary of default provider configuration templates
        """
        return {name: template for name, template in self.templates.items() if template.default}


# Global configuration provider instance
config_provider = ConfigProvider()


def get_provider_template(provider_name: str) -> Optional[ProviderConfigTemplate]:
    """
    Get a configuration template for a provider.

    Args:
        provider_name: Name of the email provider

    Returns:
        Provider configuration template if found, None otherwise
    """
    return config_provider.get_template(provider_name)


def get_all_provider_templates() -> Dict[str, ProviderConfigTemplate]:
    """
    Get all available configuration templates.

    Returns:
        Dictionary of all provider configuration templates
    """
    return config_provider.get_all_templates()


def get_default_provider_templates() -> Dict[str, ProviderConfigTemplate]:
    """
    Get only the default configuration templates.

    Returns:
        Dictionary of default provider configuration templates
    """
    return config_provider.get_default_templates()

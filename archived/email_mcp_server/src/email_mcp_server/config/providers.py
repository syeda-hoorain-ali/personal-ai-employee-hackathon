"""
Configuration handler for email providers.
"""
from typing import Dict, Optional
from pydantic import BaseModel
from .settings import settings


class ProviderConfig(BaseModel):
    """Configuration for an email provider."""
    smtp_server: str
    smtp_port: int
    imap_server: str
    imap_port: int
    use_tls: bool = True
    oauth_support: bool = False


class ProviderManager:
    """Manages configurations for different email providers."""

    def __init__(self):
        self._configs: Dict[str, ProviderConfig] = {}
        self._setup_default_configs()

    def _setup_default_configs(self):
        """Set up default configurations for common email providers."""
        # Gmail configuration
        self._configs['gmail'] = ProviderConfig(
            smtp_server='smtp.gmail.com',
            smtp_port=587,
            imap_server='imap.gmail.com',
            imap_port=993,
            use_tls=True,
            oauth_support=True
        )

        # Outlook/Hotmail configuration
        self._configs['outlook'] = ProviderConfig(
            smtp_server='smtp-mail.outlook.com',
            smtp_port=587,
            imap_server='outlook.office365.com',
            imap_port=993,
            use_tls=True,
            oauth_support=True
        )

        # Yahoo configuration
        self._configs['yahoo'] = ProviderConfig(
            smtp_server='smtp.mail.yahoo.com',
            smtp_port=587,
            imap_server='imap.mail.yahoo.com',
            imap_port=993,
            use_tls=True,
            oauth_support=True
        )

        # Generic configuration
        self._configs['other'] = ProviderConfig(
            smtp_server=settings.smtp_server,
            smtp_port=settings.smtp_port,
            imap_server=settings.imap_server,
            imap_port=settings.imap_port,
            use_tls=settings.use_tls,
            oauth_support=settings.oauth_support
        )

    def get_config(self, provider: str) -> Optional[ProviderConfig]:
        """
        Get configuration for a specific provider.

        Args:
            provider: Name of the email provider

        Returns:
            Provider configuration if found, None otherwise
        """
        return self._configs.get(provider.lower())

    def add_custom_config(self, provider: str, config: ProviderConfig):
        """
        Add a custom configuration for a provider.

        Args:
            provider: Name of the email provider
            config: Provider configuration
        """
        self._configs[provider.lower()] = config

    def get_available_providers(self) -> list:
        """
        Get list of available email providers.

        Returns:
            List of available provider names
        """
        return list(self._configs.keys())


# Global provider manager instance
provider_manager = ProviderManager()


def get_provider_config(provider: str) -> Optional[ProviderConfig]:
    """
    Get configuration for a specific provider.

    Args:
        provider: Name of the email provider

    Returns:
        Provider configuration if found, None otherwise
    """
    return provider_manager.get_config(provider)


def get_available_providers() -> list:
    """
    Get list of available email providers.

    Returns:
        List of available provider names
    """
    return provider_manager.get_available_providers()

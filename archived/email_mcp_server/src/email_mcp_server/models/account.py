"""
Email Account model representing an email account configuration.
"""
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime
from enum import Enum


class AuthMethod(str, Enum):
    """Authentication method for email accounts."""
    OAUTH2 = "oauth2"
    PASSWORD = "password"


class EmailProvider(str, Enum):
    """Supported email providers."""
    GMAIL = "gmail"
    OUTLOOK = "outlook"
    YAHOO = "yahoo"
    OTHER = "other"


class EmailAccount(BaseModel):
    """
    Represents an email account configuration.

    Attributes:
        id: Unique identifier for the account
        provider: Email provider name
        email_address: The email address
        auth_method: Authentication method used
        config_template: Configuration template used for setup
        last_connected: Last successful connection timestamp
    """
    id: str
    provider: EmailProvider
    email_address: EmailStr
    auth_method: AuthMethod
    config_template: Optional[str] = None
    last_connected: Optional[datetime] = None

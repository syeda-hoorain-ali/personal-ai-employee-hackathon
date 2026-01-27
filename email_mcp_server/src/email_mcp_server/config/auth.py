"""
Authentication handler for email accounts.
"""
import jwt
from typing import Optional
from datetime import datetime, timedelta
from enum import Enum
from pydantic import BaseModel
from dotenv import load_dotenv
from ..models.account import AuthMethod, EmailAccount, EmailProvider
from ..config.settings import settings


# Load environment variables
load_dotenv()


class TokenType(str, Enum):
    """Types of authentication tokens."""
    ACCESS = "access"
    REFRESH = "refresh"
    OAUTH = "oauth"


class TokenData(BaseModel):
    """Data contained in an authentication token."""
    account_id: str
    email: str
    exp: Optional[datetime] = None
    iat: Optional[datetime] = None


class AuthHandler:
    """Handles authentication for email accounts."""

    def __init__(self):
        self.secret_key = settings.jwt_secret_key or 'your-default-secret-key-change-this'
        self.algorithm = settings.jwt_algorithm or 'HS256'
        self.access_token_expire_minutes = settings.access_token_expire_minutes or 30
        self.refresh_token_expire_days = settings.refresh_token_expire_days or 7

    def create_access_token(self, data: TokenData) -> str:
        """
        Create an access token.

        Args:
            data: Token data

        Returns:
            Encoded access token
        """
        to_encode = data.dict()
        expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        to_encode.update({"exp": expire, "token_type": TokenType.ACCESS})
        return jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)

    def create_refresh_token(self, data: TokenData) -> str:
        """
        Create a refresh token.

        Args:
            data: Token data

        Returns:
            Encoded refresh token
        """
        to_encode = data.dict()
        expire = datetime.utcnow() + timedelta(days=self.refresh_token_expire_days)
        to_encode.update({"exp": expire, "token_type": TokenType.REFRESH})
        return jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)

    def verify_token(self, token: str) -> Optional[TokenData]:
        """
        Verify an authentication token.

        Args:
            token: Token to verify

        Returns:
            Token data if valid, None otherwise
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            token_data = TokenData(**payload)

            # Check if token is expired
            if token_data.exp and datetime.fromtimestamp(token_data.exp.timestamp()) < datetime.utcnow():
                return None

            return token_data
        except jwt.ExpiredSignatureError:
            return None
        except jwt.PyJWTError:
            return None

    def authenticate_account(self, email: str, password: Optional[str] = None,
                           oauth_token: Optional[str] = None) -> Optional[EmailAccount]:
        """
        Authenticate an email account using either password or OAuth token.

        Args:
            email: Email address to authenticate
            password: Password for traditional authentication
            oauth_token: OAuth token for OAuth authentication

        Returns:
            EmailAccount if authentication successful, None otherwise
        """
        # This is a simplified implementation
        # In a real implementation, you would validate credentials against the email provider

        if not email:
            return None

        # Determine authentication method based on provided credentials
        if oauth_token:
            auth_method = AuthMethod.OAUTH2
            # In a real implementation, you would validate the OAuth token
            # For now, we'll just check if it's provided and not empty
            if not oauth_token.strip():
                return None
        elif password:
            auth_method = AuthMethod.PASSWORD
            # In a real implementation, you would validate the password
            # For now, we'll just check if it's provided and not empty
            if not password.strip():
                return None
        else:
            # No credentials provided
            return None

        # Create a temporary account ID (in real implementation, this would come from DB)
        import uuid
        account_id = str(uuid.uuid4())

        # Return a basic EmailAccount object
        account = EmailAccount(
            id=account_id,
            provider=EmailProvider(self._detect_provider_from_email(email)),
            email_address=email,
            auth_method=auth_method
        )

        return account

    def _detect_provider_from_email(self, email: str) -> str:
        """
        Detect email provider from email address.

        Args:
            email: Email address

        Returns:
            Detected provider name
        """
        email_lower = email.lower()
        if '@gmail.com' in email_lower:
            return 'gmail'
        elif '@outlook.com' in email_lower or '@hotmail.com' in email_lower or '@live.com' in email_lower:
            return 'outlook'
        elif '@yahoo.com' in email_lower:
            return 'yahoo'
        else:
            return 'other'

    def refresh_access_token(self, refresh_token: str) -> Optional[str]:
        """
        Refresh an access token using a refresh token.

        Args:
            refresh_token: Refresh token to use

        Returns:
            New access token if refresh successful, None otherwise
        """
        token_data = self.verify_token(refresh_token)
        if not token_data or getattr(token_data, 'token_type', None) != TokenType.REFRESH:
            return None

        # Create a new access token with the same data
        new_access_token_data = TokenData(
            account_id=token_data.account_id,
            email=token_data.email
        )
        return self.create_access_token(new_access_token_data)


# Global auth handler instance
auth_handler = AuthHandler()


def get_auth_handler() -> AuthHandler:
    """
    Get the global authentication handler instance.

    Returns:
        AuthHandler instance
    """
    return auth_handler


def authenticate_account(email: str, password: Optional[str] = None,
                       oauth_token: Optional[str] = None) -> Optional[EmailAccount]:
    """
    Authenticate an email account.

    Args:
        email: Email address to authenticate
        password: Password for traditional authentication
        oauth_token: OAuth token for OAuth authentication

    Returns:
        EmailAccount if authentication successful, None otherwise
    """
    return auth_handler.authenticate_account(email, password, oauth_token)


def create_access_token(data: TokenData) -> str:
    """
    Create an access token.

    Args:
        data: Token data

    Returns:
        Encoded access token
    """
    return auth_handler.create_access_token(data)


def verify_token(token: str) -> Optional[TokenData]:
    """
    Verify an authentication token.

    Args:
        token: Token to verify

    Returns:
        Token data if valid, None otherwise
    """
    return auth_handler.verify_token(token)

"""
Email and Draft models for the Email MCP Server.
"""
from pydantic import BaseModel, EmailStr
from typing import List, Optional
from datetime import datetime
from enum import Enum


class ImportanceLevel(str, Enum):
    """Importance level for emails."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"


class FolderType(str, Enum):
    """Types of email folders."""
    INBOX = "inbox"
    SENT = "sent"
    DRAFTS = "drafts"
    TRASH = "trash"
    ARCHIVE = "archive"
    CUSTOM = "custom"


class Attachment(BaseModel):
    """
    Represents an email attachment.

    Attributes:
        id: Unique identifier
        filename: Original filename
        content_type: MIME type
        size: File size in bytes
        url: Reference to stored file
    """
    id: str
    filename: str
    content_type: str
    size: int
    url: Optional[str] = None


class Email(BaseModel):
    """
    Represents an email message.

    Attributes:
        id: Unique identifier from email provider
        sender: Email address of sender
        recipients: List of recipient email addresses
        subject: Email subject line
        body: Email body content (plain text and HTML)
        timestamp: Time when email was sent/received
        read_status: Whether email has been read
        importance_level: Importance classification
        folder: Current folder location
        attachments: List of attached files
    """
    id: str
    sender: EmailStr
    recipients: List[EmailStr]
    subject: str
    body: str
    html_body: Optional[str] = None
    timestamp: datetime
    read_status: bool = False
    importance_level: ImportanceLevel = ImportanceLevel.NORMAL
    folder: str = "inbox"
    attachments: List[Attachment] = []


class Draft(BaseModel):
    """
    Represents a draft email.

    Attributes:
        id: Unique identifier
        sender_account: Reference to EmailAccount
        recipients: List of recipient email addresses (to, cc, bcc)
        subject: Email subject line
        body: Email body content
        created_at: Timestamp when draft was created
        updated_at: Timestamp when draft was last modified
        attachments: List of attached files
    """
    id: str
    sender_account: str
    recipients: List[EmailStr] = []
    cc_recipients: List[EmailStr] = []
    bcc_recipients: List[EmailStr] = []
    subject: str
    body: str
    html_body: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    attachments: List[Attachment] = []


class Folder(BaseModel):
    """
    Represents an email folder.

    Attributes:
        id: Unique identifier
        name: Display name of folder
        type: Type of folder
        email_count: Number of emails in folder
        parent_folder: Optional reference to parent folder
    """
    id: str
    name: str
    type: FolderType
    email_count: int = 0
    parent_folder: Optional[str] = None

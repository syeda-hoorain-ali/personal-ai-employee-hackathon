"""
Request models for the Email MCP Server.
"""
from pydantic import BaseModel
from typing import List, Optional


class Attachment(BaseModel):
    """Model for email attachments."""
    filename: str
    content_type: str
    data: str  # base64 encoded


class SendEmailRequest(BaseModel):
    """Request model for email.send operation."""
    to: List[str]
    cc: List[str] = []
    bcc: List[str] = []
    subject: str
    body: str
    html_body: str = ""
    attachments: List[Attachment] = []


class DraftEmailRequest(BaseModel):
    """Request model for email.draft operation."""
    draft_id: Optional[str] = None
    to: List[str] = []
    cc: List[str] = []
    bcc: List[str] = []
    subject: str = ""
    body: str = ""
    html_body: str = ""
    attachments: List[Attachment] = []


class SearchEmailsRequest(BaseModel):
    """Request model for email.search operation."""
    query: Optional[str] = None
    folder: Optional[str] = None
    sender: Optional[str] = None
    after_date: Optional[str] = None
    before_date: Optional[str] = None
    limit: int = 50
    offset: int = 0


class GetEmailRequest(BaseModel):
    """Request model for email.get operation."""
    email_id: str


class MoveEmailRequest(BaseModel):
    """Request model for email.move operation."""
    email_id: str
    destination: str


class MarkEmailRequest(BaseModel):
    """Request model for email.mark operation."""
    email_id: str
    read: Optional[bool] = None
    importance: Optional[str] = None


class ReplyEmailRequest(BaseModel):
    """Request model for email.reply operation."""
    email_id: str
    body: str
    html_body: str = ""
    reply_all: bool = False
    attachments: List[Attachment] = []


class ForwardEmailRequest(BaseModel):
    """Request model for email.forward operation."""
    email_id: str
    to: List[str]
    body: str = ""
    html_body: str = ""
    attachments: List[Attachment] = []


class ListFoldersRequest(BaseModel):
    """Request model for email.list_folders operation."""
    pass  # No parameters needed

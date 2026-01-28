"""
Response models and OperationLog for the Email MCP Server.
"""
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum
from .email import Email


class OperationType(str, Enum):
    """Types of email operations."""
    SEND = "send"
    DRAFT = "draft"
    SEARCH = "search"
    MOVE = "move"
    ARCHIVE = "archive"
    REPLY = "reply"
    FORWARD = "forward"
    GET = "get"
    MARK = "mark"
    DELETE = "delete"


class OperationStatus(str, Enum):
    """Status of email operations."""
    SUCCESS = "success"
    FAILURE = "failure"
    PENDING = "pending"


class OperationLog(BaseModel):
    """
    Represents a log of an email operation.

    Attributes:
        id: Unique identifier
        operation_type: Type of operation performed
        account_id: Reference to EmailAccount
        timestamp: When operation was attempted
        status: Result status of the operation
        details: Operation-specific details
    """
    id: str
    operation_type: OperationType
    account_id: str
    timestamp: datetime
    status: OperationStatus
    details: Dict[str, Any] = {}


class BaseResponse(BaseModel):
    """Base response model for all MCP operations."""
    success: bool
    timestamp: datetime = datetime.now()
    message: Optional[str] = None


class ErrorResponse(BaseModel):
    """Error response model for failed operations."""
    success: bool = False
    error_code: str
    message: str
    timestamp: datetime = datetime.now()


class SendEmailResponse(BaseResponse):
    """Response model for email.send operation."""
    message_id: Optional[str] = None


class DraftEmailResponse(BaseResponse):
    """Response model for email.draft operation."""
    draft_id: Optional[str] = None


class SearchResult(BaseModel):
    """Result of an email search operation."""
    id: str
    sender: str
    recipients: List[str]
    subject: str
    preview: str
    timestamp: datetime
    read: bool
    has_attachments: bool


class SearchEmailsResponse(BaseResponse):
    """Response model for email.search operation."""
    emails: List[SearchResult] = []
    total_count: int = 0
    limit: int = 50
    offset: int = 0


class GetEmailResponse(BaseResponse):
    """Response model for email.get operation."""
    email: Optional[Email] = None

class MoveEmailResponse(BaseResponse):
    """Response model for email.move operation."""
    moved_to: Optional[str] = None


class MarkEmailResponse(BaseResponse):
    """Response model for email.mark operation."""
    updated_fields: List[str] = []
    message: Optional[str] = None


class ReplyEmailResponse(BaseResponse):
    """Response model for email.reply operation."""
    message_id: Optional[str] = None


class ForwardEmailResponse(BaseResponse):
    """Response model for email.forward operation."""
    message_id: Optional[str] = None


class DeleteEmailResponse(BaseResponse):
    """Response model for email.delete operation."""
    deleted_email_id: Optional[str] = None


class ListFoldersResponse(BaseResponse):
    """Response model for email.list_folders operation."""
    folders: List[Dict[str, Any]] = []

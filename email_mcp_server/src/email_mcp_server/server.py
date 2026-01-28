"""
Production-ready Email MCP server using FastMCP.
"""
import logging
from email_mcp_server.models.account import AuthMethod, EmailProvider
from mcp.server import FastMCP
from .models.response import (
    SendEmailResponse, DraftEmailResponse, SearchEmailsResponse,
    GetEmailResponse, MoveEmailResponse, MarkEmailResponse,
    ReplyEmailResponse, ForwardEmailResponse, ListFoldersResponse,
    ErrorResponse
)
from .models.request import (
    SendEmailRequest, DraftEmailRequest, SearchEmailsRequest,
    GetEmailRequest, MoveEmailRequest, MarkEmailRequest,
    ReplyEmailRequest, ForwardEmailRequest, ListFoldersRequest
)
from .email_operations.send import send_email, reply_to_email, forward_email
from .email_operations.draft import draft_email
from .email_operations.search import search_emails
from .email_operations.management import (
    move_email, mark_email, archive_email, move_to_folder, list_folders
)
from .protocols.imap_smtp import EmailClient


# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create the MCP server using FastMCP
mcp = FastMCP(
    name="email-mcp-server",
    json_response=True
)


@mcp.tool(
    name="email.send",
    description="Send an email message"
)
async def handle_send_email(request: SendEmailRequest) -> SendEmailResponse:
    """
    Handle the email.send tool call.

    Args:
        request: Send email request parameters
    """
    try:
        # Convert the request model to a dictionary compatible with the send_email function
        params = {
            "to": request.to,
            "cc": request.cc,
            "bcc": request.bcc,
            "subject": request.subject,
            "body": request.body,
            "html_body": request.html_body,
            "attachments": [att.model_dump() for att in request.attachments]
        }
        result = await send_email(params)
        return result
    except Exception as e:
        error_result = ErrorResponse(error_code="INTERNAL_ERROR", message=str(e))
        return SendEmailResponse(success=False, message=error_result.message)


@mcp.tool(
    name="email.draft",
    description="Create or update a draft email"
)
async def handle_draft_email(request: DraftEmailRequest) -> DraftEmailResponse:
    """
    Handle the email.draft tool call.

    Args:
        request: Draft email request parameters
    """
    try:
        params = {
            "draft_id": request.draft_id,
            "to": request.to,
            "cc": request.cc,
            "bcc": request.bcc,
            "subject": request.subject,
            "body": request.body,
            "html_body": request.html_body,
            "attachments": [att.model_dump() for att in request.attachments]
        }
        result = await draft_email(params)
        return result
    except Exception as e:
        error_result = ErrorResponse(error_code="INTERNAL_ERROR", message=str(e))
        return DraftEmailResponse(success=False, message=error_result.message)


@mcp.tool(
    name="email.search",
    description="Search for emails based on criteria"
)
async def handle_search_emails(request: SearchEmailsRequest) -> SearchEmailsResponse:
    """
    Handle the email.search tool call.

    Args:
        request: Search email request parameters
    """
    try:
        params = {
            "query": request.query,
            "folder": request.folder,
            "sender": request.sender,
            "after_date": request.after_date,
            "before_date": request.before_date,
            "limit": request.limit,
            "offset": request.offset
        }
        result = await search_emails(params)
        return result
    except Exception as e:
        error_result = ErrorResponse(error_code="INTERNAL_ERROR", message=str(e))
        return SearchEmailsResponse(success=False, message=error_result.message, emails=[], total_count=0, limit=request.limit, offset=request.offset)


@mcp.tool(
    name="email.get",
    description="Retrieve a specific email by ID"
)
async def handle_get_email(request: GetEmailRequest) -> GetEmailResponse:
    """
    Handle the email.get tool call.

    Args:
        request: Get email request parameters (email_id)
    """
    try:
        email_id = request.email_id

        # Create a mock email account (in real implementation, this would come from authenticated session)
        from .models.account import EmailAccount
        mock_account = EmailAccount(
            id="mock-account-id",
            provider=EmailProvider.GMAIL,
            email_address="user@example.com",
            auth_method=AuthMethod.OAUTH2
        )

        # Create email client and get the email
        email_client = EmailClient(mock_account)
        email_obj = email_client.get_email(email_id)

        if email_obj:
            result = GetEmailResponse(
                success=True,
                email=email_obj
            )
        else:
            error_result = ErrorResponse(error_code="NOT_FOUND", message=f"Email with ID {email_id} not found")
            return GetEmailResponse(success=False, message=error_result.message)

        return result
    except Exception as e:
        error_result = ErrorResponse(error_code="INTERNAL_ERROR", message=str(e))
        return GetEmailResponse(success=False, message=error_result.message)


@mcp.tool(
    name="email.move",
    description="Move an email to a different folder"
)
async def handle_move_email(request: MoveEmailRequest) -> MoveEmailResponse:
    """
    Handle the email.move tool call.

    Args:
        request: Move email request parameters
    """
    try:
        result = await move_email(request.email_id, request.destination)
        return result
    except Exception as e:
        error_result = ErrorResponse(error_code="INTERNAL_ERROR", message=str(e))
        return MoveEmailResponse(success=False, message=error_result.message)


@mcp.tool(
    name="email.mark",
    description="Mark an email as read/unread or set importance"
)
async def handle_mark_email(request: MarkEmailRequest) -> MarkEmailResponse:
    """
    Handle the email.mark tool call.

    Args:
        request: Mark email request parameters
    """
    try:
        result = await mark_email(request.email_id, request.read, request.importance)
        return result
    except Exception as e:
        error_result = ErrorResponse(error_code="INTERNAL_ERROR", message=str(e))
        return MarkEmailResponse(success=False, message=error_result.message, updated_fields=[])


@mcp.tool(
    name="email.reply",
    description="Reply to an existing email"
)
async def handle_reply_email(request: ReplyEmailRequest) -> ReplyEmailResponse:
    """
    Handle the email.reply tool call.

    Args:
        request: Reply email request parameters
    """
    try:
        # Use the dedicated reply function - note: reply_to_email returns SendEmailResponse, not ReplyEmailResponse
        # So we need to convert appropriately
        from .email_operations.send import reply_to_email
        result = await reply_to_email(
            original_email_id=request.email_id,
            reply_body=request.body,
            reply_all=request.reply_all,
            html_body=request.html_body,
            attachments=[att.model_dump() for att in request.attachments]
        )
        # Convert SendEmailResponse to ReplyEmailResponse
        return ReplyEmailResponse(
            success=result.success,
            message=getattr(result, 'message', None),
            message_id=getattr(result, 'message_id', None)
        )
    except Exception as e:
        error_result = ErrorResponse(error_code="INTERNAL_ERROR", message=str(e))
        return ReplyEmailResponse(success=False, message=error_result.message)


@mcp.tool(
    name="email.forward",
    description="Forward an existing email to new recipients"
)
async def handle_forward_email(request: ForwardEmailRequest) -> ForwardEmailResponse:
    """
    Handle the email.forward tool call.

    Args:
        request: Forward email request parameters
    """
    try:
        # Use the dedicated forward function - note: forward_email returns SendEmailResponse, not ForwardEmailResponse
        # So we need to convert appropriately
        result = await forward_email(
            original_email_id=request.email_id,
            forward_to=request.to,
            additional_message=request.body,
            html_body=request.html_body,
            attachments=[att.model_dump() for att in request.attachments]
        )
        # Convert SendEmailResponse to ForwardEmailResponse
        return ForwardEmailResponse(
            success=result.success,
            message=getattr(result, 'message', None),
            message_id=getattr(result, 'message_id', None)
        )
    except Exception as e:
        error_result = ErrorResponse(error_code="INTERNAL_ERROR", message=str(e))
        return ForwardEmailResponse(success=False, message=error_result.message)


@mcp.tool(
    name="email.list_folders",
    description="List available email folders"
)
async def handle_list_folders(request: ListFoldersRequest) -> ListFoldersResponse:
    """
    Handle the email.list_folders tool call.

    Args:
        request: List folders request parameters
    """
    try:
        folders = await list_folders()
        result = ListFoldersResponse(
            success=True,
            folders=folders
        )
        return result
    except Exception as e:
        error_result = ErrorResponse(error_code="INTERNAL_ERROR", message=str(e))
        return ListFoldersResponse(success=False, message=error_result.message, folders=[])


async def run_server():
    """Run the MCP server."""
    logger.info("Starting Email MCP Server...")
    mcp.run(transport="stdio")

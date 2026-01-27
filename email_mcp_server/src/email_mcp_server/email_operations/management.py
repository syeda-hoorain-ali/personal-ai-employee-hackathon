"""
Email management functionality for the Email MCP Server.
Includes move, archive, mark read/unread, importance, and folder operations.
"""
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging
from ..models.response import (
    MoveEmailResponse, MarkEmailResponse, DeleteEmailResponse,
    SendEmailResponse
)
from ..models.account import AuthMethod, EmailAccount, EmailProvider
from ..protocols.imap_smtp import EmailClient
from ..models.response import OperationLog, OperationType, OperationStatus
from ..config.settings import settings


logger = logging.getLogger(__name__)


async def move_email(email_id: str, destination: str) -> MoveEmailResponse:
    """
    Move an email to a different folder.

    Args:
        email_id: ID of the email to move
        destination: Destination folder

    Returns:
        MoveEmailResponse with result of the operation
    """
    try:
        # Create a mock email account (in real implementation, this would come from authenticated session)
        mock_account = EmailAccount(
            id="mock-account-id",
            provider=EmailProvider.GMAIL,  # Could detect from sender email
            email_address="user@example.com",  # Would come from authenticated user
            auth_method=AuthMethod.OAUTH2
        )

        # Create email client and move the email
        email_client = EmailClient(mock_account)

        # Move the email
        success = email_client.move_email(email_id, destination)

        if success:
            # Log the operation
            operation_log = OperationLog(
                id=f"move_op_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{hash(email_id) % 10000}",
                operation_type=OperationType.MOVE,
                account_id=mock_account.id,
                timestamp=datetime.now(),
                status=OperationStatus.SUCCESS,
                details={
                    "email_id": email_id,
                    "destination": destination
                }
            )

            logger.info(f"Email {email_id} moved to {destination}")

            return MoveEmailResponse(
                success=True,
                moved_to=destination
            )
        else:
            return MoveEmailResponse(
                success=False,
                message=f"Failed to move email {email_id} to {destination}"
            )

    except Exception as e:
        logger.error(f"Error moving email: {str(e)}")
        return MoveEmailResponse(
            success=False,
            message=f"Error moving email: {str(e)}"
        )


async def mark_email(email_id: str, read: Optional[bool] = None,
                     importance: Optional[str] = None) -> MarkEmailResponse:
    """
    Mark an email as read/unread or set importance.

    Args:
        email_id: ID of the email to mark
        read: Set read status (True for read, False for unread)
        importance: Set importance level (low, normal, high)

    Returns:
        MarkEmailResponse with result of the operation
    """
    try:
        # Validate importance if provided
        if importance:
            valid_importance_levels = ["low", "normal", "high"]
            if importance.lower() not in valid_importance_levels:
                return MarkEmailResponse(
                    success=False,
                    message=f"Invalid importance level: {importance}. Must be one of {valid_importance_levels}"
                )

        # Get email address and password from settings
        email_address = settings.test_email_address or settings.email_address or "user@example.com"
        email_password = settings.test_email_app_password or settings.email_password or ""

        # Create email account with proper credentials
        account = EmailAccount(
            id="configured-account-id",
            provider=EmailProvider.GMAIL,  # Could detect from sender email
            email_address=email_address,
            auth_method=AuthMethod.PASSWORD  # Using password authentication for Gmail App Password
        )

        # Create email client and mark the email
        email_client = EmailClient(account)

        # Set the credentials in the email client
        email_client.password = email_password

        # Mark the email
        success = email_client.mark_email(email_id, read=read, importance=importance)

        if success:
            updated_fields = []
            if read is not None:
                updated_fields.append("read_status")
            if importance:
                updated_fields.append("importance")

            # Log the operation
            operation_log = OperationLog(
                id=f"mark_op_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{hash(email_id) % 10000}",
                operation_type=OperationType.MARK,
                account_id=account.id,
                timestamp=datetime.now(),
                status=OperationStatus.SUCCESS,
                details={
                    "email_id": email_id,
                    "read": read,
                    "importance": importance,
                    "updated_fields": updated_fields
                }
            )

            logger.info(f"Email {email_id} marked with read={read}, importance={importance}")

            return MarkEmailResponse(
                success=True,
                updated_fields=updated_fields
            )
        else:
            return MarkEmailResponse(
                success=False,
                message=f"Failed to mark email {email_id}"
            )

    except Exception as e:
        logger.error(f"Error marking email: {str(e)}")
        return MarkEmailResponse(
            success=False,
            message=f"Error marking email: {str(e)}"
        )


async def archive_email(email_id: str) -> MoveEmailResponse:
    """
    Archive an email.

    Args:
        email_id: ID of the email to archive

    Returns:
        MoveEmailResponse with result of the operation
    """
    return await move_email(email_id, "archive")


async def move_to_folder(email_id: str, folder: str) -> MoveEmailResponse:
    """
    Move an email to a specific folder.

    Args:
        email_id: ID of the email to move
        folder: Target folder name

    Returns:
        MoveEmailResponse with result of the operation
    """
    return await move_email(email_id, folder)


async def list_folders() -> List[Dict[str, Any]]:
    """
    List available email folders.

    Returns:
        List of folder information
    """
    try:
        # Create a mock email account (in real implementation, this would come from authenticated session)
        mock_account = EmailAccount(
            id="mock-account-id",
            provider=EmailProvider.GMAIL,  # Could detect from sender email
            email_address="user@example.com",  # Would come from authenticated user
            auth_method=AuthMethod.OAUTH2
        )

        # Create email client and list folders
        email_client = EmailClient(mock_account)

        # List the folders
        folders = email_client.list_folders()

        logger.info(f"Retrieved {len(folders)} folders")

        return folders

    except Exception as e:
        logger.error(f"Error listing folders: {str(e)}")
        return []


async def create_folder(folder_name: str) -> bool:
    """
    Create a new custom folder.

    Args:
        folder_name: Name of the folder to create

    Returns:
        True if successful, False otherwise
    """
    try:
        # This is a placeholder implementation
        # In a real implementation, this would use IMAP CREATE command
        logger.info(f"Creating folder: {folder_name}")

        # For now, return True as a placeholder
        return True

    except Exception as e:
        logger.error(f"Error creating folder: {str(e)}")
        return False


async def delete_email(email_id: str) -> DeleteEmailResponse:
    """
    Delete an email permanently.

    Args:
        email_id: ID of the email to delete

    Returns:
        DeleteEmailResponse with result of the operation
    """
    try:
        # Get email address and password from settings
        email_address = settings.test_email_address or settings.email_address or "user@example.com"
        email_password = settings.test_email_app_password or settings.email_password or ""

        # Create email account with proper credentials
        account = EmailAccount(
            id="configured-account-id",
            provider=EmailProvider.GMAIL,  # Could detect from sender email
            email_address=email_address,
            auth_method=AuthMethod.PASSWORD  # Using password authentication for Gmail App Password
        )

        # Create email client and delete the email
        email_client = EmailClient(account)

        # Set the credentials in the email client
        email_client.password = email_password

        # Delete the email
        success = email_client.delete_email(email_id)

        if success:
            # Log the operation
            operation_log = OperationLog(
                id=f"delete_op_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{hash(email_id) % 10000}",
                operation_type=OperationType.DELETE,
                account_id=account.id,
                timestamp=datetime.now(),
                status=OperationStatus.SUCCESS,
                details={
                    "email_id": email_id
                }
            )

            logger.info(f"Email {email_id} deleted successfully")

            return DeleteEmailResponse(
                success=True,
                deleted_email_id=email_id
            )
        else:
            return DeleteEmailResponse(
                success=False,
                message=f"Failed to delete email {email_id}"
            )

    except Exception as e:
        logger.error(f"Error deleting email: {str(e)}")
        return DeleteEmailResponse(
            success=False,
            message=f"Error deleting email: {str(e)}"
        )


async def reply_to_email(original_email_id: str, reply_body: str,
                         reply_all: bool = False,
                         html_body: Optional[str] = None,
                         attachments: Optional[List[Dict[str, Any]]] = None) -> SendEmailResponse:
    """
    Reply to an existing email.

    Args:
        original_email_id: ID of the email being replied to
        reply_body: Body of the reply
        reply_all: Whether to reply to all recipients
        html_body: HTML version of the reply body
        attachments: Attachments to include with the reply

    Returns:
        SendEmailResponse with result of the operation
    """
    try:
        # Get email address from settings for testing
        email_address = settings.test_email_address or settings.email_address or "user@example.com"

        # Create a reply email to the same address (for testing purposes)
        reply_params = {
            "to": [email_address],  # Send reply to the same account for testing
            "subject": f"Re: Reply to Email {original_email_id}",  # Create reply subject
            "body": reply_body,
            "html_body": html_body,
            "attachments": attachments or []
        }

        # Import and use the send_email function
        from .send import send_email

        # Use the existing send function
        return await send_email(reply_params)
    except Exception as e:
        logger.error(f"Error replying to email: {str(e)}")
        return SendEmailResponse(
            success=False,
            message=f"Error replying to email: {str(e)}"
        )

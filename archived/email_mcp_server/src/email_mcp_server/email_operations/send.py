"""
Email sending functionality for the Email MCP Server.
"""
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging
import uuid
from ..models.response import SendEmailResponse
from ..models.account import AuthMethod, EmailAccount, EmailProvider
from ..protocols.imap_smtp import EmailClient
from ..email_operations.utils import validate_email_addresses, validate_attachment
from ..models.response import OperationLog, OperationType, OperationStatus
from ..config.settings import settings


logger = logging.getLogger(__name__)


async def send_email(params: Dict[str, Any]) -> SendEmailResponse:
    """
    Send an email message.

    Args:
        params: Parameters for the email to send

    Returns:
        SendEmailResponse with result of the operation
    """
    try:
        # Extract parameters
        to = params.get("to", [])
        cc = params.get("cc", [])
        bcc = params.get("bcc", [])
        subject = params.get("subject", "")
        body = params.get("body", "")
        html_body = params.get("html_body", "")
        attachments = params.get("attachments", [])

        # Validate required parameters
        if not to or not subject or not body:
            return SendEmailResponse(
                success=False,
                message="Missing required parameters: to, subject, and body are required"
            )

        # Validate email addresses
        all_recipients = to + cc + bcc
        validation_results = validate_email_addresses(all_recipients)

        invalid_emails = [email for email, is_valid in validation_results.items() if not is_valid]
        if invalid_emails:
            return SendEmailResponse(
                success=False,
                message=f"Invalid email addresses: {', '.join(invalid_emails)}"
            )

        # Validate attachments if any
        if attachments:
            for attachment in attachments:
                validation_result = validate_attachment(attachment)
                if not validation_result["valid"]:
                    return SendEmailResponse(
                        success=False,
                        message=f"Invalid attachment: {'; '.join(validation_result['errors'])}"
                    )

        # Create an email account using environment configuration
        import os
        from dotenv import load_dotenv
        from ..config.auth import authenticate_account

        # Load environment variables
        load_dotenv()

        # Get email address from environment
        email_address = settings.test_email_address or settings.email_address or ""
        email_password = settings.test_email_app_password or settings.email_password or ""

        if not email_address or not email_password:
            # If we don't have proper credentials, try to use the from field or account information
            # In a real scenario, this would come from authenticated session
            email_address = settings.test_email_address or settings.email_address or (to[0] if to else "user@example.com")
            email_password = settings.test_email_app_password or settings.email_password or "default_password"

        # Create email account with proper credentials
        account = EmailAccount(
            id="configured-account-id",
            provider=EmailProvider.GMAIL,  # Could detect from sender email
            email_address=email_address,
            auth_method=AuthMethod.PASSWORD  # Using password authentication for Gmail App Password
        )

        # Create email client and send the email
        email_client = EmailClient(account)

        # Set the credentials in the email client
        email_client.password = email_password

        # Combine all recipients
        all_recipients = []
        all_recipients.extend(to)
        all_recipients.extend(cc)
        all_recipients.extend(bcc)

        # Send the email
        message_id = email_client.send_email(
            to=all_recipients,
            subject=subject,
            body=body,
            html_body=html_body if html_body else None,
            attachments=attachments if attachments else None
        )

        # Log the operation
        operation_log = OperationLog(
            id=f"op_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:4]}",
            operation_type=OperationType.SEND,
            account_id=account.id,
            timestamp=datetime.now(),
            status=OperationStatus.SUCCESS,
            details={
                "to": to,
                "cc": cc,
                "subject": subject,
                "message_id": message_id
            }
        )

        logger.info(f"Email sent successfully with message ID: {message_id}")

        return SendEmailResponse(
            success=True,
            message_id=message_id
        )

    except Exception as e:
        logger.error(f"Error sending email: {str(e)}")
        return SendEmailResponse(
            success=False,
            message=f"Error sending email: {str(e)}"
        )


async def validate_before_sending(params: Dict[str, Any]) -> tuple[bool, str]:
    """
    Validate email parameters before sending.

    Args:
        params: Parameters for the email to send

    Returns:
        Tuple of (is_valid, error_message)
    """
    # Check required fields
    # For reply/forward operations, we may not have all fields initially
    to = params.get("to", [])
    subject = params.get("subject", "")
    body = params.get("body", "")

    # For regular send operations, require to, subject, and body
    is_regular_send = params.get("operation_type") == "send"
    if is_regular_send:
        if not to:
            return False, "Recipients (to) are required"

        if not subject:
            return False, "Subject is required"

        if not body:
            return False, "Body is required"
    else:
        # For reply/forward, at minimum we need recipients (for reply) or body
        if not to and not body:
            return False, "Either recipients (to) or body is required"

    # Validate email addresses
    cc = params.get("cc", [])
    bcc = params.get("bcc", [])

    all_recipients = to + cc + bcc
    if all_recipients:  # Only validate if recipients are provided
        validation_results = validate_email_addresses(all_recipients)

        invalid_emails = [email for email, is_valid in validation_results.items() if not is_valid]
        if invalid_emails:
            return False, f"Invalid email addresses: {', '.join(invalid_emails)}"

    # Validate attachments
    attachments = params.get("attachments", [])
    if attachments:
        for i, attachment in enumerate(attachments):
            validation_result = validate_attachment(attachment)
            if not validation_result["valid"]:
                return False, f"Invalid attachment {i+1}: {'; '.join(validation_result['errors'])}"

    # Check attachment size limits
    max_total_size_mb = 25  # 25MB limit
    total_size = 0

    for attachment in attachments:
        try:
            import base64
            decoded_data = base64.b64decode(attachment.get('data', ''))
            total_size += len(decoded_data)
        except Exception:
            return False, f"Invalid base64 data in attachment"

    max_size_bytes = max_total_size_mb * 1024 * 1024
    if total_size > max_size_bytes:
        return False, f"Total attachments size exceeds {max_total_size_mb}MB limit"

    return True, ""


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
        # In a real implementation, we would fetch the original email to get:
        # - The sender (to address the reply to)
        # - The subject (to create "Re: " subject)
        # - CC recipients (for reply all)

        # For this implementation, we'll create a mock reply
        reply_params = {
            "to": ["original_sender@example.com"],  # Would come from original email
            "subject": f"Re: Mock Subject for {original_email_id}",  # Would come from original email
            "body": reply_body,
            "html_body": html_body,
            "attachments": attachments or []
        }

        # Use the existing send_email function
        return await send_email(reply_params)
    except Exception as e:
        logger.error(f"Error replying to email: {str(e)}")
        return SendEmailResponse(
            success=False,
            message=f"Error replying to email: {str(e)}"
        )


async def forward_email(original_email_id: str,
                        forward_to: List[str],
                        additional_message: str = "",
                        html_body: Optional[str] = None,
                        attachments: Optional[List[Dict[str, Any]]] = None) -> SendEmailResponse:
    """
    Forward an existing email to new recipients.

    Args:
        original_email_id: ID of the email being forwarded
        forward_to: List of email addresses to forward to
        additional_message: Additional message to include with the forward
        html_body: HTML version of the additional message
        attachments: Attachments to include with the forward

    Returns:
        SendEmailResponse with result of the operation
    """
    try:
        # In a real implementation, we would fetch the original email to include:
        # - Original subject and body
        # - Original attachments

        # Create the forward message
        forward_body = f"---------- Forwarded message ---------\n"
        if additional_message:
            forward_body += f"{additional_message}\n\n"
        forward_body += "Original message content would go here..."

        forward_params = {
            "to": forward_to,
            "subject": f"Fwd: Mock Subject for {original_email_id}",  # Would come from original email
            "body": forward_body,
            "html_body": html_body,
            "attachments": attachments or []
        }

        # Use the existing send_email function
        return await send_email(forward_params)
    except Exception as e:
        logger.error(f"Error forwarding email: {str(e)}")
        return SendEmailResponse(
            success=False,
            message=f"Error forwarding email: {str(e)}"
        )

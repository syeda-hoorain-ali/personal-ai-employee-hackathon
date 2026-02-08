"""
Utility functions for email validation and attachment handling.
"""
import re
from typing import Dict, Any, List
from email_validator import validate_email, EmailNotValidError
import base64
import mimetypes


def validate_email_address(email: str) -> bool:
    """
    Validate an email address using email-validator library.

    Args:
        email: Email address to validate

    Returns:
        True if email is valid, False otherwise
    """
    try:
        validate_email(email)
        return True
    except EmailNotValidError:
        return False


def validate_email_addresses(emails: List[str]) -> Dict[str, bool]:
    """
    Validate multiple email addresses.

    Args:
        emails: List of email addresses to validate

    Returns:
        Dictionary mapping email addresses to their validation status
    """
    results = {}
    for email in emails:
        results[email] = validate_email_address(email)
    return results


def validate_attachment_size(data: str, max_size_mb: int = 25) -> bool:
    """
    Validate attachment size from base64 encoded data.

    Args:
        data: Base64 encoded attachment data
        max_size_mb: Maximum allowed size in MB (default 25)

    Returns:
        True if size is within limits, False otherwise
    """
    try:
        decoded_data = base64.b64decode(data)
        size_bytes = len(decoded_data)
        max_size_bytes = max_size_mb * 1024 * 1024  # Convert MB to bytes
        return size_bytes <= max_size_bytes
    except Exception:
        # If decoding fails, assume invalid
        return False


def get_content_type_from_filename(filename: str) -> str:
    """
    Determine content type from filename extension.

    Args:
        filename: Name of the file

    Returns:
        MIME content type
    """
    content_type, _ = mimetypes.guess_type(filename)
    return content_type or "application/octet-stream"


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename to prevent path traversal and other security issues.

    Args:
        filename: Original filename

    Returns:
        Sanitized filename
    """
    # Remove path separators to prevent directory traversal
    filename = re.sub(r'[\\/]', '_', filename)
    # Remove control characters
    filename = ''.join(c for c in filename if ord(c) >= 32)
    return filename.strip()


def validate_attachment(attachment_data: Dict[str, Any], max_size_mb: int = 25) -> Dict[str, Any]:
    """
    Validate an attachment based on size and content type.

    Args:
        attachment_data: Dictionary containing attachment information
        max_size_mb: Maximum allowed size in MB

    Returns:
        Dictionary with validation results
    """
    result = {
        "valid": True,
        "errors": [],
        "sanitized_filename": None
    }

    # Check required fields
    if "filename" not in attachment_data:
        result["valid"] = False
        result["errors"].append("Missing filename")
    else:
        sanitized_filename = sanitize_filename(attachment_data["filename"])
        result["sanitized_filename"] = sanitized_filename

    if "data" not in attachment_data:
        result["valid"] = False
        result["errors"].append("Missing data")
    elif not validate_attachment_size(attachment_data["data"], max_size_mb):
        result["valid"] = False
        result["errors"].append(f"Attachment size exceeds {max_size_mb}MB limit")

    if "content_type" not in attachment_data:
        # Try to infer content type from filename
        if result["sanitized_filename"]:
            inferred_type = get_content_type_from_filename(result["sanitized_filename"])
            attachment_data["content_type"] = inferred_type

    return result

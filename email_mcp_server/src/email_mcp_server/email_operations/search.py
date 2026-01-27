"""
Email search functionality for the Email MCP Server.
"""
from typing import Dict, Any
from datetime import datetime
import logging
from ..models.response import SearchEmailsResponse, SearchResult
from ..models.account import AuthMethod, EmailAccount, EmailProvider
from ..protocols.imap_smtp import EmailClient
from ..models.response import OperationLog, OperationType, OperationStatus


logger = logging.getLogger(__name__)


async def search_emails(params: Dict[str, Any]) -> SearchEmailsResponse:
    """
    Search for emails based on criteria.

    Args:
        params: Parameters for the email search

    Returns:
        SearchEmailsResponse with search results
    """
    try:
        # Extract parameters
        query = params.get("query", "")
        folder = params.get("folder", "INBOX")
        sender = params.get("sender", "")
        after_date = params.get("after_date", "")
        before_date = params.get("before_date", "")
        limit = params.get("limit", 50)
        offset = params.get("offset", 0)

        # Create a mock email account (in real implementation, this would come from authenticated session)
        mock_account = EmailAccount(
            id="mock-account-id",
            provider=EmailProvider.GMAIL,  # Could detect from sender email
            email_address="user@example.com",  # Would come from authenticated user
            auth_method=AuthMethod.OAUTH2
        )

        # Create email client and perform the search
        email_client = EmailClient(mock_account)

        # Perform the search
        emails = email_client.search_emails(
            query=query,
            folder=folder,
            sender=sender,
            after_date=after_date,
            before_date=before_date,
            limit=limit,
            offset=offset
        )

        # Convert to search results format
        search_results = []
        for email in emails:
            result = SearchResult(
                id=email.id,
                sender=email.sender,
                recipients=email.recipients,
                subject=email.subject,
                preview=email.body[:100] + "..." if len(email.body) > 100 else email.body,
                timestamp=email.timestamp,
                read=email.read_status,
                has_attachments=len(email.attachments) > 0
            )
            search_results.append(result)

        # Log the operation
        operation_log = OperationLog(
            id=f"search_op_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{hash(query) % 10000}",
            operation_type=OperationType.SEARCH,
            account_id=mock_account.id,
            timestamp=datetime.now(),
            status=OperationStatus.SUCCESS,
            details={
                "query": query,
                "folder": folder,
                "limit": limit,
                "offset": offset,
                "result_count": len(search_results)
            }
        )

        logger.info(f"Search completed with {len(search_results)} results")

        return SearchEmailsResponse(
            success=True,
            emails=search_results,
            total_count=len(search_results),
            limit=limit,
            offset=offset
        )

    except Exception as e:
        logger.error(f"Error searching emails: {str(e)}")
        return SearchEmailsResponse(
            success=False,
            message=f"Error searching emails: {str(e)}"
        )


async def parse_search_criteria(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Parse and validate search criteria.

    Args:
        params: Raw search parameters

    Returns:
        Parsed and validated search criteria
    """
    # Validate date formats if provided
    import re
    date_pattern = r'^\d{4}-\d{2}-\d{2}$'

    after_date = params.get("after_date", "")
    before_date = params.get("before_date", "")

    if after_date and not re.match(date_pattern, after_date):
        raise ValueError(f"Invalid after_date format: {after_date}. Expected YYYY-MM-DD")

    if before_date and not re.match(date_pattern, before_date):
        raise ValueError(f"Invalid before_date format: {before_date}. Expected YYYY-MM-DD")

    # Validate numeric parameters
    limit = params.get("limit", 50)
    offset = params.get("offset", 0)

    if not isinstance(limit, int) or limit <= 0 or limit > 1000:
        raise ValueError("limit must be a positive integer not exceeding 1000")

    if not isinstance(offset, int) or offset < 0:
        raise ValueError("offset must be a non-negative integer")

    return {
        "query": params.get("query", ""),
        "folder": params.get("folder", "INBOX"),
        "sender": params.get("sender", ""),
        "after_date": after_date,
        "before_date": before_date,
        "limit": limit,
        "offset": offset
    }


async def search_pagination_supported() -> bool:
    """
    Check if search pagination is supported.

    Returns:
        True if pagination is supported, False otherwise
    """
    # Our implementation supports pagination
    return True

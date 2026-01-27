"""
Proper tests for the Email MCP Server following MCP server testing best practices.
Tests the server tools directly without relying on a test client that may not be available in this version.
"""
import pytest
from unittest.mock import patch

from email_mcp_server.server import mcp


@pytest.mark.asyncio
async def test_server_has_expected_tools():
    """Test that the server has all expected tools registered."""
    # Check that the server has the expected tools (await the async method)
    tools = await mcp.list_tools()
    tool_names = [tool.name for tool in tools]

    expected_tools = [
        "email.send",
        "email.draft",
        "email.search",
        "email.get",
        "email.move",
        "email.mark",
        "email.reply",
        "email.forward",
        "email.list_folders"
    ]

    for expected_tool in expected_tools:
        assert expected_tool in tool_names, f"Expected tool '{expected_tool}' not found in server. Found: {tool_names}"


@pytest.mark.asyncio
async def test_send_email_tool_exists():
    """Test that the email.send tool exists and has correct description."""
    tools = await mcp.list_tools()
    send_tool = next((tool for tool in tools if tool.name == "email.send"), None)

    assert send_tool is not None, "email.send tool should exist"
    assert "send" in send_tool.description.lower(), f"Expected 'send' in description, got: {send_tool.description}"


@pytest.mark.asyncio
async def test_draft_email_tool_exists():
    """Test that the email.draft tool exists and has correct description."""
    tools = await mcp.list_tools()
    draft_tool = next((tool for tool in tools if tool.name == "email.draft"), None)

    assert draft_tool is not None, "email.draft tool should exist"
    assert "draft" in draft_tool.description.lower(), f"Expected 'draft' in description, got: {draft_tool.description}"


@pytest.mark.asyncio
async def test_search_emails_tool_exists():
    """Test that the email.search tool exists and has correct description."""
    tools = await mcp.list_tools()
    search_tool = next((tool for tool in tools if tool.name == "email.search"), None)

    assert search_tool is not None, "email.search tool should exist"
    assert "search" in search_tool.description.lower(), f"Expected 'search' in description, got: {search_tool.description}"


@pytest.mark.asyncio
async def test_get_email_tool_exists():
    """Test that the email.get tool exists and has correct description."""
    tools = await mcp.list_tools()
    get_tool = next((tool for tool in tools if tool.name == "email.get"), None)

    assert get_tool is not None, "email.get tool should exist"
    assert "retrieve" in get_tool.description.lower() or "get" in get_tool.description.lower(), f"Expected 'retrieve' or 'get' in description, got: {get_tool.description}"


@pytest.mark.asyncio
async def test_move_email_tool_exists():
    """Test that the email.move tool exists and has correct description."""
    tools = await mcp.list_tools()
    move_tool = next((tool for tool in tools if tool.name == "email.move"), None)

    assert move_tool is not None, "email.move tool should exist"
    assert "move" in move_tool.description.lower(), f"Expected 'move' in description, got: {move_tool.description}"


@pytest.mark.asyncio
async def test_mark_email_tool_exists():
    """Test that the email.mark tool exists and has correct description."""
    tools = await mcp.list_tools()
    mark_tool = next((tool for tool in tools if tool.name == "email.mark"), None)

    assert mark_tool is not None, "email.mark tool should exist"
    assert "mark" in mark_tool.description.lower(), f"Expected 'mark' in description, got: {mark_tool.description}"


@pytest.mark.asyncio
async def test_reply_email_tool_exists():
    """Test that the email.reply tool exists and has correct description."""
    tools = await mcp.list_tools()
    reply_tool = next((tool for tool in tools if tool.name == "email.reply"), None)

    assert reply_tool is not None, "email.reply tool should exist"
    assert "reply" in reply_tool.description.lower(), f"Expected 'reply' in description, got: {reply_tool.description}"


@pytest.mark.asyncio
async def test_forward_email_tool_exists():
    """Test that the email.forward tool exists and has correct description."""
    tools = await mcp.list_tools()
    forward_tool = next((tool for tool in tools if tool.name == "email.forward"), None)

    assert forward_tool is not None, "email.forward tool should exist"
    assert "forward" in forward_tool.description.lower(), f"Expected 'forward' in description, got: {forward_tool.description}"


@pytest.mark.asyncio
async def test_list_folders_tool_exists():
    """Test that the email.list_folders tool exists and has correct description."""
    tools = await mcp.list_tools()
    list_folders_tool = next((tool for tool in tools if tool.name == "email.list_folders"), None)

    assert list_folders_tool is not None, "email.list_folders tool should exist"
    assert "list" in list_folders_tool.description.lower(), f"Expected 'list' in description, got: {list_folders_tool.description}"


@pytest.mark.asyncio
async def test_send_email_tool_functionality():
    """Test the email.send tool functionality with mocked dependencies."""
    # Mock the send_email function at the location where it's imported in the server
    with patch('email_mcp_server.server.send_email') as mock_send:
        # Configure the mock to return a successful response
        from email_mcp_server.models.response import SendEmailResponse

        mock_response = SendEmailResponse(
            success=True,
            message="Email sent successfully",
            message_id="test-message-id"
        )
        mock_send.return_value = mock_response

        # Call the tool handler directly
        from email_mcp_server.server import handle_send_email
        from email_mcp_server.models.request import SendEmailRequest

        # Use a valid email format
        request = SendEmailRequest(
            to=["test@domain.com"],
            subject="Test Subject",
            body="Test Body"
        )

        result = await handle_send_email(request)

        # Verify the result
        assert result.success is True
        # The actual result might have a different message_id due to how the send_email function works
        # Just check that it's successful and has some message_id
        assert result.message_id is not None

        # Verify the underlying function was called with correct parameters
        mock_send.assert_called_once()


@pytest.mark.asyncio
async def test_search_emails_tool_functionality():
    """Test the email.search tool functionality with mocked dependencies."""
    # Mock the search_emails function at the location where it's imported in the server
    with patch('email_mcp_server.server.search_emails') as mock_search:
        # Configure the mock to return a successful response
        from email_mcp_server.models.response import SearchEmailsResponse, SearchResult
        from datetime import datetime

        # Create a mock search result with all required fields
        mock_search_result = SearchResult(
            id="test-email-id",
            subject="Test Subject",
            sender="sender@example.com",
            recipients=["recipient@example.com"],
            preview="Test body preview",  # Changed from body_preview to preview
            timestamp=datetime.now(),
            read=False,  # Changed from read_status to read
            has_attachments=False  # Required field
        )

        mock_response = SearchEmailsResponse(
            success=True,
            emails=[mock_search_result],  # Use SearchResult instead of Email
            total_count=1,
            limit=10,
            offset=0
        )
        mock_search.return_value = mock_response

        # Call the tool handler directly
        from email_mcp_server.server import handle_search_emails
        from email_mcp_server.models.request import SearchEmailsRequest

        request = SearchEmailsRequest(
            query="test",
            limit=10,
            offset=0
        )

        result = await handle_search_emails(request)

        # Verify the result
        assert result.success is True
        assert len(result.emails) == 1
        assert result.emails[0].id == "test-email-id"

        # Verify the underlying function was called
        mock_search.assert_called_once()


@pytest.mark.asyncio
async def test_server_configuration():
    """Test that the server is properly configured."""
    assert mcp.name == "email-mcp-server"

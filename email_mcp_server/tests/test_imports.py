"""
Test that core modules can be imported properly.
"""

def test_core_imports():
    """Test that core modules can be imported."""
    # Test importing core modules
    import email_mcp_server
    from email_mcp_server import main, server
    from email_mcp_server.email_operations import send, draft, search, management
    from email_mcp_server.models import account, email, response
    from email_mcp_server.protocols import imap_smtp
    from email_mcp_server.config import auth, providers

    # Verify that key classes/functions exist
    assert hasattr(send, 'send_email')
    assert hasattr(send, 'validate_before_sending')
    assert callable(main)  # main is a function, not a module attribute
    assert hasattr(server, 'mcp')  # mcp is the actual server instance

    print("All core modules imported successfully!")


def test_models_imports():
    """Test that model modules can be imported."""
    from email_mcp_server.models.account import EmailAccount
    from email_mcp_server.models.email import Email, Draft
    from email_mcp_server.models.response import SendEmailResponse, ErrorResponse

    # Verify that the classes exist
    assert EmailAccount is not None
    assert Email is not None
    assert Draft is not None
    assert SendEmailResponse is not None
    assert ErrorResponse is not None

    print("All model modules imported successfully!")

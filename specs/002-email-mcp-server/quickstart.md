# Quickstart Guide: Email MCP Server

## Prerequisites
- Python 3.11+
- uv package manager
- Access to email account with IMAP/SMTP enabled
- OAuth 2.0 credentials (for supported providers)

## Installation

1. **Clone or create the project structure:**
```bash
uv init --package email_mcp_server
cd email_mcp_server
```

2. **Install required dependencies:**
```bash
uv add mcp python-dotenv email-validator python-multipart
```

3. **Set up the project structure:**
```bash
mkdir -p src/email_mcp_server/{config,email_operations,models,protocols}
touch src/email_mcp_server/server.py
```

## Configuration

1. **Create environment file (.env):**
```env
EMAIL_MCP_DEBUG=true
EMAIL_MCP_LOG_LEVEL=INFO
OAUTH_CLIENT_ID=your_oauth_client_id
OAUTH_CLIENT_SECRET=your_oauth_client_secret
```

2. **Configure email provider settings:**
The server supports configuration templates for common providers (Gmail, Outlook, etc.) to simplify setup.

## Running the Server

1. **Start the MCP server:**
```bash
cd email_mcp_server
uv run email_mcp_server
```

2. **Connect to Claude:**
The server will output connection instructions for Claude to connect via MCP.

## Basic Operations

### Send an Email
```json
{
  "method": "email.send",
  "params": {
    "to": ["recipient@example.com"],
    "subject": "Test Email",
    "body": "This is a test email from the MCP server.",
    "attachments": []
  }
}
```

### Draft an Email
```json
{
  "method": "email.draft",
  "params": {
    "to": ["recipient@example.com"],
    "subject": "Draft Email",
    "body": "This is a draft email."
  }
}
```

### Search Emails
```json
{
  "method": "email.search",
  "params": {
    "query": "meeting notes",
    "folder": "inbox",
    "limit": 10
  }
}
```

### Move Email to Trash
```json
{
  "method": "email.move",
  "params": {
    "email_id": "msg123456",
    "destination": "trash"
  }
}
```

## Testing

Run the test suite:
```bash
uv run pytest
```

## Development

1. **Environment Setup:**
```bash
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

2. **Run in development mode:**
```bash
uv run --with-dev main.py --debug
```

## Troubleshooting

- **Connection Issues**: Verify email provider settings and authentication credentials
- **Authentication Failures**: Check OAuth 2.0 configuration or IMAP/SMTP settings
- **Rate Limiting**: The server implements rate limiting; check logs for exceeded limits
- **Attachment Issues**: Verify file size is under 25MB limit and type is supported
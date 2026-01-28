# Email MCP Server API Contract

## Overview
This document defines the API contract for the Email MCP Server. The server communicates via MCP protocol using JSON-RPC over stdio. This contract specifies all the methods and data structures for the email operations supported by the server.

## Common Response Format
All methods return a response in this format:
```json
{
  "result": {
    // Method-specific result data
  },
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message"
  }
}
```

## Methods

### email.send
Send an email message.

**Request:**
```json
{
  "method": "email.send",
  "params": {
    "to": ["recipient@example.com"],
    "cc": ["copy@example.com"],
    "bcc": ["blind-copy@example.com"],
    "subject": "Subject line",
    "body": "Email body content",
    "html_body": "<p>Email body content</p>",
    "attachments": [
      {
        "filename": "document.pdf",
        "content_type": "application/pdf",
        "data": "base64-encoded-content"
      }
    ]
  }
}
```

**Response:**
```json
{
  "result": {
    "success": true,
    "message_id": "server-generated-message-id",
    "timestamp": "2026-01-20T10:30:00Z"
  }
}
```

### email.draft
Create or update a draft email.

**Request:**
```json
{
  "method": "email.draft",
  "params": {
    "draft_id": "optional-draft-id-for-update",
    "to": ["recipient@example.com"],
    "cc": ["copy@example.com"],
    "bcc": ["blind-copy@example.com"],
    "subject": "Subject line",
    "body": "Email body content",
    "html_body": "<p>Email body content</p>",
    "attachments": [
      {
        "filename": "document.pdf",
        "content_type": "application/pdf",
        "data": "base64-encoded-content"
      }
    ]
  }
}
```

**Response:**
```json
{
  "result": {
    "success": true,
    "draft_id": "generated-or-existing-draft-id",
    "timestamp": "2026-01-20T10:30:00Z"
  }
}
```

### email.search
Search for emails based on criteria.

**Request:**
```json
{
  "method": "email.search",
  "params": {
    "query": "search terms",
    "folder": "inbox",
    "sender": "sender@example.com",
    "after_date": "2026-01-01",
    "before_date": "2026-01-31",
    "limit": 50,
    "offset": 0
  }
}
```

**Response:**
```json
{
  "result": {
    "emails": [
      {
        "id": "message-id",
        "sender": "sender@example.com",
        "recipients": ["recipient@example.com"],
        "subject": "Subject line",
        "preview": "First 100 characters of email body...",
        "timestamp": "2026-01-20T10:30:00Z",
        "read": false,
        "has_attachments": true
      }
    ],
    "total_count": 5,
    "limit": 50,
    "offset": 0
  }
}
```

### email.get
Retrieve a specific email by ID.

**Request:**
```json
{
  "method": "email.get",
  "params": {
    "email_id": "message-id"
  }
}
```

**Response:**
```json
{
  "result": {
    "id": "message-id",
    "sender": "sender@example.com",
    "recipients": ["recipient@example.com"],
    "cc": ["copy@example.com"],
    "bcc": [],
    "subject": "Subject line",
    "body": "Plain text body",
    "html_body": "<p>HTML body</p>",
    "timestamp": "2026-01-20T10:30:00Z",
    "read": false,
    "importance": "normal",
    "folder": "inbox",
    "attachments": [
      {
        "id": "attachment-id",
        "filename": "document.pdf",
        "content_type": "application/pdf",
        "size": 123456
      }
    ]
  }
}
```

### email.move
Move an email to a different folder.

**Request:**
```json
{
  "method": "email.move",
  "params": {
    "email_id": "message-id",
    "destination": "trash|archive|custom-folder-name"
  }
}
```

**Response:**
```json
{
  "result": {
    "success": true,
    "moved_to": "trash",
    "timestamp": "2026-01-20T10:30:00Z"
  }
}
```

### email.mark
Mark an email as read/unread or set importance.

**Request:**
```json
{
  "method": "email.mark",
  "params": {
    "email_id": "message-id",
    "read": true,
    "importance": "high"
  }
}
```

**Response:**
```json
{
  "result": {
    "success": true,
    "updated_fields": ["read", "importance"],
    "timestamp": "2026-01-20T10:30:00Z"
  }
}
```

### email.reply
Reply to an existing email.

**Request:**
```json
{
  "method": "email.reply",
  "params": {
    "email_id": "message-id-to-reply-to",
    "body": "Reply content",
    "html_body": "<p>Reply content</p>",
    "reply_all": false,
    "attachments": []
  }
}
```

**Response:**
```json
{
  "result": {
    "success": true,
    "message_id": "server-generated-message-id",
    "timestamp": "2026-01-20T10:30:00Z"
  }
}
```

### email.forward
Forward an existing email to new recipients.

**Request:**
```json
{
  "method": "email.forward",
  "params": {
    "email_id": "message-id-to-forward",
    "to": ["new-recipient@example.com"],
    "body": "Additional message",
    "html_body": "<p>Additional message</p>",
    "attachments": []
  }
}
```

**Response:**
```json
{
  "result": {
    "success": true,
    "message_id": "server-generated-message-id",
    "timestamp": "2026-01-20T10:30:00Z"
  }
}
```

### email.list_folders
List available email folders.

**Request:**
```json
{
  "method": "email.list_folders",
  "params": {}
}
```

**Response:**
```json
{
  "result": {
    "folders": [
      {
        "name": "inbox",
        "type": "inbox",
        "email_count": 42
      },
      {
        "name": "sent",
        "type": "sent",
        "email_count": 28
      },
      {
        "name": "drafts",
        "type": "drafts",
        "email_count": 5
      },
      {
        "name": "trash",
        "type": "trash",
        "email_count": 120
      },
      {
        "name": "archive",
        "type": "archive",
        "email_count": 350
      }
    ]
  }
}
```

## Error Codes
- `AUTH_ERROR`: Authentication failed
- `VALIDATION_ERROR`: Invalid parameters provided
- `RATE_LIMIT_EXCEEDED`: Too many requests
- `PROVIDER_UNAVAILABLE`: Email provider is temporarily unavailable
- `QUOTA_EXCEEDED`: Storage or attachment size limits exceeded
- `NOT_FOUND`: Requested email or folder does not exist
- `PERMISSION_DENIED`: Insufficient permissions for the operation
- `INTERNAL_ERROR`: Server-side error occurred
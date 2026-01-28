# Data Model: Email MCP Server

## Core Entities

### Email
- **id**: String (unique identifier from email provider)
- **sender**: String (email address of sender)
- **recipients**: Array<String> (email addresses of recipients)
- **subject**: String (email subject line)
- **body**: String (email body content, supports plain text and HTML)
- **timestamp**: DateTime (time when email was sent/received)
- **read_status**: Boolean (whether email has been read)
- **importance_level**: Enum ['low', 'normal', 'high'] (importance classification)
- **folder**: String (current folder location: inbox, sent, drafts, trash, archive, etc.)
- **attachments**: Array<Attachment> (list of attached files)

### Attachment
- **id**: String (unique identifier)
- **filename**: String (original filename)
- **content_type**: String (MIME type)
- **size**: Integer (file size in bytes)
- **url**: String (reference to stored file)

### Draft
- **id**: String (unique identifier)
- **sender_account**: String (reference to EmailAccount)
- **recipients**: Array<String> (to, cc, bcc recipients)
- **subject**: String (email subject line)
- **body**: String (email body content)
- **created_at**: DateTime (timestamp when draft was created)
- **updated_at**: DateTime (timestamp when draft was last modified)
- **attachments**: Array<Attachment> (list of attached files)

### EmailAccount
- **id**: String (unique identifier)
- **provider**: String (email provider name: Gmail, Outlook, etc.)
- **email_address**: String (the email address)
- **auth_method**: Enum ['oauth2', 'password'] (authentication method used)
- **config_template**: String (configuration template used for setup)
- **last_connected**: DateTime (last successful connection timestamp)

### OperationLog
- **id**: String (unique identifier)
- **operation_type**: Enum ['send', 'draft', 'search', 'move', 'archive', 'reply', 'forward']
- **account_id**: String (reference to EmailAccount)
- **timestamp**: DateTime (when operation was attempted)
- **status**: Enum ['success', 'failure', 'pending']
- **details**: Object (operation-specific details)

### Folder
- **id**: String (unique identifier)
- **name**: String (display name of folder)
- **type**: Enum ['inbox', 'sent', 'drafts', 'trash', 'archive', 'custom']
- **email_count**: Integer (number of emails in folder)
- **parent_folder**: String (optional, reference to parent folder for hierarchical structure)

### SearchResult
- **query**: String (search query that was executed)
- **results**: Array<Email> (emails matching the search criteria)
- **total_count**: Integer (total number of matching emails)
- **timestamp**: DateTime (when search was performed)

## Relationships
- EmailAccount 1 → * Email (an account can have many emails)
- EmailAccount 1 → * Draft (an account can have many drafts)
- Email 1 → * Attachment (an email can have multiple attachments)
- Email * → 1 Folder (emails belong to a folder)
- OperationLog * → 1 EmailAccount (operations are logged per account)

## Validation Rules
- Email addresses must be valid format
- Attachment sizes must not exceed 25MB
- Subject and body must not be empty for sending operations
- Account credentials must be validated before operations
- Operation logs must be created for all email operations

## State Transitions
- Email: draft → sent, inbox → trash, inbox → archive
- Draft: created → modified → sent/deleted
- OperationLog: pending → success/

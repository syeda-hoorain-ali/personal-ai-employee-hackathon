---
id: PHR-003
title: Fix-Email-Marking-Functionality
stage: misc
date: 2026-01-21
model: qwen3-coder-plus
feature: 002-email-mcp-server
branch: 002-email-mcp-server
user: dell
command: "fix email marking functionality and tests"
labels: ["email-mcp-server", "bug-fix", "email-marking", "imap", "integration-tests"]
files:
  - "email_mcp_server/src/email_mcp_server/protocols/imap_smtp.py"
  - "email_mcp_server/src/email_mcp_server/email_operations/management.py"
  - "email_mcp_server/src/email_mcp_server/models/response.py"
  - "email_mcp_server/tests/email_mcp_server/integration/test_email_marking.py"
tests:
  - "tests/email_mcp_server/integration/test_email_marking.py"
---

# Fix Email Marking Functionality

## Prompt

Fix email marking functionality and tests - the IMAP STORE command was failing due to incorrect flag formatting, and the tests were using invalid email IDs.

## Response

Successfully fixed the email marking functionality in the Email MCP Server with the following changes:

### Issues Fixed

1. **IMAP STORE Command Error**: Fixed "Could not parse command" error by correcting the flag format in the IMAP STORE command in `imap_smtp.py`. The issue was with escape sequences - changed from `\\\\Seen` to `\\Seen` which is the proper IMAP flag format.

2. **Invalid Email IDs**: Updated tests to search for real emails in the mailbox instead of using fake email IDs like "test-message-id-12345".

3. **Response Model Issue**: Added optional `message` field to `MarkEmailResponse` model to properly handle error responses.

4. **Account Reference Bug**: Fixed incorrect reference to `mock_account` instead of `account` in the management.py file.

### Changes Made

1. **Fixed IMAP Flag Format** (`email_mcp_server/src/email_mcp_server/protocols/imap_smtp.py`):
   - Changed `\\\\Seen` to `\\Seen` for read/unread flags
   - Changed `\\\\Flagged` and `\\\\Draft` to `\\Flagged` and `\\Draft` for importance flags
   - Added result assignment to STORE commands

2. **Fixed Account Reference** (`email_mcp_server/src/email_mcp_server/email_operations/management.py`):
   - Changed `account_id=mock_account.id` to `account_id=account.id` in operation logging

3. **Enhanced Response Model** (`email_mcp_server/src/email_mcp_server/models/response.py`):
   - Added `message: Optional[str] = None` to `MarkEmailResponse` model

4. **Updated Tests** (`email_mcp_server/tests/email_mcp_server/integration/test_email_marking.py`):
   - Modified all test methods to search for real emails in the INBOX before attempting to mark them
   - Added logic to send a test email if none exist in the mailbox
   - Implemented proper email client setup with credentials

### Testing

All email marking tests now pass successfully:
- `test_mark_email_as_read`: ✓ PASSED
- `test_mark_email_as_unread`: ✓ PASSED
- `test_mark_email_importance_low`: ✓ PASSED
- `test_mark_email_importance_normal`: ✓ PASSED
- `test_mark_email_importance_high`: ✓ PASSED
- `test_mark_email_both_read_and_importance`: ✓ PASSED
- `test_invalid_importance_level`: ✓ PASSED

Additionally, all 22 integration tests pass (22 passed, 1 skipped), confirming that the fix didn't break any existing functionality.

## Outcome

The Email MCP Server now properly supports email marking functionality (read/unread status and importance levels) with working integration tests that use real email IDs from the user's mailbox. The IMAP STORE command errors have been resolved, and the system can successfully mark emails with various flags.
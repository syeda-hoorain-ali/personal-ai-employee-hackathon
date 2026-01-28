---
id: PHR-004
title: Add-Email-Delete-Functionality
stage: misc
date: 2026-01-22
model: qwen3-coder-plus
feature: 002-email-mcp-server
branch: 002-email-mcp-server
user: dell
command: "add email delete functionality and tests"
labels: ["email-mcp-server", "feature-addition", "email-delete", "imap", "integration-tests"]
files:
  - "email_mcp_server/src/email_mcp_server/protocols/imap_smtp.py"
  - "email_mcp_server/src/email_mcp_server/models/response.py"
  - "email_mcp_server/src/email_mcp_server/email_operations/management.py"
  - "email_mcp_server/tests/email_mcp_server/integration/test_delete_email.py"
  - "email_mcp_server/tests/email_mcp_server/integration/test_complete_workflow.py"
tests:
  - "tests/email_mcp_server/integration/test_delete_email.py"
  - "tests/email_mcp_server/integration/test_complete_workflow.py"
---

# Add Email Delete Functionality

## Prompt

Add a test to delete emails in the Email MCP Server.

## Response

Successfully implemented complete email deletion functionality in the Email MCP Server with the following additions:

### Features Added

1. **IMAP Delete Function**: Added `delete_email()` method to the `EmailClient` class in `imap_smtp.py` that marks emails with the `\Deleted` flag and expunges them to permanently remove.

2. **Response Model**: Added `DeleteEmailResponse` model with `deleted_email_id` field to track deleted emails.

3. **Operation Type**: Added `DELETE` operation type to the `OperationType` enum.

4. **Management Function**: Added `delete_email()` async function in the management module that provides the public API for email deletion.

5. **Comprehensive Tests**: Created `test_delete_email.py` with tests for single email deletion, multiple email deletion, and error handling for nonexistent emails.

6. **Complete Workflow Integration**: Updated the complete workflow test to include a delete step, making the full workflow: Send → Search → Move → Archive → Delete.

### Changes Made

1. **Protocol Handler** (`email_mcp_server/src/email_mcp_server/protocols/imap_smtp.py`):
   - Added `delete_email()` method that implements the IMAP deletion process
   - Uses `STORE` command with `\Deleted` flag and `EXPUNGE` to permanently remove emails

2. **Response Models** (`email_mcp_server/src/email_mcp_server/models/response.py`):
   - Added `DeleteEmailResponse` class
   - Added `DELETE` to `OperationType` enum

3. **Management Operations** (`email_mcp_server/src/email_mcp_server/email_operations/management.py`):
   - Added `delete_email()` async function
   - Updated imports to include `DeleteEmailResponse`

4. **Integration Tests** (`email_mcp_server/tests/email_mcp_server/integration/test_delete_email.py`):
   - Created comprehensive test suite for email deletion
   - Tests single email deletion, multiple email deletion, and error handling

5. **Complete Workflow Test** (`email_mcp_server/tests/email_mcp_server/integration/test_complete_workflow.py`):
   - Added delete step to the complete workflow
   - Updated workflow documentation to include deletion step

### Testing Results

- All 3 new email deletion tests pass successfully
- Complete workflow test now includes deletion step and passes
- All 26 integration tests pass (26 passed, 1 skipped)
- The email deletion functionality works correctly for:
  - Deleting single emails
  - Deleting multiple emails in sequence
  - Proper error handling for invalid email IDs
  - Integration with the complete email workflow

## Outcome

The Email MCP Server now fully supports email deletion functionality with proper integration tests. Users can permanently delete emails using the new delete API, which properly marks emails for deletion and expunges them from the mailbox. The complete email workflow now includes all five steps: Send → Search → Move → Archive → Delete.
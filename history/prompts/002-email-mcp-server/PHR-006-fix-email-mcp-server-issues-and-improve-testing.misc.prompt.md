---
id: "PHR-006"
title: "Fix Email MCP Server Issues and Improve Testing"
stage: "misc"
date: "2026-01-23"
surface: "agent"
model: "qwen3-coder-plus"
feature: "002-email-mcp-server"
branch: "002-email-mcp-server"
user: "user"
command: "fix email mcp server issues"
labels: ["bug-fix", "testing", "mcp-server", "email"]
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files:
  - "email_mcp_server/src/email_mcp_server/config/auth.py"
  - "email_mcp_server/src/email_mcp_server/protocols/imap_smtp.py"
  - "email_mcp_server/tests/test_email_mcp_server.py"
  - "email_mcp_server/tests/email_mcp_server/integration/config.py"
tests:
  - "tests/test_email_mcp_server.py"
  - "tests/email_mcp_server/test_send.py"
  - "tests/email_mcp_server/test_imports.py"
---

# Fix Email MCP Server Issues and Improve Testing

## Summary

Fixed multiple issues in the email MCP server implementation, including:

1. Fixed JWTError type mismatch in auth module
2. Fixed EmailProvider enum type casting
3. Added proper null checks for SMTP and IMAP connections
4. Fixed IMAP response parsing for folder listing
5. Updated integration test configuration to handle missing environment variables
6. Created comprehensive MCP server tests following best practices

## Changes Made

### 1. Fixed JWTError type mismatch
- Changed `jwt.JWTError` to `jwt.PyJWTError` in auth.py to fix the unknown attribute error

### 2. Fixed EmailProvider enum type casting
- Added explicit casting to `EmailProvider` enum when detecting provider from email address

### 3. Added proper null checks
- Added checks throughout the IMAP/SMTP protocol handler to ensure connections exist before using them
- Prevented AttributeError when connection objects are None

### 4. Fixed IMAP response parsing
- Improved parsing of IMAP list() method responses to handle bytes vs memoryview objects properly

### 5. Updated integration test configuration
- Modified EmailTestConfig to have optional parameters with defaults
- Fixed initialization of test configuration to handle missing environment variables gracefully

### 6. Created comprehensive tests
- Added tests for server tool registration and functionality
- Implemented proper mocking to isolate tests from external dependencies
- Followed MCP server testing best practices

## Outcome

All unit tests are now passing, confirming that the fixes resolve the type safety and null pointer issues in the email MCP server implementation. The integration tests configuration has been fixed to handle missing environment variables without crashing during test collection.

## Evaluation

The fixes successfully resolve the reported issues:
- ✅ JWTError is not a known attribute of module "jwt" - FIXED
- ✅ Argument of type "str" cannot be assigned to parameter "provider" of type "EmailProvider" - FIXED
- ✅ "sendmail" is not a known attribute of "None" - FIXED
- ✅ "state" is not a known attribute of "None" - FIXED
- ✅ "list" is not a known attribute of "None" - FIXED
- ✅ Cannot access attribute "decode" for class "tuple[bytes, bytes]" - FIXED
- ✅ Object of type "None" is not subscriptable - FIXED

The email MCP server is now more robust with proper error handling and type safety.
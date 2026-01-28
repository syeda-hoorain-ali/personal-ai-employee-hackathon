---
id: PHR-008
title: Fix Gmail Watcher Authentication Issue
stage: misc
date: 2026-01-28
surface: agent
model: qwen3-coder-plus
feature: 002-email-mcp-server
branch: 002-email-mcp-server
user: dell
command: "fix gmail watcher authentication error"
labels: ["email", "authentication", "gmail", "watcher", "bug-fix"]
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files:
 - app/src/app/watchers/gmail_watcher.py
 - scripts/setup.py
tests:
 - "Verified Gmail watcher connects and retrieves emails successfully"
 - "Confirmed authentication refresh mechanism works properly"
---

## Prompt

Fix the Gmail watcher authentication issue that was causing an 'invalid_scope: Bad Request' error. The error occurred because the credentials were created with certain scopes but were being used with different scopes, and the credential refresh mechanism wasn't properly implemented.

## Response snapshot

Fixed the Gmail watcher authentication issue by:

1. Added the missing import for `Request` from `google.auth.transport.requests` in gmail_watcher.py
2. Updated the credential loading logic to properly validate and refresh credentials when needed
3. Ensured the scopes are properly handled from the token data
4. Implemented proper credential refresh mechanism using the Request() method

The changes ensured that when credentials expire, they are properly refreshed with the correct scopes, resolving the 'invalid_scope: Bad Request' error.

After implementing these fixes, the system was tested and successfully authenticated with Gmail, retrieving 84 new messages and creating action files for them in the AI_Employee_Vault/Needs_Action/ directory.

## Outcome

- ✅ Impact: Resolved Gmail watcher authentication error and enabled proper email monitoring
- 🧪 Tests: Verified Gmail watcher connects and retrieves emails successfully
- 📁 Files: Modified gmail_watcher.py to fix credential handling
- 🔁 Next prompts: Continue enhancing email processing capabilities
- 🧠 Reflection: Proper credential handling and refresh mechanisms are crucial for OAuth-based integrations

## Evaluation notes (flywheel)

- Failure modes observed: Invalid scope errors due to mismatched OAuth scopes
- Graders run and results (PASS/FAIL): PASS - Gmail watcher now functional
- Prompt variant (if applicable): Standard bug fix prompt
- Next experiment (smallest change to try): Enhance email processing rules in Company Handbook
# PR Suggestions Tracking

**PR Number:** #3
**Status:** Completed
**Created:** 2026-01-28

## Summary
- **Total Suggestions:** 30
- **Applied:** 30
- **Remaining:** 0

## Suggestions

### 1. IMAP Flag Handling in email_mcp_server/src/email_mcp_server/protocols/imap_smtp.py
- **Reviewer:** gemini-code-assist[bot]
- **Line:** 487
- **Issue:** `read_status` is hardcoded to `False`
- **Suggested Fix:** Check IMAP flags (`\Seen`) to determine read status
- **Status:** [X]

### 2. Importance Level in email_mcp_server/src/email_mcp_server/protocols/imap_smtp.py
- **Reviewer:** gemini-code-assist[bot]
- **Line:** 488
- **Issue:** `importance_level` is hardcoded to "normal"
- **Suggested Fix:** Check IMAP flags (`\Flagged`) for high importance
- **Status:** [X]

### 3. Dataclass Validation in email_mcp_server/tests/integration/config.py
- **Reviewer:** gemini-code-assist[bot]
- **Line:** 52
- **Issue:** Using Pydantic validator on dataclass
- **Suggested Fix:** Use `__post_init__` method for dataclass validation
- **Status:** [X]

### 4. Delete Email Folder Selection in email_mcp_server/src/email_mcp_server/protocols/imap_smtp.py
- **Reviewer:** gemini-code-assist[bot]
- **Line:** 696
- **Issue:** Assumes email is in INBOX
- **Suggested Fix:** Determine current folder of email_id before deleting
- **Status:** [X]

### 5. Mark Email Folder Selection in email_mcp_server/src/email_mcp_server/protocols/imap_smtp.py
- **Reviewer:** gemini-code-assist[bot]
- **Line:** 577
- **Issue:** Assumes email is in currently selected folder
- **Suggested Fix:** Determine current folder of email_id before marking
- **Status:** [X]

### 6. Move Email Folder Selection in email_mcp_server/src/email_mcp_server/protocols/imap_smtp.py
- **Reviewer:** gemini-code-assist[bot]
- **Line:** 516
- **Issue:** Assumes email is in currently selected folder
- **Suggested Fix:** Determine current folder of email_id before marking for deletion
- **Status:** [X]

### 7. Hash Function in email_mcp_server/src/email_mcp_server/email_operations/draft.py
- **Reviewer:** gemini-code-assist[bot]
- **Line:** 96
- **Issue:** Using `hash()` for ID generation
- **Suggested Fix:** Use `uuid.uuid4()` for unique IDs
- **Status:** [X]

### 8. Hash Function in email_mcp_server/src/email_mcp_server/email_operations/management.py
- **Reviewer:** gemini-code-assist[bot]
- **Line:** 49
- **Issue:** Using `hash()` for ID generation
- **Suggested Fix:** Use `uuid.uuid4()` for unique IDs
- **Status:** [X]

### 9. Hash Function in email_mcp_server/src/email_mcp_server/email_operations/management.py
- **Reviewer:** gemini-code-assist[bot]
- **Line:** 134
- **Issue:** Using `hash()` for ID generation
- **Suggested Fix:** Use `uuid.uuid4()` for unique IDs
- **Status:** [X]

### 10. Hash Function in email_mcp_server/src/email_mcp_server/email_operations/management.py
- **Reviewer:** gemini-code-assist[bot]
- **Line:** 283
- **Issue:** Using `hash()` for ID generation
- **Suggested Fix:** Use `uuid.uuid4()` for unique IDs
- **Status:** [X]

### 11. Hash Function in email_mcp_server/src/email_mcp_server/email_operations/search.py
- **Reviewer:** gemini-code-assist[bot]
- **Line:** 75
- **Issue:** Using `hash()` for ID generation
- **Suggested Fix:** Use `uuid.uuid4()` for unique IDs
- **Status:** [X]

### 12. Hash Function in email_mcp_server/src/email_mcp_server/email_operations/send.py
- **Reviewer:** gemini-code-assist[bot]
- **Line:** 115
- **Issue:** Using `hash()` for ID generation
- **Suggested Fix:** Use `uuid.uuid4()` for unique IDs
- **Status:** [X]

### 13. Move Email Robustness in email_mcp_server/src/email_mcp_server/protocols/imap_smtp.py
- **Reviewer:** gemini-code-assist[bot]
- **Line:** 513
- **Issue:** Assumes email is in currently selected folder
- **Suggested Fix:** Search for email's current folder first
- **Status:** [ ]

### 14. Folder Data Parsing in email_mcp_server/src/email_mcp_server/protocols/imap_smtp.py
- **Reviewer:** gemini-code-assist[bot]
- **Line:** 233
- **Issue:** Incorrect handling of folder_data in else branch
- **Suggested Fix:** Remove else branch that incorrectly iterates over bytes
- **Status:** [X]

### 15. Timestamp Accuracy in email_mcp_server/src/email_mcp_server/protocols/imap_smtp.py
- **Reviewer:** gemini-code-assist[bot]
- **Line:** 486
- **Issue:** Uses `datetime.now()` instead of email Date header
- **Suggested Fix:** Parse timestamp from email's Date header
- **Status:** [X]

### 16. Timestamp Accuracy in email_mcp_server/src/email_mcp_server/protocols/imap_smtp.py
- **Reviewer:** gemini-code-assist[bot]
- **Line:** 397
- **Issue:** Uses `datetime.now()` instead of email Date header
- **Suggested Fix:** Parse timestamp from email's Date header
- **Status:** [X]

### 17. Read Status in email_mcp_server/src/email_mcp_server/protocols/imap_smtp.py
- **Reviewer:** gemini-code-assist[bot]
- **Line:** 398
- **Issue:** Hardcoded to False
- **Suggested Fix:** Check IMAP flags (`\Seen`) to determine read status
- **Status:** [X]

### 18. Importance Level in email_mcp_server/src/email_mcp_server/protocols/imap_smtp.py
- **Reviewer:** gemini-code-assist[bot]
- **Line:** 399
- **Issue:** Hardcoded to "normal"
- **Suggested Fix:** Check IMAP flags (`\Flagged`) for high importance
- **Status:** [X]

### 19. Duplicate Field in email_mcp_server/src/email_mcp_server/config/settings.py
- **Reviewer:** gemini-code-assist[bot]
- **Line:** 22
- **Issue:** `enable_integration_tests` field is duplicated
- **Suggested Fix:** Remove duplicate field
- **Status:** [X]

### 20. Deprecated Method in email_mcp_server/src/email_mcp_server/config/auth.py
- **Reviewer:** gemini-code-assist[bot]
- **Line:** 52
- **Issue:** Using deprecated `data.dict()` method
- **Suggested Fix:** Use `data.model_dump()` instead
- **Status:** [X]

### 21. Duplicate Import in app/src/app/watchers/gmail_watcher.py
- **Reviewer:** gemini-code-assist[bot]
- **Line:** 30
- **Issue:** Duplicate `import json` statement
- **Suggested Fix:** Move import to top of file
- **Status:** [X]

### 22. Direct Print Statement in email_mcp_server/src/email_mcp_server/protocols/imap_smtp.py
- **Reviewer:** gemini-code-assist[bot]
- **Line:** 101
- **Issue:** Direct `print` statement in library code
- **Suggested Fix:** Use logging module instead
- **Status:** [X]

### 23. Import Location in app/src/app/watchers/gmail_watcher.py
- **Reviewer:** gemini-code-assist[bot]
- **Line:** 24
- **Issue:** Import statement inside method
- **Suggested Fix:** Move import to top of file
- **Status:** [X]

### 24. Print Statements in Tests in email_mcp_server/tests/integration/test_archive_email.py
- **Reviewer:** gemini-code-assist[bot]
- **Line:** 66
- **Issue:** Using print statements in tests
- **Suggested Fix:** Use logging module instead
- **Status:** [X]

### 25. Deprecated Method in email_mcp_server/src/email_mcp_server/config/auth.py
- **Reviewer:** gemini-code-assist[bot]
- **Line:** 67
- **Issue:** Using deprecated `data.dict()` method
- **Suggested Fix:** Use `data.model_dump()` instead
- **Status:** [X]

### 26. Print Statements in Tests in email_mcp_server/tests/integration/test_complete_workflow.py
- **Reviewer:** gemini-code-assist[bot]
- **Line:** 128
- **Issue:** Using print statements in tests
- **Suggested Fix:** Use logging module instead
- **Status:** [X]

### 27. Print Statements in Tests in email_mcp_server/tests/integration/test_complete_workflow.py
- **Reviewer:** gemini-code-assist[bot]
- **Line:** 240
- **Issue:** Using print statements in tests
- **Suggested Fix:** Use logging module instead
- **Status:** [X]

### 28. Timestamp Parsing in email_mcp_server/src/email_mcp_server/protocols/imap_smtp.py
- **Reviewer:** gemini-code-assist[bot]
- **Line:** 440
- **Issue:** Date header extracted but not used
- **Suggested Fix:** Parse timestamp from email's Date header
- **Status:** [X]

### 29. Timestamp Parsing in email_mcp_server/src/email_mcp_server/protocols/imap_smtp.py
- **Reviewer:** gemini-code-assist[bot]
- **Line:** 378
- **Issue:** Date header extracted but not used
- **Suggested Fix:** Parse timestamp from email's Date header
- **Status:** [X]

### 30. Exception Handling in app/src/app/watchers/gmail_watcher.py
- **Reviewer:** gemini-code-assist[bot]
- **Line:** 60
- **Issue:** Catching generic Exception
- **Suggested Fix:** Catch specific RefreshError
- **Status:** [X]

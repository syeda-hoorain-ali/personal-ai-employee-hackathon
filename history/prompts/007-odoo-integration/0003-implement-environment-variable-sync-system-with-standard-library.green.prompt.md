---
id: 0003
title: Implement Environment Variable Sync System with Standard Library
stage: green
date: 2026-03-04
surface: agent
model: claude-sonnet-4-6
feature: 007-odoo-integration
branch: 007-odoo-integration
user: user
command: implementation
labels: ["environment-variables", "setup", "ux-improvement", "standard-library", "cross-platform"]
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files:
  - scripts/env_sync.py (created)
  - scripts/sync_env_vars.py (created)
  - scripts/setup.py (modified)
  - USER_GUIDE.md (modified)
  - app/scripts/weekly_briefing_trigger.py (modified)
  - .env.example (validated)
tests:
  - Ran sync_env_vars.py successfully
  - Verified 11 environment variables synced
  - Confirmed sensitive values masked in output
  - Tested cross-platform path handling
---

## Prompt

User identified a UX problem: Claude Code's MCP servers don't support .env files directly - they need actual environment variables. Users were being asked to run complex shell commands to set environment variables, which is inconvenient.

User requested implementation of a solution:
1. Users maintain all variables in .env file (simple, familiar)
2. setup.py automatically reads .env and sets variables permanently + in current session
3. Standalone script for syncing when .env is updated
4. CRITICAL CONSTRAINT: Use only built-in Python modules (no external dependencies) since scripts run before/outside virtual environment

User also requested:
- Update weekly_briefing_trigger.py to use VAULT_PATH instead of OBSIDIAN_VAULT for consistency
- Document the new workflow in USER_GUIDE.md

## Response snapshot

Implemented a complete environment variable sync system using only Python standard library:

**1. Core Module (scripts/env_sync.py)**
- Custom .env parser using regex (handles comments, quotes, empty lines)
- Platform detection (Windows vs Unix)
- Permanent variable setting:
  - Windows: Uses `setx` command for user-level variables
  - Unix: Appends export statements to shell profile (.bashrc, .zshrc, etc.)
- Session variable setting: `os.environ[key] = value`
- Security: Masks sensitive values (PASSWORD, SECRET, KEY, TOKEN) in output
- Error handling with graceful degradation

**2. Standalone Script (scripts/sync_env_vars.py)**
- User-friendly wrapper around env_sync module
- Clear output with progress indicators
- Helpful error messages if .env missing
- Platform-specific next steps guidance

**3. Integration into setup.py**
- Added import: `import env_sync`
- Added sync call at start of main() (before venv setup)
- Warns if .env missing but continues setup
- Makes variables available for MCP servers

**4. Documentation (USER_GUIDE.md)**
- Added step 3: "Configure Environment Variables" in setup process
- Added new section: "Updating Environment Variables"
- Clear instructions on when and how to update
- Platform-specific notes for Windows and Unix

**5. Consistency Fix (weekly_briefing_trigger.py)**
- Changed from `OBSIDIAN_VAULT` to `VAULT_PATH`
- Uses `Path(vault_path).name` to extract directory name
- Handles relative and absolute paths correctly

**Testing Results:**
```
[SUCCESS] Environment variables synced:
          11 variables set successfully
          Variables are available in current session
          Permanent variables set via setx (user-level)
          Note: New terminals will have these variables
```

## Outcome

- ✅ Impact: Dramatically improved UX - users now only edit .env file instead of running complex shell commands. Zero-dependency solution works before venv activation.
- 🧪 Tests: Successfully ran sync_env_vars.py, verified 11 variables synced with sensitive values masked
- 📁 Files: Created 2 new scripts (env_sync.py, sync_env_vars.py), modified 3 files (setup.py, USER_GUIDE.md, weekly_briefing_trigger.py)
- 🔁 Next prompts: Test full setup.py flow, verify MCP servers pick up variables, consider adding validation for required variables
- 🧠 Reflection: Standard library constraint was critical - solution must work before any dependencies installed. Path handling needed careful consideration for cross-platform compatibility.

## Evaluation notes (flywheel)

- Failure modes observed: Initial attempt to add OBSIDIAN_VAULT to .env.example was rejected - user correctly identified VAULT_PATH should be used instead for consistency
- Graders run and results (PASS/FAIL): Manual testing PASS - sync script successfully set 11 variables with proper masking
- Prompt variant (if applicable): N/A
- Next experiment (smallest change to try): Add validation to check for required variables (VAULT_PATH, AGENT_NAME) and warn if missing

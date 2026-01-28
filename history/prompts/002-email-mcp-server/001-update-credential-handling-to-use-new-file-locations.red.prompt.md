---
id: PHR-001
title: Update Credential Handling to Use New File Locations
stage: red
date: 2026-01-27
surface: agent
model: qwen3-coder-plus
feature: 002-email-mcp-server
branch: 002-email-mcp-server
user: dell
command: /sp.phr
labels: ['gmail', 'authentication', 'credentials', 'oauth', 'security']
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files:
  - scripts/setup.py
  - app/src/app/watchers/gmail_watcher.py
  - USER_GUIDE.md
tests: []
---

# Update Credential Handling to Use New File Locations

## Original Prompt

--title "Update Credential Handling to Use New File Locations" --stage "red"

## Summary

Updated the Personal AI Employee system to use new credential file locations:
- Changed from `gmail_credentials.json` in project root to `~/.gmail-mcp/gcp-oauth.keys.json`
- Changed from `token.pickle` to `~/.gmail-mcp/credentials.json` (JSON format)
- Updated setup script to use `npx -y @gongrzhe/server-gmail-autoauth-mcp auth` for authentication
- Modified Gmail watcher to handle JSON-formatted credentials
- Updated documentation in USER_GUIDE.md

## Files Modified

- scripts/setup.py: Updated credential paths and authentication flow
- app/src/app/watchers/gmail_watcher.py: Updated to load JSON credentials
- USER_GUIDE.md: Updated documentation for new credential locations

## Outcome

Successfully updated the credential handling system to use the new standardized locations and authentication flow.

## Reflection

This change improves security by storing credentials in a user-specific location rather than in the project directory.

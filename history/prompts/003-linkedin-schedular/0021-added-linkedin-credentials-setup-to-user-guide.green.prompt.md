---
id: 0021
title: Added LinkedIn Credentials Setup To User Guide
stage: green
date: 2026-01-26
surface: agent
model: qwen3-coder-plus
feature: 003-linkedin-schedular
branch: 003-linkedin-schedular
user: dell
command: "manual-write"
labels: [linkedin, credentials, user-guide, documentation, setup]
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files:
 - USER_GUIDE.md
tests:
 - none
---

## Prompt

Add information about setting up LinkedIn credentials in the config.json file to the user guide.

## Response snapshot

Added a comprehensive section to the USER_GUIDE.md file explaining how to set up LinkedIn credentials for the automated posting feature. The new section includes:

1. Instructions for creating the config.json file in the AI_Employee_Vault directory
2. Proper format for adding LinkedIn email and password
3. Important security warnings about storing credentials
4. Information about configuring LinkedIn auto-posting with the scheduler

## Outcome

- ✅ Impact: Users now have clear instructions on how to set up LinkedIn credentials for automated posting
- ✅ Files: Updated USER_GUIDE.md with comprehensive LinkedIn setup instructions
- ✅ Documentation: Added security warnings and best practices for credential management
- ✅ Integration: Connected LinkedIn posting feature with existing scheduler functionality
- 🔄 Next prompts: Users can now properly configure LinkedIn automation following the documented steps

## Evaluation notes (flywheel)

- Failure modes observed: Previously users had no documentation on how to set up LinkedIn credentials
- Graders run and results (PASS/FAIL): PASS - documentation now covers LinkedIn credential setup
- Next experiment (smallest change to try): Test that users can follow the instructions to successfully set up LinkedIn posting
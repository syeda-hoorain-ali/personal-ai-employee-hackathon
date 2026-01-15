---
id: "PHR-003"
title: "Update Setup Script to Auto-Start Watchers"
stage: "misc"
date: "2026-01-15"
surface: "agent"
model: "qwen3-code-plus"
feature: "bronze-tier"
branch: "001-bronze-tier"
user: "Syeda Hoorain Ali"
command: "/sp.phr"
labels: ["ai-employee", "setup", "automation", "watchers", "bronze-tier"]
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files:
  - "setup.py"
tests:
  - "none"
---

# Update Setup Script to Auto-Start Watchers

## PROMPT TEXT

title="Update Setup Script to Auto-Start Watchers" stage="misc" feature="bronze-tier"

## RESPONSE TEXT

Updated the setup.py script to automatically start the AI Employee system after completing the setup process, eliminating the need for separate startup commands.

## OUTCOME IMPACT

Enhanced the setup script with automatic startup functionality, streamlining the user experience by combining setup and runtime into a single command flow. The system now automatically begins monitoring for tasks immediately after setup completes.

## TESTS SUMMARY

- Manual test of updated setup.py script showing successful combined setup and startup

## FILES SUMMARY

- setup.py: Enhanced with automatic startup functionality after setup completion

## NEXT PROMPTS

Consider adding auto-restart capabilities or Windows service integration for automatic startup on boot.

## REFLECTION NOTE

Combining setup and runtime into a single script improves user experience by reducing the number of commands needed to get the system operational.

## EVALUATION

**Failure modes observed:** Initial implementation had emoji character encoding issues on Windows that caused crashes; these were resolved by replacing emojis with plain text indicators.

**Next experiment to improve prompt quality:** Continue using unified setup and runtime scripts to simplify user workflows.
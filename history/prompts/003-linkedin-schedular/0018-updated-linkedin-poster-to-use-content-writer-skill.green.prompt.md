---
id: 0018
title: Updated LinkedIn Poster to Use Content Writer Skill
stage: green
date: 2026-01-25
surface: agent
model: qwen3-coder-plus
feature: 003-linkedin-schedular
branch: 003-linkedin-schedular
user: dell
command: "manual-write"
labels: [linkedin, content-writer, skill, automation, silver-tier, refactoring]
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files:
 - app/scripts/linkedin_poster_cli.py
 - .claude/skills/linkedin-content-writer/SKILL.md
tests:
 - python app/scripts/linkedin_poster_cli.py
---
## Prompt

update the script to use the linkedin-content-writer skill

## Response snapshot

Updated the LinkedIn poster CLI script to reference the LinkedIn content writer skill when generating posts, by modifying the prompt to first use the linkedin-content-writer skill to generate quality content before using the linkedin-poster skill to publish it.

## Outcome

- ✅ Impact: Updated LinkedIn poster script to utilize the LinkedIn content writer skill for better post generation
- ✅ Files: Modified app/scripts/linkedin_poster_cli.py to reference linkedin-content-writer skill, and created .claude/skills/linkedin-content-writer/SKILL.md with content guidelines
- ✅ Silver Tier Requirements: Enhanced automated LinkedIn posting with professional content generation capabilities
- 🔄 Next prompts: Ready to use the improved system for generating business-focused LinkedIn content

## Evaluation notes (flywheel)

- Failure modes observed: Initially had encoding issues with Unicode characters in Claude's output, resolved by proper encoding handling
- Graders run and results (PASS/FAIL): PASS - script now properly communicates with Claude Code and uses both LinkedIn skills
- Next experiment (smallest change to try): Grant permission for the LinkedIn poster skill to complete the actual posting process

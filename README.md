# Personal AI Employee

This is a hackathon project to build an autonomous AI employee that can manage personal and business affairs using Claude Code as the reasoning engine and Obsidian as the management dashboard.

## Architecture

- **The Brain**: Claude Code acts as the reasoning engine
- **The Memory/GUI**: Obsidian (local Markdown) is used as the dashboard
- **The Senses (Watchers)**: Lightweight Python scripts monitor Gmail, WhatsApp, and filesystems
- **The Hands (MCP)**: Model Context Protocol (MCP) servers handle external actions

## Features

- Autonomous business auditing (Monday Morning CEO Briefing)
- Human-in-the-loop approval system for sensitive actions
- Ralph Wiggum loop for persistent task completion
- Multiple achievement tiers (Bronze to Platinum)
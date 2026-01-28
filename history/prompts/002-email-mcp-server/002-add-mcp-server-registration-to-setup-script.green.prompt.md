---
id: PHR-002
title: Add MCP Server Registration to Setup Script
stage: green
date: 2026-01-27
surface: agent
model: qwen3-coder-plus
feature: 002-email-mcp-server
branch: 002-email-mcp-server
user: dell
command: /sp.phr
labels: ['mcp', 'servers', 'registration', 'setup', 'automation']
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files:
  - scripts/setup.py
tests: []
---

# Add MCP Server Registration to Setup Script

## Original Prompt

Add commands to register MCP servers after successful credential setup

## Summary

Added MCP server registration commands to the setup script that run automatically after successful Gmail authentication:
- Registered gmail MCP server using @gongrzhe/server-gmail-autoauth-mcp
- Registered context7 MCP server using @upstash/context7-mcp
- Registered playwright MCP server using @playwright/mcp@latest

## Files Modified

- scripts/setup.py: Added MCP server registration after Gmail authentication

## Outcome

MCP servers are now automatically registered during the setup process if Gmail authentication is successful.

## Reflection

This automation simplifies the setup process by registering all necessary MCP servers in one go.
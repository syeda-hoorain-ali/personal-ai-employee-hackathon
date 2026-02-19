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

## Hackathon Tiers

### **Bronze Tier: Foundation (Minimum Viable Deliverable)**

Estimated time: 8-12 hours

- [X] Obsidian vault with Dashboard.md and Company_Handbook.md
- [X] One working Watcher script (Gmail OR file system monitoring)
- [X] Claude Code successfully reading from and writing to the vault
- [X] Basic folder structure: /Inbox, /Needs_Action, /Done
- [X] All AI functionality should be implemented as [Agent Skills](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview)

### **Silver Tier: Functional Assistant**

Estimated time: 20-30 hours

- [X] All Bronze requirements
- [X] Two or more Watcher scripts (e.g., Gmail + Whatsapp + LinkedIn)
- [X] Automatically Post on LinkedIn about business to generate sales
- [X] Claude reasoning loop that creates Plan.md files
- [X] One working MCP server for external action (e.g., sending emails)
- [X] Human-in-the-loop approval workflow for sensitive actions
- [X] Basic scheduling via cron or Task Scheduler
- [X] All AI functionality should be implemented as [Agent Skills](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview)

### **Gold Tier: Autonomous Employee**

Estimated time: 40+ hours

- [X] All Silver requirements
- [X] Full cross-domain integration (Personal + Business)
- [X] Create accounting system for your business in Xero ( [https://www.xero.com/](https://www.xero.com/) ) and integrate it with its MCP Server ( [https://github.com/XeroAPI/xero-mcp-server](https://github.com/XeroAPI/xero-mcp-server) )
- [-] Integrate Facebook and Instagram and post messages and generate summary
- [X] Integrate Twitter (X) and post messages and generate summary
- [X] Multiple MCP servers for different action types
- [X] Weekly Business and Accounting Audit with CEO Briefing generation
- [ ] Error recovery and graceful degradation
- [x] Comprehensive audit logging
- [X] Ralph Wiggum loop for autonomous multi-step task completion
- [X] Documentation of your architecture and decisions

### **Platinum Tier: Enterprise Solution**

Estimated time: 80+ hours

- [ ] All Gold requirements
- [ ] Advanced AI reasoning with predictive capabilities
- [ ] Multi-user support with role-based access controls
- [ ] Advanced reporting and analytics dashboard
- [ ] Integration with enterprise systems (CRM, ERP, etc.)
- [ ] Advanced security features and compliance
- [ ] Scalable infrastructure with load balancing
- [ ] Advanced error handling and self-healing capabilities
- [ ] Complete documentation suite and user guides
- [ ] Performance optimization and caching strategies

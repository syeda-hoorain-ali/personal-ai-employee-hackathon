# Personal AI Employee - Digital FTE

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
- **Comprehensive Error Recovery System**:
  - Centralized error logging with daily JSON files
  - Automatic retry with exponential backoff for transient errors
  - Circuit breaker pattern to prevent cascading failures
  - Component health monitoring with automatic restart (Watchdog)
  - Operation queuing for service unavailability
  - File quarantine for corrupted data
  - Real-time error dashboard with component health status

## Hackathon Tiers

### Bronze Tier: Foundation (Minimum Viable Deliverable)

Estimated time: 8-12 hours

- [X] Obsidian vault with Dashboard.md and Company_Handbook.md
- [X] One working Watcher script (Gmail OR file system monitoring)
- [X] Claude Code successfully reading from and writing to the vault
- [X] Basic folder structure: `/Inbox`, `/Needs_Action`, `/Done`
- [X] All AI functionality should be implemented as [Agent Skills](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview)

### Silver Tier: Functional Assistant

Estimated time: 20-30 hours
All Bronze requirements plus:

- [X] Two or more Watcher scripts (e.g., Gmail + Whatsapp + LinkedIn)
- [X] Automatically Post on LinkedIn about business to generate sales
- [X] Claude reasoning loop that creates Plan.md files
- [X] One working MCP server for external action (e.g., sending emails)
- [X] Human-in-the-loop approval workflow for sensitive actions
- [X] Basic scheduling via cron or Task Scheduler
- [X] All AI functionality should be implemented as [Agent Skills](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview)

### Gold Tier: Autonomous Employee

Estimated time: 40+ hours
All Silver requirements plus:

- [X] Full cross-domain integration (Personal + Business)
- [X] Create an accounting system for your business in Odoo Community (self-hosted, local) and integrate it via an [MCP server](https://github.com/AlanOgic/mcp-odoo-adv) using Odoo’s JSON-RPC APIs (Odoo 19+).
- [ ] Integrate Facebook and Instagram and post messages and generate summary
- [X] Integrate Twitter (X) and post messages and generate summary
- [X] Multiple MCP servers for different action types
- [X] Weekly Business and Accounting Audit with CEO Briefing generation
- [X] Error recovery and graceful degradation
- [X] Comprehensive audit logging
- [X] Ralph Wiggum loop for autonomous multi-step task completion
- [X] Documentation of your architecture and lessons learned
- [X] All AI functionality should be implemented as [Agent Skills](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview)

### Platinum Tier: Always-On Cloud + Local Executive (Production-ish AI Employee)

Estimated time: 60+ hours
All Gold requirements plus:

- [ ] **Run the AI Employee on Cloud 24/7** (always-on watchers + orchestrator + health monitoring). Deploy to Cloud VM (Oracle/AWS/etc.) - [Oracle Cloud Free VMs](https://www.oracle.com/cloud/free/) can be used for this (subject to limits/availability).

- [ ] **Work-Zone Specialization (domain ownership)**:
  - **Cloud owns:** Email triage + draft replies + social post drafts/scheduling (draft-only; requires Local approval before send/post)
  - **Local owns:** approvals, WhatsApp session, payments/banking, and final "send/post" actions

- [ ] **Delegation via Synced Vault (Phase 1)**
  - Agents communicate by writing files into: `/Needs_Action/<domain>/`, `/Plans/<domain>/`, `/Pending_Approval/<domain>/`
  - Prevent double-work using:
    - `/In_Progress/<agent>/` claim-by-move rule
    - single-writer rule for Dashboard.md (Local)
    - Cloud writes updates to `/Updates/` (or `/Signals/`), and Local merges them into Dashboard.md
  - For Vault sync (Phase 1) use Git (recommended) or Syncthing
  - **Claim-by-move rule:** first agent to move an item from `/Needs_Action` to `/In_Progress/<agent>/` owns it; other agents must ignore it.

- [ ] **Security rule:** Vault sync includes only markdown/state. Secrets never sync (.env, tokens, WhatsApp sessions, banking creds). Cloud never stores or uses WhatsApp sessions, banking credentials, or payment tokens
- [ ] **Deploy Odoo Community on a Cloud VM (24/7)** with HTTPS, backups, and health monitoring; integrate Cloud Agent with Odoo via MCP for draft-only accounting actions and Local approval for posting invoices/payments.
- [ ] **Optional A2A Upgrade (Phase 2):** Replace some file handoffs with direct A2A messages later, while keeping the vault as the audit record
- [ ] **Platinum demo (minimum passing gate):** Email arrives while Local is offline → Cloud drafts reply + writes approval file → when Local returns, user approves → Local executes send via MCP → logs → moves task to `/Done`

#### **Platinum Phase 1A: Vault Sync Infrastructure (COMPLETE)**

**Status**: Implementation complete - Core infrastructure ready for Cloud-Local coordination

**What's Delivered**:
- **Secure Vault Synchronization (US1)**: Git-based vault sync with zero secrets in repository. Pre-commit hooks and .gitignore ensure credentials never leave local machine
- **Domain-Based Work Separation (US2)**: Organized vault structure with domain-specific directories (email/, social/, local-only/) so agents have clear ownership boundaries
- **Conflict-Free Task Claiming (US3)**: Atomic claim-by-move protocol prevents duplicate work. Watchdog monitors stalled tasks and recovers them automatically
- **Dashboard Single-Writer Rule (US4)**: Local agent owns Dashboard.md writes, Cloud agent writes to Updates/ directory to prevent merge conflicts

**Setup Instructions**: See [Platinum Vault Sync Quickstart Guide](specs/006-platinum-vault-sync/quickstart.md) for complete setup and configuration steps

**Architecture**: Cloud and Local agents coordinate through a Git-synced vault with domain-based work zones, atomic task claiming, and single-writer dashboard updates

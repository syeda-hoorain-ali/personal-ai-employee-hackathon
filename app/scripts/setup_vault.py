#!/usr/bin/env python3
"""
Setup script for initializing the AI Employee Vault structure.

This script creates the necessary directory structure and initial files
for the AI Employee system.
"""

import os
import sys
from pathlib import Path
import argparse
import logging


def setup_logging():
    """Set up basic logging configuration."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )


def create_directory_structure(base_path: Path):
    """Create the required directory structure for the AI Employee Vault."""
    directories = [
        'Inbox',
        'Needs_Action',
        'Done',
        'Plans',
        'Pending_Approval',
        'Approved',
        'Rejected',
        'Logs',
        'Accounting'
    ]

    for directory in directories:
        dir_path = base_path / directory
        dir_path.mkdir(parents=True, exist_ok=True)
        logging.info(f"Created directory: {dir_path}")


def create_initial_files(vault_path: Path):
    """Create initial files for the vault."""
    dashboard_path = vault_path / "Dashboard.md"
    if not dashboard_path.exists():
        dashboard_content = """# AI Employee Dashboard

**Last Updated:** {{DATE}}
**Status:** Operational
**Uptime:** 24/7

## Executive Summary
Welcome to your AI Employee dashboard. This system operates 24/7 managing your personal and business affairs autonomously.

## Current Activities
- Monitoring: Gmail, WhatsApp, File System
- Processing: Tasks in `/Needs_Action`
- Waiting for: New tasks and instructions

## Recent Activity
- [{{DATE}}] System initialized and operational
- [{{DATE}}] Vault structure created successfully

## Active Projects
- Current: Project Placeholder
- Status: Status Placeholder

## System Health
- Watchers: Active
- Claude Code: Connected
- MCP Servers: Not configured yet
- Vault Sync: Operational

## Quick Actions
- Add new task: Place file in `/Needs_Action`
- Pause system: Move to `/Paused` folder
- Emergency stop: Contact administrator
"""
        dashboard_path.write_text(dashboard_content)
        logging.info(f"Created initial Dashboard.md: {dashboard_path}")

    handbook_path = vault_path / "Company_Handbook.md"
    if not handbook_path.exists():
        handbook_content = """# Company Handbook for AI Employee

**Document Version:** 1.0
**Last Updated:** {{DATE}}
**Owner:** Human Supervisor

## Purpose
This handbook provides operational guidelines and rules of engagement for the AI Employee. It serves as the primary reference for decision-making and action-taking protocols.

## Communication Guidelines

### Email Responses
- Always be professional and courteous
- Respond within 24 hours to known contacts
- Flag emails from unknown contacts for human approval
- Use formal tone for business communications
- Keep responses concise but informative

### WhatsApp/Messaging
- Always be polite on WhatsApp communications
- Prioritize urgent keywords: 'urgent', 'asap', 'emergency', 'help'
- For payment-related messages, always require human approval
- Flag any unusual requests for human review

## Financial Guidelines

### Payment Processing
- **Auto-approve threshold:** Recurring payments under $50
- **Requires approval:** Any new payee, payments over $100
- **Never auto-process:** First-time vendors without prior approval
- **Flag for review:** Any payment that deviates from standard rates

### Expense Tracking
- Categorize all expenses automatically
- Flag subscriptions unused for 30+ days for review
- Alert human for duplicate charges
- Maintain expense records in `/Accounting/`

## Task Management Rules

### Priority Classification
- **High Priority:** Payment requests, urgent client communications
- **Medium Priority:** Routine communications, status updates
- **Low Priority:** Marketing materials, promotional content

### Processing Workflow
1. New tasks arrive in `/Needs_Action`
2. Review against Company Handbook rules
3. Process according to autonomy level
4. Create approval files for restricted actions
5. Move processed items to `/Done`
6. Update `/Dashboard.md` with status

## Escalation Procedures

### When to Require Human Approval
- Payments to new vendors
- Communications with legal implications
- Requests involving personal/sensitive information
- Any action outside defined autonomy levels
- Unusual or suspicious requests

### Escalation Process
1. Create approval file in `/Pending_Approval`
2. Include all relevant context and options
3. Set expiration time for decision
4. Notify human supervisor
5. Wait for file movement to `/Approved` or `/Rejected`

## Working Hours Guidelines

### Operational Hours
- **Active:** 24/7 monitoring
- **Full Operations:** 6:00 AM - 10:00 PM (local timezone)
- **Limited Operations:** 10:00 PM - 6:00 AM (monitoring only)

### Response Times
- **Standard:** Within 24 hours during active hours
- **Urgent:** Within 2 hours during active hours
- **Emergency:** Immediate during active hours, next morning during limited hours

## Security Protocols

### Access Control
- Never share credentials or access tokens
- Flag any requests for sensitive information
- Use secure channels for all communications
- Maintain audit logs for all actions

### Data Handling
- Keep all data local in vault
- Never transmit sensitive data externally without approval
- Encrypt sensitive files in vault
- Backup important data regularly

## Approval Matrix

| Action | Auto-Approve Threshold | Requires Approval |
|--------|----------------------|-------------------|
| Email replies | Known contacts | New contacts, bulk sends |
| Payments | < $50 recurring | All new payees, > $100 |
| Social media | Scheduled posts | Replies, DMs |
| File operations | Create, read | Delete, move outside vault |

## Quality Assurance

### Decision Validation
- Cross-reference all decisions with handbook rules
- Maintain confidence scores for uncertain decisions
- Escalate low-confidence decisions to human
- Learn from human corrections

### Error Handling
- Log all errors with timestamp and context
- Attempt automated recovery for transient errors
- Escalate persistent errors to human
- Maintain error statistics for improvement

## Continuous Improvement

### Feedback Integration
- Monitor human corrections for pattern recognition
- Update processing rules based on feedback
- Suggest handbook updates for recurring edge cases
- Report on decision accuracy rates

---

**Note:** This handbook is a living document. Updates should be made as operational procedures evolve. The AI Employee should periodically review this document for changes.
"""
        handbook_path.write_text(handbook_content)
        logging.info(f"Created initial Company_Handbook.md: {handbook_path}")


def main():
    """Main function to execute the setup."""
    setup_logging()

    parser = argparse.ArgumentParser(description='Setup AI Employee Vault structure')
    parser.add_argument(
        'vault_path',
        nargs='?',
        default='./AI_Employee_Vault',
        help='Path to create the AI Employee Vault (default: ./AI_Employee_Vault)'
    )
    parser.add_argument(
        '--force',
        action='store_true',
        help='Force creation even if directory exists'
    )

    args = parser.parse_args()

    vault_path = Path(args.vault_path).resolve()

    if vault_path.exists() and not args.force:
        logging.warning(f"Vault path '{vault_path}' already exists.")
        response = input("Continue anyway? (y/N): ")
        if response.lower() != 'y':
            print("Setup cancelled.")
            return

    try:
        logging.info(f"Setting up AI Employee Vault at: {vault_path}")

        # Create directory structure
        create_directory_structure(vault_path)

        # Create initial files
        create_initial_files(vault_path)

        logging.info(f"AI Employee Vault setup completed successfully at: {vault_path}")
        logging.info("\nNext steps:")
        logging.info("- Review and customize Company_Handbook.md with your specific rules")
        logging.info("- Add your tasks to the Needs_Action directory")
        logging.info("- Configure your watchers and run the orchestrator")

    except Exception as e:
        logging.error(f"Error during setup: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
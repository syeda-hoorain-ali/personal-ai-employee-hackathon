#!/usr/bin/env python3
"""
Trigger script for Weekly CEO Briefing generation.
This script calls Claude Code to generate the weekly business audit and CEO briefing.

Architecture:
- This script is the TRIGGER (scheduled to run weekly)
- Claude Code is the ORCHESTRATOR (uses skills and MCP tools)
- Skills provide KNOWLEDGE (how to generate briefing)
- MCP tools provide ACTIONS (fetch data from Odoo)
"""

import subprocess
import sys
import os
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv


def run_weekly_briefing():
    """
    Trigger Claude Code to generate the weekly CEO briefing.
    Claude will use skills and Odoo MCP tools to fetch data and generate the briefing.
    """
    # Load environment variables to get vault path
    project_root = Path(__file__).parent.parent.parent
    env_file = project_root / ".env"
    load_dotenv(env_file)

    # Get vault path from environment or use default
    vault_path = os.getenv("VAULT_PATH", "AI_Employee_Vault")
    # Extract vault directory name from path (handles relative and absolute paths)
    vault_name = Path(project_root / vault_path).name
    briefings_path = f"{vault_name}/Briefings/"

    # Define the prompt for Claude Code
    prompt = (
        "Generate the Weekly CEO Briefing for this week. "
        "Use the weekly-ceo-briefing skill to understand the process. "
        "Use the odoo-report-generator skill to fetch financial data from Odoo. "
        "Fetch revenue, expenses, outstanding invoices, and subscription patterns from Odoo using MCP tools. "
        f"Generate a comprehensive briefing markdown file in the {briefings_path} directory. "
        "Include: Executive Summary, Financial Performance, Outstanding Invoices, Top Customers, Recurring Expenses, and Action Items."
    )

    try:
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Triggering Claude Code for Weekly CEO Briefing...")

        # Execute Claude Code with the briefing generation prompt
        result = subprocess.run(
            [
                'ccr', 'code',
                '--allowedTools', 'Bash,Read,Write,Edit,Glob,Grep,Skill,mcp__odoo__search_records,mcp__odoo__list_invoices,mcp__odoo__list_contacts,mcp__odoo__list_payments',
                '--disallowedTools', 'Bash(rm:*,sudo:*)',
                '--no-session-persistence',
                '-p', prompt
            ],
            capture_output=True,
            text=True,
            timeout=600,  # 10 minute timeout
            encoding='utf-8',
            errors='replace',
            shell=True
        )

        if result.returncode == 0:
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Successfully generated Weekly CEO Briefing")
            # Handle potential encoding issues when printing Claude's output
            try:
                print(result.stdout.encode('utf-8', errors='replace').decode('utf-8'))
            except Exception:
                print("(Output contains special characters that couldn't be displayed)")
            return True
        else:
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Failed to generate Weekly CEO Briefing")
            # Handle potential encoding issues when printing error output
            try:
                print(result.stderr.encode('utf-8', errors='replace').decode('utf-8'))
            except Exception:
                print("(Error output contains special characters that couldn't be displayed)")
            return False

    except subprocess.TimeoutExpired:
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Claude Code command timed out while generating briefing")
        return False
    except FileNotFoundError:
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] ccr command not found, unable to trigger Claude Code")
        return False
    except Exception as e:
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Error triggering Claude Code: {e}")
        return False


def main():
    """
    Main function to run the weekly briefing trigger.
    """
    print("=" * 60)
    print("Weekly CEO Briefing Trigger - Starting")
    print("=" * 60)

    success = run_weekly_briefing()

    print("=" * 60)
    if success:
        print("Weekly CEO Briefing generation completed successfully")
        print("=" * 60)
        sys.exit(0)
    else:
        print("Weekly CEO Briefing generation failed")
        print("=" * 60)
        sys.exit(1)


if __name__ == "__main__":
    main()

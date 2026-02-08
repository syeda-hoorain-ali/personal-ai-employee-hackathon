#!/usr/bin/env python3
"""
Script for processing Needs_Action files in the AI Employee vault.
This script is designed to be used by Claude Code to process files
according to the Company Handbook rules.
"""

import os
import glob
import sys
import argparse
from pathlib import Path
import datetime


def read_company_handbook(vault_path: str | Path):
    """Read the Company Handbook rules."""
    handbook_path = Path(vault_path) / "Company_Handbook.md"
    if handbook_path.exists():
        return handbook_path.read_text(encoding='utf-8')
    return ""


def update_dashboard(vault_path: str | Path, action_summary: str):
    """Update the Dashboard.md file with processing outcomes."""
    dashboard_path = Path(vault_path) / "Dashboard.md"

    if dashboard_path.exists():
        with open(dashboard_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Find the Recent Activity section
        lines = content.split('\n')
        updated_lines = []
        activity_section_found = False

        for line in lines:
            if line.startswith('## Recent Activity'):
                activity_section_found = True
                updated_lines.append(line)
                # Add the new activity entry
                date_str = datetime.datetime.now().strftime('%Y-%m-%d %H:%M')
                updated_lines.append(f'- [{date_str}] {action_summary}')
            elif activity_section_found and line.startswith('- [') and '] System initialized' in line:
                # Insert our new entry before the original system initialized line
                updated_lines.append(f'- [{date_str}] {action_summary}')
                updated_lines.append(line)
                activity_section_found = False  # Reset flag after adding our entry
            else:
                updated_lines.append(line)

        # Write the updated content back
        with open(dashboard_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(updated_lines))
    else:
        # Create a basic dashboard if it doesn't exist
        date_str = datetime.datetime.now().strftime('%Y-%m-%d %H:%M')
        dashboard_content = f"""# AI Employee Dashboard

**Last Updated:** {date_str}
**Status:** Operational
**Uptime:** 24/7

## Executive Summary
Welcome to your AI Employee dashboard. This system operates 24/7 managing your personal and business affairs autonomously.

## Current Activities
- Monitoring: Gmail, WhatsApp, File System
- Processing: Tasks in `/Needs_Action`
- Waiting for: New tasks and instructions

## Recent Activity
- [{date_str}] {action_summary}
- [{date_str}] System initialized and operational
- [{date_str}] Vault structure created successfully

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
        with open(dashboard_path, 'w', encoding='utf-8') as f:
            f.write(dashboard_content)


def add_log_entry(vault_path: str | Path, log_message: str):
    """Add a log entry to the Logs folder."""
    logs_dir = os.path.join(vault_path, "Logs")
    os.makedirs(logs_dir, exist_ok=True)

    # Create a log file with today's date
    date_str = datetime.datetime.now().strftime('%Y-%m-%d')
    log_file_path = os.path.join(logs_dir, f"log_{date_str}.txt")

    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    with open(log_file_path, 'a', encoding='utf-8') as f:
        f.write(f"{timestamp} - {log_message}\n")


def move_file_to_done(vault_path: str | Path, file_path: str | Path):
    """Move a processed file to the Done folder."""
    done_dir = os.path.join(vault_path, "Done")
    os.makedirs(done_dir, exist_ok=True)

    filename = os.path.basename(file_path)
    dest_path = os.path.join(done_dir, filename)

    os.rename(file_path, dest_path)
    return dest_path


def move_file_to_pending_approval(vault_path: str | Path, file_path: str | Path):
    """Move a file to the Pending_Approval folder."""
    pending_dir = os.path.join(vault_path, "Pending_Approval")
    os.makedirs(pending_dir, exist_ok=True)

    filename = os.path.basename(file_path)
    dest_path = os.path.join(pending_dir, filename)

    os.rename(file_path, dest_path)
    return dest_path


def scan_needs_action_folder(vault_path: str | Path ="./AI_Employee_Vault"):
    """Scan the Needs_Action folder for pending files."""
    needs_action_dir = os.path.join(vault_path, "Needs_Action")

    if not os.path.exists(needs_action_dir):
        print(f"Needs_Action directory does not exist: {needs_action_dir}")
        return []

    # Find all .md files in Needs_Action
    files = glob.glob(os.path.join(needs_action_dir, "*.md"))

    print(f"Found {len(files)} files in Needs_Action folder:")
    for file in files:
        print(f"  - {os.path.basename(file)}")

    return files


def print_help():
    """Print help information."""
    help_text = """
Usage: python process_needs_action.py [command] [options]

Commands:
  read-company-handbook    Read the Company Handbook
  move-to-done            Move a file to the Done folder
  move-to-pending         Move a file to the Pending Approval folder
  scan-needs-action       Scan the Needs_Action folder for pending files
  update-dashboard        Update the dashboard with an activity entry
  add-log                 Add a log entry to the logs folder

Examples:
  python process_needs_action.py read-company-handbook --vault ./AI_Employee_Vault
  python process_needs_action.py move-to-done --file ./AI_Employee_Vault/Needs_Action/task.md --vault ./AI_Employee_Vault
  python process_needs_action.py scan-needs-action --vault ./AI_Employee_Vault
"""
    print(help_text)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Process needs action files for the AI Employee",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )

    # Commands
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Command to read company handbook
    handbook_parser = subparsers.add_parser("read-company-handbook", help="Read Company Handbook")
    handbook_parser.add_argument("--vault", "-v", default="./AI_Employee_Vault", help="Vault path")

    # Command to move file to done
    done_parser = subparsers.add_parser("move-to-done", help="Move a file to Done folder")
    done_parser.add_argument("--file", "-f", required=True, help="File to move")
    done_parser.add_argument("--vault", "-v", default="./AI_Employee_Vault", help="Vault path")

    # Command to move file to pending approval
    pending_parser = subparsers.add_parser("move-to-pending", help="Move a file to Pending Approval folder")
    pending_parser.add_argument("--file", "-f", required=True, help="File to move")
    pending_parser.add_argument("--vault", "-v", default="./AI_Employee_Vault", help="Vault path")

    # Command to scan needs action folder
    scan_parser = subparsers.add_parser("scan-needs-action", help="Scan Needs_Action folder")
    scan_parser.add_argument("--vault", "-v", default="./AI_Employee_Vault", help="Vault path")

    # Command to update dashboard
    dashboard_parser = subparsers.add_parser("update-dashboard", help="Update dashboard with activity")
    dashboard_parser.add_argument("--activity", "-a", required=True, help="Activity description to add")
    dashboard_parser.add_argument("--vault", "-v", default="./AI_Employee_Vault", help="Vault path")

    # Command to add log entry
    log_parser = subparsers.add_parser("add-log", help="Add a log entry")
    log_parser.add_argument("--message", "-m", required=True, help="Log message to add")
    log_parser.add_argument("--vault", "-v", default="./AI_Employee_Vault", help="Vault path")

    args = parser.parse_args()

    try:
        if args.command == "read-company-handbook":
            content = read_company_handbook(args.vault)
            print(content)

        elif args.command == "move-to-done":
            new_path = move_file_to_done(args.vault, args.file)
            print(f"Moved file to Done: {new_path}")

        elif args.command == "move-to-pending":
            new_path = move_file_to_pending_approval(args.vault, args.file)
            print(f"Moved file to Pending Approval: {new_path}")

        elif args.command == "scan-needs-action":
            scan_needs_action_folder(args.vault)

        elif args.command == "update-dashboard":
            update_dashboard(args.vault, args.activity)
            print("Dashboard updated successfully")

        elif args.command == "add-log":
            add_log_entry(args.vault, args.message)
            print("Log entry added successfully")

        else:
            parser.print_help()

    except KeyboardInterrupt:
        sys.exit(130)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

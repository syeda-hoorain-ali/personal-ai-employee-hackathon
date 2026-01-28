#!/usr/bin/env python3
"""
Script to log time entries to tasks.txt file.
Each entry includes a timestamp and allows for optional task description.

Usage:
    python log_time.py                    # Logs current time without description
    python log_time.py "Description"      # Logs current time with description

Examples:
    python log_time.py "Started coding"
    python log_time.py "Meeting with team"
    python log_time.py "Review pull request"
"""

import datetime
import os
import sys


def log_time_entry(description=""):
    """
    Log a time entry to tasks.txt file

    Args:
        description (str): Optional description of the task
    """
    # Create the tasks.txt file path using absolute path
    script_dir = os.path.dirname(os.path.abspath(__file__))
    tasks_file = os.path.join(os.path.dirname(script_dir), "tasks.txt")

    # Get current timestamp
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S %p")

    # Create the entry
    if description:
        entry = f"[{timestamp}] Task: {description}\n"
    else:
        entry = f"[{timestamp}] Time logged\n"

    # Write the entry to the file
    with open(tasks_file, "a", encoding="utf-8") as f:
        f.write(entry)

    print(f"Time logged: {entry.strip()}")


def main():
    # Get command line argument as task description
    if len(sys.argv) > 1:
        description = " ".join(sys.argv[1:])
    else:
        description = ""

    log_time_entry(description)


if __name__ == "__main__":
    main()

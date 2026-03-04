#!/usr/bin/env python3
"""
Standalone script to set up the Weekly CEO Briefing scheduled task.
Run this script as Administrator.
"""

import os
import sys
import subprocess
from pathlib import Path


def is_admin():
    """Check if the script is running with administrator privileges."""
    try:
        if os.name == 'nt':
            import ctypes
            return ctypes.windll.shell32.IsUserAnAdmin()
        else:
            return os.geteuid() == 0
    except AttributeError:
        return False


def main():
    """Set up the Weekly CEO Briefing scheduled task."""
    print("=" * 60)
    print("Weekly CEO Briefing - Scheduler Setup")
    print("=" * 60)
    print()

    # Check if running as administrator
    if not is_admin():
        print("[ERROR] This script requires administrator privileges.")
        print("        Please run this script as Administrator.")
        print()
        print("To run as Administrator:")
        print("  1. Right-click on Command Prompt")
        print("  2. Select 'Run as administrator'")
        print("  3. Navigate to the scripts directory")
        print("  4. Run: python setup_weekly_briefing_scheduler.py")
        return 1

    print("[INFO] Running with administrator privileges")
    print()

    # Check OS type
    if os.name != 'nt':
        print("[INFO] For Unix/Linux systems, use cron to schedule weekly audits.")
        print("       Add this to your crontab (crontab -e):")
        print()
        print("       0 20 * * 0 cd /path/to/project/app && python -m src.app.weekly_audit.audit_orchestrator")
        print()
        return 0

    task_name = "WeeklyCEOBriefing"
    project_root = Path(__file__).parent.parent.resolve()
    python_exe = sys.executable

    print(f"[INFO] Project root: {project_root}")
    print(f"[INFO] Python executable: {python_exe}")
    print(f"[INFO] Task name: {task_name}")
    print()

    # First, try to delete the existing task if it exists
    print("[INFO] Checking for existing task...")
    delete_cmd = ['schtasks', '/delete', '/tn', task_name, '/f']
    try:
        result = subprocess.run(delete_cmd, capture_output=True, text=True, check=False)
        if result.returncode == 0:
            print(f"[INFO] Deleted existing task '{task_name}'")
        else:
            print(f"[INFO] No existing task found (this is OK)")
    except Exception as e:
        print(f"[INFO] No existing task to delete: {e}")

    print()
    print("[INFO] Creating scheduled task...")

    # PowerShell script to create the task
    ps_script = f'''
    $action = New-ScheduledTaskAction -Execute "{python_exe}" -Argument '-m src.app.weekly_audit.audit_orchestrator' -WorkingDirectory "{project_root}/app"

    # Trigger: Run every Sunday at 8:00 PM
    $trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Sunday -At "8:00PM"

    # Settings to ensure task runs reliably
    $settings = New-ScheduledTaskSettingsSet `
        -AllowStartIfOnBatteries `
        -DontStopIfGoingOnBatteries `
        -StartWhenAvailable `
        -RunOnlyIfNetworkAvailable:$true `
        -ExecutionTimeLimit (New-TimeSpan -Hours 1) `
        -MultipleInstances Queue

    # Principal to run whether logged in or not
    $principal = New-ScheduledTaskPrincipal -UserId "$env:USERNAME" -LogonType ServiceAccount -RunLevel Highest

    # Register the task
    Register-ScheduledTask -TaskName "{task_name}" -Action $action -Trigger $trigger -Settings $settings -Principal $principal -Force
    '''

    try:
        # Create new task using PowerShell
        result = subprocess.run(
            ['powershell', '-Command', ps_script],
            capture_output=True,
            text=True,
            check=True
        )
        print(f"[SUCCESS] Successfully created scheduled task '{task_name}'")
        print()
        print("Task Details:")
        print(f"  - Name: {task_name}")
        print(f"  - Schedule: Every Sunday at 8:00 PM")
        print(f"  - Command: python -m src.app.weekly_audit.audit_orchestrator")
        print(f"  - Working Directory: {project_root}/app")
        print()
        print("To verify the task was created, run:")
        print(f"  schtasks /query /tn {task_name}")
        print()
        print("To test the task manually, run:")
        print(f"  schtasks /run /tn {task_name}")
        print()
        return 0
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Error creating scheduled task: {e}")
        print(f"[ERROR] Error output: {e.stderr}")
        print()
        print("Troubleshooting:")
        print("  1. Make sure you're running as Administrator")
        print("  2. Check that PowerShell execution policy allows scripts")
        print("  3. Try running the PowerShell command manually")
        return 1


if __name__ == "__main__":
    sys.exit(main())

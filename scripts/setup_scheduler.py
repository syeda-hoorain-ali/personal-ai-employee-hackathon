#!/usr/bin/env python3
"""
Simple script to set up a Windows Task Scheduler task that runs the log_time.py script
every minute (as close to 30-second intervals as Task Scheduler allows).

IMPORTANT: This script must be run with administrator privileges to create scheduled tasks.
"""

import subprocess
import os
import sys
from pathlib import Path


def check_os():
    """Check the operating system and provide appropriate messaging."""
    if os.name == 'nt':  # Windows
        return 'windows'
    elif os.name == 'posix':  # Unix-like (Linux, macOS)
        if sys.platform.startswith('darwin'):
            return 'macos'
        else:
            return 'linux'
    else:
        return 'unknown'


def setup_minute_scheduled_task(task_name, script_path):
    """
    Set up a scheduled task to run the log_time.py script every minute.

    Args:
        task_name (str): Name of the scheduled task
        script_path (str): Path to the script to be scheduled
    """

    # Get the absolute path of the script
    script_abs_path = Path(script_path).resolve()

    # Verify the script exists
    if not script_abs_path.exists():
        print(f"Error: Script {script_abs_path} does not exist!")
        return False

    app_folder = script_abs_path.parent.parent.resolve()
    python_exe = sys.executable

    print("Note: This script requires administrator privileges to create scheduled tasks.")
    print("Please run this script as an administrator if you encounter permission errors.")

    # First, try to delete the existing task if it exists
    delete_cmd = ['schtasks', '/delete', '/tn', task_name, '/f']
    try:
        subprocess.run(delete_cmd, capture_output=True, text=True, check=False)
        print(f"Deleted existing task '{task_name}' if it existed")
    except Exception as e:
        print(f"No existing task to delete or error deleting: {e}")


    # PowerShell script to create the task
    ps_script = f'''
    $action = New-ScheduledTaskAction -Execute "{python_exe}" -Argument '"{script_abs_path}" "LinkedIn activity log 2"' -WorkingDirectory "{app_folder}"

    # Trigger 1: Run every minute starting now
    $trigger1 = New-ScheduledTaskTrigger -Once -At (Get-Date) -RepetitionInterval (New-TimeSpan -Minutes 1)

    # Trigger 2: Run at startup (also with repetition)
    $trigger2 = New-ScheduledTaskTrigger -AtStartup
    $trigger2.Repetition = $trigger1.Repetition  # Copy the repetition settings from trigger1

    # Settings to ensure task runs even when not logged in
    $settings = New-ScheduledTaskSettingsSet `
        -AllowStartIfOnBatteries `
        -DontStopIfGoingOnBatteries `
        -StartWhenAvailable `
        -RunOnlyIfNetworkAvailable:$false `
        -ExecutionTimeLimit (New-TimeSpan -Hours 0) `
        -MultipleInstances IgnoreNew

    # Principal to run whether logged in or not
    $principal = New-ScheduledTaskPrincipal -UserId "$env:USERNAME" -LogonType S4U -RunLevel Highest

    # Register the task
    Register-ScheduledTask -TaskName "{task_name}" -Action $action -Trigger @($trigger1, $trigger2) -Settings $settings -Principal $principal -Force
    '''

    # # This command creates a task that runs every Monday and Thursday at 12:00 PM
    # cmd = [
    #     'schtasks',
    #     '/create',
    #     '/tn', task_name,  # Task name
    #     '/tr', f'"{sys.executable}" "{script_abs_path}" "LinkedIn activity log"',  # Task to run
    #     '/sc', 'weekly',  # Schedule type: weekly
    #     '/d', 'MON,THU',  # Days: Monday and Thursday
    #     '/st', '12:00',   # Start time: 12:00 PM
    #     '/f'  # Force creation (overwrite if exists)
    # ]

    try:
        # Create new task using PowerShell
        result = subprocess.run(
            ['powershell', '-Command', ps_script],
            capture_output=True,
            text=True,
            check=True
        )
        print(f"Successfully created scheduled task '{task_name}'")
        print(f"The task will run '{script_abs_path}' every minute")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error creating scheduled task: {e}")
        print(f"Error output: {e.stderr}")
        return False


def main():
    # Check the operating system
    os_type = check_os()

    if os_type in ['linux', 'macos']:
        print(f"Task Scheduler is not available on {os_type}.")
        print("Please update the script to use cron jobs instead.")
        return

    # For Windows, proceed with the task creation
    # Define the task name and script path
    task_name = "LinkedInMinuteScheduler"
    script_path = "app/scripts/log_time.py"

    print("Setting up scheduled task to run log_time.py every minute...")
    setup_minute_scheduled_task(task_name, script_path)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Simple script to create a Windows Task Scheduler task that runs the log_time.py script
automatically when the computer starts up.

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


def setup_startup_task(task_name, script_path):
    """
    Set up a scheduled task to run on system startup.

    Args:
        task_name (str): Name of the scheduled task
        script_path (str): Path to the Python script to run on startup
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
    $action = New-ScheduledTaskAction -Execute "{python_exe}" -Argument '"{script_abs_path}" "Your pc have started"' -WorkingDirectory "{app_folder}"


    # Create trigger for startup
    $trigger = New-ScheduledTaskTrigger -AtLogon

    # Settings to ensure task runs at startup
    $settings = New-ScheduledTaskSettingsSet `
        -AllowStartIfOnBatteries `
        -DontStopIfGoingOnBatteries `
        -StartWhenAvailable `
        -RunOnlyIfNetworkAvailable:$false `
        -ExecutionTimeLimit (New-TimeSpan -Hours 0) `
        -MultipleInstances IgnoreNew

    # Principal to run with highest privileges
    $principal = New-ScheduledTaskPrincipal -UserId "$env:USERNAME" -LogonType S4U -RunLevel Highest

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
        print(f"Successfully created startup task '{task_name}'")
        print(f"The task will run automatically when Windows starts")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error creating startup task: {e}")
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
    # Define the task name and batch file path
    task_name = "LinkedInActivityLoggerOnStartup"
    script_path = "app/scripts/log_time.py"

    print("Setting up startup task to run log_time script automatically when Windows starts...")
    setup_startup_task(task_name, script_path)


if __name__ == "__main__":
    main()

"""Windows scheduler implementation using Task Scheduler.

This module provides functionality to schedule the weekly audit on Windows
using PowerShell commands to interact with Task Scheduler.
"""

import logging
import subprocess
from pathlib import Path
from typing import Optional

from .base_scheduler import BaseScheduler

logger = logging.getLogger("weekly_audit.schedulers.windows")


class WindowsScheduler(BaseScheduler):
    """Scheduler implementation for Windows Task Scheduler."""

    def __init__(self, script_path: Path, schedule_time: str = "20:00"):
        """Initialize the Windows scheduler.

        Args:
            script_path: Path to the run_weekly_audit.bat script
            schedule_time: Time to run the audit (HH:MM format, 24-hour)
        """
        super().__init__(script_path, schedule_time)
        self.task_name = "WeeklyCEOBriefingAudit"

    def schedule_weekly_audit(self) -> bool:
        """Create a scheduled task to run the audit every Sunday.

        Returns:
            True if scheduling succeeded, False otherwise
        """
        try:
            # Check if task already exists
            if self.is_scheduled():
                logger.warning(f"Task '{self.task_name}' already exists")
                return True

            # Parse schedule time
            hour, minute = self.schedule_time.split(":")

            # Build PowerShell command to create scheduled task
            ps_command = f"""
$action = New-ScheduledTaskAction -Execute '{self.script_path}'
$trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Sunday -At {self.schedule_time}
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries
$principal = New-ScheduledTaskPrincipal -UserId "$env:USERNAME" -LogonType Interactive
Register-ScheduledTask -TaskName '{self.task_name}' -Action $action -Trigger $trigger -Settings $settings -Principal $principal -Description 'Weekly CEO Briefing Audit - Automated business review'
"""

            # Execute PowerShell command
            result = subprocess.run(
                ["powershell", "-Command", ps_command],
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.returncode == 0:
                logger.info(f"Successfully scheduled task '{self.task_name}' for Sundays at {self.schedule_time}")
                return True
            else:
                logger.error(f"Failed to schedule task: {result.stderr}")
                return False

        except subprocess.TimeoutExpired:
            logger.error("PowerShell command timed out")
            return False
        except Exception as e:
            logger.error(f"Failed to schedule weekly audit: {e}", exc_info=True)
            return False

    def remove_scheduled_audit(self) -> bool:
        """Remove the scheduled audit task.

        Returns:
            True if removal succeeded, False otherwise
        """
        try:
            if not self.is_scheduled():
                logger.warning(f"Task '{self.task_name}' does not exist")
                return True

            # Build PowerShell command to remove scheduled task
            ps_command = f"Unregister-ScheduledTask -TaskName '{self.task_name}' -Confirm:$false"

            # Execute PowerShell command
            result = subprocess.run(
                ["powershell", "-Command", ps_command],
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.returncode == 0:
                logger.info(f"Successfully removed scheduled task '{self.task_name}'")
                return True
            else:
                logger.error(f"Failed to remove task: {result.stderr}")
                return False

        except subprocess.TimeoutExpired:
            logger.error("PowerShell command timed out")
            return False
        except Exception as e:
            logger.error(f"Failed to remove scheduled audit: {e}", exc_info=True)
            return False

    def is_scheduled(self) -> bool:
        """Check if the audit is currently scheduled.

        Returns:
            True if a scheduled task exists, False otherwise
        """
        try:
            # Build PowerShell command to check if task exists
            ps_command = f"Get-ScheduledTask -TaskName '{self.task_name}' -ErrorAction SilentlyContinue"

            # Execute PowerShell command
            result = subprocess.run(
                ["powershell", "-Command", ps_command],
                capture_output=True,
                text=True,
                timeout=30,
            )

            # Task exists if command succeeded and output is not empty
            return result.returncode == 0 and bool(result.stdout.strip())

        except subprocess.TimeoutExpired:
            logger.error("PowerShell command timed out")
            return False
        except Exception as e:
            logger.error(f"Failed to check scheduled task: {e}", exc_info=True)
            return False

    def get_next_run_time(self) -> Optional[str]:
        """Get the next scheduled run time.

        Returns:
            ISO format datetime string of next run, or None if not scheduled
        """
        try:
            if not self.is_scheduled():
                return None

            # Build PowerShell command to get next run time
            ps_command = f"""
$task = Get-ScheduledTask -TaskName '{self.task_name}'
$info = Get-ScheduledTaskInfo -TaskName '{self.task_name}'
$info.NextRunTime.ToString('o')
"""

            # Execute PowerShell command
            result = subprocess.run(
                ["powershell", "-Command", ps_command],
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.returncode == 0 and result.stdout.strip():
                return result.stdout.strip()
            else:
                return None

        except subprocess.TimeoutExpired:
            logger.error("PowerShell command timed out")
            return None
        except Exception as e:
            logger.error(f"Failed to get next run time: {e}", exc_info=True)
            return None

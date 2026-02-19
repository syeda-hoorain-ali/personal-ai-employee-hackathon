"""Unix scheduler implementation using cron.

This module provides functionality to schedule the weekly audit on Unix-based
systems (Linux, macOS) using crontab.
"""

import logging
import subprocess
from pathlib import Path
from typing import Optional

from .base_scheduler import BaseScheduler

logger = logging.getLogger("weekly_audit.schedulers.unix")


class UnixScheduler(BaseScheduler):
    """Scheduler implementation for Unix cron."""

    def __init__(self, script_path: Path, schedule_time: str = "20:00"):
        """Initialize the Unix scheduler.

        Args:
            script_path: Path to the run_weekly_audit.sh script
            schedule_time: Time to run the audit (HH:MM format, 24-hour)
        """
        super().__init__(script_path, schedule_time)
        self.cron_comment = "# Weekly CEO Briefing Audit"

    def schedule_weekly_audit(self) -> bool:
        """Add a crontab entry to run the audit every Sunday.

        Cron format: 0 20 * * 0 (minute hour day month weekday)
        Sunday = 0

        Returns:
            True if scheduling succeeded, False otherwise
        """
        try:
            # Check if already scheduled
            if self.is_scheduled():
                logger.warning("Weekly audit is already scheduled in crontab")
                return True

            # Parse schedule time
            hour, minute = self.schedule_time.split(":")

            # Build cron entry
            cron_entry = f"{minute} {hour} * * 0 {self.script_path} {self.cron_comment}"

            # Get current crontab
            result = subprocess.run(
                ["crontab", "-l"],
                capture_output=True,
                text=True,
                timeout=10,
            )

            # Handle case where no crontab exists yet
            if result.returncode != 0:
                current_crontab = ""
            else:
                current_crontab = result.stdout

            # Add new entry
            new_crontab = current_crontab.rstrip() + "\n" + cron_entry + "\n"

            # Write new crontab
            result = subprocess.run(
                ["crontab", "-"],
                input=new_crontab,
                capture_output=True,
                text=True,
                timeout=10,
            )

            if result.returncode == 0:
                logger.info(f"Successfully scheduled weekly audit for Sundays at {self.schedule_time}")
                return True
            else:
                logger.error(f"Failed to update crontab: {result.stderr}")
                return False

        except subprocess.TimeoutExpired:
            logger.error("Crontab command timed out")
            return False
        except Exception as e:
            logger.error(f"Failed to schedule weekly audit: {e}", exc_info=True)
            return False

    def remove_scheduled_audit(self) -> bool:
        """Remove the crontab entry for the weekly audit.

        Returns:
            True if removal succeeded, False otherwise
        """
        try:
            if not self.is_scheduled():
                logger.warning("Weekly audit is not scheduled in crontab")
                return True

            # Get current crontab
            result = subprocess.run(
                ["crontab", "-l"],
                capture_output=True,
                text=True,
                timeout=10,
            )

            if result.returncode != 0:
                logger.warning("No crontab found")
                return True

            current_crontab = result.stdout

            # Remove lines containing the comment
            new_lines = []
            for line in current_crontab.split("\n"):
                if self.cron_comment not in line:
                    new_lines.append(line)

            new_crontab = "\n".join(new_lines)

            # Write new crontab
            result = subprocess.run(
                ["crontab", "-"],
                input=new_crontab,
                capture_output=True,
                text=True,
                timeout=10,
            )

            if result.returncode == 0:
                logger.info("Successfully removed weekly audit from crontab")
                return True
            else:
                logger.error(f"Failed to update crontab: {result.stderr}")
                return False

        except subprocess.TimeoutExpired:
            logger.error("Crontab command timed out")
            return False
        except Exception as e:
            logger.error(f"Failed to remove scheduled audit: {e}", exc_info=True)
            return False

    def is_scheduled(self) -> bool:
        """Check if the audit is currently scheduled in crontab.

        Returns:
            True if a crontab entry exists, False otherwise
        """
        try:
            # Get current crontab
            result = subprocess.run(
                ["crontab", "-l"],
                capture_output=True,
                text=True,
                timeout=10,
            )

            if result.returncode != 0:
                return False

            # Check if our comment exists in crontab
            return self.cron_comment in result.stdout

        except subprocess.TimeoutExpired:
            logger.error("Crontab command timed out")
            return False
        except Exception as e:
            logger.error(f"Failed to check crontab: {e}", exc_info=True)
            return False

    def get_next_run_time(self) -> Optional[str]:
        """Get the next scheduled run time.

        Note: Calculating next cron run time requires complex logic.
        This is a simplified implementation that returns the schedule time.

        Returns:
            Schedule time string, or None if not scheduled
        """
        if not self.is_scheduled():
            return None

        # Return the configured schedule time
        # A full implementation would calculate the next Sunday at this time
        return f"Every Sunday at {self.schedule_time}"

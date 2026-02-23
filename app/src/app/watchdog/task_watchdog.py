"""
Task watchdog for monitoring stalled tasks.

Detects and recovers tasks that have been claimed but not completed.
"""

import logging
import time
from pathlib import Path
from typing import List, Dict
from datetime import datetime, timezone, timedelta

logger = logging.getLogger("vault_sync.task_watchdog")


class TaskWatchdog:
    """Monitors tasks for staleness and triggers recovery."""

    def __init__(
        self,
        vault_path: str,
        check_interval_seconds: int = 300,
        stale_threshold_minutes: int = 30
    ):
        """
        Initialize TaskWatchdog.

        Args:
            vault_path: Absolute path to vault directory
            check_interval_seconds: Interval between watchdog checks
            stale_threshold_minutes: Time before task is considered stalled
        """
        self.vault_path = Path(vault_path)
        self.check_interval_seconds = check_interval_seconds
        self.stale_threshold_minutes = stale_threshold_minutes
        self.running = False

    def check_stalled_tasks(self) -> List[Dict]:
        """
        Check for stalled tasks in In_Progress directory.

        Returns:
            List of stalled task information
        """
        start_time = time.time()
        logger.info(
            f"[WATCHDOG_CHECK_START] operation=check_stalled_tasks "
            f"threshold_minutes={self.stale_threshold_minutes}"
        )
        stalled_tasks = []
        files_processed = 0

        try:
            in_progress_dir = self.vault_path / "In_Progress"
            if not in_progress_dir.exists():
                duration_ms = int((time.time() - start_time) * 1000)
                logger.info(
                    f"[WATCHDOG_CHECK_COMPLETE] operation=check_stalled_tasks "
                    f"duration_ms={duration_ms} files_processed=0 stalled_tasks_found=0 "
                    f"reason=in_progress_dir_not_found"
                )
                return stalled_tasks

            # Check all agent directories
            for agent_dir in in_progress_dir.iterdir():
                if not agent_dir.is_dir():
                    continue

                # Check all tasks in agent directory
                for task_file in agent_dir.glob("*.md"):
                    files_processed += 1
                    if self._is_task_stalled(task_file):
                        stalled_info = self._get_stalled_task_info(task_file)
                        if stalled_info:
                            stalled_tasks.append(stalled_info)

            duration_ms = int((time.time() - start_time) * 1000)

            if stalled_tasks:
                logger.warning(
                    f"[WATCHDOG_CHECK_COMPLETE] operation=check_stalled_tasks "
                    f"duration_ms={duration_ms} files_processed={files_processed} "
                    f"stalled_tasks_found={len(stalled_tasks)}"
                )
            else:
                logger.info(
                    f"[WATCHDOG_CHECK_COMPLETE] operation=check_stalled_tasks "
                    f"duration_ms={duration_ms} files_processed={files_processed} "
                    f"stalled_tasks_found=0"
                )

            return stalled_tasks

        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            logger.error(
                f"[WATCHDOG_CHECK_FAILED] operation=check_stalled_tasks "
                f"duration_ms={duration_ms} files_processed={files_processed} "
                f"error={str(e)}"
            )
            return stalled_tasks

    def run_watchdog_loop(self) -> None:
        """Run watchdog monitoring loop."""
        logger.info(
            f"[WATCHDOG_START] operation=run_watchdog_loop "
            f"check_interval_seconds={self.check_interval_seconds} "
            f"stale_threshold_minutes={self.stale_threshold_minutes}"
        )
        self.running = True

        while self.running:
            try:
                stalled_tasks = self.check_stalled_tasks()

                # Log stalled tasks for monitoring
                for task_info in stalled_tasks:
                    logger.warning(
                        f"[STALLED_TASK_DETECTED] operation=watchdog_monitoring "
                        f"task={task_info.get('task_name', 'unknown')} "
                        f"claimed_by={task_info.get('claimed_by', 'unknown')} "
                        f"claimed_at={task_info.get('claimed_at', 'unknown')} "
                        f"domain={task_info.get('domain', 'unknown')}"
                    )

                time.sleep(self.check_interval_seconds)

            except Exception as e:
                logger.error(
                    f"[WATCHDOG_LOOP_ERROR] operation=run_watchdog_loop "
                    f"error={str(e)}"
                )
                time.sleep(self.check_interval_seconds)

    def stop(self) -> None:
        """Stop watchdog monitoring loop."""
        logger.info(
            f"[WATCHDOG_STOP] operation=stop_watchdog_loop"
        )
        self.running = False

    def _is_task_stalled(self, task_file: Path) -> bool:
        """Check if a task is stalled."""
        try:
            # Check file modification time
            mtime = datetime.fromtimestamp(task_file.stat().st_mtime, tz=timezone.utc)
            current_time = datetime.now(timezone.utc)
            time_since_update = current_time - mtime

            # Task is stalled if no updates for threshold period
            return time_since_update > timedelta(minutes=self.stale_threshold_minutes)

        except Exception as e:
            logger.error(f"Error checking if task is stalled: {e}")
            return False

    def _get_stalled_task_info(self, task_file: Path) -> Dict:
        """Get information about a stalled task."""
        try:
            metadata = self._parse_task_metadata(task_file)
            if not metadata:
                return {}

            mtime = datetime.fromtimestamp(task_file.stat().st_mtime, tz=timezone.utc)

            return {
                "task_file": str(task_file),
                "task_name": task_file.name,
                "claimed_by": metadata.get("claimed_by"),
                "claimed_at": metadata.get("claimed_at"),
                "last_modified": mtime.isoformat(),
                "domain": metadata.get("domain"),
                "priority": metadata.get("priority"),
                "status": metadata.get("status")
            }

        except Exception as e:
            logger.error(f"Error getting stalled task info: {e}")
            return {}

    def _parse_task_metadata(self, task_file: Path) -> Dict:
        """Parse task file frontmatter."""
        try:
            content = task_file.read_text(encoding='utf-8')

            if content.startswith('---'):
                parts = content.split('---', 2)
                if len(parts) >= 3:
                    frontmatter = parts[1]
                    metadata = {}

                    for line in frontmatter.split('\n'):
                        if ':' in line:
                            key, value = line.split(':', 1)
                            metadata[key.strip()] = value.strip()

                    return metadata

            return {}

        except Exception as e:
            logger.error(f"Error parsing task metadata: {e}")
            return {}

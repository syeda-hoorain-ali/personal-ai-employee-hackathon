"""
Analyzer for completed tasks in the /Done folder.

This module scans the /Done folder for completed tasks and extracts
metadata from task files.
"""

import logging
import os
import re
import yaml
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional

from .entities import CompletedTask, TaskBottleneck

logger = logging.getLogger("weekly_audit.task_analyzer")


class TaskAnalyzer:
    """
    Analyzer for completed tasks and bottleneck identification.

    Scans the /Done folder for task files modified within the analysis period
    and extracts task metadata from YAML frontmatter.
    """

    def __init__(self, done_folder: Path):
        """
        Initialize the task analyzer.

        Args:
            done_folder: Path to the /Done folder
        """
        self.done_folder = done_folder

    def analyze_completed_tasks(self, days: int = 7) -> List[CompletedTask]:
        """
        Scan /Done folder for tasks completed in the last N days.

        Args:
            days: Number of days to look back (default: 7)

        Returns:
            List of CompletedTask entities

        Raises:
            FileNotFoundError: If /Done folder doesn't exist
        """
        if not self.done_folder.exists():
            logger.error(f"/Done folder not found at {self.done_folder}")
            raise FileNotFoundError(f"/Done folder not found at {self.done_folder}")

        logger.info(f"Analyzing completed tasks from last {days} days")

        cutoff_time = datetime.now() - timedelta(days=days)
        completed_tasks = []

        # Scan all .md files in /Done folder
        for task_file in self.done_folder.glob("*.md"):
            try:
                # Get file modification time
                mtime = datetime.fromtimestamp(os.path.getmtime(task_file))

                if mtime >= cutoff_time:
                    task = self._parse_task_file(task_file, mtime)
                    completed_tasks.append(task)
                    logger.debug(f"Found completed task: {task.name}")

            except Exception as e:
                logger.warning(f"Error parsing task file {task_file}: {e}")
                continue

        logger.info(f"Found {len(completed_tasks)} completed tasks")
        return completed_tasks

    def _parse_task_file(self, file_path: Path, completion_date: datetime) -> CompletedTask:
        """
        Parse a task file and extract metadata.

        Args:
            file_path: Path to the task file
            completion_date: File modification time (completion date)

        Returns:
            CompletedTask entity
        """
        # Extract task name from filename
        task_name = file_path.stem.replace("-", " ").replace("_", " ").title()

        # Try to parse YAML frontmatter for metadata
        metadata = self.parse_task_metadata(file_path)

        return CompletedTask(
            name=task_name,
            completion_date=completion_date,
            file_path=file_path,
            expected_duration=self.parse_duration(metadata.get("expected_duration")) if metadata.get("expected_duration") else None,
            actual_duration=self.parse_duration(metadata.get("actual_duration")) if metadata.get("actual_duration") else None,
            priority=metadata.get("priority"),
            project=metadata.get("project")
        )

    def parse_task_metadata(self, file_path: Path) -> dict:
        """
        Extract YAML frontmatter from a task file.

        Args:
            file_path: Path to the task file

        Returns:
            Dictionary with task metadata (empty if no frontmatter)
        """
        try:
            content = file_path.read_text(encoding="utf-8")

            if not content.startswith("---"):
                return {}

            # Split by frontmatter delimiters
            parts = content.split("---", 2)
            if len(parts) < 3:
                return {}

            yaml_content = parts[1].strip()
            metadata = yaml.safe_load(yaml_content)

            return metadata if metadata else {}

        except Exception as e:
            logger.debug(f"No valid YAML frontmatter in {file_path}: {e}")
            return {}

    def parse_duration(self, duration_str: str) -> Optional[timedelta]:
        """
        Convert duration strings to timedelta objects.

        Supports formats: "2h", "30m", "1.5h", "2h 30m"

        Args:
            duration_str: Duration string to parse

        Returns:
            timedelta object or None if parsing fails
        """
        if not duration_str:
            return None

        try:
            duration_str = str(duration_str).lower().strip()

            # Pattern: "2h 30m" or "2h" or "30m" or "1.5h"
            hours = 0
            minutes = 0

            # Extract hours
            hour_match = re.search(r'([\d.]+)\s*h', duration_str)
            if hour_match:
                hours = float(hour_match.group(1))

            # Extract minutes
            minute_match = re.search(r'(\d+)\s*m', duration_str)
            if minute_match:
                minutes = int(minute_match.group(1))

            if hours == 0 and minutes == 0:
                return None

            return timedelta(hours=hours, minutes=minutes)

        except Exception as e:
            logger.warning(f"Failed to parse duration '{duration_str}': {e}")
            return None

    def identify_bottlenecks(self, completed_tasks: List[CompletedTask], threshold: float = 0.5) -> List[TaskBottleneck]:
        """
        Identify tasks that took significantly longer than expected.

        Args:
            completed_tasks: List of completed tasks
            threshold: Delay threshold (0.5 = 50% over expected)

        Returns:
            List of TaskBottleneck entities, sorted by delay percentage (descending)
        """
        logger.info(f"Identifying bottlenecks with threshold {threshold * 100}%")

        bottlenecks = []

        for task in completed_tasks:
            if task.expected_duration and task.actual_duration:
                if task.actual_duration > task.expected_duration * (1 + threshold):
                    delay_percent = ((task.actual_duration - task.expected_duration) / task.expected_duration) * 100

                    bottleneck = TaskBottleneck(
                        task_name=task.name,
                        expected_duration=task.expected_duration,
                        actual_duration=task.actual_duration,
                        delay_percent=delay_percent,
                        completion_date=task.completion_date.date()
                    )
                    bottlenecks.append(bottleneck)
                    logger.debug(f"Bottleneck identified: {task.name} ({delay_percent:.1f}% delay)")

        # Sort by delay percentage (highest first)
        bottlenecks.sort(key=lambda b: b.delay_percent, reverse=True)

        logger.info(f"Found {len(bottlenecks)} bottlenecks")
        return bottlenecks

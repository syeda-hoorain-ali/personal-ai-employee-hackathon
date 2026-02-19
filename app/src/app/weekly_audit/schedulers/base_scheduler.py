"""
Abstract base class for platform-specific schedulers.

This module defines the interface that all scheduler implementations must follow.
"""

from abc import ABC, abstractmethod
from pathlib import Path


class BaseScheduler(ABC):
    """
    Abstract base class for scheduling weekly audit execution.

    Platform-specific implementations (Windows, Unix) must inherit from this class
    and implement the schedule_weekly_audit method.
    """

    def __init__(self, script_path: Path, schedule_time: str = "20:00"):
        """
        Initialize the scheduler.

        Args:
            script_path: Path to the audit execution script
            schedule_time: Time to run the audit (HH:MM format, 24-hour)
        """
        self.script_path = script_path
        self.schedule_time = schedule_time

    @abstractmethod
    def schedule_weekly_audit(self) -> bool:
        """
        Schedule the weekly audit to run automatically.

        Returns:
            True if scheduling was successful, False otherwise
        """
        pass

    @abstractmethod
    def remove_schedule(self) -> bool:
        """
        Remove the scheduled weekly audit task.

        Returns:
            True if removal was successful, False otherwise
        """
        pass

    @abstractmethod
    def is_scheduled(self) -> bool:
        """
        Check if the weekly audit is currently scheduled.

        Returns:
            True if scheduled, False otherwise
        """
        pass

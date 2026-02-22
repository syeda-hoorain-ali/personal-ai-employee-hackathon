"""
Centralized error logging system for Personal AI Employee.

This module provides the ErrorLogger class for logging errors to daily JSON files
with automatic sanitization, file locking, and dashboard integration.
"""

import uuid
import traceback
from datetime import datetime, UTC
from pathlib import Path
from typing import Optional, Dict, Any

from .entities import ErrorLogEntry, ErrorType, ResolutionStatus
from .utils import (
    sanitize_sensitive_data,
    sanitize_dict,
    file_lock,
    ensure_directory,
    append_to_json_array,
    read_json_file,
    write_json_file
)


class ErrorLogger:
    """
    Centralized error logger that writes to daily JSON files.

    Features:
    - Daily error log files (YYYY-MM-DD.json)
    - Automatic sensitive data sanitization
    - File locking for concurrent access
    - Dashboard integration with atomic updates
    """

    def __init__(self, logs_dir: Path, dashboard_path: Optional[Path] = None):
        """
        Initialize the error logger.

        Args:
            logs_dir: Directory for daily error log files
            dashboard_path: Optional path to dashboard JSON file
        """
        self.logs_dir = Path(logs_dir)
        self.dashboard_path = Path(dashboard_path) if dashboard_path else None
        ensure_directory(self.logs_dir)

        if self.dashboard_path:
            ensure_directory(self.dashboard_path.parent)

    def log_error(
        self,
        component: str,
        error_type: ErrorType,
        message: str,
        error: Optional[Exception] = None,
        error_code: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        retry_count: int = 0
    ) -> str:
        """
        Log an error to the daily error log file.

        Args:
            component: Name of the component where error occurred
            error_type: Type of error (TRANSIENT, AUTHENTICATION, etc.)
            message: Human-readable error message
            error: Optional exception object for stack trace
            error_code: Optional error code (e.g., HTTP status, API error code)
            context: Optional additional context (sanitized automatically)
            retry_count: Number of retry attempts made

        Returns:
            Error ID (UUID) for tracking
        """
        # Generate error ID
        error_id = str(uuid.uuid4())

        # Get current timestamp
        timestamp = datetime.now(UTC).isoformat().replace('+00:00', 'Z')

        # Extract stack trace if exception provided
        stack_trace = None
        if error:
            stack_trace = "".join(traceback.format_exception(
                type(error), error, error.__traceback__
            ))
            # Sanitize stack trace
            stack_trace = sanitize_sensitive_data(stack_trace)

        # Sanitize message and context
        sanitized_message = sanitize_sensitive_data(message)
        sanitized_context = sanitize_dict(context) if context else {}

        # Create error log entry
        entry = ErrorLogEntry(
            id=error_id,
            timestamp=timestamp,
            component=component,
            error_type=error_type,
            message=sanitized_message,
            stack_trace=stack_trace,
            retry_count=retry_count,
            error_code=error_code,
            context=sanitized_context,
            resolution_status=ResolutionStatus.UNRESOLVED,
            resolved_at=None
        )

        # Write to daily log file
        self._write_to_daily_log(entry)

        # Update dashboard if configured
        if self.dashboard_path:
            self._update_dashboard(entry)

        return error_id

    def _write_to_daily_log(self, entry: ErrorLogEntry) -> None:
        """
        Write error entry to daily log file with file locking.

        Args:
            entry: Error log entry to write
        """
        # Get today's date for filename
        date_str = datetime.now(UTC).strftime("%Y-%m-%d")
        log_file = self.logs_dir / f"{date_str}.json"

        # Append to daily log with file locking
        append_to_json_array(log_file, entry.to_dict())

    def _update_dashboard(self, entry: ErrorLogEntry) -> None:
        """
        Update dashboard with latest error statistics.

        Uses atomic write to prevent corruption during concurrent access.

        Args:
            entry: Error log entry to include in dashboard
        """
        # Guard against None dashboard_path
        if self.dashboard_path is None:
            return

        # Read current dashboard data with file locking
        with file_lock(self.dashboard_path):
            dashboard = read_json_file(self.dashboard_path, default={
                "last_updated": None,
                "total_errors": 0,
                "errors_by_type": {},
                "errors_by_component": {},
                "recent_errors": [],
                "paused_components": {},
                "action_required_alerts": []
            })

            # Update statistics
            dashboard["last_updated"] = datetime.now(UTC).isoformat().replace('+00:00', 'Z')
            dashboard["total_errors"] = dashboard.get("total_errors", 0) + 1

            # Update errors by type
            error_type_key = entry.error_type.value
            errors_by_type = dashboard.get("errors_by_type", {})
            errors_by_type[error_type_key] = errors_by_type.get(error_type_key, 0) + 1
            dashboard["errors_by_type"] = errors_by_type

            # Update errors by component with nested by_type structure
            errors_by_component = dashboard.get("errors_by_component", {})
            if entry.component not in errors_by_component:
                errors_by_component[entry.component] = {"by_type": {}}

            # Update component's error count by type
            component_data = errors_by_component[entry.component]
            by_type = component_data.get("by_type", {})
            by_type[error_type_key] = by_type.get(error_type_key, 0) + 1
            component_data["by_type"] = by_type

            dashboard["errors_by_component"] = errors_by_component

            # Add to recent errors (keep last 50)
            recent_errors = dashboard.get("recent_errors", [])
            recent_errors.insert(0, {
                "id": entry.id,
                "timestamp": entry.timestamp,
                "component": entry.component,
                "error_type": entry.error_type.value,
                "message": entry.message,
                "error_code": entry.error_code
            })
            dashboard["recent_errors"] = recent_errors[:50]

            # Ensure paused_components exists
            if "paused_components" not in dashboard:
                dashboard["paused_components"] = {}

            # Add action-required alert for authentication errors
            if entry.error_type == ErrorType.AUTHENTICATION:
                action_required_alerts = dashboard.get("action_required_alerts", [])
                action_required_alerts.insert(0, {
                    "id": entry.id,
                    "timestamp": entry.timestamp,
                    "component": entry.component,
                    "message": entry.message,
                    "error_type": "AUTHENTICATION",
                    "action": "Update credentials and restart component"
                })
                # Keep last 10 action-required alerts
                dashboard["action_required_alerts"] = action_required_alerts[:10]

            # Write dashboard atomically
            write_json_file(self.dashboard_path, dashboard)

    def get_errors_by_date(self, date: datetime) -> list[ErrorLogEntry]:
        """
        Retrieve all errors for a specific date.

        Args:
            date: Date to retrieve errors for

        Returns:
            List of error log entries for that date
        """
        date_str = date.strftime("%Y-%m-%d")
        log_file = self.logs_dir / f"{date_str}.json"

        if not log_file.exists():
            return []

        data = read_json_file(log_file, default=[])
        return [ErrorLogEntry.from_dict(entry) for entry in data]

    def get_error_by_id(self, error_id: str, date: Optional[datetime] = None) -> Optional[ErrorLogEntry]:
        """
        Retrieve a specific error by ID.

        Args:
            error_id: Error ID to search for
            date: Optional date to search (searches today if not provided)

        Returns:
            Error log entry if found, None otherwise
        """
        if date is None:
            date = datetime.now(UTC)

        errors = self.get_errors_by_date(date)
        for error in errors:
            if error.id == error_id:
                return error

        return None

    def mark_error_resolved(
        self,
        error_id: str,
        resolution_status: ResolutionStatus,
        date: Optional[datetime] = None
    ) -> bool:
        """
        Mark an error as resolved.

        Args:
            error_id: Error ID to mark as resolved
            resolution_status: Resolution status to set
            date: Optional date to search (searches today if not provided)

        Returns:
            True if error was found and updated, False otherwise
        """
        if date is None:
            date = datetime.now(UTC)

        date_str = date.strftime("%Y-%m-%d")
        log_file = self.logs_dir / f"{date_str}.json"

        if not log_file.exists():
            return False

        # Read, update, and write with file locking
        with file_lock(log_file):
            data = read_json_file(log_file, default=[])

            updated = False
            for entry_dict in data:
                if entry_dict.get("id") == error_id:
                    entry_dict["resolution_status"] = resolution_status.value
                    entry_dict["resolved_at"] = datetime.now(UTC).isoformat().replace('+00:00', 'Z')
                    updated = True
                    break

            if updated:
                write_json_file(log_file, data)

            return updated

    def update_paused_component(
        self,
        component: str,
        is_paused: bool,
        reason: Optional[str] = None,
        failure_count: int = 0
    ) -> None:
        """
        Update the paused components section of the dashboard.

        Args:
            component: Name of the component
            is_paused: Whether the component is currently paused
            reason: Optional reason for pause/resume
            failure_count: Number of consecutive failures
        """
        if not self.dashboard_path:
            return

        with file_lock(self.dashboard_path):
            dashboard = read_json_file(self.dashboard_path, default={
                "last_updated": None,
                "total_errors": 0,
                "errors_by_type": {},
                "errors_by_component": {},
                "recent_errors": [],
                "paused_components": {}
            })

            paused_components = dashboard.get("paused_components", {})

            if is_paused:
                # Add or update paused component
                paused_components[component] = {
                    "paused_at": datetime.now(UTC).isoformat().replace('+00:00', 'Z'),
                    "reason": reason or "Circuit breaker opened due to consecutive failures",
                    "failure_count": failure_count
                }
            else:
                # Remove from paused components
                paused_components.pop(component, None)

            dashboard["paused_components"] = paused_components
            dashboard["last_updated"] = datetime.now(UTC).isoformat().replace('+00:00', 'Z')

            # Write dashboard atomically
            write_json_file(self.dashboard_path, dashboard)

    def update_quarantined_files(
        self,
        quarantine_stats: Dict[str, Any]
    ) -> None:
        """
        Update the quarantined files section of the dashboard.

        Args:
            quarantine_stats: Statistics from FileQuarantine.get_quarantine_stats()
        """
        # Guard against None dashboard_path
        if self.dashboard_path is None:
            return

        with file_lock(self.dashboard_path):
            dashboard = read_json_file(self.dashboard_path, default={})

            # Update quarantined files section
            dashboard["quarantined_files"] = {
                "total_files": quarantine_stats.get("total_files", 0),
                "by_component": quarantine_stats.get("by_component", {}),
                "by_error_type": quarantine_stats.get("by_error_type", {}),
                "total_size_mb": quarantine_stats.get("total_size_mb", 0),
                "last_updated": datetime.now(UTC).isoformat().replace('+00:00', 'Z')
            }

            dashboard["last_updated"] = datetime.now(UTC).isoformat().replace('+00:00', 'Z')

            # Write dashboard atomically
            write_json_file(self.dashboard_path, dashboard)

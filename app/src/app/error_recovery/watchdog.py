"""
Watchdog process for monitoring and restarting crashed components.

This module provides the Watchdog class that monitors component health,
detects crashes, and automatically restarts components with exponential backoff.
"""

import time
import psutil
import logging
from datetime import datetime, UTC, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass, field

from .entities import ComponentStatus, ComponentHealthStatus, ErrorType
from .exceptions import WatchdogError
from .error_logger import ErrorLogger
from .circuit_breaker import CircuitBreaker
from .operation_queue import OperationQueue
from .utils import read_json_file, write_json_file, file_lock


logger = logging.getLogger(__name__)


@dataclass
class ComponentConfig:
    """Configuration for a monitored component."""

    name: str
    start_command: Callable[[], int]  # Function that starts component and returns PID
    health_check: Optional[Callable[[], bool]] = None  # Optional health check function
    restart_on_failure: bool = True
    max_restart_attempts: int = 3
    restart_backoff_seconds: int = 60
    crash_detection_window_minutes: int = 5
    crash_threshold: int = 3


class Watchdog:
    """
    Watchdog process that monitors component health and restarts crashed components.

    Features:
    - Periodic health checks
    - Automatic restart on crash
    - Crash detection (3 crashes in 5 minutes triggers pause)
    - Exponential backoff for restarts
    - Integration with circuit breaker
    """

    def __init__(
        self,
        vault_path: Path,
        check_interval_seconds: int = 30,
        error_logger: Optional[ErrorLogger] = None
    ):
        """
        Initialize watchdog.

        Args:
            vault_path: Path to AI_Employee_Vault
            check_interval_seconds: Seconds between health checks
            error_logger: Optional ErrorLogger instance
        """
        self.vault_path = Path(vault_path)
        self.check_interval = check_interval_seconds
        self.error_logger = error_logger or ErrorLogger(
            self.vault_path / "Logs" / "Errors",
            self.vault_path / ".system" / "error_dashboard.json"
        )

        # Component registry
        self.components: Dict[str, ComponentConfig] = {}
        self.component_pids: Dict[str, int] = {}
        self.component_create_times: Dict[str, float] = {}  # Track process creation time to prevent PID reuse issues
        self.component_status: Dict[str, ComponentHealthStatus] = {}
        self.restart_counts: Dict[str, int] = {}
        self.crash_history: Dict[str, List[str]] = {}  # component -> list of crash timestamps
        self.consecutive_healthy_checks: Dict[str, int] = {}  # Track consecutive successful health checks
        self.scheduled_restarts: Dict[str, datetime] = {}  # Track scheduled restart times (non-blocking)

        # Operation queue registry
        self.operation_queues: Dict[str, OperationQueue] = {}
        self.operation_handlers: Dict[str, Dict[str, Callable]] = {}

        # State persistence
        self.state_file = self.vault_path / ".system" / "watchdog_state.json"
        self._load_state()

        self.running = False

    def register_component(self, config: ComponentConfig):
        """
        Register a component for monitoring.

        Args:
            config: Component configuration
        """
        self.components[config.name] = config
        self.restart_counts[config.name] = 0
        self.crash_history[config.name] = []
        self.consecutive_healthy_checks[config.name] = 0

        logger.info(f"Registered component: {config.name}")

    def register_operation_queue(
        self,
        queue_name: str,
        operation_queue: OperationQueue,
        handlers: Dict[str, Callable[[Dict], bool]]
    ):
        """
        Register an operation queue for processing during monitoring loop.

        Args:
            queue_name: Name of the queue (e.g., "gmail_api", "linkedin_api")
            operation_queue: OperationQueue instance
            handlers: Dictionary mapping operation types to handler functions
                     Handler should return True on success, False on failure
        """
        self.operation_queues[queue_name] = operation_queue
        self.operation_handlers[queue_name] = handlers
        logger.info(f"Registered operation queue: {queue_name} with {len(handlers)} handlers")

    def _process_scheduled_restarts(self):
        """Process scheduled component restarts (non-blocking)."""
        current_time = datetime.now(UTC)
        components_to_restart = []

        # Find components ready for restart
        for name, restart_time in list(self.scheduled_restarts.items()):
            if current_time >= restart_time:
                components_to_restart.append(name)
                del self.scheduled_restarts[name]

        # Execute scheduled restarts
        for name in components_to_restart:
            logger.info(f"Executing scheduled restart for {name}")
            success = self._start_component(name)

            if success:
                self.error_logger.log_error(
                    component=name,
                    error_type=ErrorType.SYSTEM,
                    message=f"Component restarted (attempt {self.restart_counts[name]}/{self.components[name].max_restart_attempts})",
                    context={
                        "restart_count": self.restart_counts[name],
                        "max_attempts": self.components[name].max_restart_attempts
                    }
                )
            else:
                logger.error(f"Failed to restart component {name}")
                self.error_logger.log_error(
                    component=name,
                    error_type=ErrorType.SYSTEM,
                    message=f"Failed to restart component",
                    context={
                        "restart_count": self.restart_counts[name],
                        "max_attempts": self.components[name].max_restart_attempts
                    }
                )

    def _process_operation_queues(self):
        """
        Process all registered operation queues.

        Note: Queue processing is synchronous and may block health checks if queues
        are large or handlers perform slow operations. For production systems with
        high-volume queues, consider async processing or dedicated worker threads.
        """
        for queue_name, queue in self.operation_queues.items():
            try:
                handlers = self.operation_handlers.get(queue_name, {})
                if not handlers:
                    continue

                # Process queue with registered handlers
                stats = queue.process_queue(handlers)

                # Log processing results if any operations were processed
                if stats["processed"] > 0:
                    logger.info(
                        f"Processed {stats['processed']} operations from {queue_name}: "
                        f"{stats['succeeded']} succeeded, {stats['failed']} failed"
                    )

                    self.error_logger.log_error(
                        component="Watchdog",
                        error_type=ErrorType.SYSTEM,
                        message=f"Processed queued operations for {queue_name}",
                        context={
                            "queue_name": queue_name,
                            "processed": stats["processed"],
                            "succeeded": stats["succeeded"],
                            "failed": stats["failed"]
                        }
                    )

            except Exception as e:
                logger.error(f"Error processing queue {queue_name}: {e}")
                self.error_logger.log_error(
                    component="Watchdog",
                    error_type=ErrorType.SYSTEM,
                    message=f"Failed to process operation queue",
                    error=e,
                    context={"queue_name": queue_name}
                )

    def start(self):
        """Start the watchdog monitoring loop."""
        self.running = True
        logger.info("Watchdog started")

        # Start all registered components
        for name, config in self.components.items():
            self._start_component(name)

        # Main monitoring loop
        while self.running:
            try:
                self._process_scheduled_restarts()
                self._check_all_components()
                self._process_operation_queues()
                self._save_state()
                time.sleep(self.check_interval)
            except Exception as e:
                logger.error(f"Error in watchdog loop: {e}")
                self.error_logger.log_error(
                    component="Watchdog",
                    error_type=ErrorType.SYSTEM,
                    message="Error in watchdog monitoring loop",
                    error=e
                )

    def stop(self):
        """Stop the watchdog monitoring loop."""
        self.running = False
        logger.info("Watchdog stopped")

    def _start_component(self, name: str) -> bool:
        """
        Start a component.

        Args:
            name: Component name

        Returns:
            True if started successfully, False otherwise
        """
        config = self.components[name]

        try:
            logger.info(f"Starting component: {name}")
            pid = config.start_command()

            if pid:
                self.component_pids[name] = pid

                # Track process creation time to prevent PID reuse issues
                try:
                    process = psutil.Process(pid)
                    self.component_create_times[name] = process.create_time()
                except Exception as e:
                    logger.warning(f"Could not get creation time for PID {pid}: {e}")
                    self.component_create_times[name] = time.time()

                self.component_status[name] = ComponentHealthStatus(
                    component=name,
                    status=ComponentStatus.STARTING,
                    process_id=pid,
                    health_check_last_run=datetime.now(UTC).isoformat().replace('+00:00', 'Z')
                )

                logger.info(f"Component {name} started with PID {pid}")
                return True
            else:
                logger.error(f"Failed to start component {name}: no PID returned")
                return False

        except Exception as e:
            logger.error(f"Error starting component {name}: {e}")
            self.error_logger.log_error(
                component=name,
                error_type=ErrorType.SYSTEM,
                message=f"Failed to start component",
                error=e
            )
            return False

    def restart_component(self, name: str) -> bool:
        """
        Restart a component.

        Args:
            name: Component name

        Returns:
            True if restarted successfully, False otherwise
        """
        config = self.components[name]

        # Check if component should be restarted
        if not config.restart_on_failure:
            logger.info(f"Component {name} is configured not to restart")
            return False

        # Check restart attempts
        if self.restart_counts[name] >= config.max_restart_attempts:
            logger.warning(f"Component {name} exceeded max restart attempts")
            self.pause_component(name, "Exceeded max restart attempts")
            return False

        # Check for crash loop (3 crashes in 5 minutes)
        if self._is_crash_loop(name):
            logger.warning(f"Component {name} is in crash loop")
            self.pause_component(name, "Crash loop detected (3 crashes in 5 minutes)")
            return False

        # Record crash
        current_time = datetime.now(UTC)
        self.crash_history[name].append(
            current_time.isoformat().replace('+00:00', 'Z')
        )

        # Prune old crash timestamps outside the detection window
        window_start = current_time - timedelta(minutes=config.crash_detection_window_minutes)
        self.crash_history[name] = [
            ts for ts in self.crash_history[name]
            if datetime.fromisoformat(ts.replace('Z', '+00:00')) > window_start
        ]

        # Stop existing process if running
        if name in self.component_pids:
            self._stop_component(name)

        # Schedule restart with backoff period (non-blocking)
        backoff = config.restart_backoff_seconds * (2 ** self.restart_counts[name])
        restart_time = datetime.now(UTC) + timedelta(seconds=backoff)
        self.scheduled_restarts[name] = restart_time
        logger.info(f"Scheduled restart for {name} in {backoff}s at {restart_time.isoformat()}")

        # Increment restart count
        self.restart_counts[name] += 1

        return True  # Restart scheduled successfully

        if success:
            self.error_logger.log_error(
                component=name,
                error_type=ErrorType.SYSTEM,
                message=f"Component restarted (attempt {self.restart_counts[name]}/{config.max_restart_attempts})",
                context={
                    "restart_count": self.restart_counts[name],
                    "max_attempts": config.max_restart_attempts
                }
            )

        return success

    def pause_component(self, name: str, reason: str):
        """
        Pause a component (stop monitoring and restarting).

        Args:
            name: Component name
            reason: Reason for pausing
        """
        logger.warning(f"Pausing component {name}: {reason}")

        # Stop component
        self._stop_component(name)

        # Update status
        self.component_status[name] = ComponentHealthStatus(
            component=name,
            status=ComponentStatus.PAUSED,
            health_check_last_run=datetime.now(UTC).isoformat().replace('+00:00', 'Z')
        )

        # Log to error logger
        self.error_logger.log_error(
            component=name,
            error_type=ErrorType.SYSTEM,
            message=f"Component paused: {reason}",
            context={
                "reason": reason,
                "restart_count": self.restart_counts[name],
                "crash_count": len(self.crash_history[name])
            }
        )

    def _stop_component(self, name: str):
        """Stop a component process."""
        if name not in self.component_pids:
            return

        pid = self.component_pids[name]
        process = None

        try:
            process = psutil.Process(pid)
            process.terminate()
            process.wait(timeout=10)
            logger.info(f"Stopped component {name} (PID {pid})")
        except psutil.NoSuchProcess:
            logger.warning(f"Process {pid} for component {name} not found")
        except psutil.TimeoutExpired:
            logger.warning(f"Process {pid} for component {name} did not terminate, killing")
            if process is not None:
                try:
                    process.kill()
                except:
                    pass
        except Exception as e:
            logger.error(f"Error stopping component {name}: {e}")

        # Remove from tracking
        del self.component_pids[name]

    def _check_all_components(self):
        """Check health of all registered components."""
        for name, config in self.components.items():
            # Skip paused components
            if name in self.component_status:
                if self.component_status[name].status == ComponentStatus.PAUSED:
                    continue

            # Check if process is running
            is_running = self._is_process_running(name)

            # Run health check if configured
            is_healthy = True
            if config.health_check:
                try:
                    is_healthy = config.health_check()
                except Exception as e:
                    logger.error(f"Health check failed for {name}: {e}")
                    is_healthy = False

            # Update status
            if is_running and is_healthy:
                self.component_status[name] = ComponentHealthStatus(
                    component=name,
                    status=ComponentStatus.RUNNING,
                    process_id=self.component_pids.get(name),
                    health_check_last_run=datetime.now(UTC).isoformat().replace('+00:00', 'Z')
                )
                # Increment consecutive healthy checks
                self.consecutive_healthy_checks[name] = self.consecutive_healthy_checks.get(name, 0) + 1

                # Reset restart count only after 3 consecutive healthy checks to prevent flapping
                if self.consecutive_healthy_checks[name] >= 3:
                    self.restart_counts[name] = 0
            elif is_running and not is_healthy:
                # Process running but unhealthy
                logger.warning(f"Component {name} is unhealthy")
                self.component_status[name] = ComponentHealthStatus(
                    component=name,
                    status=ComponentStatus.CRASHED,
                    process_id=self.component_pids.get(name),
                    health_check_last_run=datetime.now(UTC).isoformat().replace('+00:00', 'Z')
                )
                self.restart_component(name)
            else:
                # Process not running
                logger.warning(f"Component {name} is not running")
                self.component_status[name] = ComponentHealthStatus(
                    component=name,
                    status=ComponentStatus.CRASHED,
                    health_check_last_run=datetime.now(UTC).isoformat().replace('+00:00', 'Z')
                )
                self.restart_component(name)

    def _is_process_running(self, name: str) -> bool:
        """Check if a component's process is running and matches expected creation time."""
        if name not in self.component_pids:
            return False

        pid = self.component_pids[name]
        expected_create_time = self.component_create_times.get(name)

        try:
            process = psutil.Process(pid)

            # Verify process is running
            if not process.is_running():
                return False

            # Verify process creation time matches to prevent PID reuse issues
            if expected_create_time is not None:
                actual_create_time = process.create_time()
                # Allow small tolerance for timing differences (1 second)
                if abs(actual_create_time - expected_create_time) > 1.0:
                    logger.warning(
                        f"PID {pid} for {name} has different creation time "
                        f"(expected: {expected_create_time}, actual: {actual_create_time}). "
                        f"PID may have been reused."
                    )
                    return False

            return True
        except psutil.NoSuchProcess:
            return False
        except Exception as e:
            logger.error(f"Error checking process {pid} for {name}: {e}")
            return False

    def _is_crash_loop(self, name: str) -> bool:
        """
        Check if component is in a crash loop.

        A crash loop is defined as 3 or more crashes within the configured window.

        Args:
            name: Component name

        Returns:
            True if in crash loop, False otherwise
        """
        config = self.components[name]
        crashes = self.crash_history[name]

        if len(crashes) < config.crash_threshold:
            return False

        # Check recent crashes within window
        now = datetime.now(UTC)
        window_start = now - timedelta(minutes=config.crash_detection_window_minutes)

        recent_crashes = [
            crash for crash in crashes
            if datetime.fromisoformat(crash.replace('Z', '+00:00')) > window_start
        ]

        return len(recent_crashes) >= config.crash_threshold

    def _load_state(self):
        """Load watchdog state from persistence file."""
        if not self.state_file.exists():
            return

        try:
            with file_lock(self.state_file):
                data = read_json_file(self.state_file, default={})

                self.restart_counts = data.get("restart_counts", {})
                self.crash_history = data.get("crash_history", {})

        except Exception as e:
            logger.error(f"Error loading watchdog state: {e}")

    def _save_state(self):
        """Save watchdog state to persistence file."""
        try:
            with file_lock(self.state_file):
                data = {
                    "restart_counts": self.restart_counts,
                    "crash_history": self.crash_history,
                    "last_updated": datetime.now(UTC).isoformat().replace('+00:00', 'Z')
                }

                write_json_file(self.state_file, data)

        except Exception as e:
            logger.error(f"Error saving watchdog state: {e}")

    def get_component_status(self, name: str) -> Optional[ComponentHealthStatus]:
        """
        Get current status of a component.

        Args:
            name: Component name

        Returns:
            ComponentHealthStatus or None if not found
        """
        return self.component_status.get(name)

    def get_all_status(self) -> Dict[str, ComponentHealthStatus]:
        """
        Get status of all components.

        Returns:
            Dictionary mapping component names to their status
        """
        return self.component_status.copy()

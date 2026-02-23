import threading
import logging
import time
import os
from pathlib import Path
from typing import List, Optional
from .watchers.base_watcher import BaseWatcher
from .logging_config import get_logger
from .file_processor import FileProcessor
from .ralph_wiggum_controller import RalphWiggumController
from .vault_sync.git_manager import GitManager
from .watchdog.task_watchdog import TaskWatchdog
from .watchdog.recovery_handler import RecoveryHandler
from .dashboard_manager.cloud_update_writer import CloudUpdateWriter
from .dashboard_manager.update_merger import UpdateMerger
from .error_recovery import with_retry, ErrorLogger, ErrorType


class FileProcessorComponent:
    """
    Component that monitors and processes files in the Needs_Action directory.
    """
    def __init__(self, vault_path: str, check_interval: int = 30):
        self.vault_path = Path(vault_path)
        self.processor = FileProcessor(str(vault_path))
        self.check_interval = check_interval
        self.logger = get_logger(self.__class__.__name__)
        self.running = False


    def run(self):
        """Run the file processor continuously."""
        self.logger.info("Starting file processor...")
        self.running = True

        while self.running:
            try:
                # Process all files in Needs_Action directory
                results = self.processor.process_needs_action_directory()

                if results["processed_count"] > 0:
                    self.logger.info(f"Notified Claude Code of {results['processed_count']} files ready for processing")
                    if results["successful"]:
                        self.logger.info(f"Successfully notified Claude for: {len(results['successful'])} files")
                    if results["failed"]:
                        self.logger.warning(f"Failed to notify Claude for: {len(results['failed'])} files")

                # Sleep for the check interval
                time.sleep(self.check_interval)
            except Exception as e:
                self.logger.error(f"Error in file processor: {e}")
                time.sleep(self.check_interval)  # Continue running even if there's an error


class Orchestrator:
    """
    Coordinates multiple watcher activities and manages their lifecycle.
    """
    def __init__(self, vault_path: str, enable_git_sync: bool = None, agent_name: str = None):
        self.vault_path = Path(vault_path)
        self.watchers: List[BaseWatcher] = []
        self.file_processor_component = FileProcessorComponent(str(vault_path))
        self.logger = get_logger(self.__class__.__name__)
        self.running = False
        self.threads = []

        # Git sync configuration
        self.enable_git_sync = enable_git_sync if enable_git_sync is not None else os.getenv("GIT_SYNC_ENABLED", "false").lower() == "true"
        self.agent_name = agent_name or os.getenv("AGENT_NAME", "local-agent")
        self.git_manager: Optional[GitManager] = None
        self.error_logger = ErrorLogger(str(self.vault_path / "Logs" / "error_recovery.log"))

        # Initialize Git manager if sync is enabled
        if self.enable_git_sync:
            try:
                self.git_manager = GitManager(str(vault_path), self.agent_name)
                self.logger.info(f"Git sync enabled for agent: {self.agent_name}")
            except Exception as e:
                self.logger.error(f"Failed to initialize Git manager: {e}")
                self.error_logger.log_error(
                    error_type=ErrorType.SYSTEM,
                    message=f"Git manager initialization failed: {e}",
                    component="orchestrator",
                    operation="init_git_manager"
                )

        # Initialize task watchdog if enabled
        self.enable_watchdog = os.getenv("WATCHDOG_ENABLED", "true").lower() == "true"
        self.task_watchdog: Optional[TaskWatchdog] = None
        self.recovery_handler: Optional[RecoveryHandler] = None

        if self.enable_watchdog:
            try:
                watchdog_interval = int(os.getenv("WATCHDOG_INTERVAL_SECONDS", "300"))
                stale_threshold = int(os.getenv("CLAIM_TIMEOUT_MINUTES", "30"))
                self.task_watchdog = TaskWatchdog(str(vault_path), watchdog_interval, stale_threshold)
                self.recovery_handler = RecoveryHandler(str(vault_path))
                self.logger.info(f"Task watchdog enabled (interval: {watchdog_interval}s, threshold: {stale_threshold}m)")
            except Exception as e:
                self.logger.error(f"Failed to initialize task watchdog: {e}")
                self.error_logger.log_error(
                    error_type=ErrorType.SYSTEM,
                    message=f"Task watchdog initialization failed: {e}",
                    component="orchestrator",
                    operation="init_watchdog"
                )

        # Initialize dashboard management components
        self.cloud_update_writer: Optional[CloudUpdateWriter] = None
        self.update_merger: Optional[UpdateMerger] = None
        self.dashboard_merge_interval = int(os.getenv("DASHBOARD_MERGE_INTERVAL_SECONDS", "300"))

        # Cloud agent uses CloudUpdateWriter, local agent uses UpdateMerger
        if self.agent_name.startswith("cloud"):
            try:
                self.cloud_update_writer = CloudUpdateWriter(str(vault_path), self.agent_name)
                self.logger.info(f"CloudUpdateWriter initialized for {self.agent_name}")
            except Exception as e:
                self.logger.error(f"Failed to initialize CloudUpdateWriter: {e}")
        elif self.agent_name.startswith("local"):
            try:
                self.update_merger = UpdateMerger(str(vault_path))
                self.logger.info(f"UpdateMerger initialized for {self.agent_name}")
            except Exception as e:
                self.logger.error(f"Failed to initialize UpdateMerger: {e}")

    def add_watcher(self, watcher: BaseWatcher):
        """Add a watcher to the orchestrator."""
        self.watchers.append(watcher)
        self.logger.info(f"Added watcher: {watcher.__class__.__name__}")

    def start_all_watchers(self):
        """Start all registered watchers in separate threads."""
        if self.running:
            self.logger.warning("Orchestrator already running")
            return

        self.running = True
        self.logger.info("Starting all watchers...")

        # Perform initial Git sync if enabled
        if self.enable_git_sync and self.git_manager:
            self._sync_vault_with_retry("Initial sync before starting watchers")

        # Start the file processor component
        processor_thread = threading.Thread(target=self.file_processor_component.run, daemon=True)
        processor_thread.start()
        self.threads.append(processor_thread)
        self.logger.info("Started FileProcessor thread")

        # Start all registered watchers
        for watcher in self.watchers:
            thread = threading.Thread(target=watcher.run, daemon=True)
            thread.start()
            self.threads.append(thread)
            self.logger.info(f"Started {watcher.__class__.__name__} thread")

        # Start periodic Git sync thread if enabled
        if self.enable_git_sync and self.git_manager:
            sync_thread = threading.Thread(target=self._periodic_sync_loop, daemon=True)
            sync_thread.start()
            self.threads.append(sync_thread)
            self.logger.info("Started periodic Git sync thread")

        # Start task watchdog thread if enabled
        if self.enable_watchdog and self.task_watchdog:
            watchdog_thread = threading.Thread(target=self._watchdog_loop, daemon=True)
            watchdog_thread.start()
            self.threads.append(watchdog_thread)
            self.logger.info("Started task watchdog thread")

        # Start dashboard merger thread if local agent
        if self.update_merger:
            merger_thread = threading.Thread(target=self._dashboard_merger_loop, daemon=True)
            merger_thread.start()
            self.threads.append(merger_thread)
            self.logger.info("Started dashboard merger thread")

    def stop_all_watchers(self):
        """Stop all running watchers."""
        self.logger.info("Stopping all watchers...")
        self.running = False

        # Stop the file processor component
        self.file_processor_component.running = False

        # Stop the task watchdog
        if self.task_watchdog:
            self.task_watchdog.stop()

        # Wait for all threads to finish (with timeout)
        for thread in self.threads:
            thread.join(timeout=5.0)  # 5-second timeout

        self.logger.info("All watchers stopped")

    def is_running(self):
        """Check if the orchestrator is currently running."""
        return self.running

    def get_watcher_status(self):
        """Get status information for all watchers."""
        status = {}
        for watcher in self.watchers:
            status[watcher.__class__.__name__] = {
                'name': watcher.__class__.__name__,
                'vault_path': str(watcher.vault_path),
                'check_interval': getattr(watcher, 'check_interval', 'N/A'),
            }
        return status

    def start_reasoning_loop(self, task_description: str, max_iterations: int = 10):
        """Start a Claude reasoning loop that creates Plan.md files."""
        self.logger.info(f"Starting reasoning loop for task: {task_description}")

        controller = RalphWiggumController(str(self.vault_path), max_iterations=max_iterations)
        success = controller.run_reasoning_loop(task_description)

        if success:
            self.logger.info("Reasoning loop completed successfully")
        else:
            self.logger.warning("Reasoning loop did not complete the task")

        return success

    def run(self):
        """Run the orchestrator."""
        self.logger.info("Starting orchestrator...")
        self.start_all_watchers()

        try:
            # Keep the main thread alive
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            self.logger.info("Received interrupt signal, shutting down...")
        finally:
            # Perform final Git sync before shutdown if enabled
            if self.enable_git_sync and self.git_manager:
                self._sync_vault_with_retry("Final sync before shutdown")
            self.stop_all_watchers()

    def _periodic_sync_loop(self):
        """Periodically sync vault with remote repository."""
        sync_interval = int(os.getenv("GIT_SYNC_INTERVAL_SECONDS", "300"))  # Default: 5 minutes
        self.logger.info(f"Starting periodic Git sync (interval: {sync_interval}s)")

        while self.running:
            time.sleep(sync_interval)
            if self.running:  # Check again after sleep
                self._sync_vault_with_retry("Periodic sync")

    def _sync_vault_with_retry(self, commit_message: str):
        """
        Sync vault with error recovery.

        Args:
            commit_message: Commit message for the sync operation
        """
        if not self.git_manager:
            return

        try:
            # Use error recovery retry mechanism
            @with_retry(max_attempts=3, delay=5, backoff=2)
            def sync_operation():
                return self.git_manager.sync_vault(commit_message)

            result = sync_operation()
            self.logger.info(f"Git sync completed: {result}")

        except Exception as e:
            self.logger.error(f"Git sync failed after retries: {e}")
            self.error_logger.log_error(
                error_type=ErrorType.TRANSIENT,
                message=f"Git sync failed: {e}",
                component="orchestrator",
                operation="sync_vault",
                context={"commit_message": commit_message}
            )

    def sync_now(self, commit_message: str = "Manual sync") -> bool:
        """
        Manually trigger a vault sync.

        Args:
            commit_message: Commit message for the sync

        Returns:
            True if sync succeeded, False otherwise
        """
        if not self.enable_git_sync or not self.git_manager:
            self.logger.warning("Git sync is not enabled")
            return False

        try:
            self._sync_vault_with_retry(commit_message)
            return True
        except Exception as e:
            self.logger.error(f"Manual sync failed: {e}")
            return False

    def _watchdog_loop(self):
        """Periodically check for stalled tasks and recover them."""
        if not self.task_watchdog or not self.recovery_handler:
            return

        self.logger.info("Starting watchdog loop")

        while self.running:
            try:
                # Check for stalled tasks
                stalled_tasks = self.task_watchdog.check_stalled_tasks()

                # Recover stalled tasks
                for task_info in stalled_tasks:
                    self.logger.warning(f"Recovering stalled task: {task_info['task_name']}")
                    result = self.recovery_handler.recover_stalled_task(task_info)

                    if result.get("success"):
                        self.logger.info(f"Successfully recovered task: {task_info['task_name']}")
                    else:
                        self.logger.error(f"Failed to recover task: {result.get('error')}")

                # Sleep for watchdog interval
                time.sleep(self.task_watchdog.check_interval_seconds)

            except Exception as e:
                self.logger.error(f"Error in watchdog loop: {e}")
                self.error_logger.log_error(
                    error_type=ErrorType.SYSTEM,
                    message=f"Watchdog loop error: {e}",
                    component="orchestrator",
                    operation="watchdog_loop"
                )
                time.sleep(self.task_watchdog.check_interval_seconds)

    def _dashboard_merger_loop(self):
        """Periodically merge updates into Dashboard.md (local agent only)."""
        if not self.update_merger:
            return

        self.logger.info(f"Starting dashboard merger loop (interval: {self.dashboard_merge_interval}s)")

        while self.running:
            try:
                # Merge updates into Dashboard.md
                result = self.update_merger.merge_updates_to_dashboard()

                if result.get("success") and result.get("updates_merged", 0) > 0:
                    self.logger.info(f"Merged {result['updates_merged']} updates into Dashboard.md")

                # Sleep for merge interval
                time.sleep(self.dashboard_merge_interval)

            except Exception as e:
                self.logger.error(f"Error in dashboard merger loop: {e}")
                self.error_logger.log_error(
                    error_type=ErrorType.SYSTEM,
                    message=f"Dashboard merger loop error: {e}",
                    component="orchestrator",
                    operation="dashboard_merger_loop"
                )
                time.sleep(self.dashboard_merge_interval)

    def write_status_update(
        self,
        message: str,
        update_type: str = "status",
        priority: str = "medium",
        related_task: Optional[str] = None
    ) -> bool:
        """
        Write a status update (cloud agent only).

        Args:
            message: Status update message
            update_type: Type of update
            priority: Priority level
            related_task: Optional related task ID

        Returns:
            True if successful, False otherwise
        """
        if not self.cloud_update_writer:
            self.logger.warning("CloudUpdateWriter not available (local agent or not initialized)")
            return False

        try:
            result = self.cloud_update_writer.write_status_update(
                message=message,
                update_type=update_type,
                priority=priority,
                related_task=related_task
            )
            return result.get("success", False)
        except Exception as e:
            self.logger.error(f"Failed to write status update: {e}")
            return False


# Example usage
if __name__ == "__main__":
    import sys

    # Example of how to use the orchestrator
    # This would typically be configured based on settings or command line args
    vault_path = sys.argv[1] if len(sys.argv) > 1 else "./AI_Employee_Vault"

    # Set up basic logging
    logging.basicConfig(level=logging.INFO)

    orchestrator = Orchestrator(vault_path)

    # Add watchers (these would be imported and instantiated)
    # orchestrator.add_watcher(SomeWatcher(vault_path))

    # Run the orchestrator
    orchestrator.run()

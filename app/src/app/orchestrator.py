import threading
import logging
import time
from pathlib import Path
from typing import List
from .watchers.base_watcher import BaseWatcher
from .logging_config import get_logger
from .file_processor import FileProcessor


class FileProcessorComponent:
    """
    Component that monitors and processes files in the Needs-Action directory.
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
                # Process all files in Needs-Action directory
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
    def __init__(self, vault_path: str):
        self.vault_path = Path(vault_path)
        self.watchers: List[BaseWatcher] = []
        self.file_processor_component = FileProcessorComponent(str(vault_path))
        self.logger = get_logger(self.__class__.__name__)
        self.running = False
        self.threads = []

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

    def stop_all_watchers(self):
        """Stop all running watchers."""
        self.logger.info("Stopping all watchers...")
        self.running = False

        # Stop the file processor component
        self.file_processor_component.running = False

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
            self.stop_all_watchers()


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

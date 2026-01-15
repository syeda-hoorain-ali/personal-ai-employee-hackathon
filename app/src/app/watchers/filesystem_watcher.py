from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from pathlib import Path
import shutil
import logging
from .base_watcher import BaseWatcher
from ..logging_config import get_logger


class DropFolderHandler(FileSystemEventHandler):
    def __init__(self, vault_path: str):
        self.Needs-Action = Path(vault_path) / 'Needs-Action'
        self.logger = get_logger(self.__class__.__name__)

    def on_created(self, event):
        if event.is_directory:
            return
        source = Path(event.src_path)
        try:
            if source.suffix.lower() == '.md':
                # Only process files that don't already have the FILE_ prefix, EMAIL_ prefix, or _meta suffix
                # This prevents the infinite loop when the handler creates its own files
                if not source.name.startswith('FILE_') and not source.name.startswith('EMAIL_') and not source.name.endswith('_meta.md'):
                    # Move the file from Inbox to Needs-Action to indicate it needs processing
                    dest = self.Needs-Action / source.name
                    shutil.move(str(source), str(dest))
                    self.logger.info(f"Moved file from {source} to {dest}")

                    # Create metadata for the moved file
                    self.create_metadata(dest, dest)
                else:
                    # Skip processing files that were created by the system itself
                    self.logger.debug(f"Skipping system-created file: {source.name}")
        except Exception as e:
            self.logger.error(f"Error processing created file {source}: {e}")

    def on_modified(self, event):
        if event.is_directory:
            return
        source = Path(event.src_path)
        try:
            if source.suffix.lower() == '.md':
                # Only process files that don't already have the FILE_ prefix, EMAIL_ prefix, or _meta suffix
                # This prevents the infinite loop when the handler creates its own files
                if not source.name.startswith('FILE_') and not source.name.startswith('EMAIL_') and not source.name.endswith('_meta.md'):
                    # Handle file modifications if needed
                    self.logger.info(f"Detected modification of file: {source}")
                else:
                    # Skip processing files that were created by the system itself
                    self.logger.debug(f"Skipping system-created file modification: {source.name}")
        except Exception as e:
            self.logger.error(f"Error processing modified file {source}: {e}")

    def on_deleted(self, event):
        if event.is_directory:
            return
        source = Path(event.src_path)
        try:
            self.logger.info(f"Detected deletion of file: {source}")
        except Exception as e:
            self.logger.error(f"Error processing deleted file {source}: {e}")

    def create_metadata(self, source: Path, dest: Path):
        try:
            meta_path = dest.with_name(dest.stem + '_meta.md')
            content = f'''---
type: file_drop
original_name: {source.name}
size: {source.stat().st_size}
detected_at: {Path(source).stat().st_ctime}
---

New file dropped for processing.
'''
            # Write with UTF-8 encoding to handle special characters
            with open(meta_path, 'w', encoding='utf-8') as f:
                f.write(content)
            self.logger.info(f"Created metadata file: {meta_path}")
        except Exception as e:
            self.logger.error(f"Error creating metadata file for {source}: {e}")


class FileSystemWatcher(BaseWatcher):
    def __init__(self, vault_path: str, watch_path: str = None):
        super().__init__(vault_path)

        # Monitor the Inbox directory for incoming files, not Needs-Action
        # This prevents the infinite loop when the watcher creates files in Needs-Action
        self.watch_path = Path(watch_path) if watch_path else self.vault_path / 'Inbox'

        # Validate watch path exists
        if not self.watch_path.exists():
            self.watch_path.mkdir(parents=True, exist_ok=True)
            self.logger.info(f"Created watch path: {self.watch_path}")

        self.observer = Observer()
        self.handler = DropFolderHandler(str(self.vault_path))

    def check_for_updates(self) -> list:
        # The file system watcher uses event-driven approach rather than polling
        # This method is kept for compatibility with the base class
        return []

    def create_action_file(self, item) -> Path:
        # This method is kept for compatibility with the base class
        pass

    def start_monitoring(self):
        """Start monitoring the specified directory for file changes."""
        self.observer.schedule(self.handler, str(self.watch_path), recursive=True)
        self.observer.start()
        self.logger.info(f'Starting file system monitoring for: {self.watch_path}')

    def stop_monitoring(self):
        """Stop monitoring the directory."""
        self.observer.stop()
        self.observer.join()

    def run(self):
        """Override the base run method to use the observer."""
        self.start_monitoring()
        try:
            # Keep the observer running
            import time
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            self.logger.info('Stopping file system watcher...')
            self.stop_monitoring()

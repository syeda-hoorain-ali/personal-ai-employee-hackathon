"""
Module for handling file writing functionality for Claude Code to save processed results.
"""

import os
from pathlib import Path
from typing import Union, Dict, Any
import logging
import shutil
from datetime import datetime


class VaultWriter:
    """
    Class to handle writing files to the Obsidian vault.
    """
    def __init__(self, vault_path: str):
        self.vault_path = Path(vault_path)
        self.logger = logging.getLogger(self.__class__.__name__)

    def write_file(self, file_path: str, content: str, overwrite: bool = True) -> bool:
        """
        Write content to a specific file in the vault.

        Args:
            file_path: Path to the file relative to vault root
            content: Content to write to the file
            overwrite: Whether to overwrite existing files (default: True)

        Returns:
            True if successful, False otherwise
        """
        full_path = self.vault_path / file_path
        full_path.parent.mkdir(parents=True, exist_ok=True)  # Create parent directories if needed

        try:
            if full_path.exists() and not overwrite:
                self.logger.warning(f"File already exists and overwrite=False: {full_path}")
                return False

            full_path.write_text(content, encoding='utf-8')
            self.logger.info(f"Successfully wrote file: {full_path}")
            return True
        except Exception as e:
            self.logger.error(f"Error writing file {full_path}: {e}")
            return False

    def append_to_file(self, file_path: str, content: str) -> bool:
        """
        Append content to an existing file in the vault.

        Args:
            file_path: Path to the file relative to vault root
            content: Content to append to the file

        Returns:
            True if successful, False otherwise
        """
        full_path = self.vault_path / file_path

        try:
            if not full_path.exists():
                self.logger.warning(f"File does not exist, creating new: {full_path}")
                return self.write_file(file_path, content)

            with full_path.open('a', encoding='utf-8') as f:
                f.write(content)

            self.logger.info(f"Successfully appended to file: {full_path}")
            return True
        except Exception as e:
            self.logger.error(f"Error appending to file {full_path}: {e}")
            return False

    def move_file(self, source_path: str, dest_path: str, overwrite: bool = False) -> bool:
        """
        Move a file from one location to another within the vault.

        Args:
            source_path: Source path relative to vault root
            dest_path: Destination path relative to vault root
            overwrite: Whether to overwrite if destination exists (default: False)

        Returns:
            True if successful, False otherwise
        """
        source_full = self.vault_path / source_path
        dest_full = self.vault_path / dest_path
        dest_full.parent.mkdir(parents=True, exist_ok=True)  # Create parent directories if needed

        try:
            if not source_full.exists():
                self.logger.error(f"Source file does not exist: {source_full}")
                return False

            if dest_full.exists() and not overwrite:
                self.logger.warning(f"Destination file exists and overwrite=False: {dest_full}")
                return False

            shutil.move(str(source_full), str(dest_full))
            self.logger.info(f"Successfully moved file: {source_full} -> {dest_full}")
            return True
        except Exception as e:
            self.logger.error(f"Error moving file {source_full} to {dest_full}: {e}")
            return False

    def copy_file(self, source_path: str, dest_path: str, overwrite: bool = False) -> bool:
        """
        Copy a file from one location to another within the vault.

        Args:
            source_path: Source path relative to vault root
            dest_path: Destination path relative to vault root
            overwrite: Whether to overwrite if destination exists (default: False)

        Returns:
            True if successful, False otherwise
        """
        source_full = self.vault_path / source_path
        dest_full = self.vault_path / dest_path
        dest_full.parent.mkdir(parents=True, exist_ok=True)  # Create parent directories if needed

        try:
            if not source_full.exists():
                self.logger.error(f"Source file does not exist: {source_full}")
                return False

            if dest_full.exists() and not overwrite:
                self.logger.warning(f"Destination file exists and overwrite=False: {dest_full}")
                return False

            shutil.copy2(str(source_full), str(dest_full))  # copy2 preserves metadata
            self.logger.info(f"Successfully copied file: {source_full} -> {dest_full}")
            return True
        except Exception as e:
            self.logger.error(f"Error copying file {source_full} to {dest_full}: {e}")
            return False

    def create_timestamped_file(self, directory: str, base_name: str, content: str,
                              extension: str = ".md") -> str:
        """
        Create a file with a timestamp in its name.

        Args:
            directory: Directory relative to vault root
            base_name: Base name for the file
            content: Content to write
            extension: File extension (default: .md)

        Returns:
            Path to the created file (relative to vault root)
        """
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = f"{base_name}_{timestamp}{extension}"
        file_path = f"{directory}/{filename}"

        success = self.write_file(file_path, content)
        if success:
            return file_path
        else:
            return ""

    def update_dashboard(self, activity_message: str) -> bool:
        """
        Update the dashboard with a new activity message.

        Args:
            activity_message: Message to add to the dashboard

        Returns:
            True if successful, False otherwise
        """
        dashboard_path = "Dashboard.md"

        # Read current dashboard
        current_content = ""
        dashboard_full_path = self.vault_path / dashboard_path

        if dashboard_full_path.exists():
            current_content = dashboard_full_path.read_text(encoding='utf-8')

        # Add the new activity with timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d")
        new_activity = f"- [{timestamp}] {activity_message}"

        # Find the "Recent Activity" section and add the new activity
        lines = current_content.split('\n')
        updated_lines = []
        activity_section_found = False

        for line in lines:
            updated_lines.append(line)
            if line.strip() == "## Recent Activity":
                activity_section_found = True
                # Add the new activity after the heading
                updated_lines.append(new_activity)
            elif activity_section_found and line.startswith('- [') and not line.startswith('- [{'):
                # Insert the new activity before the first activity item
                updated_lines.insert(-1, new_activity)
                activity_section_found = False  # Reset flag after insertion

        # If the section wasn't found, create it
        if not activity_section_found:
            # Add the activity section with the new activity
            if updated_lines and updated_lines[-1].strip() != "":
                updated_lines.append("")  # Empty line before section
            updated_lines.extend([
                "## Recent Activity",
                new_activity
            ])

        updated_content = '\n'.join(updated_lines)
        return self.write_file(dashboard_path, updated_content)


# Example usage
if __name__ == "__main__":
    # Example of how to use the VaultWriter
    writer = VaultWriter("./AI_Employee_Vault")

    # Write a test file
    success = writer.write_file("test_output.md", "# Test Output\nThis is a test file from Claude Code.")
    print(f"Write success: {success}")

    # Update dashboard with an activity
    writer.update_dashboard("Test activity added by Claude Code")

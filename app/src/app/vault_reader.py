"""
Module for handling file reading functionality for Claude Code to access vault files.
"""

import os
from pathlib import Path
from typing import List, Dict, Optional
import logging


class VaultReader:
    """
    Class to handle reading files from the Obsidian vault.
    """
    def __init__(self, vault_path: str):
        self.vault_path = Path(vault_path)
        self.logger = logging.getLogger(self.__class__.__name__)

    def read_file(self, file_path: str) -> Optional[str]:
        """
        Read a specific file from the vault.

        Args:
            file_path: Path to the file relative to vault root

        Returns:
            Content of the file as string, or None if file doesn't exist
        """
        full_path = self.vault_path / file_path

        try:
            if full_path.exists() and full_path.is_file():
                content = full_path.read_text(encoding='utf-8')
                self.logger.info(f"Successfully read file: {full_path}")
                return content
            else:
                self.logger.warning(f"File does not exist: {full_path}")
                return None
        except Exception as e:
            self.logger.error(f"Error reading file {full_path}: {e}")
            return None

    def read_files_in_directory(self, directory: str, extension: str = ".md") -> Dict[str, str]:
        """
        Read all files with a specific extension in a directory.

        Args:
            directory: Directory name relative to vault root
            extension: File extension to filter by (default: .md)

        Returns:
            Dictionary mapping filenames to their content
        """
        dir_path = self.vault_path / directory
        files_content = {}

        if not dir_path.exists():
            self.logger.warning(f"Directory does not exist: {dir_path}")
            return files_content

        for file_path in dir_path.glob(f"*{extension}"):
            try:
                content = file_path.read_text(encoding='utf-8')
                files_content[file_path.name] = content
                self.logger.info(f"Read file: {file_path.name}")
            except Exception as e:
                self.logger.error(f"Error reading file {file_path}: {e}")

        return files_content

    def get_file_list(self, directory: str, extension: str = ".md") -> List[str]:
        """
        Get a list of files with a specific extension in a directory.

        Args:
            directory: Directory name relative to vault root
            extension: File extension to filter by (default: .md)

        Returns:
            List of filenames
        """
        dir_path = self.vault_path / directory
        files = []

        if not dir_path.exists():
            self.logger.warning(f"Directory does not exist: {dir_path}")
            return files

        for file_path in dir_path.glob(f"*{extension}"):
            files.append(file_path.name)

        self.logger.info(f"Found {len(files)} files in {directory}")
        return files

    def search_content(self, directory: str, search_term: str, extension: str = ".md") -> List[Dict[str, str]]:
        """
        Search for a term in files within a directory.

        Args:
            directory: Directory name relative to vault root
            search_term: Term to search for
            extension: File extension to search in (default: .md)

        Returns:
            List of dictionaries containing filename and matching content snippets
        """
        dir_path = self.vault_path / directory
        matches = []

        if not dir_path.exists():
            self.logger.warning(f"Directory does not exist: {dir_path}")
            return matches

        for file_path in dir_path.glob(f"*{extension}"):
            try:
                content = file_path.read_text(encoding='utf-8')
                if search_term.lower() in content.lower():
                    # Find context around the search term
                    lines = content.split('\n')
                    found_lines = []

                    for i, line in enumerate(lines):
                        if search_term.lower() in line.lower():
                            # Add context (previous and next lines)
                            start = max(0, i - 1)
                            end = min(len(lines), i + 2)
                            context = '\n'.join(lines[start:end])
                            found_lines.append(context)

                    matches.append({
                        'filename': file_path.name,
                        'content_snippet': '\n...\n'.join(found_lines[:3])  # Limit to first 3 matches
                    })
            except Exception as e:
                self.logger.error(f"Error searching in file {file_path}: {e}")

        self.logger.info(f"Found {len(matches)} matches for '{search_term}' in {directory}")
        return matches


# Example usage
if __name__ == "__main__":
    # Example of how to use the VaultReader
    reader = VaultReader("./AI_Employee_Vault")

    # Read specific file
    handbook_content = reader.read_file("Company_Handbook.md")
    if handbook_content:
        print(f"Handbook length: {len(handbook_content)} characters")

    # Read all files in Needs_Action
    needs_action_files = reader.read_files_in_directory("Needs_Action")
    print(f"Found {len(needs_action_files)} files in Needs_Action")

    # Get list of files in Plans
    plan_files = reader.get_file_list("Plans")
    print(f"Plan files: {plan_files}")

"""
Module for monitoring files and automatically triggering Claude Code to process them based on rules defined in Company-Handbook.md.
This module automatically invokes Claude Code when files in the Needs_Action folder need processing.
"""

import os
from pathlib import Path
from typing import Dict, List, Tuple, Any
from .vault_reader import VaultReader
from .vault_writer import VaultWriter
import re
import logging
import subprocess
import time


class FileProcessor:
    """
    Class to monitor and automatically trigger Claude Code to process files based on Company Handbook rules.
    This version actively invokes Claude Code when files are detected in the Needs-Action folder.
    """
    def __init__(self, vault_path: str):
        self.vault_path = Path(vault_path)
        self.reader = VaultReader(vault_path)
        self.writer = VaultWriter(vault_path)
        self.logger = logging.getLogger(self.__class__.__name__)

        # Load company handbook rules
        self.handbook_rules = self._load_handbook_rules()

    def _load_handbook_rules(self) -> Dict[str, str]:
        """
        Load rules from Company-Handbook.md.

        Returns:
            Dictionary of rule categories and their definitions
        """
        handbook_content = self.reader.read_file("Company-Handbook.md")
        rules = {}

        if not handbook_content:
            self.logger.warning("Could not load Company-Handbook.md, using default rules")
            return self._get_default_rules()

        # Extract sections from handbook
        sections = self._parse_handbook(handbook_content)

        # Process each section for rules
        for section_title, section_content in sections.items():
            if "guideline" in section_title.lower() or "rule" in section_title.lower():
                rules[section_title] = section_content

        return rules

    def _parse_handbook(self, content: str) -> Dict[str, str]:
        """
        Parse the Company Handbook into sections.

        Args:
            content: Content of the handbook

        Returns:
            Dictionary mapping section titles to their content
        """
        sections = {}
        lines = content.split('\n')

        current_section = ""
        current_content = []

        for line in lines:
            # Check if this is a header (starts with #)
            if line.strip().startswith('#'):
                # Save previous section
                if current_section:
                    sections[current_section] = '\n'.join(current_content)

                # Start new section
                current_section = line.strip('# ')
                current_content = []
            else:
                current_content.append(line)

        # Save the last section
        if current_section:
            sections[current_section] = '\n'.join(current_content)

        return sections

    def _get_default_rules(self) -> Dict[str, str]:
        """
        Get default rules if handbook is not available.

        Returns:
            Dictionary of default rules
        """
        return {
            "Communication Guidelines": "Always be professional and courteous in communications",
            "Financial Guidelines": "Require approval for payments over $100",
            "Task Management": "Process tasks in priority order"
        }

    def process_file(self, file_path: str, rules_context: str = "default") -> Tuple[bool, str]:
        """
        Create a Claude Code interaction prompt for processing a file based on rules defined in the Company Handbook.
        Instead of processing the file directly, this creates a prompt that would be handled by Claude Code.

        Args:
            file_path: Path to the file to process
            rules_context: Context for which rules to apply (default: "default")

        Returns:
            Tuple of (success: bool, message: str)
        """
        content = self.reader.read_file(file_path)
        if not content:
            return False, f"Could not read file: {file_path}"

        # Indicate to Claude Code that this file needs processing
        success = self._trigger_claude_processing(file_path)

        if success:
            # Update dashboard
            self.writer.update_dashboard(f"File {os.path.basename(file_path)} is ready for Claude Code processing")
            return True, f"Claude Code notified to process {file_path}"
        else:
            return False, f"Failed to notify Claude Code to process: {file_path}"

    def _trigger_claude_processing(self, file_path: str) -> bool:
        """
        Trigger Claude Code to process this file using the needs-action-processor skill.
        Uses the ccr code -p command to run Claude Code in non-interactive mode.

        Args:
            file_path: Path to the file to process

        Returns:
            True if successful, False otherwise
        """
        try:
            self.logger.info(f"Triggering Claude Code to process: {file_path}")

            # Create a prompt that tells Claude Code to use the needs-action-processor skill
            prompt = f'Use the needs-action-processor skill to process files in the Needs-Action folder. The file {file_path} needs processing according to the Company Handbook rules.'

            # Execute Claude Code with the prompt in non-interactive mode
            result = subprocess.run(
                ['ccr', 'code', '-p', prompt],
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )

            if result.returncode == 0:
                self.logger.info(f"Successfully triggered Claude Code for: {file_path}")
                self.writer.update_dashboard(f"Claude Code triggered to process {os.path.basename(file_path)}")
                return True
            else:
                self.logger.error(f"Failed to trigger Claude Code: {result.stderr}")
                return False

        except subprocess.TimeoutExpired:
            self.logger.error(f"Claude Code command timed out for: {file_path}")
            return False
        except FileNotFoundError:
            self.logger.warning("ccr command not found, unable to trigger Claude Code. Manual processing required.")
            # Still update the dashboard so user knows the file needs processing
            self.writer.update_dashboard(f"File {os.path.basename(file_path)} is ready for Claude Code processing (ccr not found)")
            return True  # Return True to indicate this is not a permanent failure
        except Exception as e:
            self.logger.error(f"Error triggering Claude Code for {file_path}: {e}")
            return False

    def _mark_file_as_queued(self, file_path: str) -> bool:
        """
        Mark the original file as queued for Claude processing.

        Args:
            file_path: Path to the file to mark

        Returns:
            True if successful, False otherwise
        """
        try:
            # Read the original file
            content = self.reader.read_file(file_path)
            if not content:
                return False

            # Add a processing status indicator to the file
            status_indicator = f"\n\n<!-- Queued for Claude Code processing at {Path(file_path).stat().st_mtime} -->\n"
            updated_content = content + status_indicator

            # Write back to the file
            file_full_path = self.vault_path / file_path
            with open(file_full_path, 'a', encoding='utf-8') as f:
                f.write(status_indicator)

            return True
        except Exception as e:
            self.logger.error(f"Error marking file as queued {file_path}: {e}")
            return False

    def _apply_rules(self, content: str, file_path: str, context: str) -> Tuple[str, List[str]]:
        """
        Apply rules from the handbook to the file content.
        This method is maintained for backward compatibility but now primarily creates Claude prompts.

        Args:
            content: Content of the file to process
            file_path: Path to the file being processed
            context: Context for which rules to apply

        Returns:
            Tuple of (processed content: str, list of actions needed: List[str])
        """
        actions_needed = []

        # Look for keywords in the content that might trigger specific rules
        content_lower = content.lower()

        # Check for payment-related keywords
        payment_keywords = ['payment', 'pay', 'invoice', 'bill', 'expense', 'cost', 'charge']
        if any(keyword in content_lower for keyword in payment_keywords):
            # Apply financial guidelines
            handbook_content = self.handbook_rules.get("Financial Guidelines", "")

            # Check for amounts
            amount_pattern = r'\$([0-9,]+\.?[0-9]*)'
            amounts = re.findall(amount_pattern, content.replace(',', ''))

            for amount_str in amounts:
                try:
                    amount = float(amount_str)
                    # Check if approval is needed based on handbook rules
                    if amount > 100:  # Default threshold
                        # Extract more specific rules from handbook if available
                        if "requires approval" in handbook_content.lower() and str(amount) in handbook_content:
                            actions_needed.append(f"APPROVAL_NEEDED: Payment of ${amount} requires approval")
                except ValueError:
                    continue

        # Check for communication-related keywords
        comm_keywords = ['email', 'message', 'contact', 'reply', 'response', 'communication']
        if any(keyword in content_lower for keyword in comm_keywords):
            # Apply communication guidelines
            actions_needed.append("COMMUNICATION_RULES_APPLIED")

        # Check for urgency indicators
        urgency_keywords = ['urgent', 'asap', 'emergency', 'immediate', 'right now', 'today']
        if any(keyword in content_lower for keyword in urgency_keywords):
            actions_needed.append("HIGH_PRIORITY_TAGGED")

        return content, actions_needed

    def _determine_next_action(self, actions_needed: List[str], file_path: str) -> str:
        """
        Determine the next action based on applied rules.
        This method is maintained for backward compatibility but Claude Code will ultimately decide.

        Args:
            actions_needed: List of actions that need to be taken
            file_path: Path to the file being processed

        Returns:
            Next action (folder to move file to)
        """
        # Default action is to move to Done
        next_action = "Done"

        # Check if any action requires approval
        if any("APPROVAL_NEEDED" in action for action in actions_needed):
            next_action = "Pending-Approval"
        elif any("HIGH_PRIORITY" in action for action in actions_needed):
            # For high priority items, they might need special handling
            # Claude Code will make the final decision
            next_action = "Done"
        else:
            next_action = "Done"

        return next_action

    def _move_processed_file(self, original_path: str, next_action: str) -> bool:
        """
        Move the processed file to the appropriate location.
        In the Claude-integrated version, this would be handled by Claude Code after processing.

        Args:
            original_path: Original file path
            next_action: Next action (destination folder)

        Returns:
            True if successful, False otherwise
        """
        # Extract just the filename
        filename = Path(original_path).name

        # Create destination path
        if next_action == "Pending-Approval":
            # For approval items, we might create a specific approval file
            dest_path = f"Pending-Approval/{filename}"
        else:
            dest_path = f"{next_action}/{filename}"

        # In the Claude-integrated version, the actual movement would be done by Claude Code
        # We'll just log that this action should be taken
        self.logger.info(f"Scheduled file movement: {original_path} -> {dest_path} (to be handled by Claude Code)")
        return True

    def process_needs_action_directory(self) -> Dict[str, Any]:
        """
        Process all files in the Needs-Action directory by creating Claude Code prompts.
        This simulates how Claude Code would process files in the Needs_Action folder.

        Returns:
            Dictionary with processing results
        """
        results = {
            "processed_count": 0,
            "successful": [],
            "failed": [],
            "approval_needed": []
        }

        # Get all files in Needs-Action directory, excluding metadata files
        needs_action_files = [f for f in self.reader.get_file_list("Needs-Action", ".md") if not f.endswith('_meta.md')]

        for filename in needs_action_files:
            file_path = f"Needs-Action/{filename}"
            success, message = self.process_file(file_path)

            if success:
                results["successful"].append(filename)
                results["processed_count"] += 1

                # In the Claude-integrated version, approval decisions would be made by Claude
                if "Claude Code notified" in message:
                    # We'll assume Claude will handle approval decisions
                    pass
            else:
                results["failed"].append(filename)
                self.logger.error(f"Failed to process {filename}: {message}")

        return results


# Example usage
if __name__ == "__main__":
    processor = FileProcessor("./AI_Employee_Vault")

    # Process all files in Needs-Action directory
    results = processor.process_needs_action_directory()

    print(f"Processed {results['processed_count']} files")
    print(f"Successful: {len(results['successful'])}")
    print(f"Failed: {len(results['failed'])}")
    print(f"Approval needed: {len(results['approval_needed'])}")

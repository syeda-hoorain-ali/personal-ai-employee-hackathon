"""
Module for processing files based on rules defined in Company-Handbook.md.
"""

import os
from pathlib import Path
from typing import Dict, List, Tuple
from .vault_reader import VaultReader
from .vault_writer import VaultWriter
import re
import logging


class FileProcessor:
    """
    Class to process files based on rules defined in the Company Handbook.
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
        Process a file based on rules defined in the Company Handbook.

        Args:
            file_path: Path to the file to process
            rules_context: Context for which rules to apply (default: "default")

        Returns:
            Tuple of (success: bool, message: str)
        """
        content = self.reader.read_file(file_path)
        if not content:
            return False, f"Could not read file: {file_path}"

        # Apply rules based on the content type
        processed_content, actions_needed = self._apply_rules(content, file_path, rules_context)

        # Determine next action based on rules
        next_action = self._determine_next_action(actions_needed, file_path)

        # Move file to appropriate location based on rules
        success = self._move_processed_file(file_path, next_action)

        if success:
            # Update dashboard
            self.writer.update_dashboard(f"Processed file: {os.path.basename(file_path)} -> {next_action}")
            return True, f"File processed and moved to {next_action}"
        else:
            return False, f"Failed to move processed file: {file_path}"

    def _apply_rules(self, content: str, file_path: str, context: str) -> Tuple[str, List[str]]:
        """
        Apply rules from the handbook to the file content.

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
            # But for now, we'll move them to Done after processing
            next_action = "Done"
        else:
            next_action = "Done"

        return next_action

    def _move_processed_file(self, original_path: str, next_action: str) -> bool:
        """
        Move the processed file to the appropriate location.

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

        # Move the file
        success = self.writer.move_file(original_path, dest_path)
        return success

    def process_Needs-Action_directory(self) -> Dict[str, any]:
        """
        Process all files in the Needs-Action directory.

        Returns:
            Dictionary with processing results
        """
        results = {
            "processed_count": 0,
            "successful": [],
            "failed": [],
            "approval_needed": []
        }

        # Get all files in Needs-Action directory
        Needs-Action_files = self.reader.get_file_list("Needs-Action", ".md")

        for filename in Needs-Action_files:
            file_path = f"Needs-Action/{filename}"
            success, message = self.process_file(file_path)

            if success:
                results["successful"].append(filename)
                results["processed_count"] += 1

                # Check if approval was needed
                if "Pending-Approval" in message:
                    results["approval_needed"].append(filename)
            else:
                results["failed"].append(filename)
                self.logger.error(f"Failed to process {filename}: {message}")

        return results


# Example usage
if __name__ == "__main__":
    processor = FileProcessor("./AI_Employee_Vault")

    # Process all files in Needs-Action directory
    results = processor.process_Needs-Action_directory()

    print(f"Processed {results['processed_count']} files")
    print(f"Successful: {len(results['successful'])}")
    print(f"Failed: {len(results['failed'])}")
    print(f"Approval needed: {len(results['approval_needed'])}")

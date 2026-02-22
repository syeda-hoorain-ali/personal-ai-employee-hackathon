"""
Module for monitoring files and automatically triggering Claude Code to process them based on rules defined in Company_Handbook.md.
This module automatically invokes Claude Code when files in the Needs_Action folder need processing.
"""

import os
import re
import logging
import subprocess
from pathlib import Path
from typing import Dict, List, Tuple, Any
from .vault_reader import VaultReader
from .vault_writer import VaultWriter
from .error_recovery import (
    ErrorLogger,
    CircuitBreaker,
    FileQuarantine,
    ErrorType,
    CircuitBreakerOpenError,
    QuarantineError
)


class FileProcessor:
    """
    Class to monitor and automatically trigger Claude Code to process files based on Company Handbook rules.
    This version actively invokes Claude Code when files are detected in the Needs_Action folder.
    """
    def __init__(self, vault_path: str):
        self.vault_path = Path(vault_path)
        self.reader = VaultReader(vault_path)
        self.writer = VaultWriter(vault_path)
        self.logger = logging.getLogger(self.__class__.__name__)

        # Initialize error logger
        logs_dir = self.vault_path / "Logs"
        error_logs_dir = logs_dir / "Errors"
        dashboard_path = self.vault_path / ".system" / "error_dashboard.json"
        self.error_logger = ErrorLogger(error_logs_dir, dashboard_path)

        # Initialize circuit breaker
        health_status_path = self.vault_path / ".system" / "health_status.json"
        self.circuit_breaker = CircuitBreaker(
            component="FileProcessor",
            failure_threshold=4,
            timeout_seconds=60,
            health_status_path=health_status_path,
            error_logger=self.error_logger
        )

        # Initialize file quarantine
        quarantine_dir = self.vault_path / ".system" / "quarantine"
        self.file_quarantine = FileQuarantine(
            quarantine_dir=quarantine_dir,
            error_logger=self.error_logger
        )

        # Load company handbook rules
        self.handbook_rules = self._load_handbook_rules()

        # Track files that have already been processed to avoid repetitive logging
        self.processed_files = set()

    def _load_handbook_rules(self) -> Dict[str, str]:
        """
        Load rules from Company_Handbook.md.

        Returns:
            Dictionary of rule categories and their definitions
        """
        handbook_content = self.reader.read_file("Company_Handbook.md")
        rules = {}

        if not handbook_content:
            self.logger.warning("Could not load Company_Handbook.md, using default rules")
            # Log as DATA error since handbook file is missing/corrupted
            self.error_logger.log_error(
                component="FileProcessor",
                error_type=ErrorType.DATA,
                message="Could not load Company_Handbook.md, using default rules",
                context={"handbook_path": "Company_Handbook.md"}
            )
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
        try:
            content = self.reader.read_file(file_path)
            if not content:
                # Quarantine corrupted/unreadable files
                try:
                    file_full_path = self.vault_path / file_path
                    if file_full_path.exists():
                        quarantine_id = self.file_quarantine.quarantine_file(
                            file_path=file_full_path,
                            reason="File could not be read - possibly corrupted or invalid encoding",
                            error_type=ErrorType.DATA,
                            component="FileProcessor",
                            additional_metadata={"rules_context": rules_context}
                        )
                        self.logger.warning(f"Quarantined unreadable file: {file_path} (ID: {quarantine_id})")
                        return False, f"File quarantined due to read error: {quarantine_id}"
                except QuarantineError as qe:
                    self.logger.error(f"Failed to quarantine corrupted file {file_path}: {qe}")

                # Log as DATA error since file is missing/corrupted
                self.error_logger.log_error(
                    component="FileProcessor",
                    error_type=ErrorType.DATA,
                    message=f"Could not read file: {file_path}",
                    context={"file_path": file_path, "rules_context": rules_context}
                )
                return False, f"Could not read file: {file_path}"

            # Validate file content (basic checks for corruption)
            if not self._validate_file_content(content, file_path):
                # Quarantine invalid files
                try:
                    file_full_path = self.vault_path / file_path
                    quarantine_id = self.file_quarantine.quarantine_file(
                        file_path=file_full_path,
                        reason="File content validation failed - malformed or corrupted data",
                        error_type=ErrorType.DATA,
                        component="FileProcessor",
                        additional_metadata={"rules_context": rules_context, "content_length": len(content)}
                    )
                    self.logger.warning(f"Quarantined invalid file: {file_path} (ID: {quarantine_id})")
                    return False, f"File quarantined due to validation failure: {quarantine_id}"
                except QuarantineError as qe:
                    self.logger.error(f"Failed to quarantine invalid file {file_path}: {qe}")
                    return False, f"File validation failed and quarantine failed: {file_path}"

            # Execute through circuit breaker to prevent cascading failures
            success = self.circuit_breaker.call(self._trigger_claude_processing, file_path)

            if success:
                return True, f"Claude Code notified to process {file_path}"
            else:
                return False, f"Failed to notify Claude Code to process: {file_path}"
        except CircuitBreakerOpenError as e:
            self.logger.warning(f"Circuit breaker is open, cannot process file: {e}")
            return False, f"Circuit breaker is open, file processing paused: {file_path}"
        except Exception as e:
            # Catch any unexpected errors and quarantine the file
            self.logger.error(f"Unexpected error processing file {file_path}: {e}")
            try:
                file_full_path = self.vault_path / file_path
                if file_full_path.exists():
                    quarantine_id = self.file_quarantine.quarantine_file(
                        file_path=file_full_path,
                        reason=f"Unexpected error during processing: {str(e)[:200]}",
                        error_type=ErrorType.SYSTEM,
                        component="FileProcessor",
                        additional_metadata={"rules_context": rules_context, "error_type": type(e).__name__}
                    )
                    self.logger.warning(f"Quarantined problematic file: {file_path} (ID: {quarantine_id})")
                    return False, f"File quarantined due to processing error: {quarantine_id}"
            except QuarantineError:
                pass

            self.error_logger.log_error(
                component="FileProcessor",
                error_type=ErrorType.SYSTEM,
                message=f"Unexpected error processing file",
                error=e,
                context={"file_path": file_path, "rules_context": rules_context}
            )
            return False, f"Error processing file: {file_path}"

    def _validate_file_content(self, content: str, file_path: str) -> bool:
        """
        Validate file content for basic corruption checks.

        Args:
            content: File content to validate
            file_path: Path to the file being validated

        Returns:
            True if valid, False if corrupted/invalid
        """
        try:
            # Check for null bytes (indicates binary corruption in text files)
            if '\x00' in content:
                self.logger.warning(f"File contains null bytes: {file_path}")
                return False

            # Check for excessive control characters (might indicate corruption)
            control_char_count = sum(1 for c in content if ord(c) < 32 and c not in '\n\r\t')
            if len(content) > 0 and control_char_count / len(content) > 0.1:
                self.logger.warning(f"File contains excessive control characters: {file_path}")
                return False

            # For markdown files, check for basic structure
            if file_path.endswith('.md'):
                # Very basic check - markdown should have some readable text
                if len(content.strip()) == 0:
                    self.logger.warning(f"Markdown file is empty: {file_path}")
                    return False

            return True

        except Exception as e:
            self.logger.error(f"Error validating file content for {file_path}: {e}")
            return False

    def _trigger_claude_processing(self, file_path: str) -> bool:
        """
        Trigger Claude Code to process this file using the Needs_Action-processor skill.
        Uses the ccr code -p command to run Claude Code in non-interactive mode.

        Args:
            file_path: Path to the file to process

        Returns:
            True if successful, False otherwise
        """
        try:
            self.logger.info(f"Triggering Claude Code to process: {file_path}")

            # Create a prompt that tells Claude Code to use the needs-action-processor skill
            prompt = f'/ralph-loop:ralph-loop "Use the needs-action-processor skill to process files in the Needs_Action folder. The file {file_path} needs processing according to the Company Handbook rules." --max-iterations 15 --completion-promise "<promise>DONE: File processed successfully</promise>"'

            # Execute Claude Code with the prompt in non-interactive mode
            result = subprocess.run(
                [
                    'ccr', 'code',
                    '--allowedTools', 'Bash,Read,Write(./AI_Employee_Vault*),Edit(./AI_Employee_Vault*),Skill,mcp__gmail__*,mcp__playwright__*,mcp__xero__*,mcp__twitter-x__*',
                    '--disallowedTools', 'Bash(rm:*),mcp__gmail__delete_email,mcp__gmail__batch_delete_emails',
                    '--no-session-persistence',
                    '-p', prompt
                ],
                capture_output=True,
                text=True,
                timeout=600,  # 10 minute timeout
                encoding='utf-8',
                errors='replace',    # Replace bad characters with �
                shell=True,
            )

            if result.returncode == 0:
                self.logger.info(f"Successfully triggered Claude Code for: {file_path}")
                return True
            else:
                self.logger.error(f"Failed to trigger Claude Code: {result.stderr}")
                # Log as LOGIC error since Claude Code invocation failed
                self.error_logger.log_error(
                    component="FileProcessor",
                    error_type=ErrorType.LOGIC,
                    message=f"Claude Code invocation failed with non-zero return code",
                    error_code=str(result.returncode),
                    context={
                        "file_path": file_path,
                        "stderr": result.stderr[:500] if result.stderr else None,
                        "stdout": result.stdout[:500] if result.stdout else None
                    }
                )
                return False

        except subprocess.TimeoutExpired as e:
            self.logger.error(f"Claude Code command timed out for: {file_path}")
            # Log as TRANSIENT error since timeout might be temporary
            self.error_logger.log_error(
                component="FileProcessor",
                error_type=ErrorType.TRANSIENT,
                message=f"Claude Code command timed out after 600 seconds",
                error=e,
                context={"file_path": file_path, "timeout_seconds": 600}
            )
            return False
        except FileNotFoundError as e:
            self.logger.warning("ccr command not found, unable to trigger Claude Code. Manual processing required.")
            # Log as SYSTEM error since ccr command is missing
            self.error_logger.log_error(
                component="FileProcessor",
                error_type=ErrorType.SYSTEM,
                message="ccr command not found - Claude Code CLI not installed or not in PATH",
                error=e,
                context={"file_path": file_path}
            )
            return False
        except Exception as e:
            self.logger.error(f"Error triggering Claude Code for {file_path}: {e}")
            # Log as SYSTEM error for unexpected exceptions
            self.error_logger.log_error(
                component="FileProcessor",
                error_type=ErrorType.SYSTEM,
                message=f"Unexpected error triggering Claude Code",
                error=e,
                context={"file_path": file_path}
            )
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
                # Log as DATA error since file is missing/corrupted
                self.error_logger.log_error(
                    component="FileProcessor",
                    error_type=ErrorType.DATA,
                    message=f"Could not read file to mark as queued: {file_path}",
                    context={"file_path": file_path, "operation": "mark_as_queued"}
                )
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
            # Log as SYSTEM error for file write failures
            self.error_logger.log_error(
                component="FileProcessor",
                error_type=ErrorType.SYSTEM,
                message=f"Failed to mark file as queued",
                error=e,
                context={"file_path": file_path, "operation": "mark_as_queued"}
            )
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
        actions_needed: List[str] = []

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
            next_action = "Pending_Approval"
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
        if next_action == "Pending_Approval":
            # For approval items, we might create a specific approval file
            dest_path = f"Pending_Approval/{filename}"
        else:
            dest_path = f"{next_action}/{filename}"

        # In the Claude-integrated version, the actual movement would be done by Claude Code
        # We'll just log that this action should be taken
        self.logger.info(f"Scheduled file movement: {original_path} -> {dest_path} (to be handled by Claude Code)")
        return True

    def process_needs_action_directory(self) -> Dict[str, Any]:
        """
        Process all files in the Needs_Action directory by creating Claude Code prompts.
        This simulates how Claude Code would process files in the Needs_Action folder.

        Returns:
            Dictionary with processing results
        """
        results = {
            "processed_count": 0,
            "successful": [],
            "failed": [],
            "approval_needed": [],
        }

        try:
            # Get all files in Needs_Action directory, excluding metadata files
            needs_action_files = [f for f in self.reader.get_file_list("Needs_Action", ".md") if not f.endswith('_meta.md')]

            for filename in needs_action_files:
                file_path = f"Needs_Action/{filename}"

                # Check if this file has already been processed to avoid repetitive logging
                if file_path in self.processed_files:
                    continue

                success, message = self.process_file(file_path)

                if success:
                    results["successful"].append(filename)
                    results["processed_count"] += 1
                    # Mark this file as processed to avoid re-processing
                    self.processed_files.add(file_path)

                    # In the Claude-integrated version, approval decisions would be made by Claude
                    if "Claude Code notified" in message:
                        # We'll assume Claude will handle approval decisions
                        pass
                else:
                    results["failed"].append(filename)
                    self.logger.error(f"Failed to process {filename}: {message}")
                    # Error already logged in process_file(), no need to duplicate

        except Exception as e:
            self.logger.error(f"Error processing Needs_Action directory: {e}")
            # Log as SYSTEM error for unexpected directory processing failures
            self.error_logger.log_error(
                component="FileProcessor",
                error_type=ErrorType.SYSTEM,
                message="Failed to process Needs_Action directory",
                error=e,
                context={
                    "processed_count": results["processed_count"],
                    "successful_count": len(results["successful"]),
                    "failed_count": len(results["failed"])
                }
            )

        return results


# Example usage
if __name__ == "__main__":
    processor = FileProcessor("./AI_Employee_Vault")

    # Process all files in Needs_Action directory
    results = processor.process_needs_action_directory()

    print(f"Processed {results['processed_count']} files")
    print(f"Successful: {len(results['successful'])}")
    print(f"Failed: {len(results['failed'])}")
    print(f"Approval needed: {len(results['approval_needed'])}")

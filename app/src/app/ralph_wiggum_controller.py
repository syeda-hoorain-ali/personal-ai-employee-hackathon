"""
Ralph Wiggum Loop Controller for the Personal AI Employee.

This module implements the Ralph Wiggum pattern to create an autonomous reasoning loop
that generates Plan.md files for task management. The controller keeps Claude Code
working until a task is complete by managing iterative prompts and tracking progress.
"""
import os
import sys
import time
import subprocess
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime


class RalphWiggumController:
    """
    Controls the Ralph Wiggum loop for autonomous task completion.

    This controller manages Claude's iterative processing until tasks are complete,
    creating Plan.md files to track progress and using ccr code to execute prompts.
    """

    def __init__(self, vault_path: str, max_iterations: int = 10):
        """
        Initialize the Ralph Wiggum controller.

        Args:
            vault_path: Path to the Obsidian vault
            max_iterations: Maximum number of iterations to prevent infinite loops
        """
        self.vault_path = Path(vault_path)
        self.max_iterations = max_iterations
        self.logger = self._setup_logging()

    def _setup_logging(self) -> logging.Logger:
        """Set up logging for the controller."""
        logger = logging.getLogger("RalphWiggumController")
        logger.setLevel(logging.INFO)

        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)

        return logger

    def _create_plan_file(self, task_description: str, iteration: int) -> Path:
        """
        Create a Plan.md file in the Plans directory with structured content.

        Args:
            task_description: Description of the task to be planned
            iteration: Current iteration number

        Returns:
            Path to the created plan file
        """
        plans_dir = self.vault_path / "Plans"
        plans_dir.mkdir(exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        plan_filename = f"PLAN_{timestamp}_iteration_{iteration}.md"
        plan_path = plans_dir / plan_filename

        plan_content = f"""# Task Plan - Iteration {iteration}

**Created:** {datetime.now().isoformat()}
**Task:** {task_description}
**Iteration:** {iteration}/{self.max_iterations}

## Claude Reasoning Layer Workflow
Following the Claude reasoning layer pattern:
1. READ: Files from Needs_Action folder
2. UNDERSTAND: Content and requirements
3. PLAN: Create and update Plan.md files
4. DECIDE: Human approval vs direct action
5. ACT: Execute appropriate actions
6. REPEAT: Until all tasks are processed

## Objective
Process files from Needs_Action folder following the reasoning layer workflow until all tasks are completed.

## Progress Tracking
- [ ] **Iteration {iteration}**: READ - Scan Needs_Action folder for new files
- [ ] **Iteration {iteration}**: UNDERSTAND - Analyze file content and requirements
- [ ] **Iteration {iteration}**: PLAN - Create/update Plan.md files with action items
- [ ] **Iteration {iteration}**: DECIDE - Determine if human approval needed
- [ ] **Iteration {iteration}**: ACT - Move files to appropriate folders (Pending_Approval or Done)
- [ ] **Iteration {iteration}**: UPDATE - Update Dashboard.md with outcomes

## Current Status
Processing iteration {iteration} of maximum {self.max_iterations}.
**Last Updated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Files Processed in This Session
- [ ] Identify files in Needs_Action folder
- [ ] Apply Company Handbook rules to each file
- [ ] Create specific action plans for each file

## Approval Checking
- [ ] Check for payment amounts > $100 (requires approval)
- [ ] Check for sensitive communications (may require approval)
- [ ] Check for other approval-required conditions per Company Handbook

## Next Steps
1. Scan Needs_Action folder for new files
2. Process each file according to Company Handbook rules
3. Create/update Plan.md files for tracking
4. Move files to appropriate destination (Pending_Approval or Done)
5. Update Dashboard.md with outcomes

## Completion Criteria
- [ ] All files in Needs_Action folder are processed
- [ ] Files requiring approval are moved to Pending_Approval folder
- [ ] Files not requiring approval are moved to Done folder after action
- [ ] Dashboard.md is updated with all outcomes
- [ ] Plan file is marked as complete
"""

        plan_path.write_text(plan_content)
        self.logger.info(f"Created plan file: {plan_path}")

        return plan_path

    def _create_task_processing_prompt(self, task_description: str, iteration: int, plan_file: Path) -> str:
        """
        Create a prompt for Claude to process the task and update the plan.

        Args:
            task_description: Description of the task to process
            iteration: Current iteration number
            plan_file: Path to the plan file

        Returns:
            Formatted prompt for Claude
        """
        prompt = f"""
        You are operating in autonomous reasoning mode following the Claude reasoning layer workflow. Your task is to process files from the Needs_Action folder:

        {task_description}

        ## Claude Reasoning Layer Workflow:
        1. READ: Read files from the Needs_Action folder
        2. UNDERSTAND: Analyze and understand the content of each file
        3. PLAN: Create and update Plan.md files in the Plans folder
        4. DECIDE: If human approval is needed, move files to Pending_Approval folder
        5. ACT: Otherwise, perform the required action and move files to Done folder
        6. REPEAT: Continue until all tasks are processed

        ## Current State:
        - Needs_Action folder contains files waiting for processing
        - Company_Handbook.md contains rules for processing
        - Plans folder is where Plan.md files should be created
        - Pending_Approval folder is for items needing human approval
        - Done folder is for completed items
        - Dashboard.md tracks outcomes

        ## Instructions for this iteration:
        1. Read the current plan file at {plan_file.relative_to(self.vault_path)}
        2. Assess the current state of the task
        3. Read files from Needs_Action folder to understand what needs processing
        4. Apply rules from Company_Handbook.md to determine appropriate actions
        5. Create/update Plan.md files in the Plans folder to track your work
        6. For each file:
           - If it requires human approval (> $100 payments, sensitive actions, etc.), move to Pending_Approval folder
           - Otherwise, perform the required action and move to Done folder
        7. Update Dashboard.md with outcomes
        8. Continue working until all tasks are processed

        ## Current Iteration:
        This is iteration {iteration} of maximum {self.max_iterations}. Focus on making progress toward completion.

        ## Available Tools:
        - File system tools to read/write files in the vault
        - MCP servers for external actions (email, browser automation, etc.)
        - Skills as defined in the system, especially the needs-action-processor skill

        Work autonomously following the Claude reasoning layer workflow until all tasks are processed.
        """

        return prompt

    def _run_claude_with_prompt(self, prompt: str) -> bool:
        """
        Run Claude Code with the given prompt using ccr code.

        Args:
            prompt: The prompt to send to Claude

        Returns:
            True if Claude executed successfully, False otherwise
        """
        try:
            # Run Claude Code with the prompt using ccr
            result = subprocess.run([
                'ccr', 'code',
                '--cwd', str(self.vault_path),
                '--allowedTools', 'Read,Glob,Grep,Write,Edit,Skill',
                '--disallowedTools', 'Bash(rm:*,sudo:*)',
                '--no-session-persistence',
                '-p', prompt
            ], capture_output=True, text=True, timeout=600)  # 10 minute timeout

            if result.returncode == 0:
                self.logger.info("Claude executed successfully")
                self.logger.debug(f"Output: {result.stdout[:500]}...")  # Log first 500 chars
                return True
            else:
                self.logger.error(f"Claude execution failed: {result.stderr}")
                return False

        except subprocess.TimeoutExpired:
            self.logger.error("Claude execution timed out")
            return False
        except FileNotFoundError:
            self.logger.error("'ccr' command not found. Please ensure Claude Code Router is installed.")
            return False
        except Exception as e:
            self.logger.error(f"Error running Claude: {e}")
            return False

    def _check_completion_condition(self, task_description: str) -> bool:
        """
        Check if the task completion condition is met based on the reasoning layer workflow.

        Args:
            task_description: Description of the task to check

        Returns:
            True if task is complete, False otherwise
        """
        # Check if Needs_Action folder is empty (no more files to process)
        needs_action_dir = self.vault_path / "Needs_Action"
        if needs_action_dir.exists():
            needs_action_files = list(needs_action_dir.glob("*.md"))
            # If there are no more files in Needs_Action to process, consider complete
            if len(needs_action_files) == 0:
                self.logger.info("No more files in Needs_Action folder, considering task complete")
                return True

        # Look for completed tasks in the Done directory
        done_dir = self.vault_path / "Done"
        if done_dir.exists():
            for file_path in done_dir.glob("*.md"):
                try:
                    content = file_path.read_text()
                    # Check if the file contains indicators of completion related to our task
                    if (task_description.lower() in content.lower() and
                        ('completed' in content.lower() or 'done' in content.lower())):
                        return True
                except Exception:
                    continue  # Skip files that can't be read

        # Check Plans directory for completed plan files
        plans_dir = self.vault_path / "Plans"
        if plans_dir.exists():
            for plan_file in plans_dir.glob("*.md"):
                try:
                    content = plan_file.read_text()
                    # Check if all major checkboxes in the plan are completed
                    unchecked_items = content.count('- [ ] ')
                    checked_items = content.count('- [x] ')

                    # If most items are checked (more than 80% of checkable items), consider complete
                    total_checkable = unchecked_items + checked_items
                    if total_checkable > 0 and (checked_items / total_checkable) > 0.8:
                        # Additional check for completion keywords
                        if 'complete' in content.lower() or 'completed' in content.lower():
                            return True
                except Exception:
                    continue  # Skip files that can't be read

        # Check Dashboard for completion indicators
        dashboard_path = self.vault_path / "Dashboard.md"
        if dashboard_path.exists():
            try:
                dashboard_content = dashboard_path.read_text()
                if task_description.lower() in dashboard_content.lower():
                    if 'completed' in dashboard_content.lower() or 'done' in dashboard_content.lower():
                        return True
            except Exception:
                pass  # Dashboard couldn't be read, continue checking other conditions

        return False

    def run_reasoning_loop(self, task_description: str) -> bool:
        """
        Run the Claude reasoning loop that creates Plan.md files.

        Args:
            task_description: Description of the task to complete

        Returns:
            True if task was completed successfully, False otherwise
        """
        self.logger.info(f"Starting Claude reasoning loop for task: {task_description}")

        # Initialize plan_file variable to avoid unbound error
        plan_file = None

        for iteration in range(1, self.max_iterations + 1):
            self.logger.info(f"Starting iteration {iteration}/{self.max_iterations}")

            # Create a plan file for this iteration
            plan_file = self._create_plan_file(task_description, iteration)

            # Create a prompt that tells Claude to work on the task
            prompt = self._create_task_processing_prompt(task_description, iteration, plan_file)

            # Run Claude with the prompt
            success = self._run_claude_with_prompt(prompt)

            if not success:
                self.logger.warning(f"Iteration {iteration} failed, continuing...")

            # Check if the task is complete
            if self._check_completion_condition(task_description):
                self.logger.info(f"Task completed successfully after {iteration} iterations")

                # Final update to the plan file indicating completion
                try:
                    plan_content = plan_file.read_text()
                    updated_content = plan_content + f"\n\n## Task Completed\nTask completed on {datetime.now().isoformat()} after {iteration} iterations.\n"
                    plan_file.write_text(updated_content)
                except Exception as e:
                    self.logger.warning(f"Could not update plan file with completion status: {e}")

                return True

            # Small delay between iterations to prevent overwhelming the system
            time.sleep(10)

        self.logger.warning(f"Max iterations ({self.max_iterations}) reached without completing task")

        # Update the final plan file with status if we have a plan file
        if plan_file is not None:
            try:
                plan_content = plan_file.read_text()
                updated_content = plan_content + f"\n\n## Task Incomplete\nMax iterations ({self.max_iterations}) reached without completing the task.\n"
                plan_file.write_text(updated_content)
            except Exception as e:
                self.logger.warning(f"Could not update plan file with incomplete status: {e}")

        return False


def main():
    """Main function to run the Ralph Wiggum controller from command line."""
    if len(sys.argv) < 3:
        print("Usage: python ralph_wiggum_controller.py <vault_path> <task_description>")
        print("Example: python ralph_wiggum_controller.py ./AI_Employee_Vault \"Process all emails in Needs_Action folder\"")
        sys.exit(1)

    vault_path = sys.argv[1]
    task_description = " ".join(sys.argv[2:])

    # Create and run the Ralph Wiggum controller
    controller = RalphWiggumController(vault_path)
    success = controller.run_reasoning_loop(task_description)

    if success:
        print("Task completed successfully!")
        sys.exit(0)
    else:
        print("Task could not be completed within the iteration limit.")
        sys.exit(1)


if __name__ == "__main__":
    main()
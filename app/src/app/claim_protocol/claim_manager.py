"""
Task claim manager for AI Employee vault with comprehensive logging.

Implements atomic claim-by-move protocol to prevent duplicate work.
"""

import logging
import os
import time
from pathlib import Path
from typing import Dict, Optional
from datetime import datetime, timezone

logger = logging.getLogger("vault_sync.claim_manager")


class ClaimManager:
    """Manages task claiming using atomic file moves with comprehensive logging."""

    def __init__(self, vault_path: str, agent_name: str):
        """
        Initialize ClaimManager.

        Args:
            vault_path: Absolute path to vault directory
            agent_name: Name of the agent (e.g., "cloud-agent", "local-agent")
        """
        self.vault_path = Path(vault_path)
        self.agent_name = agent_name
        self.claim_timeout_minutes = int(os.getenv("CLAIM_TIMEOUT_MINUTES", "30"))

        logger.info(
            f"[INIT] agent={self.agent_name} component=ClaimManager "
            f"vault_path={self.vault_path} claim_timeout_minutes={self.claim_timeout_minutes}"
        )

    def claim_task(self, task_file: Path, domain: str) -> Dict:
        """
        Claim a task by atomically moving it to In_Progress directory.

        Args:
            task_file: Path to task file in Needs_Action
            domain: Domain of the task (e.g., "email", "social")

        Returns:
            Dict with claim result including success status and new path
        """
        start_time = time.time()
        logger.info(
            f"[CLAIM_START] agent={self.agent_name} operation=claim_task "
            f"task={task_file.name} domain={domain}"
        )

        try:
            # Validate task file exists
            if not task_file.exists():
                logger.warning(
                    f"[CLAIM_FAILED] agent={self.agent_name} operation=claim_task "
                    f"task={task_file.name} reason=file_not_found"
                )
                return {
                    "success": False,
                    "error": "Task file does not exist",
                    "task_file": str(task_file)
                }

            # Pre-check: verify file is still in Needs_Action
            if "Needs_Action" not in str(task_file):
                logger.warning(
                    f"[CLAIM_FAILED] agent={self.agent_name} operation=claim_task "
                    f"task={task_file.name} reason=not_in_needs_action"
                )
                return {
                    "success": False,
                    "error": "Task is not in Needs_Action directory",
                    "task_file": str(task_file)
                }

            # Pre-check: verify source file still exists
            if not task_file.exists():
                logger.warning(
                    f"[CLAIM_FAILED] agent={self.agent_name} operation=claim_task "
                    f"task={task_file.name} reason=file_not_found_before_move"
                )
                return {
                    "success": False,
                    "error": "Task file disappeared before claim (already claimed)",
                    "task_file": str(task_file)
                }

            # Determine target directory
            target_dir = self.vault_path / "In_Progress" / self.agent_name
            target_dir.mkdir(parents=True, exist_ok=True)

            # Target file path
            target_file = target_dir / task_file.name

            # Pre-check: ensure task isn't already claimed by ANY agent
            in_progress_dir = self.vault_path / "In_Progress"
            if in_progress_dir.exists():
                for agent_dir in in_progress_dir.iterdir():
                    if agent_dir.is_dir():
                        potential_claim = agent_dir / task_file.name
                        if potential_claim.exists():
                            logger.warning(
                                f"[CLAIM_FAILED] agent={self.agent_name} operation=claim_task "
                                f"task={task_file.name} reason=already_claimed_by_{agent_dir.name}"
                            )
                            return {
                                "success": False,
                                "error": f"Task already claimed by {agent_dir.name}",
                                "task_file": str(task_file)
                            }

            # Atomic move: use os.replace for atomic operation
            try:
                os.replace(str(task_file), str(target_file))
            except (FileNotFoundError, PermissionError, OSError) as e:
                # File was already moved by another agent - race condition
                logger.warning(
                    f"[CLAIM_FAILED] agent={self.agent_name} operation=claim_task "
                    f"task={task_file.name} reason=race_condition error={str(e)}"
                )
                return {
                    "success": False,
                    "error": f"Task was claimed by another agent (race condition): {str(e)}",
                    "task_file": str(task_file)
                }

            # Post-validation: verify the move succeeded and file is at target
            if not target_file.exists():
                logger.error(
                    f"[CLAIM_FAILED] agent={self.agent_name} operation=claim_task "
                    f"task={task_file.name} reason=move_failed_validation"
                )
                return {
                    "success": False,
                    "error": "Move operation failed validation",
                    "task_file": str(task_file)
                }

            # Post-validation: verify no other agent has the same file (race condition check)
            for agent_dir in in_progress_dir.iterdir():
                if agent_dir.is_dir() and agent_dir.name != self.agent_name:
                    other_claim = agent_dir / task_file.name
                    if other_claim.exists():
                        # Race condition detected - another agent also claimed it
                        # Remove our claim and fail
                        try:
                            target_file.unlink()
                        except:
                            pass
                        logger.warning(
                            f"[CLAIM_FAILED] agent={self.agent_name} operation=claim_task "
                            f"task={task_file.name} reason=race_condition_detected_post_move "
                            f"other_agent={agent_dir.name}"
                        )
                        return {
                            "success": False,
                            "error": f"Race condition: {agent_dir.name} also claimed this task",
                            "task_file": str(task_file)
                        }

            # Verify source file is gone (confirming atomic move)
            if task_file.exists():
                # This shouldn't happen with os.replace, but if it does, we have a problem
                # Clean up our target file and fail
                try:
                    target_file.unlink()
                except:
                    pass
                logger.error(
                    f"[CLAIM_FAILED] agent={self.agent_name} operation=claim_task "
                    f"task={task_file.name} reason=source_still_exists_after_move"
                )
                return {
                    "success": False,
                    "error": "Atomic move failed - source file still exists",
                    "task_file": str(task_file)
                }

            # Update task metadata with claim information after successful move
            try:
                updated_content = self._add_claim_metadata(target_file, self.agent_name)
                if updated_content:
                    target_file.write_text(updated_content, encoding='utf-8')
            except Exception as meta_error:
                # Metadata update failed but claim succeeded - log warning
                logger.warning(
                    f"[CLAIM_METADATA_FAILED] agent={self.agent_name} "
                    f"task={task_file.name} error={str(meta_error)}"
                )

            duration_ms = int((time.time() - start_time) * 1000)
            result = {
                "success": True,
                "claimed_by": self.agent_name,
                "claimed_at": datetime.now(timezone.utc).isoformat(),
                "original_path": str(task_file),
                "new_path": str(target_file),
                "domain": domain
            }

            logger.info(
                f"[CLAIM_SUCCESS] agent={self.agent_name} operation=claim_task "
                f"success=True duration_ms={duration_ms} task={task_file.name} "
                f"domain={domain} new_path={target_file}"
            )
            return result

        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            logger.error(
                f"[CLAIM_FAILED] agent={self.agent_name} operation=claim_task "
                f"success=False duration_ms={duration_ms} task={task_file.name} "
                f"error={str(e)}"
            )
            return {
                "success": False,
                "error": str(e),
                "task_file": str(task_file)
            }

    def release_task(self, task_file: Path, domain: str, reason: str = "Released by agent") -> Dict:
        """
        Release a claimed task back to Needs_Action.

        Args:
            task_file: Path to task file in In_Progress
            domain: Domain of the task
            reason: Reason for releasing the task

        Returns:
            Dict with release result
        """
        start_time = time.time()
        logger.info(
            f"[RELEASE_START] agent={self.agent_name} operation=release_task "
            f"task={task_file.name} domain={domain} reason={reason}"
        )

        try:
            # Validate task file exists
            if not task_file.exists():
                logger.warning(
                    f"[RELEASE_FAILED] agent={self.agent_name} operation=release_task "
                    f"task={task_file.name} reason=file_not_found"
                )
                return {
                    "success": False,
                    "error": "Task file does not exist",
                    "task_file": str(task_file)
                }

            # Determine target directory
            target_dir = self.vault_path / "Needs_Action" / domain
            target_dir.mkdir(parents=True, exist_ok=True)

            # Target file path
            target_file = target_dir / task_file.name

            # Remove claim metadata
            updated_content = self._remove_claim_metadata(task_file)
            if not updated_content:
                logger.error(
                    f"[RELEASE_FAILED] agent={self.agent_name} operation=release_task "
                    f"task={task_file.name} reason=metadata_update_failed"
                )
                return {
                    "success": False,
                    "error": "Failed to update task metadata",
                    "task_file": str(task_file)
                }

            # Write updated content to a temporary file first for atomicity
            temp_file = target_file.with_suffix(f"{target_file.suffix}.tmp")
            temp_file.write_text(updated_content, encoding='utf-8')

            # Atomically move the temporary file to the final destination
            os.replace(temp_file, target_file)

            # Now that the new file is safely in place, remove the original
            task_file.unlink()

            duration_ms = int((time.time() - start_time) * 1000)
            result = {
                "success": True,
                "released_by": self.agent_name,
                "released_at": datetime.now(timezone.utc).isoformat(),
                "original_path": str(task_file),
                "new_path": str(target_file),
                "reason": reason
            }

            logger.info(
                f"[RELEASE_SUCCESS] agent={self.agent_name} operation=release_task "
                f"success=True duration_ms={duration_ms} task={task_file.name} "
                f"domain={domain} reason={reason}"
            )
            return result

        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            logger.error(
                f"[RELEASE_FAILED] agent={self.agent_name} operation=release_task "
                f"success=False duration_ms={duration_ms} task={task_file.name} "
                f"error={str(e)}"
            )
            return {
                "success": False,
                "error": str(e),
                "task_file": str(task_file)
            }

    def complete_task(self, task_file: Path, domain: str) -> Dict:
        """
        Mark a task as complete by moving it to Done directory.

        Args:
            task_file: Path to task file in In_Progress
            domain: Domain of the task

        Returns:
            Dict with completion result
        """
        start_time = time.time()
        logger.info(
            f"[COMPLETE_START] agent={self.agent_name} operation=complete_task "
            f"task={task_file.name} domain={domain}"
        )

        try:
            # Validate task file exists
            if not task_file.exists():
                logger.warning(
                    f"[COMPLETE_FAILED] agent={self.agent_name} operation=complete_task "
                    f"task={task_file.name} reason=file_not_found"
                )
                return {
                    "success": False,
                    "error": "Task file does not exist",
                    "task_file": str(task_file)
                }

            # Determine target directory
            target_dir = self.vault_path / "Done" / domain
            target_dir.mkdir(parents=True, exist_ok=True)

            # Target file path
            target_file = target_dir / task_file.name

            # Update task metadata with completion information
            updated_content = self._add_completion_metadata(task_file, self.agent_name)
            if not updated_content:
                logger.error(
                    f"[COMPLETE_FAILED] agent={self.agent_name} operation=complete_task "
                    f"task={task_file.name} reason=metadata_update_failed"
                )
                return {
                    "success": False,
                    "error": "Failed to update task metadata",
                    "task_file": str(task_file)
                }

            # Write updated content to a temporary file first for atomicity
            temp_file = target_file.with_suffix(f"{target_file.suffix}.tmp")
            temp_file.write_text(updated_content, encoding='utf-8')

            # Atomically move the temporary file to the final destination
            os.replace(temp_file, target_file)

            # Now that the new file is safely in place, remove the original
            task_file.unlink()

            duration_ms = int((time.time() - start_time) * 1000)
            result = {
                "success": True,
                "completed_by": self.agent_name,
                "completed_at": datetime.now(timezone.utc).isoformat(),
                "original_path": str(task_file),
                "new_path": str(target_file),
                "domain": domain
            }

            logger.info(
                f"[COMPLETE_SUCCESS] agent={self.agent_name} operation=complete_task "
                f"success=True duration_ms={duration_ms} task={task_file.name} "
                f"domain={domain}"
            )
            return result

        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            logger.error(
                f"[COMPLETE_FAILED] agent={self.agent_name} operation=complete_task "
                f"success=False duration_ms={duration_ms} task={task_file.name} "
                f"error={str(e)}"
            )
            return {
                "success": False,
                "error": str(e),
                "task_file": str(task_file)
            }

    def _add_claim_metadata(self, task_file: Path, agent_name: str) -> Optional[str]:
        """Add claim metadata to task file frontmatter."""
        try:
            content = task_file.read_text(encoding='utf-8')

            # Parse frontmatter
            if content.startswith('---'):
                parts = content.split('---', 2)
                if len(parts) >= 3:
                    frontmatter = parts[1]
                    body = parts[2]

                    # Add claim fields
                    claim_time = datetime.now(timezone.utc).isoformat()
                    updated_frontmatter = frontmatter.rstrip() + f"\nclaimed_by: {agent_name}\nclaimed_at: {claim_time}\nstatus: in_progress\n"

                    return f"---{updated_frontmatter}---{body}"

            return None

        except Exception as e:
            logger.error(f"Error adding claim metadata: {e}")
            return None

    def _remove_claim_metadata(self, task_file: Path) -> Optional[str]:
        """Remove claim metadata from task file frontmatter."""
        try:
            content = task_file.read_text(encoding='utf-8')

            # Parse frontmatter
            if content.startswith('---'):
                parts = content.split('---', 2)
                if len(parts) >= 3:
                    frontmatter = parts[1]
                    body = parts[2]

                    # Remove claim fields and reset status
                    lines = frontmatter.split('\n')
                    updated_lines = []
                    for line in lines:
                        if not line.startswith('claimed_by:') and not line.startswith('claimed_at:'):
                            if line.startswith('status:'):
                                updated_lines.append('status: pending')
                            else:
                                updated_lines.append(line)

                    updated_frontmatter = '\n'.join(updated_lines)
                    return f"---{updated_frontmatter}---{body}"

            return None

        except Exception as e:
            logger.error(f"Error removing claim metadata: {e}")
            return None

    def _add_completion_metadata(self, task_file: Path, agent_name: str) -> Optional[str]:
        """Add completion metadata to task file frontmatter."""
        try:
            content = task_file.read_text(encoding='utf-8')

            # Parse frontmatter
            if content.startswith('---'):
                parts = content.split('---', 2)
                if len(parts) >= 3:
                    frontmatter = parts[1]
                    body = parts[2]

                    # Update status to completed
                    lines = frontmatter.split('\n')
                    updated_lines = []
                    for line in lines:
                        if line.startswith('status:'):
                            updated_lines.append('status: completed')
                        else:
                            updated_lines.append(line)

                    # Add completion timestamp
                    completion_time = datetime.now(timezone.utc).isoformat()
                    updated_lines.append(f"completed_at: {completion_time}")

                    updated_frontmatter = '\n'.join(updated_lines)
                    return f"---{updated_frontmatter}---{body}"

            return None

        except Exception as e:
            logger.error(f"Error adding completion metadata: {e}")
            return None

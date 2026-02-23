"""
Recovery handler for stalled tasks.

Handles recovery of tasks that have been stalled or abandoned.
"""

import logging
import time
from pathlib import Path
from typing import Dict, Optional

logger = logging.getLogger("vault_sync.recovery_handler")


class RecoveryHandler:
    """Handles recovery of stalled tasks."""

    def __init__(self, vault_path: str):
        """
        Initialize RecoveryHandler.

        Args:
            vault_path: Absolute path to vault directory
        """
        self.vault_path = Path(vault_path)

    def recover_stalled_task(self, task_info: Dict) -> Dict:
        """
        Recover a stalled task by moving it back to Needs_Action.

        Args:
            task_info: Information about the stalled task

        Returns:
            Dict with recovery result
        """
        task_file_path = task_info.get("task_file")
        if not task_file_path:
            logger.error(
                f"[RECOVERY_FAILED] operation=recover_stalled_task "
                f"reason=no_task_file_path"
            )
            return {
                "success": False,
                "error": "No task file path provided"
            }

        task_file = Path(task_file_path)
        start_time = time.time()
        logger.info(
            f"[RECOVERY_START] operation=recover_stalled_task "
            f"task={task_file.name} claimed_by={task_info.get('claimed_by', 'unknown')}"
        )

        try:
            # Validate task file exists
            if not task_file.exists():
                return {
                    "success": False,
                    "error": "Task file does not exist",
                    "task_file": str(task_file)
                }

            # Get domain from task info
            domain = task_info.get("domain")
            if not domain:
                logger.warning(f"No domain found for task {task_file.name}, using 'email' as default")
                domain = "email"

            # Determine target directory
            target_dir = self.vault_path / "Needs_Action" / domain
            target_dir.mkdir(parents=True, exist_ok=True)

            # Target file path
            target_file = target_dir / task_file.name

            # Remove claim metadata
            updated_content = self._remove_claim_metadata(task_file)
            if not updated_content:
                return {
                    "success": False,
                    "error": "Failed to update task metadata",
                    "task_file": str(task_file)
                }

            # Write updated content to target location
            target_file.write_text(updated_content, encoding='utf-8')

            # Remove original file
            task_file.unlink()

            duration_ms = int((time.time() - start_time) * 1000)
            result = {
                "success": True,
                "recovered_task": task_file.name,
                "original_path": str(task_file),
                "new_path": str(target_file),
                "domain": domain,
                "previously_claimed_by": task_info.get("claimed_by")
            }

            logger.info(
                f"[RECOVERY_SUCCESS] operation=recover_stalled_task "
                f"success=True duration_ms={duration_ms} task={task_file.name} "
                f"domain={domain} previously_claimed_by={task_info.get('claimed_by', 'unknown')}"
            )
            return result

        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            logger.error(
                f"[RECOVERY_FAILED] operation=recover_stalled_task "
                f"success=False duration_ms={duration_ms} task={task_file.name} "
                f"error={str(e)}"
            )
            return {
                "success": False,
                "error": str(e),
                "task_file": str(task_file)
            }

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

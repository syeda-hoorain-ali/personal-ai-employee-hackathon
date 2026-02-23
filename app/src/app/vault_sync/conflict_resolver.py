"""
Conflict resolution strategies for Git merge conflicts.

Handles merge conflicts during vault synchronization.
"""

import logging
import time
from pathlib import Path
from typing import Dict, List, Optional
import git

logger = logging.getLogger("vault_sync.conflict_resolver")


class ConflictResolver:
    """Resolves Git merge conflicts using predefined strategies."""

    def __init__(self, vault_path: str):
        """
        Initialize ConflictResolver.

        Args:
            vault_path: Absolute path to vault directory
        """
        self.vault_path = Path(vault_path)
        self.repo = git.Repo(vault_path)

    def resolve_conflict(
        self,
        file_path: str,
        strategy: str = "local_wins"
    ) -> Dict:
        """
        Resolve merge conflict for a specific file.

        Args:
            file_path: Path to conflicted file (relative to vault root)
            strategy: Resolution strategy - "local_wins", "remote_wins", or "manual"

        Returns:
            Dict with resolution result

        Raises:
            ValueError: If strategy is invalid or file not in conflict
        """
        start_time = time.time()
        logger.info(
            f"[CONFLICT_RESOLVE_START] operation=resolve_conflict "
            f"file={file_path} strategy={strategy}"
        )

        full_path = self.vault_path / file_path

        if not full_path.exists():
            raise ValueError(f"File not found: {file_path}")

        # Check if file is actually in conflict
        if not self._is_conflicted(file_path):
            logger.warning(f"File {file_path} is not in conflict")
            return {
                "success": True,
                "file": file_path,
                "strategy": strategy,
                "message": "No conflict detected"
            }

        try:
            if strategy == "local_wins":
                self._resolve_local_wins(file_path)
            elif strategy == "remote_wins":
                self._resolve_remote_wins(file_path)
            elif strategy == "manual":
                return {
                    "success": False,
                    "file": file_path,
                    "strategy": strategy,
                    "message": "Manual resolution required",
                    "requires_user_action": True
                }
            else:
                raise ValueError(f"Invalid strategy: {strategy}")

            # Mark as resolved
            self.repo.index.add([file_path])

            duration_ms = int((time.time() - start_time) * 1000)
            result = {
                "success": True,
                "file": file_path,
                "strategy": strategy,
                "message": f"Conflict resolved using {strategy}"
            }

            logger.info(
                f"[CONFLICT_RESOLVE_SUCCESS] operation=resolve_conflict "
                f"success=True duration_ms={duration_ms} file={file_path} "
                f"strategy={strategy}"
            )
            return result

        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            logger.error(
                f"[CONFLICT_RESOLVE_FAILED] operation=resolve_conflict "
                f"success=False duration_ms={duration_ms} file={file_path} "
                f"error={str(e)}"
            )
            raise

    def get_conflicts(self) -> List[Dict]:
        """
        Get list of all conflicted files.

        Returns:
            List of dicts with conflict information
        """
        start_time = time.time()
        conflicts = []

        try:
            # Get unmerged paths (files in conflict)
            unmerged = self.repo.index.unmerged_blobs()

            for file_path in unmerged.keys():
                conflict_type = self._detect_conflict_type(file_path)
                conflicts.append({
                    "file": file_path,
                    "conflict_type": conflict_type,
                    "resolution_strategy": self._suggest_strategy(file_path, conflict_type)
                })

            duration_ms = int((time.time() - start_time) * 1000)
            logger.info(
                f"[CONFLICTS_DETECTED] operation=get_conflicts "
                f"duration_ms={duration_ms} conflicts_found={len(conflicts)}"
            )
            return conflicts

        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            logger.error(
                f"[CONFLICTS_CHECK_FAILED] operation=get_conflicts "
                f"duration_ms={duration_ms} error={str(e)}"
            )
            return []

    def _is_conflicted(self, file_path: str) -> bool:
        """Check if file is in conflict state."""
        try:
            unmerged = self.repo.index.unmerged_blobs()
            return file_path in unmerged
        except Exception:
            return False

    def _resolve_local_wins(self, file_path: str) -> None:
        """Resolve conflict by keeping local version."""
        logger.info(f"Resolving {file_path} with local version")
        self.repo.git.checkout("--ours", file_path)

    def _resolve_remote_wins(self, file_path: str) -> None:
        """Resolve conflict by keeping remote version."""
        logger.info(f"Resolving {file_path} with remote version")
        self.repo.git.checkout("--theirs", file_path)

    def _detect_conflict_type(self, file_path: str) -> str:
        """
        Detect type of conflict.

        Returns:
            "content", "delete", or "rename"
        """
        # Simple heuristic: check if file exists
        full_path = self.vault_path / file_path
        if not full_path.exists():
            return "delete"

        # Check for rename conflicts (would need more sophisticated detection)
        # For now, assume content conflict
        return "content"

    def _suggest_strategy(self, file_path: str, conflict_type: str) -> str:
        """
        Suggest resolution strategy based on file and conflict type.

        Args:
            file_path: Path to conflicted file
            conflict_type: Type of conflict

        Returns:
            Suggested strategy: "local_wins", "remote_wins", or "manual"
        """
        # Dashboard.md: local wins (local agent is single writer)
        if "Dashboard.md" in file_path:
            return "local_wins"

        # Task files in In_Progress: local wins (agent owns claimed tasks)
        if "In_Progress" in file_path:
            return "local_wins"

        # Updates directory: remote wins (cloud agent writes here)
        if "Updates" in file_path:
            return "remote_wins"

        # Default: manual resolution for safety
        return "manual"

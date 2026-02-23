"""
Claim validator for AI Employee vault.

Validates task claims and checks claim ownership.
"""

import logging
import yaml
from pathlib import Path
from typing import Dict, Optional
from datetime import datetime, timezone, timedelta

logger = logging.getLogger("vault_sync.claim_validator")


class ClaimValidator:
    """Validates task claims and ownership."""

    def __init__(self, vault_path: str, claim_timeout_minutes: int = 30):
        """
        Initialize ClaimValidator.

        Args:
            vault_path: Absolute path to vault directory
            claim_timeout_minutes: Time in minutes before a claim is considered stale
        """
        self.vault_path = Path(vault_path)
        self.claim_timeout_minutes = claim_timeout_minutes

    def validate_claim(self, task_file: Path, agent_name: str) -> Dict:
        """
        Validate that an agent owns a specific task claim.

        Args:
            task_file: Path to task file
            agent_name: Name of agent to validate

        Returns:
            Dict with validation result
        """
        logger.debug(f"Validating claim for {task_file.name} by {agent_name}")

        try:
            if not task_file.exists():
                return {
                    "is_valid": False,
                    "error": "Task file does not exist"
                }

            # Parse task metadata
            metadata = self._parse_task_metadata(task_file)
            if not metadata:
                return {
                    "is_valid": False,
                    "error": "Could not parse task metadata"
                }

            # Check if task is claimed
            claimed_by = metadata.get("claimed_by")
            if not claimed_by:
                return {
                    "is_valid": False,
                    "error": "Task is not claimed",
                    "claimed_by": None
                }

            # Check if claimed by this agent
            if claimed_by != agent_name:
                return {
                    "is_valid": False,
                    "error": f"Task is claimed by different agent: {claimed_by}",
                    "claimed_by": claimed_by
                }

            # Check if claim is stale
            claimed_at = metadata.get("claimed_at")
            if claimed_at:
                is_stale = self._is_claim_stale(claimed_at)
                if is_stale:
                    return {
                        "is_valid": False,
                        "error": "Claim has expired (stale)",
                        "claimed_by": claimed_by,
                        "claimed_at": claimed_at,
                        "is_stale": True
                    }

            return {
                "is_valid": True,
                "claimed_by": claimed_by,
                "claimed_at": claimed_at
            }

        except Exception as e:
            logger.error(f"Error validating claim: {e}")
            return {
                "is_valid": False,
                "error": str(e)
            }

    def is_claimed(self, task_file: Path) -> bool:
        """
        Check if a task is currently claimed.

        Args:
            task_file: Path to task file

        Returns:
            True if task is claimed, False otherwise
        """
        try:
            metadata = self._parse_task_metadata(task_file)
            if not metadata:
                return False

            claimed_by = metadata.get("claimed_by")
            return claimed_by is not None

        except Exception as e:
            logger.error(f"Error checking claim status: {e}")
            return False

    def get_claim_info(self, task_file: Path) -> Optional[Dict]:
        """
        Get claim information for a task.

        Args:
            task_file: Path to task file

        Returns:
            Dict with claim info or None if not claimed
        """
        try:
            metadata = self._parse_task_metadata(task_file)
            if not metadata:
                return None

            claimed_by = metadata.get("claimed_by")
            if not claimed_by:
                return None

            claimed_at = metadata.get("claimed_at")
            is_stale = self._is_claim_stale(claimed_at) if claimed_at else False

            return {
                "claimed_by": claimed_by,
                "claimed_at": claimed_at,
                "is_stale": is_stale,
                "status": metadata.get("status"),
                "domain": metadata.get("domain")
            }

        except Exception as e:
            logger.error(f"Error getting claim info: {e}")
            return None

    def _parse_task_metadata(self, task_file: Path) -> Optional[Dict]:
        """Parse task file frontmatter."""
        try:
            content = task_file.read_text(encoding='utf-8')

            if content.startswith('---'):
                parts = content.split('---', 2)
                if len(parts) >= 3:
                    frontmatter_text = parts[1]
                    metadata = yaml.safe_load(frontmatter_text)
                    return metadata if isinstance(metadata, dict) else None
            return None
        except (yaml.YAMLError, Exception) as e:
            logger.error(f"Error parsing task metadata for {task_file.name}: {e}")
            return None

    def _is_claim_stale(self, claimed_at: str) -> bool:
        """Check if a claim is stale based on timeout."""
        try:
            claimed_time = datetime.fromisoformat(claimed_at.replace('Z', '+00:00'))
            current_time = datetime.now(timezone.utc)
            time_elapsed = current_time - claimed_time

            return time_elapsed > timedelta(minutes=self.claim_timeout_minutes)

        except Exception as e:
            logger.error(f"Error checking claim staleness: {e}")
            return False

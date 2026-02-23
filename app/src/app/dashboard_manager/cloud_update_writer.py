"""
Cloud update writer for AI Employee vault.

Allows cloud agent to write status updates without directly modifying Dashboard.md.
"""

import logging
import time
from pathlib import Path
from typing import Dict, Optional
from datetime import datetime, timezone

logger = logging.getLogger("vault_sync.cloud_update_writer")


class CloudUpdateWriter:
    """Writes status updates for cloud agent to Updates directory."""

    def __init__(self, vault_path: str, agent_name: str = "cloud-agent"):
        """
        Initialize CloudUpdateWriter.

        Args:
            vault_path: Absolute path to vault directory
            agent_name: Name of the agent writing updates
        """
        self.vault_path = Path(vault_path)
        self.agent_name = agent_name
        self.updates_dir = self.vault_path / "Updates"
        self.updates_dir.mkdir(parents=True, exist_ok=True)

    def write_status_update(
        self,
        message: str,
        update_type: str = "status",
        priority: str = "medium",
        related_task: Optional[str] = None
    ) -> Dict:
        """
        Write a status update to Updates directory.

        Args:
            message: Status update message
            update_type: Type of update (status, completion, error, info)
            priority: Priority level (high, medium, low)
            related_task: Optional task ID this update relates to

        Returns:
            Dict with write result including file path
        """
        start_time = time.time()
        logger.info(
            f"[UPDATE_WRITE_START] agent={self.agent_name} operation=write_status_update "
            f"update_type={update_type} priority={priority}"
        )

        try:
            # Generate timestamp-based filename with microseconds for uniqueness
            timestamp = datetime.now(timezone.utc)
            filename = f"cloud-status-{timestamp.strftime('%Y%m%d-%H%M%S-%f')}.md"
            file_path = self.updates_dir / filename

            # Create YAML frontmatter
            frontmatter = self._create_frontmatter(
                timestamp=timestamp.isoformat(),
                agent=self.agent_name,
                update_type=update_type,
                priority=priority,
                related_task=related_task
            )

            # Create full content
            content = f"{frontmatter}\n\n{message}\n"

            # Write to file
            file_path.write_text(content, encoding='utf-8')

            duration_ms = int((time.time() - start_time) * 1000)
            result = {
                "success": True,
                "file_path": str(file_path),
                "filename": filename,
                "timestamp": timestamp.isoformat()
            }

            logger.info(
                f"[UPDATE_WRITE_SUCCESS] agent={self.agent_name} operation=write_status_update "
                f"success=True duration_ms={duration_ms} filename={filename} "
                f"update_type={update_type} priority={priority}"
            )
            return result

        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            logger.error(
                f"[UPDATE_WRITE_FAILED] agent={self.agent_name} operation=write_status_update "
                f"success=False duration_ms={duration_ms} error={str(e)}"
            )
            return {
                "success": False,
                "error": str(e)
            }

    def _create_frontmatter(
        self,
        timestamp: str,
        agent: str,
        update_type: str,
        priority: str,
        related_task: Optional[str]
    ) -> str:
        """Create YAML frontmatter for update file."""
        frontmatter_lines = [
            "---",
            f"timestamp: {timestamp}",
            f"agent: {agent}",
            f"type: {update_type}",
            f"priority: {priority}"
        ]

        if related_task:
            frontmatter_lines.append(f"related_task: {related_task}")

        frontmatter_lines.append("---")

        return "\n".join(frontmatter_lines)

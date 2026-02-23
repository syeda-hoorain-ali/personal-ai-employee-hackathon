"""
Update merger for AI Employee vault.

Merges cloud agent updates into Dashboard.md (local agent only).
"""

import logging
import time
import yaml
from pathlib import Path
from typing import Dict, List
from datetime import datetime, timezone

logger = logging.getLogger("vault_sync.update_merger")


class UpdateMerger:
    """Merges updates from Updates directory into Dashboard.md."""

    def __init__(self, vault_path: str):
        """
        Initialize UpdateMerger.

        Args:
            vault_path: Absolute path to vault directory
        """
        self.vault_path = Path(vault_path)
        self.updates_dir = self.vault_path / "Updates"
        self.archive_dir = self.updates_dir / "archive"
        self.dashboard_path = self.vault_path / "Dashboard.md"

        # Ensure directories exist
        self.updates_dir.mkdir(parents=True, exist_ok=True)
        self.archive_dir.mkdir(parents=True, exist_ok=True)

    def merge_updates_to_dashboard(self) -> Dict:
        """
        Merge all pending updates into Dashboard.md.

        Returns:
            Dict with merge results
        """
        start_time = time.time()
        logger.info(
            f"[MERGE_START] operation=merge_updates_to_dashboard "
            f"dashboard_path={self.dashboard_path}"
        )

        try:
            # Get all update files
            update_files = sorted(self.updates_dir.glob("cloud-status-*.md"))

            if not update_files:
                duration_ms = int((time.time() - start_time) * 1000)
                logger.info(
                    f"[MERGE_COMPLETE] operation=merge_updates_to_dashboard "
                    f"duration_ms={duration_ms} updates_merged=0"
                )
                return {
                    "success": True,
                    "updates_merged": 0,
                    "message": "No updates to merge"
                }

            # Parse all updates
            updates = []
            for update_file in update_files:
                update_data = self._parse_update_file(update_file)
                if update_data:
                    updates.append(update_data)

            # Read current Dashboard.md
            dashboard_content = self._read_dashboard()

            # Append updates to dashboard
            updated_dashboard = self._append_updates_to_dashboard(dashboard_content, updates)

            # Write updated dashboard
            self.dashboard_path.write_text(updated_dashboard, encoding='utf-8')

            # Archive processed updates
            archived_count = self._archive_updates(update_files)

            duration_ms = int((time.time() - start_time) * 1000)
            result = {
                "success": True,
                "updates_merged": len(updates),
                "updates_archived": archived_count,
                "dashboard_path": str(self.dashboard_path)
            }

            logger.info(
                f"[MERGE_COMPLETE] operation=merge_updates_to_dashboard "
                f"success=True duration_ms={duration_ms} updates_merged={len(updates)} "
                f"updates_archived={archived_count}"
            )
            return result

        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            logger.error(
                f"[MERGE_FAILED] operation=merge_updates_to_dashboard "
                f"success=False duration_ms={duration_ms} error={str(e)}"
            )
            return {
                "success": False,
                "error": str(e)
            }

    def _parse_update_file(self, update_file: Path) -> Dict:
        """Parse an update file and extract metadata and content."""
        try:
            content = update_file.read_text(encoding='utf-8')

            # Parse frontmatter
            if content.startswith('---'):
                parts = content.split('---', 2)
                if len(parts) >= 3:
                    frontmatter_text = parts[1].strip()
                    body = parts[2].strip()

                    metadata = yaml.safe_load(frontmatter_text)

                    return {
                        "filename": update_file.name,
                        "metadata": metadata,
                        "content": body,
                        "file_path": update_file
                    }

            return None

        except Exception as e:
            logger.error(f"Error parsing update file {update_file.name}: {e}")
            return None

    def _read_dashboard(self) -> str:
        """Read current Dashboard.md content."""
        if self.dashboard_path.exists():
            return self.dashboard_path.read_text(encoding='utf-8')
        else:
            # Create default dashboard if it doesn't exist
            return "# Dashboard\n\n## Recent Updates\n\n"

    def _append_updates_to_dashboard(self, dashboard_content: str, updates: List[Dict]) -> str:
        """Append updates to dashboard content."""
        # Find or create "Recent Updates" section
        if "## Recent Updates" not in dashboard_content:
            dashboard_content += "\n## Recent Updates\n\n"

        # Format updates
        update_entries = []
        for update in updates:
            metadata = update["metadata"]
            content = update["content"]

            timestamp = metadata.get("timestamp", "Unknown")
            agent = metadata.get("agent", "Unknown")
            update_type = metadata.get("type", "status")
            priority = metadata.get("priority", "medium")

            # Format timestamp for display
            try:
                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                display_time = dt.strftime("%Y-%m-%d %H:%M UTC")
            except:
                display_time = timestamp

            # Create update entry
            priority_emoji = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(priority, "⚪")
            entry = f"### {priority_emoji} {update_type.title()} - {display_time}\n"
            entry += f"**Agent**: {agent}\n\n"
            entry += f"{content}\n\n"

            update_entries.append(entry)

        # Insert updates after "## Recent Updates" header
        insert_position = dashboard_content.find("## Recent Updates") + len("## Recent Updates\n\n")
        updated_content = (
            dashboard_content[:insert_position] +
            "".join(update_entries) +
            dashboard_content[insert_position:]
        )

        return updated_content

    def _archive_updates(self, update_files: List[Path]) -> int:
        """Move processed updates to archive directory."""
        archived_count = 0

        for update_file in update_files:
            try:
                archive_path = self.archive_dir / update_file.name
                update_file.rename(archive_path)
                archived_count += 1
            except Exception as e:
                logger.error(f"Failed to archive {update_file.name}: {e}")

        return archived_count

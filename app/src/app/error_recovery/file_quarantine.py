"""
File quarantine system for handling corrupted or problematic files.

This module provides the FileQuarantine class for moving corrupted files
to quarantine, tracking metadata, and providing management capabilities.
"""

import shutil
from datetime import datetime, UTC
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import asdict

from .entities import QuarantinedFile, ErrorType
from .exceptions import QuarantineError
from .error_logger import ErrorLogger
from .utils import read_json_file, write_json_file, ensure_directory, sanitize_sensitive_data


class FileQuarantine:
    """
    File quarantine system for handling corrupted or problematic files.

    Features:
    - Move files to quarantine with metadata
    - Track quarantine reason and timestamp
    - Provide quarantine management (list, restore, delete)
    - Integration with error logging
    """

    def __init__(
        self,
        quarantine_dir: Path,
        error_logger: Optional[ErrorLogger] = None
    ):
        """
        Initialize file quarantine.

        Args:
            quarantine_dir: Directory for quarantined files
            error_logger: Optional ErrorLogger instance
        """
        self.quarantine_dir = Path(quarantine_dir)
        self.error_logger = error_logger

        # Ensure quarantine directory exists
        ensure_directory(self.quarantine_dir)
        ensure_directory(self.quarantine_dir / "metadata")

        # In-memory index
        self.quarantined_files: Dict[str, QuarantinedFile] = {}
        self._load_index()

    def quarantine_file(
        self,
        file_path: Path,
        reason: str,
        error_type: ErrorType = ErrorType.DATA,
        component: str = "Unknown",
        additional_metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Move a file to quarantine.

        Args:
            file_path: Path to file to quarantine
            reason: Reason for quarantine
            error_type: Type of error that caused quarantine
            component: Component that quarantined the file
            additional_metadata: Optional additional metadata

        Returns:
            Quarantine ID

        Raises:
            QuarantineError: If file cannot be quarantined
        """
        file_path = Path(file_path)

        # Check if file exists
        if not file_path.exists():
            raise QuarantineError(f"File not found: {file_path}")

        # Generate quarantine ID
        quarantine_id = f"{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}_{file_path.name}"

        # Create quarantined file record
        quarantined_file = QuarantinedFile(
            id=quarantine_id,
            original_path=str(file_path.absolute()),
            quarantine_path=str(self.quarantine_dir / quarantine_id),
            quarantined_at=datetime.now(UTC).isoformat().replace('+00:00', 'Z'),
            reason=reason,
            error_type=error_type,
            component=component,
            file_size_bytes=file_path.stat().st_size,
            file_hash=self._calculate_file_hash(file_path),
            metadata=additional_metadata or {}
        )

        try:
            # Move file to quarantine
            shutil.move(str(file_path), quarantined_file.quarantine_path)

            # Save metadata
            self._save_metadata(quarantined_file)

            # Add to index
            self.quarantined_files[quarantine_id] = quarantined_file

            # Log
            if self.error_logger:
                self.error_logger.log_error(
                    component=component,
                    error_type=error_type,
                    message=f"File quarantined: {reason}",
                    context={
                        "quarantine_id": quarantine_id,
                        "original_path": str(file_path),
                        "file_size": quarantined_file.file_size_bytes,
                        "reason": sanitize_sensitive_data(reason)
                    }
                )

            return quarantine_id

        except Exception as e:
            raise QuarantineError(f"Failed to quarantine file: {e}") from e

    def restore_file(
        self,
        quarantine_id: str,
        restore_path: Optional[Path] = None
    ) -> Path:
        """
        Restore a quarantined file.

        Args:
            quarantine_id: Quarantine ID
            restore_path: Optional custom restore path (defaults to original path)

        Returns:
            Path where file was restored

        Raises:
            QuarantineError: If file cannot be restored
        """
        if quarantine_id not in self.quarantined_files:
            raise QuarantineError(f"Quarantined file not found: {quarantine_id}")

        quarantined_file = self.quarantined_files[quarantine_id]

        # Determine restore path
        if restore_path is None:
            restore_path = Path(quarantined_file.original_path)
        else:
            restore_path = Path(restore_path)

        # Check if restore path already exists
        if restore_path.exists():
            raise QuarantineError(f"Restore path already exists: {restore_path}")

        try:
            # Ensure parent directory exists
            ensure_directory(restore_path.parent)

            # Move file back
            shutil.move(quarantined_file.quarantine_path, str(restore_path))

            # Update record
            quarantined_file.restored_at = datetime.now(UTC).isoformat().replace('+00:00', 'Z')
            quarantined_file.restored_to = str(restore_path.absolute())

            # Save updated metadata
            self._save_metadata(quarantined_file)

            # Remove from active index
            del self.quarantined_files[quarantine_id]

            # Log
            if self.error_logger:
                self.error_logger.log_error(
                    component=quarantined_file.component,
                    error_type=ErrorType.SYSTEM,
                    message=f"File restored from quarantine",
                    context={
                        "quarantine_id": quarantine_id,
                        "restored_to": str(restore_path)
                    }
                )

            return restore_path

        except Exception as e:
            raise QuarantineError(f"Failed to restore file: {e}") from e

    def delete_quarantined_file(self, quarantine_id: str) -> bool:
        """
        Permanently delete a quarantined file.

        Args:
            quarantine_id: Quarantine ID

        Returns:
            True if deleted, False if not found

        Raises:
            QuarantineError: If file cannot be deleted
        """
        if quarantine_id not in self.quarantined_files:
            return False

        quarantined_file = self.quarantined_files[quarantine_id]

        try:
            # Delete file
            quarantine_path = Path(quarantined_file.quarantine_path)
            if quarantine_path.exists():
                quarantine_path.unlink()

            # Delete metadata
            metadata_path = self.quarantine_dir / "metadata" / f"{quarantine_id}.json"
            if metadata_path.exists():
                metadata_path.unlink()

            # Remove from index
            del self.quarantined_files[quarantine_id]

            # Log
            if self.error_logger:
                self.error_logger.log_error(
                    component=quarantined_file.component,
                    error_type=ErrorType.SYSTEM,
                    message=f"Quarantined file permanently deleted",
                    context={
                        "quarantine_id": quarantine_id,
                        "original_path": quarantined_file.original_path
                    }
                )

            return True

        except Exception as e:
            raise QuarantineError(f"Failed to delete quarantined file: {e}") from e

    def list_quarantined_files(
        self,
        component: Optional[str] = None,
        error_type: Optional[ErrorType] = None
    ) -> List[QuarantinedFile]:
        """
        List quarantined files with optional filters.

        Args:
            component: Optional component filter
            error_type: Optional error type filter

        Returns:
            List of quarantined files
        """
        files = list(self.quarantined_files.values())

        # Apply filters
        if component:
            files = [f for f in files if f.component == component]

        if error_type:
            files = [f for f in files if f.error_type == error_type]

        # Sort by quarantine time (newest first)
        files.sort(key=lambda f: f.quarantined_at, reverse=True)

        return files

    def get_quarantined_file(self, quarantine_id: str) -> Optional[QuarantinedFile]:
        """
        Get quarantined file by ID.

        Args:
            quarantine_id: Quarantine ID

        Returns:
            QuarantinedFile or None if not found
        """
        return self.quarantined_files.get(quarantine_id)

    def get_quarantine_stats(self) -> Dict[str, Any]:
        """
        Get quarantine statistics.

        Returns:
            Dictionary with statistics
        """
        files = list(self.quarantined_files.values())

        # Count by component
        by_component = {}
        for f in files:
            by_component[f.component] = by_component.get(f.component, 0) + 1

        # Count by error type
        by_error_type = {}
        for f in files:
            error_type_str = f.error_type.value.lower() if hasattr(f.error_type, 'value') else str(f.error_type).lower()
            by_error_type[error_type_str] = by_error_type.get(error_type_str, 0) + 1

        # Calculate total size
        total_size = sum(f.file_size_bytes for f in files)

        return {
            "total_files": len(files),
            "by_component": by_component,
            "by_error_type": by_error_type,
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2)
        }

    def _calculate_file_hash(self, file_path: Path) -> str:
        """Calculate SHA-256 hash of file."""
        import hashlib

        sha256_hash = hashlib.sha256()

        try:
            with open(file_path, "rb") as f:
                # Read in chunks to handle large files
                for byte_block in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(byte_block)

            return sha256_hash.hexdigest()
        except Exception:
            return "unknown"

    def _load_index(self):
        """Load quarantine index from metadata files."""
        metadata_dir = self.quarantine_dir / "metadata"

        if not metadata_dir.exists():
            return

        for metadata_file in metadata_dir.glob("*.json"):
            try:
                data = read_json_file(metadata_file)
                quarantined_file = QuarantinedFile.from_dict(data)

                # Only load if not restored
                if quarantined_file.restored_at is None:
                    self.quarantined_files[quarantined_file.id] = quarantined_file

            except Exception as e:
                if self.error_logger:
                    self.error_logger.log_error(
                        component="FileQuarantine",
                        error_type=ErrorType.DATA,
                        message=f"Failed to load quarantine metadata",
                        error=e,
                        context={"file": str(metadata_file)}
                    )

    def _save_metadata(self, quarantined_file: QuarantinedFile):
        """Save quarantine metadata to disk."""
        metadata_path = self.quarantine_dir / "metadata" / f"{quarantined_file.id}.json"

        try:
            write_json_file(metadata_path, quarantined_file.to_dict())
        except Exception as e:
            if self.error_logger:
                self.error_logger.log_error(
                    component="FileQuarantine",
                    error_type=ErrorType.SYSTEM,
                    message=f"Failed to save quarantine metadata",
                    error=e,
                    context={"quarantine_id": quarantined_file.id}
                )

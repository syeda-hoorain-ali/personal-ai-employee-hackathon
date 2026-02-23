"""
Secret scanner for detecting sensitive information in vault files.

Prevents secrets from being committed to Git repository.
"""

import logging
import time
import re
from pathlib import Path
from typing import Dict, List, Set

logger = logging.getLogger("vault_sync.secret_scanner")


class SecretScanner:
    """Scans files for potential secrets before Git commit."""

    # Patterns for detecting common secret types
    SECRET_PATTERNS = {
        "api_key": re.compile(r'(?i)(api[_-]?key|apikey)["\s:=]+([a-zA-Z0-9_\-]{20,})'),
        "password": re.compile(r'(?i)(password|passwd|pwd)["\s:=]+([^\s]{8,})'),
        "token": re.compile(r'(?i)(token|auth[_-]?token)["\s:=]+([a-zA-Z0-9_\-]{20,})'),
        "secret": re.compile(r'(?i)(secret|client[_-]?secret)["\s:=]+([a-zA-Z0-9_\-]{20,})'),
        "private_key": re.compile(r'-----BEGIN (RSA |EC )?PRIVATE KEY-----'),
        "aws_key": re.compile(r'AKIA[0-9A-Z]{16}'),
        "github_token": re.compile(r'gh[pousr]_[A-Za-z0-9_]{36,}'),
        "jwt": re.compile(r'eyJ[A-Za-z0-9_-]*\.eyJ[A-Za-z0-9_-]*\.[A-Za-z0-9_-]*'),
    }

    # File extensions to scan
    SCANNABLE_EXTENSIONS = {".md", ".txt", ".yaml", ".yml", ".json", ".py", ".sh"}

    # Files/directories to always exclude
    EXCLUDED_PATHS = {
        ".git",
        ".secrets.baseline",
        "Logs",
        ".env.example"
    }

    def __init__(self, vault_path: str):
        """
        Initialize SecretScanner.

        Args:
            vault_path: Absolute path to vault directory
        """
        self.vault_path = Path(vault_path)

    def scan_for_secrets(
        self,
        file_paths: List[str] = None,
        scan_all: bool = False
    ) -> Dict:
        """
        Scan files for potential secrets.

        Args:
            file_paths: List of specific files to scan (relative to vault root)
            scan_all: If True, scan all files in vault

        Returns:
            Dict with scan results including found secrets
        """
        start_time = time.time()
        logger.info(
            f"[SCAN_START] operation=scan_for_secrets "
            f"scan_all={scan_all} file_count={len(file_paths) if file_paths else 0}"
        )

        if scan_all:
            files_to_scan = self._get_all_scannable_files()
        elif file_paths:
            files_to_scan = [self.vault_path / fp for fp in file_paths]
        else:
            # Default: scan staged files
            files_to_scan = self._get_staged_files()

        secrets_found = []
        files_scanned = 0

        for file_path in files_to_scan:
            if not file_path.exists():
                continue

            if self._should_exclude(file_path):
                continue

            file_secrets = self._scan_file(file_path)
            if file_secrets:
                secrets_found.extend(file_secrets)

            files_scanned += 1

        duration_ms = int((time.time() - start_time) * 1000)
        result = {
            "success": len(secrets_found) == 0,
            "files_scanned": files_scanned,
            "secrets_found": len(secrets_found),
            "details": secrets_found
        }

        if secrets_found:
            logger.warning(
                f"[SCAN_COMPLETE] operation=scan_for_secrets "
                f"success=False duration_ms={duration_ms} "
                f"files_scanned={files_scanned} secrets_found={len(secrets_found)}"
            )
        else:
            logger.info(
                f"[SCAN_COMPLETE] operation=scan_for_secrets "
                f"success=True duration_ms={duration_ms} "
                f"files_scanned={files_scanned} secrets_found=0"
            )

        return result

    def _scan_file(self, file_path: Path) -> List[Dict]:
        """
        Scan a single file for secrets.

        Args:
            file_path: Path to file to scan

        Returns:
            List of found secrets with details
        """
        secrets = []

        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()

            for secret_type, pattern in self.SECRET_PATTERNS.items():
                matches = pattern.finditer(content)
                for match in matches:
                    # Get line number
                    line_num = content[:match.start()].count('\n') + 1

                    secrets.append({
                        "file": str(file_path.relative_to(self.vault_path)),
                        "type": secret_type,
                        "line": line_num,
                        "snippet": self._get_snippet(content, match.start(), match.end())
                    })

        except Exception as e:
            logger.warning(f"Could not scan {file_path}: {e}")

        return secrets

    def _get_snippet(self, content: str, start: int, end: int, context: int = 20) -> str:
        """Get snippet of text around match with context."""
        snippet_start = max(0, start - context)
        snippet_end = min(len(content), end + context)
        snippet = content[snippet_start:snippet_end]

        # Mask the actual secret value
        match_text = content[start:end]
        masked = match_text[:10] + "***" if len(match_text) > 10 else "***"
        snippet = snippet.replace(match_text, masked)

        return snippet.strip()

    def _get_all_scannable_files(self) -> List[Path]:
        """Get all scannable files in vault."""
        files = []
        for ext in self.SCANNABLE_EXTENSIONS:
            files.extend(self.vault_path.rglob(f"*{ext}"))
        return files

    def _get_staged_files(self) -> List[Path]:
        """Get list of staged files from Git."""
        try:
            import git
            repo = git.Repo(self.vault_path)
            staged = [self.vault_path / item.a_path for item in repo.index.diff("HEAD")]
            return staged
        except Exception as e:
            logger.warning(f"Could not get staged files: {e}")
            return []

    def _should_exclude(self, file_path: Path) -> bool:
        """Check if file should be excluded from scanning."""
        # Check if path contains excluded directory/file
        for excluded in self.EXCLUDED_PATHS:
            if excluded in str(file_path):
                return True

        # Check file extension
        if file_path.suffix not in self.SCANNABLE_EXTENSIONS:
            return True

        return False

    def validate_gitignore(self) -> Dict:
        """
        Validate that .gitignore properly excludes secret files.

        Returns:
            Dict with validation results
        """
        gitignore_path = self.vault_path / ".gitignore"

        if not gitignore_path.exists():
            return {
                "success": False,
                "message": ".gitignore not found",
                "missing_patterns": []
            }

        with open(gitignore_path, 'r') as f:
            gitignore_content = f.read()

        # Required patterns for secret protection
        required_patterns = [
            ".env",
            "*.token",
            "*.key",
            "*.pem",
            "credentials/",
            "sessions/"
        ]

        missing_patterns = []
        for pattern in required_patterns:
            if pattern not in gitignore_content:
                missing_patterns.append(pattern)

        result = {
            "success": len(missing_patterns) == 0,
            "message": "All required patterns present" if not missing_patterns else "Missing patterns",
            "missing_patterns": missing_patterns
        }

        if missing_patterns:
            logger.warning(f"Missing .gitignore patterns: {missing_patterns}")

        return result

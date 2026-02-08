"""
Security scanning functionality for attachments in the Email MCP Server.
"""
import hashlib
import re
from typing import Any, Dict, Optional, Tuple
from ..email_operations.utils import validate_attachment_size


class SecurityScanner:
    """
    Scans attachments for potential security threats.
    """

    def __init__(self):
        # Known malicious file extensions
        self.malicious_extensions = {
            '.ade', '.adp', '.app', '.asp', '.bas', '.bat', '.cer', '.chm',
            '.cmd', '.com', '.cpl', '.crt', '.csh', '.csr', '.der', '.exe',
            '.fxp', '.gadget', '.grp', '.hlp', '.hpj', '.hta', '.inf',
            '.ins', '.isp', '.its', '.jar', '.js', '.jse', '.ksh', '.lnk',
            '.mad', '.maf', '.mag', '.mam', '.maq', '.mar', '.mas', '.mat',
            '.mau', '.mav', '.mbd', '.mcf', '.mda', '.mdb', '.mde', '.mdt',
            '.mdw', '.mdz', '.mht', '.mhtm', '.mhtml', '.mmc', '.msc','.msi',
            '.msp', '.mst', '.ops', '.pcd', '.pif', '.pl', '.plg', '.prf',
            '.prg', '.pst', '.reg', '.scf', '.scr', '.sct', '.shb', '.shs',
            '.shtm', '.shtml', '.stm', '.sys', '.url', '.vb', '.vbe', '.vbp',
            '.vbs', '.vxd', '.ws', '.wsc', '.wsf', '.wsh', '.xnk',
        }

        # Known malicious file signatures (magic bytes)
        self.malicious_signatures = [
            b'MZ',  # Executable files
            b'PK\x03\x04',  # ZIP files (can contain executables)
        ]

        # Dangerous content patterns
        self.dangerous_patterns = [
            re.compile(rb'<script', re.IGNORECASE),
            re.compile(rb'javascript:', re.IGNORECASE),
            re.compile(rb'vbscript:', re.IGNORECASE),
            re.compile(rb'on\w+\s*=', re.IGNORECASE),  # Event handlers
        ]

    def scan_attachment(self, attachment_data: Dict[str, Any], max_size_mb: int = 25) -> Tuple[bool, str]:
        """
        Scan an attachment for security threats.

        Args:
            attachment_data: Dictionary containing attachment information
            max_size_mb: Maximum allowed size in MB

        Returns:
            Tuple of (is_safe, reason_if_unsafe)
        """
        # Validate size first
        if not validate_attachment_size(attachment_data.get('data', ''), max_size_mb):
            return False, f"Attachment exceeds {max_size_mb}MB size limit"

        # Check file extension
        filename = attachment_data.get('filename', '')
        _, ext = self._get_file_extension(filename)

        if ext.lower() in self.malicious_extensions:
            return False, f"Potentially dangerous file extension: {ext}"

        # Decode the attachment data if possible
        data = attachment_data.get('data', '')
        try:
            decoded_data = self._decode_base64(data)
        except Exception:
            return False, "Unable to decode attachment data"

        # Check file signature
        if decoded_data and self._has_malicious_signature(decoded_data):
            return False, "Attachment has suspicious file signature"

        # Check for dangerous content patterns
        if decoded_data and self._has_dangerous_content(decoded_data):
            return False, "Attachment contains potentially dangerous content"

        return True, "Safe"

    def _get_file_extension(self, filename: str) -> Tuple[str, str]:
        """
        Extract the file name and extension.

        Args:
            filename: Original filename

        Returns:
            Tuple of (name_without_ext, extension)
        """
        if '.' in filename:
            name_part, ext_part = filename.rsplit('.', 1)
            return name_part, f'.{ext_part}'
        return filename, ''

    def _decode_base64(self, data: str) -> Optional[bytes]:
        """
        Decode base64 encoded data.

        Args:
            data: Base64 encoded string

        Returns:
            Decoded bytes or None if decoding fails
        """
        try:
            import base64
            return base64.b64decode(data)
        except Exception:
            return None

    def _has_malicious_signature(self, data: bytes) -> bool:
        """
        Check if the data has known malicious file signatures.

        Args:
            data: Binary data to check

        Returns:
            True if malicious signature is found, False otherwise
        """
        for signature in self.malicious_signatures:
            if data.startswith(signature):
                return True
        return False

    def _has_dangerous_content(self, data: bytes) -> bool:
        """
        Check if the data contains dangerous content patterns.

        Args:
            data: Binary data to check

        Returns:
            True if dangerous content is found, False otherwise
        """
        for pattern in self.dangerous_patterns:
            if pattern.search(data):
                return True
        return False

    def calculate_file_hash(self, data: bytes) -> str:
        """
        Calculate SHA-256 hash of file data for integrity checking.

        Args:
            data: Binary data to hash

        Returns:
            SHA-256 hash as hex string
        """
        sha256_hash = hashlib.sha256()
        sha256_hash.update(data)
        return sha256_hash.hexdigest()


# Global security scanner instance
security_scanner = SecurityScanner()


def get_security_scanner() -> SecurityScanner:
    """
    Get the global security scanner instance.

    Returns:
        SecurityScanner instance
    """
    return security_scanner


def scan_attachment(attachment_data: Dict[str, Any], max_size_mb: int = 25) -> Tuple[bool, str]:
    """
    Scan an attachment for security threats.

    Args:
        attachment_data: Dictionary containing attachment information
        max_size_mb: Maximum allowed size in MB

    Returns:
        Tuple of (is_safe, reason_if_unsafe)
    """
    scanner = get_security_scanner()
    return scanner.scan_attachment(attachment_data, max_size_mb)

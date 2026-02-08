"""
Audit logging for email operations.
"""
import logging
import json
from datetime import datetime
from typing import Dict, Any, Optional
from enum import Enum


class AuditEventType(Enum):
    """Types of audit events."""
    EMAIL_SEND = "email_send"
    EMAIL_DRAFT = "email_draft"
    EMAIL_SEARCH = "email_search"
    EMAIL_GET = "email_get"
    EMAIL_MOVE = "email_move"
    EMAIL_MARK = "email_mark"
    EMAIL_REPLY = "email_reply"
    EMAIL_FORWARD = "email_forward"
    EMAIL_LIST_FOLDERS = "email_list_folders"
    AUTHENTICATION = "authentication"
    CONFIGURATION_CHANGE = "configuration_change"


class AuditLogger:
    """
    Logger for audit events in the email system.
    """
    def __init__(self, log_file: Optional[str] = None):
        """
        Initialize the audit logger.

        Args:
            log_file: Optional file to write audit logs to
        """
        self.logger = logging.getLogger('email_mcp_audit')
        self.logger.setLevel(logging.INFO)

        # Prevent duplicate handlers
        if not self.logger.handlers:
            if log_file:
                handler = logging.FileHandler(log_file)
            else:
                handler = logging.StreamHandler()

            formatter = logging.Formatter(
                '%(asctime)s - AUDIT - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)

    def log_event(self, event_type: AuditEventType, user_id: str,
                  account_id: str, details: Dict[str, Any],
                  success: bool = True, ip_address: Optional[str] = None):
        """
        Log an audit event.

        Args:
            event_type: Type of event being logged
            user_id: ID of the user performing the action
            account_id: ID of the email account involved
            details: Additional details about the event
            success: Whether the operation was successful
            ip_address: IP address of the requesting client
        """
        audit_entry = {
            "timestamp": datetime.now().isoformat(),
            "event_type": event_type.value,
            "user_id": user_id,
            "account_id": account_id,
            "success": success,
            "details": details
        }

        if ip_address:
            audit_entry["ip_address"] = ip_address

        log_message = json.dumps(audit_entry)

        if success:
            self.logger.info(log_message)
        else:
            self.logger.warning(log_message)

    def log_email_operation(self, operation: str, user_id: str,
                          account_id: str, email_id: Optional[str] = None,
                          recipients: Optional[list] = None,
                          subject: Optional[str] = None,
                          success: bool = True, ip_address: Optional[str] = None):
        """
        Log an email operation.

        Args:
            operation: Type of email operation (send, draft, etc.)
            user_id: ID of the user performing the action
            account_id: ID of the email account involved
            email_id: ID of the email being operated on
            recipients: List of email recipients
            subject: Subject of the email
            success: Whether the operation was successful
            ip_address: IP address of the requesting client
        """
        details = {
            "operation": operation,
            "email_id": email_id,
            "recipients_count": len(recipients) if recipients else 0,
            "subject_preview": subject[:50] if subject else None
        }

        event_type = AuditEventType(f"EMAIL_{operation.upper()}")
        self.log_event(event_type, user_id, account_id, details, success, ip_address)

    def log_authentication_event(self, user_id: str, account_id: str,
                               success: bool, method: str, ip_address: Optional[str] = None):
        """
        Log an authentication event.

        Args:
            user_id: ID of the user attempting authentication
            account_id: ID of the email account being accessed
            success: Whether authentication was successful
            method: Authentication method used
            ip_address: IP address of the requesting client
        """
        details = {
            "method": method,
            "timestamp": datetime.now().isoformat()
        }

        self.log_event(AuditEventType.AUTHENTICATION, user_id, account_id,
                      details, success, ip_address)

    def log_configuration_change(self, user_id: str, account_id: str,
                                config_changes: Dict[str, Any],
                                ip_address: Optional[str] = None):
        """
        Log a configuration change event.

        Args:
            user_id: ID of the user making the change
            account_id: ID of the email account being configured
            config_changes: Details of configuration changes
            ip_address: IP address of the requesting client
        """
        details = {
            "changes": config_changes,
            "timestamp": datetime.now().isoformat()
        }

        self.log_event(AuditEventType.CONFIGURATION_CHANGE, user_id,
                      account_id, details, True, ip_address)


# Global audit logger instance
audit_logger = AuditLogger()


def get_audit_logger() -> AuditLogger:
    """
    Get the global audit logger instance.

    Returns:
        AuditLogger instance
    """
    return audit_logger


def log_event(event_type: AuditEventType, user_id: str,
              account_id: str, details: Dict[str, Any],
              success: bool = True, ip_address: Optional[str] = None):
    """
    Log an audit event.

    Args:
        event_type: Type of event being logged
        user_id: ID of the user performing the action
        account_id: ID of the email account involved
        details: Additional details about the event
        success: Whether the operation was successful
        ip_address: IP address of the requesting client
    """
    logger = get_audit_logger()
    logger.log_event(event_type, user_id, account_id, details, success, ip_address)


def log_email_operation(operation: str, user_id: str,
                      account_id: str, email_id: Optional[str] = None,
                      recipients: Optional[list] = None,
                      subject: Optional[str] = None,
                      success: bool = True, ip_address: Optional[str] = None):
    """
    Log an email operation.

    Args:
        operation: Type of email operation (send, draft, etc.)
        user_id: ID of the user performing the action
        account_id: ID of the email account involved
        email_id: ID of the email being operated on
        recipients: List of email recipients
        subject: Subject of the email
        success: Whether the operation was successful
        ip_address: IP address of the requesting client
    """
    logger = get_audit_logger()
    logger.log_email_operation(operation, user_id, account_id, email_id,
                              recipients, subject, success, ip_address)


def log_authentication_event(user_id: str, account_id: str,
                           success: bool, method: str,
                           ip_address: Optional[str] = None):
    """
    Log an authentication event.

    Args:
        user_id: ID of the user attempting authentication
        account_id: ID of the email account being accessed
        success: Whether authentication was successful
        method: Authentication method used
        ip_address: IP address of the requesting client
    """
    logger = get_audit_logger()
    logger.log_authentication_event(user_id, account_id, success, method, ip_address)

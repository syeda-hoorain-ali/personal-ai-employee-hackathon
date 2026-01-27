"""
IMAP/SMTP protocol handlers for email operations.
"""
import smtplib
import imaplib
import email
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from typing import List, Dict, Any, Optional
from datetime import datetime
import base64
from ..models.email import Email, Attachment
from ..models.account import EmailAccount
from ..config.providers import get_provider_config
from ..email_operations.utils import validate_attachment, sanitize_filename
from ..config.settings import settings


class EmailClient:
    """Handles IMAP and SMTP operations for email accounts."""

    def __init__(self, account: EmailAccount, password: Optional[str] = None):
        """
        Initialize the email client with account configuration.

        Args:
            account: Email account configuration
            password: Password for authentication (optional, can be set later)
        """
        self.account = account
        provider_config = get_provider_config(account.provider)
        if not provider_config:
            raise ValueError(f"Unsupported email provider: {account.provider}")
        self.provider_config = provider_config
        self.password = password


        # Connection objects
        self.smtp_conn = None
        self.imap_conn = None

    def connect_smtp(self):
        """Establish SMTP connection."""
        if self.smtp_conn:
            return

        try:
            # Check if provider_config exists
            if not self.provider_config:
                raise Exception(f"No configuration found for provider: {self.account.provider}")

            # Create SMTP connection
            if self.provider_config.use_tls:
                self.smtp_conn = smtplib.SMTP(self.provider_config.smtp_server, self.provider_config.smtp_port)
                self.smtp_conn.starttls()
            else:
                self.smtp_conn = smtplib.SMTP(self.provider_config.smtp_server, self.provider_config.smtp_port)

            # Login using stored credentials
            # Attempt to login with email address and password
            password = getattr(self, 'password', None) or settings.test_email_app_password or settings.email_password or ''

            if not password:
                raise Exception("No password or app password provided for authentication")

            self.smtp_conn.login(self.account.email_address, password)
            print(f"Connected and authenticated to SMTP server: {self.provider_config.smtp_server}:{self.provider_config.smtp_port}")

        except Exception as e:
            raise Exception(f"Failed to connect to SMTP server: {str(e)}")

    def disconnect_smtp(self):
        """Close SMTP connection."""
        if self.smtp_conn:
            try:
                self.smtp_conn.quit()
            except:
                pass  # Ignore errors when closing
            finally:
                self.smtp_conn = None

    def connect_imap(self):
        """Establish IMAP connection."""
        if self.imap_conn:
            return

        try:
            # Check if provider_config exists
            if not self.provider_config:
                raise Exception(f"No configuration found for provider: {self.account.provider}")

            # Create IMAP connection
            self.imap_conn = imaplib.IMAP4_SSL(
                self.provider_config.imap_server,
                self.provider_config.imap_port
            )

            # Login using stored credentials (in a real implementation, you'd have the password/oauth token)
            print(f"Connecting to IMAP server: {self.provider_config.imap_server}:{self.provider_config.imap_port}")

        except Exception as e:
            raise Exception(f"Failed to connect to IMAP server: {str(e)}")

    def disconnect_imap(self):
        """Close IMAP connection."""
        if self.imap_conn:
            try:
                self.imap_conn.close()
                self.imap_conn.logout()
            except:
                pass  # Ignore errors when closing
            finally:
                self.imap_conn = None

    def send_email(self, to: List[str], subject: str, body: str,
                   html_body: Optional[str] = None,
                   attachments: Optional[List[Dict[str, Any]]] = None) -> str:
        """
        Send an email using SMTP.

        Args:
            to: List of recipient email addresses
            subject: Email subject
            body: Plain text body
            html_body: HTML body (optional)
            attachments: List of attachments (optional)

        Returns:
            Message ID of sent email
        """
        if not self.smtp_conn:
            self.connect_smtp()

        # Double-check that smtp_conn is not None after connection attempt
        if not self.smtp_conn:
            raise Exception("SMTP connection could not be established")

        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['From'] = self.account.email_address
            msg['To'] = ', '.join(to)
            msg['Subject'] = subject

            # Add plain text part
            text_part = MIMEText(body, 'plain')
            msg.attach(text_part)

            # Add HTML part if provided
            if html_body:
                html_part = MIMEText(html_body, 'html')
                msg.attach(html_part)

            # Add attachments if provided
            if attachments:
                for attachment in attachments:
                    validation_result = validate_attachment(attachment)

                    if not validation_result["valid"]:
                        raise ValueError(f"Invalid attachment: {'; '.join(validation_result['errors'])}")

                    # Decode base64 data
                    try:
                        attachment_data = base64.b64decode(attachment['data'])
                    except Exception:
                        raise ValueError("Invalid base64 data in attachment")

                    # Create MIME attachment
                    part = MIMEBase('application', 'octet-stream')
                    part.set_payload(attachment_data)
                    encoders.encode_base64(part)

                    # Set filename (using sanitized version)
                    filename = validation_result["sanitized_filename"] or attachment.get("filename", "attachment")
                    part.add_header(
                        'Content-Disposition',
                        f'attachment; filename= "{filename}"'
                    )

                    msg.attach(part)

            # Send the email
            text = msg.as_string()
            self.smtp_conn.sendmail(self.account.email_address, to, text)

            # Generate a mock message ID (in a real implementation, this would come from the server)
            import uuid
            message_id = f"<{uuid.uuid4()}@{self.account.email_address.split('@')[1]}>"

            return message_id

        except Exception as e:
            raise Exception(f"Failed to send email: {str(e)}")

    def list_folders(self) -> List[Dict[str, Any]]:
        """
        List available email folders.

        Returns:
            List of folder information
        """
        if not self.imap_conn:
            self.connect_imap()

        try:
            # Make sure we're authenticated before trying to list folders
            # Check if we're in the authenticated state, if not, authenticate
            if self.imap_conn and self.imap_conn.state != 'AUTH' and self.imap_conn.state != 'SELECTED':
                # Authenticate using stored credentials
                password = getattr(self, 'password', None) or settings.test_email_app_password or settings.email_password or ''

                if not password:
                    raise Exception("No password or app password provided for IMAP authentication")

                # Login to IMAP server
                self.imap_conn.login(self.account.email_address, password)

            # Get list of folders
            if not self.imap_conn:
                raise Exception("IMAP connection is not established")
            status, folders = self.imap_conn.list()

            folder_list = []
            if folders:  # Check if folders is not None or empty
                for folder_data in folders:
                    # Parse folder information
                    if folder_data:
                        if isinstance(folder_data, bytes):
                            folder_str = folder_data.decode('utf-8')
                        else:
                            folder_str = ''.join(tuple(data.decode('utf-8') for data in folder_data))

                        # Parse folder information - typical format is like: (\HasNoChildren) "/" "INBOX"
                        folder_parts = folder_str.split('"')
                        if len(folder_parts) >= 3:
                            folder_name = folder_parts[-1].strip()
                            if folder_name:  # Skip empty names
                                folder_list.append({
                                    'name': folder_name,
                                    'type': self._get_folder_type(folder_name),
                                    'email_count': 0  # We'll set this to 0 for now, in real implementation would get actual count
                                })

            # Add standard folders if not present
            standard_folders = ['INBOX', 'Sent', 'Drafts', 'Trash', 'Archive']
            existing_names = [f['name'].lower() for f in folder_list]

            for std_folder in standard_folders:
                if std_folder.lower() not in existing_names:
                    folder_list.append({
                        'name': std_folder,
                        'type': self._get_folder_type(std_folder),
                        'email_count': 0
                    })

            return folder_list

        except Exception as e:
            raise Exception(f"Failed to list folders: {str(e)}")

    def _get_folder_type(self, folder_name: str) -> str:
        """
        Determine folder type based on name.

        Args:
            folder_name: Name of the folder

        Returns:
            Folder type
        """
        folder_lower = folder_name.lower()
        if 'inbox' in folder_lower:
            return 'inbox'
        elif 'sent' in folder_lower or 'outbox' in folder_lower:
            return 'sent'
        elif 'draft' in folder_lower:
            return 'drafts'
        elif 'trash' in folder_lower or 'deleted' in folder_lower:
            return 'trash'
        elif 'archive' in folder_lower:
            return 'archive'
        else:
            return 'custom'

    def search_emails(self, query: str = "", folder: str = "INBOX",
                     sender: str = "", after_date: str = "",
                     before_date: str = "", limit: int = 50,
                     offset: int = 0) -> List[Email]:
        """
        Search for emails based on criteria.

        Args:
            query: Search query terms
            folder: Folder to search in
            sender: Filter by sender
            after_date: Filter emails after date (YYYY-MM-DD)
            before_date: Filter emails before date (YYYY-MM-DD)
            limit: Maximum number of results
            offset: Offset for pagination

        Returns:
            List of matching emails
        """
        if not self.imap_conn:
            self.connect_imap()

        try:
            # Make sure we're authenticated before trying to select folder
            if self.imap_conn and self.imap_conn.state != 'AUTH' and self.imap_conn.state != 'SELECTED':
                # Authenticate using stored credentials
                password = getattr(self, 'password', None) or settings.test_email_app_password or settings.email_password or ''

                if not password:
                    raise Exception("No password or app password provided for IMAP authentication")

                # Login to IMAP server
                self.imap_conn.login(self.account.email_address, password)

            # Select the folder
            if not self.imap_conn:
                raise Exception("IMAP connection is not established")
            self.imap_conn.select(folder)

            # Build search criteria
            search_criteria = []

            if query:
                search_criteria.append(f'TEXT "{query}"')
            if sender:
                search_criteria.append(f'FROM "{sender}"')
            if after_date:
                search_criteria.append(f'SINCE {after_date}')
            if before_date:
                search_criteria.append(f'BEFORE {before_date}')

            # If no specific criteria, search all
            if not search_criteria:
                search_criteria = ['ALL']

            # Join search criteria
            search_str = ' '.join(search_criteria)

            # Perform search
            if not self.imap_conn:
                raise Exception("IMAP connection is not established")
            status, messages = self.imap_conn.search(None, search_str)

            if status != 'OK':
                return []

            # Get message IDs
            email_ids = messages[0].split()

            # Apply offset and limit
            start_idx = min(offset, len(email_ids))
            end_idx = min(start_idx + limit, len(email_ids))
            email_ids = email_ids[start_idx:end_idx]

            # Fetch email details
            emails = []
            for email_id in email_ids:
                if not self.imap_conn:
                    raise Exception("IMAP connection is not established")
                resp, msg_data = self.imap_conn.fetch(email_id, '(RFC822)')

                if resp != 'OK':
                    continue

                # Parse email
                raw_email = msg_data[0][1]
                parsed_email = email.message_from_bytes(raw_email)

                # Extract email properties
                subject = parsed_email.get('Subject', 'No Subject')
                sender = parsed_email.get('From', 'Unknown Sender')
                date = parsed_email.get('Date', '')

                # Get email body
                body = ""
                if parsed_email.is_multipart():
                    for part in parsed_email.walk():
                        if part.get_content_type() == "text/plain":
                            body = part.get_payload(decode=True).decode()
                            break
                else:
                    body = parsed_email.get_payload(decode=True).decode()

                # Create Email object
                email_obj = Email(
                    id=email_id.decode(),
                    sender=sender,
                    recipients=[],
                    subject=subject,
                    body=body[:100] + "..." if len(body) > 100 else body,  # Preview
                    timestamp=datetime.now(),  # In real implementation, parse from email date
                    read_status=False,  # In real implementation, check flags
                    importance_level="normal"  # In real implementation, check priority headers
                )

                emails.append(email_obj)

            return emails

        except Exception as e:
            raise Exception(f"Failed to search emails: {str(e)}")

    def get_email(self, email_id: str) -> Optional[Email]:
        """
        Retrieve a specific email by ID.

        Args:
            email_id: ID of the email to retrieve

        Returns:
            Email object if found, None otherwise
        """
        if not self.imap_conn:
            self.connect_imap()

        try:
            # Fetch the specific email
            if not self.imap_conn:
                raise Exception("IMAP connection is not established")
            resp, msg_data = self.imap_conn.fetch(email_id.encode(), '(RFC822)')

            if resp != 'OK':
                return None

            # Parse email
            raw_email = msg_data[0][1]
            parsed_email = email.message_from_bytes(raw_email)

            # Extract email properties
            subject = parsed_email.get('Subject', 'No Subject')
            sender = parsed_email.get('From', 'Unknown Sender')
            recipients = parsed_email.get_all('To', [])
            cc = parsed_email.get_all('Cc', [])
            date = parsed_email.get('Date', '')

            # Combine all recipients
            all_recipients = []
            if recipients:
                all_recipients.extend([r.strip() for r in ','.join(recipients).split(',')])
            if cc:
                all_recipients.extend([c.strip() for c in ','.join(cc).split(',')])

            # Get email body
            body = ""
            html_body = None
            attachments = []

            if parsed_email.is_multipart():
                for part in parsed_email.walk():
                    content_type = part.get_content_type()
                    content_disposition = str(part.get("Content-Disposition"))

                    if content_type == "text/plain" and "attachment" not in content_disposition:
                        body = part.get_payload(decode=True).decode()
                    elif content_type == "text/html" and "attachment" not in content_disposition:
                        html_body = part.get_payload(decode=True).decode()
                    elif "attachment" in content_disposition:
                        # Handle attachment
                        filename = part.get_filename()
                        if filename:
                            payload = part.get_payload(decode=True)
                            attachment = Attachment(
                                id=f"att_{len(attachments)}",
                                filename=sanitize_filename(filename),
                                content_type=part.get_content_type(),
                                size=len(payload) if payload else 0
                            )
                            attachments.append(attachment)
            else:
                body = parsed_email.get_payload(decode=True).decode()

            # Create and return Email object
            email_obj = Email(
                id=email_id,
                sender=sender,
                recipients=all_recipients,
                subject=subject,
                body=body,
                html_body=html_body,
                timestamp=datetime.now(),  # In real implementation, parse from email date
                read_status=False,  # In real implementation, check flags
                importance_level="normal",  # In real implementation, check priority headers
                attachments=attachments
            )

            return email_obj

        except Exception as e:
            raise Exception(f"Failed to get email: {str(e)}")

    def move_email(self, email_id: str, destination: str) -> bool:
        """
        Move an email to a different folder.

        Args:
            email_id: ID of the email to move
            destination: Destination folder

        Returns:
            True if successful, False otherwise
        """
        if not self.imap_conn:
            self.connect_imap()

        try:
            # In IMAP, moving is done by copying to destination and deleting from source
            if not self.imap_conn:
                raise Exception("IMAP connection is not established")
            result_copy = self.imap_conn.copy(email_id.encode(), destination)
            if result_copy[0] != 'OK':
                return False

            # Mark original for deletion
            self.imap_conn.store(email_id.encode(), '+FLAGS', '\\Deleted')

            # Expunge to permanently remove
            self.imap_conn.expunge()

            return True

        except Exception as e:
            raise Exception(f"Failed to move email: {str(e)}")

    def mark_email(self, email_id: str, read: Optional[bool] = None,
                   importance: Optional[str] = None) -> bool:
        """
        Mark an email as read/unread or set importance.

        Args:
            email_id: ID of the email to mark
            read: Set read status (True for read, False for unread)
            importance: Set importance level

        Returns:
            True if successful, False otherwise
        """
        if not self.imap_conn:
            self.connect_imap()

        try:
            # Make sure we're authenticated before trying to mark email
            # Check if we're in the authenticated state, if not, authenticate
            if self.imap_conn and self.imap_conn.state != 'AUTH' and self.imap_conn.state != 'SELECTED':
                # Authenticate using stored credentials
                password = getattr(self, 'password', None) or settings.test_email_app_password or settings.email_password or ''

                if not password:
                    raise Exception("No password or app password provided for IMAP authentication")

                # Login to IMAP server
                self.imap_conn.login(self.account.email_address, password)

            # Need to select a folder before marking emails
            # For marking operations, we typically want to work in the INBOX or wherever the email exists
            # First, let's search for which folder contains this email
            # For simplicity, we'll assume it's in INBOX, but a more sophisticated implementation
            # would search across folders to find where the email exists

            # Select the INBOX folder
            if not self.imap_conn:
                raise Exception("IMAP connection is not established")
            status, _ = self.imap_conn.select('INBOX')
            if status != 'OK':
                # If INBOX doesn't work, try selecting any folder
                self.imap_conn.select()  # Selects the default folder

            # Handle read/unread status
            if read is not None:
                if read:
                    # Mark as read
                    result = self.imap_conn.store(email_id.encode(), '+FLAGS', '\\Seen')
                else:
                    # Mark as unread
                    result = self.imap_conn.store(email_id.encode(), '-FLAGS', '\\Seen')

            # Handle importance (priority)
            if importance:
                # Map importance to email priority headers
                priority_map = {
                    'high': '\\Flagged',
                    'low': '\\Draft',  # Using draft as low priority (not perfect but available)
                    'normal': None
                }

                flag = priority_map.get(importance.lower())
                if flag:
                    result = self.imap_conn.store(email_id.encode(), '+FLAGS', flag)

            return True

        except Exception as e:
            raise Exception(f"Failed to mark email: {str(e)}")

    def create_draft(self, to: List[str], subject: str, body: str,
                     html_body: Optional[str] = None,
                     attachments: Optional[List[Dict[str, Any]]] = None) -> str:
        """
        Create a draft email.

        Args:
            to: List of recipient email addresses
            subject: Email subject
            body: Plain text body
            html_body: HTML body (optional)
            attachments: List of attachments (optional)

        Returns:
            Draft ID
        """
        # In a real implementation, this would save the draft to the drafts folder
        # For now, we'll just return a mock draft ID
        import uuid
        draft_id = str(uuid.uuid4())

        # Create message
        msg = MIMEMultipart('alternative')
        msg['From'] = self.account.email_address
        msg['To'] = ', '.join(to)
        msg['Subject'] = subject
        msg['X-Draft'] = '1'  # Mark as draft

        # Add plain text part
        text_part = MIMEText(body, 'plain')
        msg.attach(text_part)

        # Add HTML part if provided
        if html_body:
            html_part = MIMEText(html_body, 'html')
            msg.attach(html_part)

        # Add attachments if provided
        if attachments:
            for attachment in attachments:
                validation_result = validate_attachment(attachment)

                if not validation_result["valid"]:
                    raise ValueError(f"Invalid attachment: {'; '.join(validation_result['errors'])}")

                # Decode base64 data
                try:
                    attachment_data = base64.b64decode(attachment['data'])
                except Exception:
                    raise ValueError("Invalid base64 data in attachment")

                # Create MIME attachment
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(attachment_data)
                encoders.encode_base64(part)

                # Set filename (using sanitized version)
                filename = validation_result["sanitized_filename"] or attachment.get("filename", "attachment")
                part.add_header(
                    'Content-Disposition',
                    f'attachment; filename= "{filename}"'
                )

                msg.attach(part)

        # In a real implementation, we would save this to the drafts folder
        # For now, we just return the draft ID
        return draft_id

    def delete_email(self, email_id: str) -> bool:
        """
        Delete an email by marking it as deleted and expunging it.

        Args:
            email_id: ID of the email to delete

        Returns:
            True if successful, False otherwise
        """
        if not self.imap_conn:
            self.connect_imap()

        try:
            # Make sure we're authenticated before trying to delete email
            if self.imap_conn and self.imap_conn.state != 'AUTH' and self.imap_conn.state != 'SELECTED':
                # Authenticate using stored credentials
                password = getattr(self, 'password', None) or settings.test_email_app_password or settings.email_password or ''

                if not password:
                    raise Exception("No password or app password provided for IMAP authentication")

                # Login to IMAP server
                self.imap_conn.login(self.account.email_address, password)

            # Need to select a folder before deleting emails
            # Select the INBOX folder by default
            status, _ = self.imap_conn.select('INBOX')
            if status != 'OK':
                # If INBOX doesn't work, try selecting any folder
                self.imap_conn.select()  # Selects the default folder

            # Mark the email with the Deleted flag
            result = self.imap_conn.store(email_id.encode(), '+FLAGS', '\\Deleted')

            # Expunge to permanently remove the email
            # NOTE: EXPUNGE affects all messages in the folder with sequence numbers
            # greater than or equal to the deleted message, so subsequent operations
            # might be affected
            self.imap_conn.expunge()

            return True

        except Exception as e:
            raise Exception(f"Failed to delete email: {str(e)}")
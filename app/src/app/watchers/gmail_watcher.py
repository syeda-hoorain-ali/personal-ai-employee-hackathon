from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.auth.transport.requests import Request
from datetime import datetime
from pathlib import Path
from .base_watcher import BaseWatcher

class GmailWatcher(BaseWatcher):
    def __init__(self, vault_path: str, credentials_path: str):
        super().__init__(vault_path, check_interval=120)
        self.credentials_path = credentials_path
        self.creds = self._load_credentials()
        self.service = build('gmail', 'v1', credentials=self.creds)
        self.processed_ids = set()

    def _load_credentials(self):
        """Load Google API credentials from file."""
        try:
            if not Path(self.credentials_path).exists():
                raise FileNotFoundError(f'Credentials file not found: {self.credentials_path}')

            # Load JSON-formatted credentials
            import json
            with open(self.credentials_path, 'r') as token:
                token_data = json.load(token)

            # Create credentials object from token data
            # Load client credentials to get client_id and client_secret
            import json
            client_creds_path = Path.home() / ".gmail-mcp" / "gcp-oauth.keys.json"
            client_creds = {}
            if client_creds_path.exists():
                with open(client_creds_path, 'r') as f:
                    client_data = json.load(f)
                    if 'installed' in client_data:
                        client_creds = client_data['installed']

            # Use the scopes from the token file, but ensure they include the required scopes
            token_scopes = token_data.get('scopes', ['https://www.googleapis.com/auth/gmail.readonly'])

            creds = Credentials(
                token=token_data.get('access_token'),
                refresh_token=token_data.get('refresh_token'),
                id_token=token_data.get('id_token'),
                token_uri=token_data.get('token_uri', client_creds.get('token_uri', 'https://oauth2.googleapis.com/token')),
                client_id=token_data.get('client_id', client_creds.get('client_id')),
                client_secret=token_data.get('client_secret', client_creds.get('client_secret')),
                scopes=token_scopes
            )

            # Validate the credentials and check if they're valid before returning
            if not creds.valid:
                if creds.expired and creds.refresh_token:
                    self.logger.info('Credentials are expired, refreshing...')
                    try:
                        creds.refresh(Request())
                    except Exception as e:
                        self.logger.error(f'Error refreshing credentials: {e}')
                        raise
                else:
                    self.logger.warning('Credentials are not valid and cannot be refreshed')
                    raise ValueError('Invalid credentials that cannot be refreshed')

            return creds
        except FileNotFoundError:
            self.logger.error(f'Credentials file not found: {self.credentials_path}')
            raise
        except Exception as e:
            self.logger.error(f'Error loading credentials: {e}')
            raise

    def check_for_updates(self) -> list:
        """Check for new emails in Gmail inbox."""
        try:
            results = self.service.users().messages().list(
                userId='me', q='is:unread is:important'
            ).execute()
            messages = results.get('messages', [])

            # Filter out already processed messages
            new_messages = [m for m in messages if m['id'] not in self.processed_ids]

            self.logger.info(f'Found {len(new_messages)} new messages to process')
            return new_messages
        except HttpError as e:
            self.logger.error(f'HTTP error checking for email updates: {e}')
            return []
        except Exception as e:
            self.logger.error(f'Error checking for email updates: {e}')
            return []

    def create_action_file(self, item) -> Path:
        """Create a markdown file for the email in the Needs_Action folder."""
        message = item
        try:
            msg = self.service.users().messages().get(
                userId='me', id=message['id']
            ).execute()

            # Extract headers
            headers = {h['name']: h['value'] for h in msg['payload']['headers']}

            # Get the actual received time from Gmail
            # The 'internalDate' field contains the timestamp when the email was received by Gmail
            import time
            received_timestamp = int(msg.get('internalDate', time.time() * 1000))  # internalDate is in milliseconds
            received_datetime = datetime.fromtimestamp(received_timestamp / 1000.0)  # convert to seconds

            # Extract email body
            body = ""
            payload = msg.get('payload', {})
            parts = payload.get('parts', [])

            if parts:
                for part in parts:
                    if part.get('mimeType') == 'text/plain':
                        import base64
                        body_data = part['body']['data']
                        if body_data:
                            body = base64.urlsafe_b64decode(body_data).decode('utf-8')
                        break
            else:
                # Handle simple message format
                if 'body' in msg.get('payload', {}) and 'data' in msg['payload']['body']:
                    import base64
                    body_data = msg['payload']['body']['data']
                    if body_data:
                        body = base64.urlsafe_b64decode(body_data).decode('utf-8')

            content = f'''---
type: email
from: {headers.get('From', 'Unknown')}
subject: {headers.get('Subject', 'No Subject')}
received: {received_datetime.isoformat()}
priority: high
status: pending
message_id: {message['id']}

---

## Email Content
{body or 'No content available'}

## Suggested Actions
- [ ] Reply to sender
- [ ] Forward to relevant party
- [ ] Archive after processing
'''

            # Write with UTF-8 encoding to handle special characters
            with open(self.needs_action / f'EMAIL_{message["id"]}.md', 'w', encoding='utf-8') as f:
                f.write(content)

            filepath = self.needs_action / f'EMAIL_{message["id"]}.md'
            self.processed_ids.add(message['id'])

            self.logger.info(f'Created action file for email: {filepath}')
            return filepath
        except HttpError as e:
            self.logger.error(f'HTTP error getting email {message["id"]}: {e}')
            return None
        except Exception as e:
            self.logger.error(f'Error creating action file for email {message["id"]}: {e}')
            return None

    def run(self):
        """Run the Gmail watcher continuously."""
        self.logger.info(f'Starting {self.__class__.__name__}')
        while True:
            try:
                items = self.check_for_updates()
                for item in items:
                    self.create_action_file(item)
            except Exception as e:
                self.logger.error(f'Error in Gmail watcher: {e}')
            # Sleep for the check interval
            import time
            time.sleep(self.check_interval)

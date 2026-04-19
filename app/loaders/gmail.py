import os
import base64
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from core.schema import BaseEmail

class GmailLoader:
    SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

    def __init__(self, token_path: str = 'token.json', credentials_path: str = 'credentials.json'):
        self.token_path = token_path
        self.credentials_path = credentials_path
        self._service = None

    def _get_service(self):
        """Internal helper to get or create the Gmail API service."""
        if self._service:
            return self._service

        creds = None
        # Load existing tokens from the specified file path
        if os.path.exists(self.token_path):
            creds = Credentials.from_authorized_user_file(self.token_path, self.SCOPES)
        
        # If no valid credentials, handle refresh or new login
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(self.credentials_path, self.SCOPES)
                creds = flow.run_local_server(port=0)
            
            # Persist the credentials for the next run
            with open(self.token_path, 'w') as token_file:
                token_file.write(creds.to_json())
                
        self._service = build('gmail', 'v1', credentials=creds)
        return self._service

    def fetch_emails(self, limit: int = 10) -> list[BaseEmail]:
        service = self._get_service()
        # Fetch list of message IDs
        results = service.users().messages().list(userId='me', maxResults=limit).execute()
        messages = results.get('messages', [])

        emails = []
        for msg in messages:
            # Get full message details
            m = service.users().messages().get(userId='me', id=msg['id']).execute()
            payload = m.get('payload', {})
            headers = payload.get('headers', [])
            
            # Parse headers for Subject and From
            subject = next((h['value'] for h in headers if h['name'] == 'Subject'), "No Subject")
            sender = next((h['value'] for h in headers if h['name'] == 'From'), "Unknown")
            
            emails.append(BaseEmail(
                source="Gmail",
                subject=subject,
                sender=sender,
                body=m.get('snippet', '')
            ))
        return emails
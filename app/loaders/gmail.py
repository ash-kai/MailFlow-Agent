import os
import base64
import logging
import datetime
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from core.schema import BaseEmail
from core.persistence import TokenStore
from typing import Optional

logger = logging.getLogger(__name__)

class GmailLoader:
    SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

    def __init__(self, token_path: str = 'token.json', credentials_path: str = 'credentials.json'):
        self.store = TokenStore(token_path)
        self.credentials_path = credentials_path
        self._service = None

    def _get_service(self):
        """Internal helper to get or create the Gmail API service."""
        if self._service:
            return self._service

        creds = None
        if self.store.exists():
            # Note: Credentials.from_authorized_user_file still takes a path, 
            # but we use the store's resolved path.
            creds = Credentials.from_authorized_user_file(self.store.filepath, self.SCOPES)
        
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                logger.info("Refreshing Gmail access token...")
                creds.refresh(Request())
            else:
                logger.info("Initiating new Gmail interactive flow...")
                flow = InstalledAppFlow.from_client_secrets_file(self.credentials_path, self.SCOPES)
                creds = flow.run_local_server(port=0)
            
            self.store.write(creds.to_json())
                
        self._service = build(
            'gmail', 
            'v1', 
            credentials=creds, 
            static_discovery=False
        )
        return self._service

    def fetch_emails(self, limit: Optional[int] = None, folder: str = "inbox", date: Optional[datetime.date] = None) -> list[BaseEmail]:
        emails = []
        try:
            service = self._get_service()
            
            # Map internal folder names to Gmail query syntax
            query_parts = []
            if folder == "unread":
                query_parts.append("is:unread")
            elif folder == "junk":
                query_parts.append("in:spam")
            elif folder == "inbox":
                query_parts.append("label:inbox")
            # Add date filtering if provided
            if date:
                date_str = date.strftime("%Y/%m/%d")
                next_day = date + datetime.timedelta(days=1)
                next_day_str = next_day.strftime("%Y/%m/%d")
                query_parts.append(f"after:{date_str} before:{next_day_str}")
            
            query = " ".join(query_parts) if query_parts else None
            
            max_results = limit if limit is not None else 500 # Gmail API maxResults default is 100, max is 500

            # Fetch list of message IDs with query
            results = service.users().messages().list(userId='me', q=query, maxResults=max_results).execute()
            messages = results.get('messages', [])

            for msg_id_obj in messages:
                msg_id = msg_id_obj['id']
                try:
                    # Get full message details
                    m = service.users().messages().get(userId='me', id=msg_id).execute()
                    payload = m.get('payload', {})
                    headers = payload.get('headers', [])
                    
                    # Parse headers safely
                    subject = next((h['value'] for h in headers if h['name'].lower() == 'subject'), "No Subject")
                    sender = next((h['value'] for h in headers if h['name'].lower() == 'from'), "Unknown")
                    
                    emails.append(BaseEmail(
                        source="Gmail",
                        subject=subject,
                        sender=sender,
                        body=m.get('snippet', '')
                    ))
                except Exception as msg_err:
                    logger.warning(f"Skipping Gmail message {msg_id} due to error: {msg_err}")
            
        except Exception as e:
            logger.error(f"Failed to fetch Gmail messages: {e}")
            
        return emails
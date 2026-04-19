import os
import base64
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from core.schema import BaseEmail

SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

def get_gmail_service():
    creds = None
    # The file token.json stores the user's access and refresh tokens
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
            
    return build('gmail', 'v1', credentials=creds)

class GmailLoader:
    def fetch_emails(self, limit: int = 10) -> list[BaseEmail]:
        service = get_gmail_service()
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
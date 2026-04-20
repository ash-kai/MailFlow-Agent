import os
import msal
import requests
import logging
import datetime
from core.schema import BaseEmail
from core.persistence import TokenStore
from typing import Optional

logger = logging.getLogger(__name__)

class OutlookLoader:
    def __init__(self, token_path: str = 'outlook_token.json'):
        self.store = TokenStore(token_path)
        self.client_id = os.getenv("OUTLOOK_CLIENT_ID")
        self.tenant_id = os.getenv("OUTLOOK_TENANT_ID", "common")
        self.authority = f"https://login.microsoftonline.com/{self.tenant_id}"
        self.scopes = ["Mail.Read", "User.Read"]
        self._app = None
        self._cache = None

    def _get_app(self):
        """Initializes the MSAL application with a persistent token cache."""
        if self._app:
            return self._app

        self._cache = msal.SerializableTokenCache()
        if self.store.exists():
            self._cache.deserialize(self.store.read())

        self._app = msal.PublicClientApplication(
            self.client_id,
            authority=self.authority,
            token_cache=self._cache
        )
        return self._app

    def _get_access_token(self):
        """Attempts silent auth from cache, falling back to interactive login."""
        app = self._get_app()
        accounts = app.get_accounts()
        result = None

        if accounts:
            logger.debug("Attempting silent token acquisition for Outlook...")
            result = app.acquire_token_silent(self.scopes, account=accounts[0])

        if not result:
            logger.info("No Outlook token in cache or silent refresh failed. Starting interactive login...")
            result = app.acquire_token_interactive(scopes=self.scopes, port=0)

        if result and "access_token" in result:
            if self._cache and self._cache.has_state_changed:
                self.store.write(self._cache.serialize())
            return result["access_token"]
        
        return None

    def fetch_emails(self, limit: Optional[int] = None, folder: str = "inbox", date: Optional[datetime.date] = None) -> list[BaseEmail]:
        """Fetches the latest emails from the Graph API."""
        token = self._get_access_token()
        if not token:
            return []

        headers = {'Authorization': f'Bearer {token}'}
        
        # Determine endpoint and filtering based on the requested folder
        base_url = "https://graph.microsoft.com/v1.0/me"
        if folder == "junk":
            endpoint = f"{base_url}/mailFolders/junkemail/messages"
        else:
            endpoint = f"{base_url}/messages"

        query_params = []
        filter_conditions = []

        if limit is not None:
            query_params.append(f"$top={limit}")
        else:
            query_params.append(f"$top=999") # Graph API max page size is 100, but we can request more and it will return up to 100.
        query_params.append("$select=subject,from,receivedDateTime,bodyPreview")

        if folder == "unread":
            filter_conditions.append("isRead eq false")
        if date:
            date_str = date.isoformat() + "T00:00:00Z"
            next_day = date + datetime.timedelta(days=1)
            next_day_str = next_day.isoformat() + "T00:00:00Z"
            filter_conditions.append(f"receivedDateTime ge {date_str} and receivedDateTime lt {next_day_str}")

        if filter_conditions:
            query_params.append(f"$filter={' and '.join(filter_conditions)}")
            
        full_url = f"{endpoint}?{'&'.join(query_params)}"
        
        try:
            response = requests.get(full_url, headers=headers, timeout=10)
            response.raise_for_status()
            
            emails = []
            for e in response.json().get('value', []):
                # Safe extraction of nested sender name
                sender_info = e.get('from', {}).get('emailAddress', {})
                sender_name = sender_info.get('name') or sender_info.get('address', 'Unknown')
                
                emails.append(BaseEmail(
                    source="Outlook",
                    sender=sender_name,
                    subject=e.get('subject', 'No Subject'),
                    body=e.get('bodyPreview', '')
                ))
            return emails
        except Exception as e:
            logger.error(f"Error fetching Outlook emails: {e}")
            return []

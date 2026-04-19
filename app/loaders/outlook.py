import os
import msal
import requests
from core.schema import BaseEmail
from core.persistence import TokenStore

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
            result = app.acquire_token_silent(self.scopes, account=accounts[0])

        if not result:
            result = app.acquire_token_interactive(scopes=self.scopes, port=0)

        if result and "access_token" in result:
            if self._cache and self._cache.has_state_changed:
                self.store.write(self._cache.serialize())
            return result["access_token"]
        
        return None

    def fetch_emails(self, limit: int = 10) -> list[BaseEmail]:
        """Fetches the latest emails from the Graph API."""
        token = self._get_access_token()
        if not token:
            return []

        headers = {'Authorization': f'Bearer {token}'}
        # Graph API Endpoint for the current user's messages
        endpoint = f"https://graph.microsoft.com/v1.0/me/messages?$top={limit}&$select=subject,from,receivedDateTime,bodyPreview"
        
        response = requests.get(endpoint, headers=headers)
        
        if response.status_code == 200:
            raw_data = response.json().get('value', [])
            return [
                BaseEmail(
                    source="Outlook",
                    sender=e['from']['emailAddress']['name'],
                    subject=e['subject'],
                    body=e.get('bodyPreview', '')
                ) for e in raw_data
            ]
        else:
            print(f"Error fetching emails: {response.status_code}")
            print(response.json())
            return []

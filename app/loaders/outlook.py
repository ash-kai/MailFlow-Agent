import os
import msal
import requests
from dotenv import load_dotenv
from core.schema import BaseEmail

load_dotenv()

CLIENT_ID = os.getenv("OUTLOOK_CLIENT_ID")
TENANT_ID = os.getenv("OUTLOOK_TENANT_ID", "common")
AUTHORITY = f"https://login.microsoftonline.com/{TENANT_ID}"

# The scope for Microsoft Graph API to read emails
SCOPES = ["Mail.Read", "User.Read"]

def get_access_token():
    app = msal.PublicClientApplication(
        CLIENT_ID,
        authority=AUTHORITY
    )
    
    # Attempt to get token from local cache first
    accounts = app.get_accounts()
    if accounts:
        print("Found account in cache, attempting silent token acquisition...")
        result = app.acquire_token_silent(SCOPES, account=accounts[0])
        if result:
            return result.get("access_token")

    # If no cache or silent fail, open the browser
    print("No valid token found. Opening browser for interactive login...")
    result = app.acquire_token_interactive(
    	scopes=SCOPES,
    	port=0 # Let the OS pick a free port for the redirect
    )

    if "access_token" in result:
        return result["access_token"]
    else:
        # Debugging the error if it fails
        print(f"Auth Error: {result.get('error')}")
        print(f"Description: {result.get('error_description')}")
        return None


class OutlookLoader:
    def fetch_emails(self, limit: int = 10) -> list[BaseEmail]:
        """Fetches the latest emails from the Graph API."""
        token = get_access_token()
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

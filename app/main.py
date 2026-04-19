from dotenv import load_dotenv
load_dotenv()

from loaders.gmail import GmailLoader
from core.chains import generate_digest
from core.schema import BaseEmail, EmailLoader
from typing import List

def run_agent():
    # We explicitly type hint this list with our Protocol
    loaders: List[EmailLoader] = [
        GmailLoader()
    ]
    
    all_emails: List[BaseEmail] = []
    
    for loader in loaders:
        print(f"📥 Fetching via {loader.__class__.__name__}...")
        emails = loader.fetch_emails(limit=5)
        all_emails.extend(emails)

    print(f"🧠 Processing {len(all_emails)} total emails...")
    digest = generate_digest(all_emails) 
    print("\n--- Daily Digest ---")
    print(f"Summary: {digest.summary}\n")
    for insight in digest.insights:
        print(f"Subject: {insight.subject}")
        print(f"Sender: {insight.sender}")
        print(f"Priority: {insight.priority}")
        print(f"Category: {insight.category}")
        print(f"Action Item: {insight.action_item}\n")
        
if __name__ == "__main__":
    run_agent()
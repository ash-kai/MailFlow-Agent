import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

from dotenv import load_dotenv
load_dotenv()

import datetime
from loaders.gmail import GmailLoader
from loaders.outlook import OutlookLoader
from core.chains import generate_digest
from core.schema import BaseEmail, EmailLoader
from core.persistence import TokenStore
from typing import List

def run_agent():
    # We explicitly type hint this list with our Protocol
    loaders: List[EmailLoader] = [
        GmailLoader(token_store=TokenStore("MailflowAgent", "Gmail", "gmail_token.json")),
        OutlookLoader(token_store=TokenStore("MailflowAgent", "Outlook", "outlook_token.json"))
    ]
    
    all_emails: List[BaseEmail] = []
    
    for loader in loaders:
        logger.info(f"📥 Fetching via {loader.__class__.__name__}...")
        try:
            emails = loader.fetch_emails(limit=None, date=datetime.date.today()) # Fetch all emails for today
            all_emails.extend(emails)
        except Exception as e:
            logger.error(f"❌ Critical error in {loader.__class__.__name__}: {e}")

    logger.info(f"🧠 Processing {len(all_emails)} total emails...")
    digest = generate_digest(all_emails) 
    logger.info("\n--- Daily Digest ---")
    logger.info(f"Summary: {digest.summary}\n")
    for insight in digest.insights:
        logger.info(f"Subject: {insight.subject}")
        logger.info(f"Sender: {insight.sender}")
        logger.info(f"Priority: {insight.priority}")
        logger.info(f"Category: {insight.category}")
        logger.info(f"Action Item: {insight.action_item}\n")
        
if __name__ == "__main__":
    run_agent()
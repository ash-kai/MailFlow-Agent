from pydantic import BaseModel, Field
from typing import List, Protocol, Optional
import datetime

class EmailInsight(BaseModel):
    subject: str = Field(..., description="Summarized subject of the email")
    sender: str = Field(..., description="Who sent the email")
    priority: str = Field(..., description="1-10 scale of importance")
    category: str = Field(..., description="Work, personal, newsletter or urgent etc.")
    action_item: str = Field(..., description="A brief description of what needs to be done, if anything")
    
class DailyDigest(BaseModel):
    summary: str = Field(..., description="A brief summary of the day's emails")
    enhanced_summary: str = Field(..., description="A detailed, thematic summary of the day's emails, grouping important threads and categories")
    insights: List[EmailInsight] = Field(..., description="A list of insights for the day")
    
class BaseEmail(BaseModel):
    message_id: str = Field(..., description="Unique identifier for the email")
    source: str = Field(..., description="Email provider, e.g. Gmail or Outlook")
    sender: str = Field(..., description="Who sent the email")
    subject: str = Field(..., description="The subject line of the email")
    body: str = Field(..., description="A preview or snippet of the email body")
    received_at: datetime.datetime = Field(..., description="Timestamp of when the email was received")

class EmailLoader(Protocol):
    def fetch_emails(self, limit: Optional[int] = None, folder: str = "inbox", date: Optional[datetime.date] = None) -> list[BaseEmail]:
        """Interface for email fetching logic."""
        ...

class DigestAnalyst(Protocol):
    def generate(self, email_data: str) -> DailyDigest:
        """Interface for LLM analysis logic."""
        ...
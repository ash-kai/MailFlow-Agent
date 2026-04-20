from pydantic import BaseModel, Field
from typing import List, Protocol

class EmailInsight(BaseModel):
    subject: str = Field(..., description="Summarized subject of the email")
    sender: str = Field(..., description="Who sent the email")
    priority: str = Field(..., description="1-10 scale of importance")
    category: str = Field(..., description="Work, personal, newsletter or urgent etc.")
    action_item: str = Field(..., description="A brief description of what needs to be done, if anything")
    
class DailyDigest(BaseModel):
    summary: str = Field(..., description="A brief summary of the day's emails")
    insights: List[EmailInsight] = Field(..., description="A list of insights for the day")
    
class BaseEmail(BaseModel):
    source: str = Field(..., description="Email provider, e.g. Gmail or Outlook")
    sender: str = Field(..., description="Who sent the email")
    subject: str = Field(..., description="The subject line of the email")
    body: str = Field(..., description="A preview or snippet of the email body")

class EmailLoader(Protocol):
    def fetch_emails(self, limit: int = 10) -> list[BaseEmail]:
        """Interface for email fetching logic."""
        ...

class DigestAnalyst(Protocol):
    def generate(self, email_data: str) -> DailyDigest:
        """Interface for LLM analysis logic."""
        ...
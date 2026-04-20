from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from .schema import DailyDigest, BaseEmail, DigestAnalyst
import os
from typing import cast, Optional
import logging

logger = logging.getLogger(__name__)

# This is now a decoupled, reusable prompt template
DEFAULT_DIGEST_PROMPT = ChatPromptTemplate.from_messages([
    ("system", "You are a highly efficient executive assistant. Your task is to analyze the following list of emails and create a structured daily digest."),
    ("user", "Here are the emails from the last 24 hours: \n\n {email_data}")
])

class GeminiAnalyst:
    """Google Gemini implementation of the DigestAnalyst."""
    def __init__(self, model_name: Optional[str] = None, prompt: Optional[ChatPromptTemplate] = None):
        self.model_name = model_name or os.getenv("GOOGLE_LLM_MODEL", "gemini-1.5-flash")
        self.prompt = prompt or DEFAULT_DIGEST_PROMPT
        
        self.llm = ChatGoogleGenerativeAI(
            model=self.model_name,
            temperature=0,
            google_api_key=os.getenv("GOOGLE_API_KEY")
        ).with_structured_output(DailyDigest)

    def generate(self, email_data: str) -> DailyDigest:
        logger.info(f"Invoking Gemini model: {self.model_name}")
        chain = self.prompt | self.llm
        try:
            response = chain.invoke({"email_data": email_data})
            return cast(DailyDigest, response)
        except Exception as e:
            logger.error(f"Gemini generation failed: {e}")
            return DailyDigest(summary="Error generating summary. Please check logs.", insights=[])

def generate_digest(emails: list[BaseEmail], analyst: Optional[DigestAnalyst] = None) -> DailyDigest:
    """Orchestrates the conversion of raw emails into a DailyDigest."""
    if not emails:
        return DailyDigest(summary="No emails found to process.", insights=[])

    logger.info(f"Preparing digest for {len(emails)} emails")

    # Step 1: Format data (This stays here as it is independent of the LLM choice)
    email_strings = [
        f"Source: {e.source} | From: {e.sender} | Subject: {e.subject} | Preview: {e.body}"
        for e in emails
    ]
    formatted_data = "\n---\n".join(email_strings)
       
    # Step 2: Use the provided analyst (defaulting to Gemini)
    if analyst is None:
        analyst = GeminiAnalyst()
    
    return analyst.generate(formatted_data)
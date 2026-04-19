from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from .schema import DailyDigest, BaseEmail
import os
from typing import cast

model_name = os.getenv("GOOGLE_LLM_MODEL", "gemini-3-flash-preview")

def generate_digest(emails: list[BaseEmail]) -> DailyDigest:
    llm = ChatGoogleGenerativeAI(
        model=model_name,
        temperature=0,
        google_api_key=os.getenv("GOOGLE_API_KEY")
        )
    
    structured_llm = llm.with_structured_output(DailyDigest)
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a highly efficient executive assistant. Your task is to analyze the following list of emails and create a structured daily digest."),
        ("user", "Here are the emails from the last 24 hours: \n\n {email_data}")
    ])
    
    # 1. Prepare data using a list comprehension + join
    email_strings = [
        f"Source: {e.source} | From: {e.sender} | Subject: {e.subject} | Preview: {e.body}"
        for e in emails
    ]
    formatted_data = "\n---\n".join(email_strings)
       
    #Run the chain
    chain = prompt | structured_llm
    response = chain.invoke({"email_data": formatted_data})
    return cast(DailyDigest, response)
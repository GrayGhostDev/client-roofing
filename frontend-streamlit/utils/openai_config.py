"""
OpenAI Configuration for Streamlit Application
Enables GPT-4o integration for all AI features
"""

import os
from typing import Optional
from openai import AsyncOpenAI, OpenAI

# Load API key from environment
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Initialize clients
openai_async_client: Optional[AsyncOpenAI] = None
openai_sync_client: Optional[OpenAI] = None

if OPENAI_API_KEY:
    openai_async_client = AsyncOpenAI(api_key=OPENAI_API_KEY)
    openai_sync_client = OpenAI(api_key=OPENAI_API_KEY)


def get_async_client() -> Optional[AsyncOpenAI]:
    """Get async OpenAI client for async operations"""
    return openai_async_client


def get_sync_client() -> Optional[OpenAI]:
    """Get sync OpenAI client for synchronous operations"""
    return openai_sync_client


def is_openai_configured() -> bool:
    """Check if OpenAI API is properly configured"""
    return OPENAI_API_KEY is not None and len(OPENAI_API_KEY) > 0


def get_openai_status() -> dict:
    """Get OpenAI configuration status"""
    return {
        "configured": is_openai_configured(),
        "api_key_set": OPENAI_API_KEY is not None,
        "model": "gpt-4o",
        "features_enabled": {
            "call_transcription": is_openai_configured(),
            "conversation_summarization": is_openai_configured(),
            "action_item_extraction": is_openai_configured(),
            "sentiment_analysis": is_openai_configured(),
            "email_personalization": is_openai_configured(),
            "subject_line_generation": is_openai_configured(),
            "email_quality_scoring": is_openai_configured(),
        }
    }


# GPT-4o Model Configuration
GPT4O_CONFIG = {
    "model": "gpt-4o",
    "max_tokens": 1000,
    "temperature": 0.7,
    "top_p": 0.9,
}

# Whisper API Configuration
WHISPER_CONFIG = {
    "model": "whisper-1",
    "language": "en",
    "response_format": "json",
}

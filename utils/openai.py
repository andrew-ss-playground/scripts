"""
Utility for interacting with the OpenAI API.
"""

import os
import logging
from typing import Optional
from openai import OpenAI
from dotenv import load_dotenv

logger = logging.getLogger(__name__)
logging.getLogger("httpx").setLevel(logging.WARNING)  # Suppress httpx info logs

load_dotenv()

OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4.1-nano")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not OPENAI_API_KEY:
    logger.error("OPENAI_API_KEY environment variable not set.")
    raise EnvironmentError("OPENAI_API_KEY environment variable not set.")

_client: Optional[OpenAI] = None

def get_client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(api_key=OPENAI_API_KEY)
    return _client

def ask_openai(prompt: str, model: Optional[str] = None) -> Optional[str]:
    """
    Get a response from the OpenAI API for a given prompt.

    Args:
        prompt (str): The input prompt to send to the model.
        model (Optional[str]): The model to use. Defaults to OPENAI_MODEL.

    Returns:
        Optional[str]: The model's response, or None if an error occurred.
    """
    model = model or OPENAI_MODEL
    try:
        client = get_client()
        response = client.responses.create(model=model, input=prompt)
        return getattr(response, "output_text", None)
    except Exception as error:
        logger.error(f"Error querying OpenAI: {error}")
        return None

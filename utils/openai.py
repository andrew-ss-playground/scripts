from openai import OpenAI
from dotenv import load_dotenv
import os
import logging

OPENAI_MODEL="gpt-4.1-nano"

logging.getLogger("httpx").setLevel(logging.WARNING) # prevent openai info logging

load_dotenv()
client = OpenAI(api_key=os.getenv("OPEN_AI_KEY"))

def ask_openai(input: str) -> str | None:
    try:
        return client.responses.create(model=OPENAI_MODEL, input=input).output_text
    except Exception as error_message:
        raise Exception(f"Error asking ChatGPT: {error_message}")

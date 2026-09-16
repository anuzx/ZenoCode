import os

from dotenv import load_dotenv
from openai import OpenAI

from src.tools import TOOL_SCHEMAS

load_dotenv()

client = OpenAI(base_url=os.getenv("BASE_URL"), api_key=os.getenv("API_KEY"))


def call_llm(messages):
    response = client.chat.completions.create(
        model="openrouter/free",
        messages=messages,
        tools=TOOL_SCHEMAS,
    )
    message = response.choices[0].message
    return message

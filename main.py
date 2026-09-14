import os

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(base_url=os.getenv("BASE_URL"), api_key=os.getenv("API_KEY"))

user_input = input("Enter your prompt >")

SYSTEM_PROMPT = """you are a coding agent. your job is to code. always code."""

response = client.chat.completions.create(
    model="openrouter/free",
    messages=[
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_input},
    ],
)

output = response.choices[0].message.content

print("\n Agent: ", output, "\n")

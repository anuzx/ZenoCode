import os
import subprocess

from dotenv import load_dotenv
from openai import OpenAI
from openai.lib import _tools

load_dotenv()

client = OpenAI(base_url=os.getenv("BASE_URL"), api_key=os.getenv("API_KEY"))

user_input = input("Enter your prompt >")

SYSTEM_PROMPT = """you are a coding agent. your job is to code. always code.
use the bash tool to inspect files.
answer backe to the user once exploration is done"""

# function tool
BASH_TOOL = {
    "type": "function",
    "function": {
        "name": "bash",
        "description": "Run a shell command and return its output.",
        "parameters": {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "The shell command to run",
                }
            },
            "required": ["command"],
        },
    },
}


# bash function
def bash(command):
    #run bash commands
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    return result.stdout + result.stderr


response = client.chat.completions.create(
    model="openrouter/free",
    messages=[
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_input},
    ],
    tools=[BASH_TOOL],
)

message = response.choices[0].message
output = message.content
tool_calls = message.tool_calls

print("\n Agent: ", output, "\n")

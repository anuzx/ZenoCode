import json

from main import call_llm
from tools import TOOLS

SYSTEM_PROMPT = """you are a coding agent. your job is to code. always code.
use the bash tool to inspect files.
answer back to the user once exploration is done"""


def main():
    user_input = input("Enter your prompt >")

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_input},
    ]

    while True:
        message = call_llm(messages)
        messages.append(message.model_dump(exclude_none=True))

        if message.content:
            print("\nAgent: ", message.content, "\n")

        if not message.tool_calls:
            break

        for tool_call in message.tool_calls:
            args = json.loads(tool_call.function.arguments)
            result = TOOLS[tool_call.function.name](**args)
            print("Tool: ", tool_call.function.name, args)
            print(result, "\n")

            messages.append(
                {"role": "tool", "tool_call_id": tool_call.id, "content": result}
            )


if __name__ == "__main__":
    main()

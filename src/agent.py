import json

from src.context import reminder
from src.main import call_llm
from src.tools import TOOLS

SYSTEM_PROMPT = """you are a coding agent. your job is to code. always code.
use the bash tool to inspect files.
answer back to the user once exploration is done"""


def main():
    while True:
        user_input = input("Enter your prompt >")

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_input},
        ]

        while True:
            # ask the llm to do something
            message = call_llm(messages + [reminder()])
            # save its response to conversation
            messages.append(message.model_dump(exclude_none=True))

            # show its text to the user
            if message.content:
                print("\nAgent: ", message.content, "\n")

            # if it doesn't want any tools,break the loop
            if not message.tool_calls:
                break

            # execute every tool requested by the llm
            for tool_call in message.tool_calls:
                # conver json string to object
                args = json.loads(tool_call.function.arguments)

                # find the actual fxn and execute it
                result = TOOLS[tool_call.function.name](**args)

                # show the result
                print("Tool: ", tool_call.function.name, args)
                print(result, "\n")

                # give the result back to llm
                messages.append(
                    {"role": "tool", "tool_call_id": tool_call.id, "content": result}
                )


if __name__ == "__main__":
    main()

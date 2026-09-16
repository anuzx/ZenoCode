import json

from src.context import reminder
from src.main import call_llm
from src.sandbox import name as sandbox_name
from src.tools import TOOLS
from src.tui.ui import ui

SYSTEM_PROMPT = """you are a coding agent. your job is to code. always code.
use the bash tool to inspect files.
answer back to the user once exploration is done"""


def main():
    ui.banner(sandbox_name())
    while True:
        user_input = ui.ask()
        if not user_input:
            break

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_input},
        ]

        while True:
            with ui.working():
                message = call_llm(messages + [reminder()])
            messages.append(message.model_dump(exclude_none=True))

            if message.content:
                ui.agent(message.content)

            if not message.tool_calls:
                break

            for tool_call in message.tool_calls:
                args = json.loads(tool_call.function.arguments)
                result = TOOLS[tool_call.function.name](**args)
                ui.tool(tool_call.function.name, args, result)
                messages.append(
                    {"role": "tool", "tool_call_id": tool_call.id, "content": result}
                )


if __name__ == "__main__":
    main()

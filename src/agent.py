import os

from src.context import reminder
from src.main import call_llm
from src.sandbox import name as sandbox_name
from src.subagent import TASK_SCHEMA, task
from src.todos import TODO_SCHEMA, write_todos
from src.tools import TOOLS, TOOL_SCHEMAS, execute
from src.tui.ui import ui

ALL_SCHEMAS = TOOL_SCHEMAS + [TODO_SCHEMA, TASK_SCHEMA]
ALL_TOOLS = {**TOOLS, "write_todos": write_todos, "task": task}

SYSTEM_PROMPT = f"""
You are a coding agent. Your job is to code. Always code.
Use the bash tool to inspect files.
Use write_file to create files and str_replace to edit them.
Answer back to the user once exploration is done.

For any task that takes more than one step, call write_todos first and plan it
out. Send the whole list every time you call it - it replaces the old one.
Keep exactly one task in_progress, mark it done the moment it is finished, and
move the next one to in_progress in the same call. Do not batch up completions
at the end. Skip the tool entirely for single-step tasks; it is noise there.

The current list is injected back to you every turn inside <todos> tags, so
that block - not the transcript - is the truth about where you are.

When you need to understand how something works - where a feature lives, how
data flows, what calls what - send a task subagent instead of grepping your
way there yourself. It explores in its own context window and hands you back
just the findings, so the search does not fill yours. It cannot see this
conversation, so write the question so it stands alone. Do all editing
yourself; the subagent only reads.

Long tool output is cut short, and the whole thing is written to a temp file
whose path is given at the cut. Page through it with head, tail, sed -n or
grep rather than asking for it again. That file only exists for the current
turn, so read it now or re-run the command later.

Your current working directory is: {os.getcwd()}

"""


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
                message, usage = call_llm(messages + [reminder()], tools=ALL_SCHEMAS)
            messages.append(message.model_dump(exclude_none=True))
            ui.usage(usage)

            if message.content:
                ui.agent(message.content)

            if not message.tool_calls:
                break

            for tool_call in message.tool_calls:
                args, result = execute(tool_call, tools=ALL_TOOLS)
                ui.tool(tool_call.function.name, args, result)
                messages.append(
                    {"role": "tool", "tool_call_id": tool_call.id, "content": result}
                )


if __name__ == "__main__":
    main()

import json
import os

from src import session
from src.commands import COMMANDS, handle
from src.commands import compact as run_compact
from src.core.compact import needed
from src.core.context import reminder
from src.core.history import cap, strip, sweep
from src.core.todos import TODO_SCHEMA, write_todos
from src.main import call_llm
from src.safety.permissions import check
from src.safety.sandbox import name as sandbox_name
from src.subagent import TASK_SCHEMA, task
from src.tools import TOOL_SCHEMAS, TOOLS, execute
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
    messages = session.open_session(session.CURRENT) or []
    if messages:
        ui.replay(messages)

    while True:
        user_input = ui.ask()
        if not user_input:
            break

        if user_input.startswith("/"):
            messages = handle(user_input.split()[0], messages)
            continue

        messages.append({"role": "user", "content": user_input})
        session.save(messages)

        while True:
            with ui.working():
                message, usage = call_llm(messages + [reminder()], tools=ALL_SCHEMAS)
            messages.append(message.model_dump(exclude_none=True))
            session.save(messages)
            ui.usage(usage)

            if message.content:
                ui.agent(message.content)
            if not message.tool_calls:
                # The turn is over: whatever tool output is sitting unlocked
                # in the transcript is now just history, not something the
                # model needs in full any more. Shrink it, and drop the temp
                # files cap() spilled for those results, before waiting on
                # the next user message.
                strip(messages)
                sweep()
                session.save(messages)
                break

            for tool_call in message.tool_calls:
                args = json.loads(tool_call.function.arguments)
                action, reason = check(tool_call.function.name, args)
                if action == "deny":
                    result = f"Blocked by policy: {reason}"
                elif action == "ask" and not ui.approve(reason):
                    result = "User declined this action."
                else:
                    _, result = execute(tool_call, tools=ALL_TOOLS)
                ui.tool(tool_call.function.name, args, result)
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": cap(result),
                    }
                )
            session.save(messages)

            # The request that just went out is the freshest read we have on
            # how full the window is. If it crossed the line, compact now,
            # before the next call, rather than waiting for /compact.
            if needed(usage):
                messages = run_compact(messages)


if __name__ == "__main__":
    main()

# function tool

import json

from src.context import note_read
from src.sandbox import run


# bash function
def bash(command: str) -> str:
    # run bash commands
    result = run(command)
    return result.stdout + result.stderr


# read_file function
def read_file(path: str) -> str:
    # read a file and return its content
    note_read(path)#updates the mtime whenever the read_file tool is used
    with open(path) as f:
        return f.read()


# write file function
def write_file(path: str, content: str) -> str:
    # create a file ,or overwrite it if it already exists
    with open(path, "w") as f:
        f.write(content)
    return f"Wrote {path}"


# replace a code function
def str_replace(path, old_str, new_str, allow_multi_edit=False):
    # swap exact text in a file, old_str must match exactly once
    with open(path) as f:
        content = f.read()

    count = content.count(old_str)
    if count == 0:
        return f"Error: old_str was not found in {path}"
    if count > 1 and not allow_multi_edit:
        return (
            f"Error : old_str matches {count} times in {path}."
            "Add surrounding lines to make it unique, "
            "or set allow_multi_edit to replace them all."
        )

    with open(path, "w") as f:
        f.write(content.replace(old_str, new_str))
    return f"Replaced {count} match(es) in {path}"


TOOL_SCHEMAS = [
    {
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
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read a file and return its contents",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "path to the file to read",
                    }
                },
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Create a file, or overwrite it if it already exists.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "File to write"},
                    "content": {"type": "string", "description": "The full contents"},
                },
                "required": ["path", "content"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "str_replace",
            "description": (
                "Replace exact text in a file. old_str must appear exactly once, "
                "so include surrounding lines if needed."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "File to edit"},
                    "old_str": {"type": "string", "description": "Exact text to find"},
                    "new_str": {
                        "type": "string",
                        "description": "Text to put in its place",
                    },
                    "allow_multi_edit": {
                        "type": "boolean",
                        "description": "Replace every match instead of failing",
                    },
                },
                "required": ["path", "old_str", "new_str"],
            },
        },
    },
]

TOOLS = {
    "bash": bash,
    "read_file": read_file,
    "write_file": write_file,
    "str_replace": str_replace,
}


def execute(tool_call, tools=None):
    lookup = tools or TOOLS
    args = json.loads(tool_call.function.arguments)
    result = lookup[tool_call.function.name](**args)
    return args, result

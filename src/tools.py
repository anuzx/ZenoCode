# function tool
import subprocess

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
]


# bash function
def bash(command: str) -> str:
    # run bash commands
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    return result.stdout + result.stderr


# read_file function
def read_file(path: str) -> str:
    # read a file and return its content
    with open(path) as f:
        return f.read()


TOOLS = {
    "bash": bash,
    "read_file": read_file,
}

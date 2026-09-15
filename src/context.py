import os
import subprocess

# alert the agent if a file has changed since it last read it ,this prevents the agent from editing based on stale info

SEEN = {}  # path -> mtime(modification time) when the agent last read it


# fxn to remember when the file was last modified
def note_read(path: str):
    SEEN[path] = os.path.getmtime(path)


# while files have changed since the agent last read them (p is file path here)
def stale_files():
    changed = []

    for p, mtime in SEEN.items():
        if not os.path.exists(p):
            changed.append(p)
        elif os.path.getmtime(p) != mtime:
            changed.append(p)

    return changed


def git(command):
    result = subprocess.run(
        f"git {command}", shell=True, capture_output=True, text=True
    )
    return result.stdout


# creates a warning that we send eventually to the llm
def stale_note():
    """warn about files that changed on disk since the agent read them"""
    changed = stale_files()
    if not changed:
        return ""
    return (
        "\n<system-reminder>\n"
        "These files changed since your last turn. Read them again before "
        "editing:\n" + "\n".join(changed) + "\n</system-reminder>"
    )

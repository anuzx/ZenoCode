"""Kernel-enforced limits on what bash can touch.

One policy - read anything, write only inside the project, no network - and a
different enforcement mechanism per OS. The idea ports; the mechanism never does.

"""

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

PROJECT = Path.cwd().resolve()

PROFILE = f"""(version 1)
(deny default)
(allow process-exec process-fork signal)
(allow file-read*)
(allow sysctl-read)
(deny network*)
(allow file-write* (subpath "{PROJECT}") (literal "/dev/null"))
(deny file-write* (subpath "{PROJECT}/.git"))
"""


def wrap(command):
    """Wrap a shell command in an OS sandbox. None means we have no sandbox."""
    if sys.platform == "darwin":
        handle = tempfile.NamedTemporaryFile(mode="w", suffix=".sb", delete=False)
        handle.write(PROFILE)
        handle.close()
        return ["sandbox-exec", "-f", handle.name, "/bin/sh", "-c", command]

    if sys.platform.startswith("linux") and shutil.which("bwrap"):
        return [
            "bwrap",
            "--ro-bind",
            "/",
            "/",  # whole filesystem read-only...
            "--bind",
            str(PROJECT),
            str(PROJECT),  # ...except the project, read-write
            "--ro-bind",
            str(PROJECT / ".git"),
            str(PROJECT / ".git"),  # ...and .git within it, back to read-only
            "--dev",
            "/dev",
            "--proc",
            "/proc",
            "--tmpfs",
            "/tmp",
            "--unshare-net",  # no network
            "--unshare-pid",  # isolate process tree
            "--die-with-parent",
            "/bin/sh",
            "-c",
            command,
        ]

    return None  # Windows, or Linux without bubblewrap


def name():
    if sys.platform == "darwin":
        return "seatbelt"
    if sys.platform.startswith("linux") and shutil.which("bwrap"):
        return "bubblewrap"
    return "none"


def run(command, timeout=60):
    """Run a command, sandboxed when the OS lets us."""
    sandboxed = wrap(command)
    return subprocess.run(
        sandboxed or command,
        shell=sandboxed is None,
        capture_output=True,
        text=True,
        timeout=timeout,
    )

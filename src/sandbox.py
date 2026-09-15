"""Kernel-enforced limits on what bash can touch — Linux edition.

Policy: read anything, write only inside the project, no network.
Enforced via bubblewrap (bwrap), which uses Linux namespaces to sandbox
the process. Falls back to unsandboxed execution if bwrap isn't installed.
"""

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

PROJECT = Path.cwd().resolve()


def wrap(command):
    """Wrap a shell command in a Linux sandbox (bubblewrap). None if unavailable."""
    if not shutil.which("bwrap"):
        return None

    return [
        "bwrap",
        "--ro-bind",
        "/",
        "/",  # whole filesystem read-only...
        "--bind",
        str(PROJECT),
        str(PROJECT),  # ...except the project, read-write
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


def name():
    if shutil.which("bwrap"):
        return "bubblewrap"
    return "none"


def run(command, timeout=60):
    """Run a command, sandboxed when bubblewrap is available."""
    sandboxed = wrap(command)
    return subprocess.run(
        sandboxed or command,
        shell=sandboxed is None,
        capture_output=True,
        text=True,
        timeout=timeout,
    )

"""Kernel-enforced limits on what bash can touch.

One policy - read anything, write only inside the project, no network - and a
different enforcement mechanism per OS. The idea ports; the mechanism never does.

One exception: package managers (bun, npm, pip, ...) cannot work without the
network and their download cache. Those commands still cannot write outside the
project, but they get the network and write access to the cache folders. They
are never auto-allowed by permissions.py, so you approve each one first.
"""

import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

PROJECT = Path.cwd().resolve()
HOME = Path.home()

# First word of a command that needs the network to do its job.
NETWORK_COMMANDS = {
    "bun", "bunx", "npm", "npx", "pnpm", "yarn",
    "pip", "pip3", "uv", "uvx", "cargo",
}

# Caches those tools write to. The first group is created if missing (a fresh
# machine has no ~/.bun yet); the second is only used if it already exists.
CACHE_DIRS = [HOME / ".bun", HOME / ".npm", HOME / ".cache"]
OPTIONAL_CACHE_DIRS = [HOME / ".yarn", HOME / ".local" / "share" / "pnpm", HOME / ".cargo"]


def needs_network(command):
    """True if any part of a compound command starts with a package manager."""
    for part in re.split(r"&&|\|\||;|\|", command):
        words = part.split()
        if words and words[0] in NETWORK_COMMANDS:
            return True
    return False


def cache_dirs():
    for path in CACHE_DIRS:
        path.mkdir(parents=True, exist_ok=True)
    return [p for p in CACHE_DIRS + OPTIONAL_CACHE_DIRS if p.exists()]


def profile(network):
    lines = [
        "(version 1)",
        "(deny default)",
        "(allow process-exec process-fork signal)",
        "(allow file-read*)",
        "(allow sysctl-read)",
        f'(allow file-write* (subpath "{PROJECT}") (literal "/dev/null"))',
    ]
    if network:
        lines += ["(allow network*)", "(allow mach-lookup)"]
        for path in cache_dirs():
            lines.append(f'(allow file-write* (subpath "{path}"))')
        # package managers stage downloads in the temp dir
        lines.append('(allow file-write* (subpath "/private/tmp") (subpath "/private/var/folders"))')
    else:
        lines.append("(deny network*)")
    lines.append(f'(deny file-write* (subpath "{PROJECT}/.git"))')
    return "\n".join(lines) + "\n"


def wrap(command, network=False):
    """Wrap a shell command in an OS sandbox. None means we have no sandbox."""
    if sys.platform == "darwin":
        handle = tempfile.NamedTemporaryFile(mode="w", suffix=".sb", delete=False)
        handle.write(profile(network))
        handle.close()
        return ["sandbox-exec", "-f", handle.name, "/bin/sh", "-c", command]

    if sys.platform.startswith("linux") and shutil.which("bwrap"):
        args = [
            "bwrap",
            "--ro-bind", "/", "/",  # whole filesystem read-only...
            "--dev", "/dev",
            "--proc", "/proc",
            "--tmpfs", "/tmp",
            "--bind", str(PROJECT), str(PROJECT),  # ...except the project, read-write
        ]
        # bwrap aborts if the source path is missing, and not every project
        # is a git repo - so only protect .git when it exists.
        git = PROJECT / ".git"
        if git.exists():
            args += ["--ro-bind", str(git), str(git)]  # .git back to read-only

        if network:
            for path in cache_dirs():
                args += ["--bind", str(path), str(path)]
        else:
            args.append("--unshare-net")  # no network

        args += ["--unshare-pid", "--die-with-parent", "/bin/sh", "-c", command]
        return args

    return None  # Windows, or Linux without bubblewrap


def name():
    if sys.platform == "darwin":
        return "seatbelt"
    if sys.platform.startswith("linux") and shutil.which("bwrap"):
        return "bubblewrap"
    return "none"


def run(command, timeout=60):
    """Run a command, sandboxed when the OS lets us."""
    network = needs_network(command)
    if network:
        timeout = max(timeout, 300)  # installs are slow
    sandboxed = wrap(command, network)
    return subprocess.run(
        sandboxed or command,
        shell=sandboxed is None,
        capture_output=True,
        text=True,
        timeout=timeout,
    )

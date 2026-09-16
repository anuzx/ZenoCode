"""Settings: real environment variables first, then ~/.agents/env."""

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

ENV_FILE = Path.home() / ".agents" / "env"

if ENV_FILE.exists():
    for line in ENV_FILE.read_text().splitlines():
        if "=" in line and not line.startswith("#"):
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip())

BASE_URL = os.getenv("BASE_URL")
API_KEY = os.getenv("API_KEY")
MODEL = os.getenv("MODEL", "openrouter/free")

# How much room the model has, and how we spend it.
CONTEXT_WINDOW = int(os.getenv("CONTEXT_WINDOW", 128_000))
COMPACT_AT = 0.85  # compact once the prompt crosses this much of the window
COMPACT_TO = 0.35  # and cut back to this much, so it does not retrigger soon

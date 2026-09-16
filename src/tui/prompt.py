import sys


def read(prompt=""):
    try:
        return input(prompt)
    except (EOFError, KeyboardInterrupt):
        raise

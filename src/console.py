from __future__ import annotations

import sys

if sys.platform == "win32":
    import os

    os.system("")
    
BOLD_RED = "\033[1;31m"
RESET = "\033[0m"


def warn(message: str) -> None:
    print(f"{BOLD_RED}{message}{RESET}")


def log_filter(name: str, detail: str, before: int, after: int) -> None:
    print(f"{name} filter: {detail}, removed {before - after}, {after} candidates remain")


def fatal(message: str, code: int = 1) -> None:
    warn(message)
    try:
        input("Press Enter to exit...")
    except EOFError:
        pass
    sys.exit(code)

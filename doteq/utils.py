import os
import shutil
import stat
import sys
import time
from typing import Optional

from colorama import Fore, Style, init as colorama_init


def is_ci_environment() -> bool:
    return os.getenv("CI") == "true" or any(
        os.getenv(var) for var in ["GITHUB_ACTIONS", "GITLAB_CI", "BUILDKITE", "CIRCLECI"]
    )


def backup_file(file_path: str) -> Optional[str]:
    if not os.path.exists(file_path):
        return None
    timestamp = time.strftime("%Y%m%d-%H%M%S")
    backup_path = f"{file_path}.bak.{timestamp}"
    shutil.copy2(file_path, backup_path)
    os.chmod(backup_path, stat.S_IRUSR | stat.S_IWUSR)
    return backup_path


def validate_env_syntax(content: str) -> None:
    lines = content.splitlines()
    for index, line in enumerate(lines, start=1):
        if not line.strip() or line.strip().startswith("#"):
            continue
        if "=" not in line and not line.strip().startswith("export "):
            raise ValueError(f"Syntax error on line {index}: Missing '='")


def colorize_output(text: str, color: str) -> str:
    colorama_init(autoreset=True)
    mapping = {
        "green": Fore.GREEN,
        "yellow": Fore.YELLOW,
        "red": Fore.RED,
        "blue": Fore.BLUE,
        "cyan": Fore.CYAN,
        "magenta": Fore.MAGENTA,
        "white": Fore.WHITE,
        "reset": Style.RESET_ALL,
    }
    prefix = mapping.get(color, "")
    suffix = Style.RESET_ALL if prefix else ""
    return f"{prefix}{text}{suffix}"


def sanitize_for_ci(text: str) -> str:
    return text.replace("\n", " ").replace("\r", " ")


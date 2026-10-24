import re
from pathlib import Path

from pathvalidate import sanitize_filename


def safe_name(value: str, max_len: int = 100) -> str:
    """Return a filesystem-safe version of *value*."""
    cleaned = sanitize_filename(value, replacement_text="_")
    cleaned = re.sub(r"[<>:\"/\\|?*]", "_", cleaned)
    cleaned = cleaned.strip(" .")
    return cleaned[:max_len] if cleaned else "Unknown"


def safe_display(name: str, max_len: int = 40) -> str:
    """Return a truncated, Windows-terminal-safe display string."""
    try:
        name.encode("cp1252")
        safe = name
    except (UnicodeEncodeError, UnicodeDecodeError):
        safe = name.encode("ascii", errors="replace").decode("ascii")
    return (safe[:max_len] + "...") if len(safe) > max_len + 3 else safe

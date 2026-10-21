import re
from pathlib import Path

from pathvalidate import sanitize_filename


def safe_name(value: str, max_len: int = 100) -> str:
    """Return a filesystem-safe version of *value*."""
    cleaned = sanitize_filename(value, replacement_text="_")
    cleaned = re.sub(r"[<>:\"/\\|?*]", "_", cleaned)
    cleaned = cleaned.strip(" .")
    return cleaned[:max_len] if cleaned else "Unknown"

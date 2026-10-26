"""Scan a directory tree and return all audio file paths."""
from pathlib import Path
from typing import Optional

AUDIO_EXTENSIONS: frozenset[str] = frozenset(
    {
        ".mp3", ".flac", ".ogg", ".opus", ".m4a", ".aac",
        ".wav", ".wma", ".ape", ".wv", ".mka", ".aiff", ".aif",
    }
)


def scan(
    directory: Path,
    recursive: bool = True,
    exclude_dirs: Optional[list[Path]] = None,
) -> list[Path]:
    """Return a sorted list of audio files found under *directory*, skipping *exclude_dirs*."""
    pattern = "**/*" if recursive else "*"
    resolved_excludes = [e.resolve() for e in (exclude_dirs or [])]

    files = []
    for p in directory.glob(pattern):
        if not (p.is_file() and p.suffix.lower() in AUDIO_EXTENSIONS):
            continue
        p_resolved = p.resolve()
        if any(p_resolved == ex or ex in p_resolved.parents for ex in resolved_excludes):
            continue
        files.append(p)

    return sorted(files)

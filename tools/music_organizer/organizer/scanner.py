"""Scan a directory tree and return all audio file paths."""
from pathlib import Path
from typing import Iterator

AUDIO_EXTENSIONS: frozenset[str] = frozenset(
    {
        ".mp3", ".flac", ".ogg", ".opus", ".m4a", ".aac",
        ".wav", ".wma", ".ape", ".wv", ".mka", ".aiff", ".aif",
    }
)


def scan(directory: Path, recursive: bool = True) -> list[Path]:
    """Return a sorted list of audio files found under *directory*."""
    pattern = "**/*" if recursive else "*"
    files = [
        p for p in directory.glob(pattern)
        if p.is_file() and p.suffix.lower() in AUDIO_EXTENSIONS
    ]
    return sorted(files)

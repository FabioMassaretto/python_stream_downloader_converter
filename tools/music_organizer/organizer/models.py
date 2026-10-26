from tools.music_organizer.organizer.utils import safe_name
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class SongInfo:
    """Holds all known metadata for an audio file."""

    artist: Optional[str] = None
    album: Optional[str] = None
    title: Optional[str] = None
    track_number: Optional[int] = None
    year: Optional[str] = None
    duration: Optional[float] = None
    # Where the info came from
    source: str = "unknown"  # "tags" | "acoustid" | "musicbrainz" | "filename" | "shazam"

    @property
    def is_organizable(self) -> bool:
        """Minimum requirement: we know artist + title."""
        return bool(self.artist and self.title)

    def dest_path(self, root: Path, original_suffix: str) -> Path:
        """
        Build the target path under *root*:
            root / artist / album (optional) / [NN - ] title.ext
        """


        parts = [safe_name(self.artist)]
        if self.album:
            parts.append(safe_name(self.album))
        else:
            parts.append("Unknown Album")

        stem = safe_name(self.title)
        if self.track_number:
            stem = f"{self.track_number:02d} - {stem}"

        return root.joinpath(*parts) / f"{stem}{original_suffix}"

    def __str__(self) -> str:
        artist = self.artist or "?"
        album = self.album or "?"
        title = self.title or "?"
        return f"{artist} / {album} / {title}  [{self.source}]"

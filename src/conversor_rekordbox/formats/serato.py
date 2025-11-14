from __future__ import annotations

from pathlib import Path
from typing import Iterable

from ..models import Track


def load(path: Path) -> list[Track]:
    """Lee un archivo de playlist M3U/M3U8 compatible con Serato."""

    tracks: list[Track] = []
    pending_info: tuple[int | None, str | None] | None = None
    with path.open("r", encoding="utf-8") as handle:
        for raw_line in handle:
            line = raw_line.strip()
            if not line:
                continue
            if line.startswith("#EXTINF:"):
                pending_info = _parse_extinf(line)
                continue
            if line.startswith("#"):
                continue

            duration, description = pending_info or (None, None)
            artist, title = _split_description(description)

            tracks.append(
                Track(
                    title=title or _guess_title(line),
                    artist=artist or "",
                    duration=duration,
                    location=line,
                )
            )
            pending_info = None
    return tracks


def dump(tracks: Iterable[Track], path: Path) -> None:
    """Escribe un archivo M3U8 con marcas compatibles con Serato."""

    with path.open("w", encoding="utf-8") as handle:
        handle.write("#EXTM3U\n")
        handle.write("#PLAYLIST:Conversor Rekordbox\n")
        for track in tracks:
            duration = int(track.duration or 0)
            handle.write(f"#EXTINF:{duration},{track.artist} - {track.title}\n")
            location = track.location or _build_location(track)
            handle.write(f"{location}\n")


def _guess_title(location: str) -> str:
    file_name = Path(location).stem
    return file_name.replace("_", " ")


def _build_location(track: Track) -> str:
    if track.location:
        return track.location
    sanitized_artist = track.artist.replace(" ", "_") if track.artist else ""
    sanitized_title = track.title.replace(" ", "_") if track.title else "track"
    return f"{sanitized_artist}-{sanitized_title}.mp3".strip("-")


def _parse_extinf(line: str) -> tuple[int | None, str | None]:
    try:
        _, payload = line.split(":", 1)
        duration_str, description = payload.split(",", 1)
        duration = int(duration_str)
        return duration, description.strip()
    except ValueError:
        return None, None


def _split_description(description: str | None) -> tuple[str | None, str | None]:
    if not description:
        return None, None
    if " - " in description:
        artist, title = description.split(" - ", 1)
        return artist.strip(), title.strip()
    return None, description.strip()

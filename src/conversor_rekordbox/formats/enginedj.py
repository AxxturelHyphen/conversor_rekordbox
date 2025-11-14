from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

from ..models import Track


ENGINE_VERSION = "2.4.0"


def load(path: Path) -> list[Track]:
    """Lee la representación JSON simplificada exportada por Engine DJ."""

    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)

    tracks: list[Track] = []
    for entry in data.get("tracks", []):
        tracks.append(
            Track(
                title=entry.get("title", ""),
                artist=entry.get("artist", ""),
                album=entry.get("album"),
                genre=entry.get("genre"),
                duration=entry.get("duration"),
                bpm=entry.get("bpm"),
                comment=entry.get("comment"),
                location=entry.get("location"),
                year=entry.get("year"),
                rating=entry.get("rating"),
            )
        )
    return tracks


def dump(tracks: Iterable[Track], path: Path) -> None:
    """Genera un archivo JSON compatible con Engine DJ (formato simplificado)."""

    payload = {
        "engine_dj_version": ENGINE_VERSION,
        "generated_by": "Conversor Rekordbox",
        "tracks": [
            {
                "title": track.title,
                "artist": track.artist,
                "album": track.album,
                "genre": track.genre,
                "duration": track.duration,
                "bpm": track.bpm,
                "comment": track.comment,
                "location": track.location,
                "year": track.year,
                "rating": track.rating,
            }
            for track in tracks
        ],
    }

    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=False)

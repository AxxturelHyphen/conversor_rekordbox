from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Track:
    """Representa una pista musical dentro de una biblioteca."""

    title: str
    artist: str
    album: str | None = None
    genre: str | None = None
    duration: float | None = None
    bpm: float | None = None
    comment: str | None = None
    location: str | None = None
    year: int | None = None
    rating: int | None = None

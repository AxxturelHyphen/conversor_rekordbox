from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Iterable

from ..models import Track


def load(path: Path) -> list[Track]:
    """Carga pistas desde un archivo XML exportado por Rekordbox."""

    tree = ET.parse(path)
    root = tree.getroot()

    collection = root.find("COLLECTION")
    if collection is None:
        raise ValueError("El archivo de Rekordbox no contiene una colección válida")

    tracks: list[Track] = []
    for track_element in collection.findall("TRACK"):
        attributes = track_element.attrib
        track = Track(
            title=attributes.get("Name", ""),
            artist=attributes.get("Artist", ""),
            album=_empty_to_none(attributes.get("Album")),
            genre=_empty_to_none(attributes.get("Genre")),
            duration=_safe_float(attributes.get("TotalTime")),
            bpm=_safe_float(attributes.get("AverageBpm")),
            comment=_empty_to_none(attributes.get("Comments")),
            location=_empty_to_none(attributes.get("Location")),
            year=_safe_int(attributes.get("Year")),
            rating=_safe_int(attributes.get("Rating")),
        )
        tracks.append(track)
    return tracks


def dump(tracks: Iterable[Track], path: Path) -> None:
    """Genera un archivo XML compatible con Rekordbox."""

    root = ET.Element("DJ_PLAYLISTS")
    root.set("Version", "1.0.0")

    product = ET.SubElement(root, "PRODUCT")
    product.set("Name", "Conversor Rekordbox")
    product.set("Version", "0.1.0")
    product.set("Company", "Conversor Team")

    collection = ET.SubElement(root, "COLLECTION")

    # Materializamos la secuencia para contar y reutilizar los valores.
    track_list = list(tracks)
    collection.set("Entries", str(len(track_list)))

    for track in track_list:
        attrs = {
            "Name": track.title,
            "Artist": track.artist,
        }
        if track.album:
            attrs["Album"] = track.album
        if track.genre:
            attrs["Genre"] = track.genre
        if track.duration is not None:
            attrs["TotalTime"] = str(int(track.duration))
        if track.bpm is not None:
            attrs["AverageBpm"] = f"{track.bpm:.2f}"
        if track.comment:
            attrs["Comments"] = track.comment
        if track.location:
            attrs["Location"] = track.location
        if track.year is not None:
            attrs["Year"] = str(track.year)
        if track.rating is not None:
            attrs["Rating"] = str(track.rating)

        ET.SubElement(collection, "TRACK", attrib=attrs)

    playlists = ET.SubElement(root, "PLAYLISTS")
    playlists.set("Entries", "0")

    tree = ET.ElementTree(root)
    tree.write(path, encoding="utf-8", xml_declaration=True)


def _safe_float(value: str | None) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except ValueError:
        return None


def _safe_int(value: str | None) -> int | None:
    if value is None or value == "":
        return None
    try:
        return int(float(value))
    except ValueError:
        return None


def _empty_to_none(value: str | None) -> str | None:
    if value is None or value.strip() == "":
        return None
    return value

from __future__ import annotations

import json
from pathlib import Path

from conversor_rekordbox.converter import Format, convert_library
from conversor_rekordbox.formats import enginedj, rekordbox, serato

DATA_DIR = Path(__file__).parent / "data"


def test_rekordbox_to_serato(tmp_path: Path) -> None:
    source = DATA_DIR / "sample_rekordbox.xml"
    output = tmp_path / "playlist.m3u8"

    convert_library(source, output)

    tracks = serato.load(output)
    assert len(tracks) == 2
    assert tracks[0].title == "Track One"
    assert tracks[0].location == "file:///music/track1.mp3"


def test_engine_to_rekordbox(tmp_path: Path) -> None:
    source = DATA_DIR / "sample_engine.json"
    output = tmp_path / "library.xml"

    convert_library(source, output)

    tracks = rekordbox.load(output)
    assert len(tracks) == 2
    assert tracks[0].artist == "Artist A"
    assert tracks[1].title == "Track Two"


def test_serato_to_engine(tmp_path: Path) -> None:
    playlist = tmp_path / "crate.m3u8"
    playlist.write_text(
        "\n".join(
            [
                "#EXTM3U",
                "#EXTINF:300,Artist A - Track One",
                "file:///music/track1.mp3",
                "#EXTINF:250,Artist B - Track Two",
                "file:///music/track2.mp3",
            ]
        ),
        encoding="utf-8",
    )

    output = tmp_path / "engine.json"
    convert_library(playlist, output, output_format=Format.ENGINE_DJ)

    with output.open("r", encoding="utf-8") as handle:
        data = json.load(handle)

    assert data["engine_dj_version"] == enginedj.ENGINE_VERSION
    assert len(data["tracks"]) == 2
    assert data["tracks"][0]["location"] == "file:///music/track1.mp3"

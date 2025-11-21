from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from yt_dlp import YoutubeDL

from ..audio.conversion import AudioFormat
from ..utils.logger import get_logger

logger = get_logger()


@dataclass
class SoundCloudCredentials:
    client_id: str | None = None
    client_secret: str | None = None
    oauth_token: str | None = None

    @classmethod
    def from_json(cls, payload: str | Path) -> "SoundCloudCredentials":
        data: dict[str, Any]
        if isinstance(payload, Path):
            data = json.loads(payload.read_text(encoding="utf-8"))
        else:
            data = json.loads(payload)
        return cls(
            client_id=data.get("client_id"),
            client_secret=data.get("client_secret"),
            oauth_token=data.get("oauth_token"),
        )

    def to_json(self) -> str:
        return json.dumps({
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "oauth_token": self.oauth_token,
        }, ensure_ascii=False, indent=2)


class SoundCloudDownloader:
    """Wraps yt-dlp to fetch 320kbps MP3 when possible.

    Even though yt-dlp maneja SoundCloud de forma pública, la clase acepta
    credenciales para escenarios donde el usuario quiera usar la API oficial
    y endpoints autenticados. Los campos se guardan y pueden reutilizarse
    para configurar cookies o cabeceras personalizadas si se requiere
    extender la integración.
    """

    def __init__(self, credentials: SoundCloudCredentials | None = None, output_dir: Path | None = None) -> None:
        self.credentials = credentials or SoundCloudCredentials()
        self.output_dir = output_dir

    def build_options(self, output_dir: Path) -> dict[str, Any]:
        output_dir.mkdir(parents=True, exist_ok=True)
        headers: dict[str, str] = {}
        if self.credentials.oauth_token:
            headers["Authorization"] = f"OAuth {self.credentials.oauth_token}"

        return {
            "outtmpl": {
                "default": str(output_dir / "%(title)s.%(ext)s"),
                "pl_video": str(
                    output_dir
                    / "%(playlist_title)s/%(playlist_index)02d - %(title)s.%(ext)s"
                ),
            },
            "format": "bestaudio/best",
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "320",
                }
            ],
            "http_headers": headers,
            "nocheckcertificate": True,
        }

    def download(self, url: str, output_dir: Path, fmt: AudioFormat = "mp3") -> list[Path]:
        if fmt != "mp3":
            raise ValueError("Solo se admite descarga directa a MP3")

        options = self.build_options(output_dir)
        logger.info("Descargando audio", extra={"url": url, "output": str(output_dir)})
        with YoutubeDL(options) as ydl:
            result = ydl.extract_info(url, download=True)
            return list(self._resolve_targets(result, ydl))

    def _resolve_targets(self, result: Any, ydl: YoutubeDL) -> Iterable[Path]:
        if isinstance(result, dict) and result.get("entries"):
            for entry in result.get("entries") or []:
                if not entry:
                    continue
                filename = Path(ydl.prepare_filename(entry))
                yield self._ensure_mp3_suffix(filename)
            return

        filename = Path(ydl.prepare_filename(result))
        yield self._ensure_mp3_suffix(filename)

    @staticmethod
    def _ensure_mp3_suffix(filename: Path) -> Path:
        final_file = filename.with_suffix(".mp3")
        return final_file if final_file.exists() else filename

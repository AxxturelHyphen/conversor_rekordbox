from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Literal

from ..utils.logger import get_logger

AudioFormat = Literal["mp3", "wav"]

logger = get_logger()


@dataclass(frozen=True)
class ConversionResult:
    source: Path
    destination: Path
    format: AudioFormat
    success: bool
    error: str | None = None


class ConversionError(RuntimeError):
    """Raised when FFmpeg cannot process the file."""


FFMPEG_COMMON_ARGS = ["-y", "-vn"]


def build_ffmpeg_command(source: Path, destination: Path, fmt: AudioFormat) -> list[str]:
    """Return the ffmpeg command for the desired output format.

    MP3 uses constant bitrate 320 kbps with libmp3lame.
    WAV uses signed 16-bit PCM at 44.1 kHz.
    """

    if fmt == "mp3":
        return [
            "ffmpeg",
            *FFMPEG_COMMON_ARGS,
            "-i",
            str(source),
            "-acodec",
            "libmp3lame",
            "-b:a",
            "320k",
            "-map_metadata",
            "0",
            "-id3v2_version",
            "3",
            str(destination),
        ]

    if fmt == "wav":
        return [
            "ffmpeg",
            *FFMPEG_COMMON_ARGS,
            "-i",
            str(source),
            "-acodec",
            "pcm_s16le",
            "-ar",
            "44100",
            str(destination),
        ]

    raise ValueError(f"Formato no soportado: {fmt}")


def convert_file(source: Path, destination_dir: Path, fmt: AudioFormat) -> ConversionResult:
    destination_dir.mkdir(parents=True, exist_ok=True)
    destination = destination_dir / f"{source.stem}.{fmt}"
    command = build_ffmpeg_command(source, destination, fmt)
    logger.debug("Ejecutando comando ffmpeg", extra={"command": " ".join(command)})

    try:
        subprocess.run(command, check=True, capture_output=True)
    except FileNotFoundError as exc:  # ffmpeg no está instalado o no está en PATH
        logger.exception("FFmpeg no encontrado")
        raise ConversionError("FFmpeg no está disponible en el sistema") from exc
    except subprocess.CalledProcessError as exc:
        logger.exception("FFmpeg devolvió error")
        raise ConversionError(exc.stderr.decode("utf-8", errors="ignore")) from exc

    return ConversionResult(source=source, destination=destination, format=fmt, success=True)


def bulk_convert(sources: Iterable[Path], destination_dir: Path, fmt: AudioFormat) -> list[ConversionResult]:
    results: list[ConversionResult] = []
    for source in sources:
        try:
            results.append(convert_file(source, destination_dir, fmt))
        except ConversionError as exc:
            results.append(
                ConversionResult(
                    source=source,
                    destination=destination_dir / f"{source.stem}.{fmt}",
                    format=fmt,
                    success=False,
                    error=str(exc),
                )
            )
    return results

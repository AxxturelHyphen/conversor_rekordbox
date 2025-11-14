from __future__ import annotations

from enum import Enum
from pathlib import Path
from typing import Iterable, Protocol

from .formats import enginedj, rekordbox, serato
from .models import Track


class LibraryFormat(Protocol):
    """Protocolo que describe el API mínimo de un formato."""

    def load(self, path: Path) -> list[Track]:
        ...

    def dump(self, tracks: Iterable[Track], path: Path) -> None:
        ...


class Format(str, Enum):
    """Formatos soportados por el conversor."""

    REKORDBOX = "rekordbox"
    SERATO = "serato"
    ENGINE_DJ = "engine_dj"

    @classmethod
    def from_extension(cls, path: Path) -> "Format | None":
        extension = path.suffix.lower()
        if extension == ".xml":
            return cls.REKORDBOX
        if extension in {".m3u", ".m3u8"}:
            return cls.SERATO
        if extension == ".json":
            return cls.ENGINE_DJ
        return None


_FORMAT_MODULES: dict[Format, LibraryFormat] = {
    Format.REKORDBOX: rekordbox,
    Format.SERATO: serato,
    Format.ENGINE_DJ: enginedj,
}


def convert_library(
    input_path: str | Path,
    output_path: str | Path,
    input_format: Format | None = None,
    output_format: Format | None = None,
) -> Path:
    """Convierte una biblioteca entre formatos.

    Args:
        input_path: ruta del archivo de entrada.
        output_path: ruta del archivo generado.
        input_format: formato explícito de entrada. Si es ``None`` se intenta
            inferir a partir de la extensión.
        output_format: formato explícito de salida. Si es ``None`` se intenta
            inferir a partir de la extensión.

    Returns:
        Ruta final del archivo generado.
    """

    input_path = Path(input_path)
    output_path = Path(output_path)

    detected_input = input_format or Format.from_extension(input_path)
    if detected_input is None:
        raise ValueError(
            f"No se pudo inferir el formato de entrada a partir de {input_path}."
        )

    detected_output = output_format or Format.from_extension(output_path)
    if detected_output is None:
        raise ValueError(
            f"No se pudo inferir el formato de salida a partir de {output_path}."
        )

    loader = _FORMAT_MODULES[detected_input]
    writer = _FORMAT_MODULES[detected_output]

    tracks = loader.load(input_path)
    writer.dump(tracks, output_path)

    return output_path

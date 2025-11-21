from __future__ import annotations

import os
import platform
import shutil
import tarfile
import tempfile
import urllib.request
import zipfile
from pathlib import Path

from .config import AppConfig
from .logger import get_logger

logger = get_logger()

# Static builds per platform. They are lightweight, include codecs, and do not
# require admin privileges to unpack.
FFMPEG_URLS = {
    "windows": "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip",
    "linux": "https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz",
    "darwin": "https://evermeet.cx/ffmpeg/ffmpeg-6.1.zip",
}


class DependencyBootstrap:
    """Detects and installs runtime dependencies such as FFmpeg."""

    def __init__(self, config: AppConfig) -> None:
        self.config = config
        self.bin_dir = Path.home() / ".conversor_audio" / "bin"

    def ensure_ffmpeg(self) -> tuple[bool, str]:
        """Ensure ffmpeg is present; download a static build if missing."""
        existing = self._find_ffmpeg()
        if existing:
            self._remember(existing)
            return True, f"FFmpeg listo en {existing}"

        try:
            installed = self._install_ffmpeg()
        except Exception as exc:  # pragma: no cover - depends on network/filesystem
            logger.exception("No se pudo instalar FFmpeg")
            return False, f"No se pudo instalar FFmpeg: {exc}"

        self._remember(installed)
        return True, f"FFmpeg instalado en {installed}"

    def _remember(self, path: Path) -> None:
        self.config.ffmpeg_path = str(path)
        self.config.first_launch_completed = True
        self.config.save()
        self._prepend_to_path(path)

    def _prepend_to_path(self, binary: Path) -> None:
        folder = binary.parent if binary.is_file() else binary
        current = os.environ.get("PATH", "")
        if str(folder) not in current.split(os.pathsep):
            os.environ["PATH"] = f"{folder}{os.pathsep}{current}"

    def _find_ffmpeg(self) -> Path | None:
        candidates = [
            self.config.ffmpeg_path,
            os.environ.get("FFMPEG_PATH"),
            shutil.which("ffmpeg"),
            self.bin_dir / "ffmpeg.exe",
            self.bin_dir / "ffmpeg",
        ]
        for candidate in candidates:
            if not candidate:
                continue
            path = Path(candidate)
            if path.exists() and path.is_file():
                return path
        return None

    def _install_ffmpeg(self) -> Path:
        system = platform.system().lower()
        url = FFMPEG_URLS.get(system)
        if not url:
            raise RuntimeError(f"Plataforma no soportada para instalar FFmpeg: {system}")

        self.bin_dir.mkdir(parents=True, exist_ok=True)
        archive_path = self.bin_dir / Path(url).name

        logger.info("Descargando FFmpeg", extra={"url": url})
        self._download(url, archive_path)

        with tempfile.TemporaryDirectory() as tmp:
            extract_dir = Path(tmp)
            self._extract_archive(archive_path, extract_dir)
            ffmpeg_bin = self._locate_ffmpeg(extract_dir)
            target = self.bin_dir / ffmpeg_bin.name
            shutil.copy2(ffmpeg_bin, target)
            target.chmod(target.stat().st_mode | 0o111)
            return target

    @staticmethod
    def _download(url: str, target: Path) -> None:
        with urllib.request.urlopen(url) as response, open(target, "wb") as file:
            shutil.copyfileobj(response, file)

    @staticmethod
    def _extract_archive(archive_path: Path, target_dir: Path) -> None:
        if archive_path.suffix == ".zip":
            with zipfile.ZipFile(archive_path, "r") as zf:
                zf.extractall(target_dir)
            return

        # Handle .tar.xz and similar
        if archive_path.suffixes[-2:] == [".tar", ".xz"] or archive_path.suffix == ".xz":
            with tarfile.open(archive_path, "r:*") as tf:
                tf.extractall(target_dir)
            return

        raise RuntimeError(f"No se reconoce el formato de {archive_path.name}")

    @staticmethod
    def _locate_ffmpeg(extracted_root: Path) -> Path:
        binary_name = "ffmpeg.exe" if os.name == "nt" else "ffmpeg"
        for candidate in extracted_root.rglob(binary_name):
            if candidate.is_file():
                return candidate
        raise RuntimeError("El paquete descargado no contiene el ejecutable ffmpeg")

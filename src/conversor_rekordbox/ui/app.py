from __future__ import annotations

import sys
from pathlib import Path

from PyQt6 import QtWidgets

# Permit running the file directly (`python src/conversor_rekordbox/ui/app.py`)
# by ensuring the project root is on sys.path before absolute imports.
if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from conversor_rekordbox.ui.main_window import MainWindow
from conversor_rekordbox.utils.config import AppConfig
from conversor_rekordbox.utils.deps import DependencyBootstrap
from conversor_rekordbox.utils.logger import get_logger

logger = get_logger()


def run() -> None:
    app = QtWidgets.QApplication(sys.argv)
    app.setApplicationName("Conversor Audio")

    config = AppConfig.load()
    bootstrap = DependencyBootstrap(config)
    ffmpeg_ready, message = bootstrap.ensure_ffmpeg()

    window = MainWindow(config=config, bootstrap_message=message, ffmpeg_ready=ffmpeg_ready)
    window.show()

    if ffmpeg_ready:
        logger.info(message)
    else:
        QtWidgets.QMessageBox.warning(window, "Dependencias", message)

    sys.exit(app.exec())


if __name__ == "__main__":
    run()

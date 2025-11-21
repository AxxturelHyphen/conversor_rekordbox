from __future__ import annotations

import threading
from pathlib import Path

from PyQt6 import QtCore, QtWidgets

from ..api.soundcloud import SoundCloudDownloader
from ..utils.config import AppConfig
from ..utils.logger import get_logger

logger = get_logger()


class MainWindow(QtWidgets.QMainWindow):
    """Interfaz principal para descargar audio de SoundCloud en MP3 320 kbps."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("SoundCloud → MP3 320 kbps")
        self.resize(650, 220)

        self.config = AppConfig.load()
        self.downloader = SoundCloudDownloader()

        self._setup_ui()
        self._load_preferences()

    def _setup_ui(self) -> None:
        central = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(central)

        intro = QtWidgets.QLabel(
            "Descarga pistas o playlists públicas de SoundCloud directamente en MP3 320 kbps."
        )
        intro.setWordWrap(True)
        layout.addWidget(intro)

        form_layout = QtWidgets.QFormLayout()
        self.url_input = QtWidgets.QLineEdit()
        self.url_input.setPlaceholderText("https://soundcloud.com/...")
        form_layout.addRow("Enlace de SoundCloud", self.url_input)

        output_layout = QtWidgets.QHBoxLayout()
        self.output_label = QtWidgets.QLabel()
        self.choose_output = QtWidgets.QPushButton("Cambiar carpeta…")
        self.choose_output.clicked.connect(self.choose_output_dir)
        output_layout.addWidget(self.output_label, stretch=1)
        output_layout.addWidget(self.choose_output)
        form_layout.addRow("Guardar en", output_layout)

        layout.addLayout(form_layout)

        self.download_button = QtWidgets.QPushButton("Descargar en MP3 320 kbps")
        self.download_button.clicked.connect(self.download_stream)
        layout.addWidget(self.download_button)

        self.log_box = QtWidgets.QTextEdit()
        self.log_box.setReadOnly(True)
        self.log_box.setPlaceholderText("El progreso y los avisos aparecerán aquí…")
        layout.addWidget(self.log_box)

        self.status = QtWidgets.QStatusBar()
        self.setStatusBar(self.status)
        self.status.showMessage("Listo para descargar")

        self.setCentralWidget(central)

    def _load_preferences(self) -> None:
        output_dir = Path(self.config.output_dir) if self.config.output_dir else None
        if not output_dir:
            output_dir = Path.home() / "Downloads"
        self._set_output_dir(output_dir)

    def _set_output_dir(self, folder: Path) -> None:
        folder.mkdir(parents=True, exist_ok=True)
        self.output_label.setText(str(folder))
        self.config.output_dir = str(folder)
        self.config.save()

    def choose_output_dir(self) -> None:
        folder = QtWidgets.QFileDialog.getExistingDirectory(self, "Seleccionar carpeta de destino")
        if folder:
            self._set_output_dir(Path(folder))

    def download_stream(self) -> None:
        url = self.url_input.text().strip()
        if not url:
            QtWidgets.QMessageBox.warning(self, "URL vacía", "Introduce un enlace de SoundCloud")
            return
        if "soundcloud.com" not in url:
            QtWidgets.QMessageBox.warning(
                self,
                "Enlace no válido",
                "Solo se aceptan enlaces de SoundCloud (pistas o playlists públicas).",
            )
            return

        output_dir = Path(self.output_label.text())
        self.download_button.setEnabled(False)
        self.status.showMessage("Descargando…")
        self.log_box.append("Iniciando descarga…")

        def task() -> None:
            try:
                targets = self.downloader.download(url, output_dir, "mp3")
                message = self._build_success_message(targets, output_dir)
                QtCore.QMetaObject.invokeMethod(
                    self,
                    "_notify_download",
                    QtCore.Qt.ConnectionType.QueuedConnection,
                    QtCore.Q_ARG(str, message),
                )
            except Exception as exc:  # pragma: no cover - seguridad adicional
                logger.exception("Error en descarga")
                QtCore.QMetaObject.invokeMethod(
                    self,
                    "_notify_download_error",
                    QtCore.Qt.ConnectionType.QueuedConnection,
                    QtCore.Q_ARG(str, str(exc)),
                )

        threading.Thread(target=task, daemon=True).start()

    def _build_success_message(self, files: list[Path], output_dir: Path) -> str:
        if not files:
            return f"Descarga completada en {output_dir}"
        if len(files) == 1:
            return f"Descarga completada: {files[0].name}"
        return f"Descarga completada ({len(files)} elementos) en {output_dir}"

    @QtCore.pyqtSlot(str)
    def _notify_download(self, message: str) -> None:
        self.download_button.setEnabled(True)
        self.status.showMessage("Descarga finalizada")
        self.log_box.append(message)
        QtWidgets.QMessageBox.information(self, "Descarga completa", message)

    @QtCore.pyqtSlot(str)
    def _notify_download_error(self, message: str) -> None:
        self.download_button.setEnabled(True)
        self.status.showMessage("Error en la descarga")
        self.log_box.append(f"Error: {message}")
        QtWidgets.QMessageBox.critical(self, "Error", message)

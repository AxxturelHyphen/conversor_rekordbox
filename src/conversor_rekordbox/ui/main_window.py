from __future__ import annotations

import threading
from pathlib import Path

from PyQt6 import QtCore, QtWidgets

from ..api.soundcloud import SoundCloudDownloader
from ..utils.config import AppConfig
from ..utils.deps import DependencyBootstrap
from ..utils.logger import get_logger

logger = get_logger()


class MainWindow(QtWidgets.QMainWindow):
    """Interfaz principal para descargar audio de SoundCloud en MP3 320 kbps."""

    def __init__(
        self,
        config: AppConfig | None = None,
        bootstrap_message: str | None = None,
        ffmpeg_ready: bool = True,
    ) -> None:
        super().__init__()
        self.setWindowTitle("SoundCloud → MP3 320 kbps")
        self.resize(820, 520)

        self.config = config or AppConfig.load()
        self.downloader = SoundCloudDownloader()
        self.ffmpeg_ready = ffmpeg_ready
        self.bootstrap_message = bootstrap_message

        self._setup_ui()
        self.apply_styles()
        self._load_preferences()
        if bootstrap_message:
            self._update_dependency_badge(ffmpeg_ready, bootstrap_message)
            self.append_log(bootstrap_message)
        self.status.showMessage("Listo para descargar" if ffmpeg_ready else "FFmpeg pendiente")

    def _setup_ui(self) -> None:
        central = QtWidgets.QWidget()
        main_layout = QtWidgets.QVBoxLayout(central)
        main_layout.setContentsMargins(28, 24, 28, 20)
        main_layout.setSpacing(16)

        hero = QtWidgets.QFrame()
        hero.setObjectName("heroCard")
        hero_layout = QtWidgets.QVBoxLayout(hero)
        hero_layout.setContentsMargins(16, 14, 16, 14)
        hero_layout.setSpacing(6)

        title_row = QtWidgets.QHBoxLayout()
        title_row.setSpacing(10)
        title = QtWidgets.QLabel("Descarga SoundCloud en MP3 320 kbps")
        title.setObjectName("heroTitle")
        title_row.addWidget(title, alignment=QtCore.Qt.AlignmentFlag.AlignLeft)
        title_row.addStretch(1)

        hero_layout.addLayout(title_row)
        subtitle = QtWidgets.QLabel(
            "Convierte pistas y playlists públicas usando yt-dlp + FFmpeg sin complicarte con la consola."
        )
        subtitle.setObjectName("heroSubtitle")
        subtitle.setWordWrap(True)
        hero_layout.addWidget(subtitle)

        status_row = QtWidgets.QHBoxLayout()
        status_row.setSpacing(10)
        self.ffmpeg_status = QtWidgets.QLabel("FFmpeg: comprobando…")
        self.ffmpeg_status.setObjectName("statusPill")
        self.output_status = QtWidgets.QLabel("Carpeta: sin definir")
        self.output_status.setObjectName("ghostPill")
        self.deps_button = QtWidgets.QPushButton("Comprobar dependencias")
        self.deps_button.setObjectName("secondaryButton")
        self.deps_button.clicked.connect(self._verify_dependencies)
        status_row.addWidget(self.ffmpeg_status)
        status_row.addWidget(self.output_status)
        status_row.addStretch(1)
        status_row.addWidget(self.deps_button)
        hero_layout.addLayout(status_row)

        form_card = QtWidgets.QFrame()
        form_card.setObjectName("panelCard")
        form_layout = QtWidgets.QGridLayout(form_card)
        form_layout.setContentsMargins(18, 16, 18, 16)
        form_layout.setHorizontalSpacing(12)
        form_layout.setVerticalSpacing(12)

        url_label = QtWidgets.QLabel("Enlace de SoundCloud")
        url_label.setObjectName("fieldLabel")
        self.url_input = QtWidgets.QLineEdit()
        self.url_input.setPlaceholderText("https://soundcloud.com/tu-usuario/tu-pista-o-playlist")
        form_layout.addWidget(url_label, 0, 0)
        form_layout.addWidget(self.url_input, 0, 1, 1, 2)

        output_label = QtWidgets.QLabel("Guardar en")
        output_label.setObjectName("fieldLabel")
        self.output_label = QtWidgets.QLabel()
        self.output_label.setWordWrap(True)
        self.output_label.setTextInteractionFlags(
            QtCore.Qt.TextInteractionFlag.TextSelectableByMouse
        )
        self.choose_output = QtWidgets.QPushButton("Cambiar carpeta")
        self.choose_output.setObjectName("ghostButton")
        self.choose_output.clicked.connect(self.choose_output_dir)

        form_layout.addWidget(output_label, 1, 0, QtCore.Qt.AlignmentFlag.AlignTop)
        form_layout.addWidget(self.output_label, 1, 1)
        form_layout.addWidget(self.choose_output, 1, 2)

        buttons_row = QtWidgets.QHBoxLayout()
        self.download_button = QtWidgets.QPushButton("Descargar en MP3 320 kbps")
        self.download_button.setObjectName("primaryButton")
        self.download_button.clicked.connect(self.download_stream)
        buttons_row.addWidget(self.download_button)
        buttons_row.addStretch(1)
        form_layout.addLayout(buttons_row, 2, 0, 1, 3)

        log_card = QtWidgets.QFrame()
        log_card.setObjectName("panelCard")
        log_layout = QtWidgets.QVBoxLayout(log_card)
        log_layout.setContentsMargins(18, 14, 18, 12)
        log_layout.setSpacing(8)

        log_label = QtWidgets.QLabel("Progreso y notas")
        log_label.setObjectName("fieldLabel")
        self.log_box = QtWidgets.QTextEdit()
        self.log_box.setReadOnly(True)
        self.log_box.setMinimumHeight(160)
        self.log_box.setPlaceholderText("El progreso y los avisos aparecerán aquí…")
        log_layout.addWidget(log_label)
        log_layout.addWidget(self.log_box)

        main_layout.addWidget(hero)
        main_layout.addWidget(form_card)
        main_layout.addWidget(log_card)

        self.status = QtWidgets.QStatusBar()
        self.setStatusBar(self.status)
        self.setCentralWidget(central)

    def apply_styles(self) -> None:
        self.setStyleSheet(
            """
            QWidget {
                background-color: #0b1221;
                color: #e8edf5;
                font-family: 'Segoe UI';
                font-size: 11pt;
            }
            QFrame#heroCard {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                             stop:0 #0f172a, stop:1 #0b2038);
                border: 1px solid #14233a;
                border-radius: 16px;
            }
            QFrame#panelCard {
                background: rgba(255,255,255,0.04);
                border: 1px solid #162338;
                border-radius: 14px;
            }
            QLabel#heroTitle {
                font-size: 22px;
                font-weight: 700;
                letter-spacing: 0.2px;
            }
            QLabel#heroSubtitle {
                color: #c5d2e8;
                font-size: 11pt;
            }
            QLabel#fieldLabel {
                color: #c7d4ea;
                font-weight: 600;
                letter-spacing: 0.15px;
            }
            QLabel#statusPill, QLabel#ghostPill {
                padding: 6px 10px;
                border-radius: 10px;
                font-weight: 600;
            }
            QLabel#statusPill {
                background-color: rgba(34,197,94,0.16);
                color: #a7f3d0;
            }
            QLabel#ghostPill {
                background-color: rgba(255,255,255,0.06);
                color: #c7d4ea;
            }
            QLabel#heroTitle, QLabel#heroSubtitle, QLabel#fieldLabel {
                margin: 0;
            }
            QLineEdit, QTextEdit {
                background-color: rgba(255,255,255,0.08);
                color: #e8edf5;
                border: 1px solid #1f2e46;
                border-radius: 12px;
                padding: 10px 12px;
                selection-background-color: #2563eb;
            }
            QLineEdit:focus, QTextEdit:focus {
                border: 1px solid #2ea46f;
            }
            QPushButton {
                font-weight: 700;
                border-radius: 12px;
                padding: 10px 14px;
                border: none;
            }
            QPushButton#primaryButton {
                background-color: #16a34a;
                color: #f8fafc;
            }
            QPushButton#primaryButton:hover { background-color: #22c55e; }
            QPushButton#primaryButton:disabled {
                background-color: #1f2e46;
                color: #8ba0c2;
            }
            QPushButton#secondaryButton {
                background-color: transparent;
                color: #c7d4ea;
                border: 1px solid #20314a;
            }
            QPushButton#secondaryButton:hover {
                border-color: #2ea46f;
                color: #b8e6d3;
            }
            QPushButton#ghostButton {
                background-color: rgba(255,255,255,0.06);
                color: #d9e5fa;
                border: 1px solid #22324c;
            }
            QPushButton#ghostButton:hover { border-color: #2ea46f; }
            QStatusBar {
                background: #0f172a;
                color: #c7d4ea;
                border-top: 1px solid #162338;
            }
            """
        )

    def _load_preferences(self) -> None:
        output_dir = Path(self.config.output_dir) if self.config.output_dir else None
        if not output_dir:
            output_dir = Path.home() / "Downloads"
        self._set_output_dir(output_dir)

    def _set_output_dir(self, folder: Path) -> None:
        folder.mkdir(parents=True, exist_ok=True)
        self.output_label.setText(str(folder))
        self.output_status.setText(f"Destino: {folder}")
        self.config.output_dir = str(folder)
        self.config.save()

    def choose_output_dir(self) -> None:
        folder = QtWidgets.QFileDialog.getExistingDirectory(self, "Seleccionar carpeta de destino")
        if folder:
            self._set_output_dir(Path(folder))

    def _verify_dependencies(self) -> None:
        bootstrap = DependencyBootstrap(self.config)
        ok, message = bootstrap.ensure_ffmpeg()
        self.ffmpeg_ready = ok
        self._update_dependency_badge(ok, message)
        self.append_log(message)
        if not ok:
            QtWidgets.QMessageBox.warning(self, "FFmpeg no disponible", message)
        else:
            self.download_button.setEnabled(True)
            self.status.showMessage("Dependencias listas")

    def _update_dependency_badge(self, ok: bool, message: str) -> None:
        color = "#22c55e" if ok else "#f97316"
        bg = "rgba(34,197,94,0.18)" if ok else "rgba(249,115,22,0.18)"
        self.ffmpeg_status.setText(f"FFmpeg · {'Listo' if ok else 'Pendiente'}")
        self.ffmpeg_status.setToolTip(message)
        self.ffmpeg_status.setStyleSheet(
            f"padding: 6px 10px; border-radius: 10px; font-weight: 700; "
            f"background-color: {bg}; color: {color};"
        )
        if not ok:
            self.download_button.setEnabled(False)
        else:
            self.download_button.setEnabled(True)
            self.ffmpeg_ready = True

    def append_log(self, text: str) -> None:
        self.log_box.append(text)

    def download_stream(self) -> None:
        if not self.ffmpeg_ready:
            QtWidgets.QMessageBox.warning(
                self, "FFmpeg no disponible", "Instala las dependencias antes de descargar."
            )
            return

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
        self.append_log("Iniciando descarga…")

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
        self.append_log(message)
        QtWidgets.QMessageBox.information(self, "Descarga completa", message)

    @QtCore.pyqtSlot(str)
    def _notify_download_error(self, message: str) -> None:
        self.download_button.setEnabled(True)
        self.status.showMessage("Error en la descarga")
        self.append_log(f"Error: {message}")
        QtWidgets.QMessageBox.critical(self, "Error", message)

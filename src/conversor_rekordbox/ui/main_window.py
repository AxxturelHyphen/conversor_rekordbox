from __future__ import annotations

import threading
from dataclasses import dataclass
from pathlib import Path
from typing import List

from PyQt6 import QtCore, QtGui, QtWidgets

from ..api.soundcloud import SoundCloudCredentials, SoundCloudDownloader
from ..audio.conversion import AudioFormat, ConversionError, convert_file
from ..utils.config import AppConfig
from ..utils.logger import get_logger

logger = get_logger()


@dataclass
class QueueItem:
    path: Path
    target_format: AudioFormat
    status: str = "Pendiente"
    destination: Path | None = None


class ConversionWorker(QtCore.QObject):
    progressed = QtCore.pyqtSignal(Path, str)
    finished = QtCore.pyqtSignal(Path, Path)
    failed = QtCore.pyqtSignal(Path, str)

    def __init__(self, item: QueueItem, output_dir: Path):
        super().__init__()
        self.item = item
        self.output_dir = output_dir

    def run(self) -> None:
        try:
            self.progressed.emit(self.item.path, "Convirtiendo")
            result = convert_file(self.item.path, self.output_dir, self.item.target_format)
            self.finished.emit(self.item.path, result.destination)
        except ConversionError as exc:
            self.failed.emit(self.item.path, str(exc))
        except Exception as exc:  # pragma: no cover - seguridad adicional
            logger.exception("Error inesperado")
            self.failed.emit(self.item.path, str(exc))


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Conversor de Audio 320/WAV")
        self.resize(900, 500)
        self.config = AppConfig.load()
        self.queue: List[QueueItem] = []
        self.thread_pool: list[QtCore.QThread] = []

        self._setup_ui()
        self._load_preferences()

    # UI setup
    def _setup_ui(self) -> None:
        central = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(central)

        # Buttons and controls
        controls_layout = QtWidgets.QHBoxLayout()
        self.add_button = QtWidgets.QPushButton("Añadir archivos")
        self.add_button.clicked.connect(self.add_files)
        controls_layout.addWidget(self.add_button)

        self.remove_button = QtWidgets.QPushButton("Quitar seleccionado")
        self.remove_button.clicked.connect(self.remove_selected)
        controls_layout.addWidget(self.remove_button)

        self.clear_button = QtWidgets.QPushButton("Limpiar lista")
        self.clear_button.clicked.connect(self.clear_list)
        controls_layout.addWidget(self.clear_button)

        controls_layout.addStretch()

        self.format_combo = QtWidgets.QComboBox()
        self.format_combo.addItems(["mp3", "wav"])
        controls_layout.addWidget(QtWidgets.QLabel("Formato de salida"))
        controls_layout.addWidget(self.format_combo)

        self.use_source_checkbox = QtWidgets.QCheckBox("Usar carpeta de origen")
        controls_layout.addWidget(self.use_source_checkbox)

        self.output_button = QtWidgets.QPushButton("Elegir carpeta de salida")
        self.output_button.clicked.connect(self.choose_output_dir)
        controls_layout.addWidget(self.output_button)

        self.output_label = QtWidgets.QLabel("Sin carpeta seleccionada")
        controls_layout.addWidget(self.output_label)

        layout.addLayout(controls_layout)

        # Table
        self.table = QtWidgets.QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["Archivo", "Ruta", "Destino", "Estado"])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setAcceptDrops(True)
        self.table.dragEnterEvent = self.dragEnterEvent
        self.table.dropEvent = self.dropEvent
        layout.addWidget(self.table)

        # SoundCloud section
        sc_group = QtWidgets.QGroupBox("Descarga desde SoundCloud / streaming")
        sc_layout = QtWidgets.QHBoxLayout()
        self.sc_url = QtWidgets.QLineEdit()
        self.sc_url.setPlaceholderText("URL pública de SoundCloud, YouTube, etc.")
        self.sc_download_button = QtWidgets.QPushButton("Descargar a MP3 320")
        self.sc_download_button.clicked.connect(self.download_stream)
        sc_layout.addWidget(self.sc_url)
        sc_layout.addWidget(self.sc_download_button)
        sc_group.setLayout(sc_layout)
        layout.addWidget(sc_group)

        # Status bar
        self.status = QtWidgets.QStatusBar()
        self.setStatusBar(self.status)
        self.status.showMessage("Listo")

        self.convert_button = QtWidgets.QPushButton("Convertir")
        self.convert_button.clicked.connect(self.start_conversion)
        layout.addWidget(self.convert_button)

        self.setCentralWidget(central)

    def _load_preferences(self) -> None:
        self.use_source_checkbox.setChecked(self.config.use_source_dir)
        idx = self.format_combo.findText(self.config.last_format)
        if idx >= 0:
            self.format_combo.setCurrentIndex(idx)
        if self.config.output_dir:
            self.output_label.setText(self.config.output_dir)

    # Drag & drop
    def dragEnterEvent(self, event: QtGui.QDragEnterEvent) -> None:  # type: ignore[override]
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QtGui.QDropEvent) -> None:  # type: ignore[override]
        paths = [Path(url.toLocalFile()) for url in event.mimeData().urls()]
        self._add_to_queue(paths)

    # Queue management
    def add_files(self) -> None:
        files, _ = QtWidgets.QFileDialog.getOpenFileNames(self, "Seleccionar archivos de audio")
        if files:
            self._add_to_queue([Path(f) for f in files])

    def _add_to_queue(self, paths: list[Path]) -> None:
        target_format: AudioFormat = self.format_combo.currentText()  # type: ignore[assignment]
        for path in paths:
            item = QueueItem(path=path, target_format=target_format)
            self.queue.append(item)
            self._add_table_row(item)
        self.status.showMessage(f"{len(paths)} archivos añadidos")

    def _add_table_row(self, item: QueueItem) -> None:
        row = self.table.rowCount()
        self.table.insertRow(row)
        self.table.setItem(row, 0, QtWidgets.QTableWidgetItem(item.path.name))
        self.table.setItem(row, 1, QtWidgets.QTableWidgetItem(str(item.path)))
        self.table.setItem(row, 2, QtWidgets.QTableWidgetItem("-"))
        self.table.setItem(row, 3, QtWidgets.QTableWidgetItem(item.status))

    def remove_selected(self) -> None:
        selected = self.table.selectionModel().selectedRows()
        for idx in sorted((r.row() for r in selected), reverse=True):
            self.table.removeRow(idx)
            self.queue.pop(idx)

    def clear_list(self) -> None:
        self.queue.clear()
        self.table.setRowCount(0)
        self.status.showMessage("Lista limpia")

    def choose_output_dir(self) -> None:
        folder = QtWidgets.QFileDialog.getExistingDirectory(self, "Seleccionar carpeta de salida")
        if folder:
            self.output_label.setText(folder)
            self.config.output_dir = folder
            self.config.save()

    def start_conversion(self) -> None:
        if not self.queue:
            QtWidgets.QMessageBox.warning(self, "Sin archivos", "Añade archivos a la cola primero")
            return

        self.status.showMessage(f"Convirtiendo 0 de {len(self.queue)}")
        for item in self.queue:
            output_dir = Path(item.path.parent if self.use_source_checkbox.isChecked() else self.output_label.text())
            thread = QtCore.QThread()
            worker = ConversionWorker(item, output_dir)
            worker.moveToThread(thread)
            worker.progressed.connect(self._on_progress)
            worker.finished.connect(self._on_finished)
            worker.failed.connect(self._on_failed)
            thread.started.connect(worker.run)
            thread.start()
            self.thread_pool.append(thread)

    def _on_progress(self, path: Path, state: str) -> None:
        self._update_status(path, state)

    def _on_finished(self, path: Path, destination: Path) -> None:
        self._update_status(path, "Completado", destination)
        self.status.showMessage(f"Completado {path.name}")

    def _on_failed(self, path: Path, error: str) -> None:
        self._update_status(path, "Error")
        QtWidgets.QMessageBox.critical(self, "Error", f"{path.name}: {error}")

    def _update_status(self, path: Path, status: str, destination: Path | None = None) -> None:
        for row in range(self.table.rowCount()):
            if self.table.item(row, 1).text() == str(path):
                self.table.item(row, 3).setText(status)
                if destination:
                    self.table.item(row, 2).setText(str(destination))
                break

    # Streaming download
    def download_stream(self) -> None:
        url = self.sc_url.text().strip()
        if not url:
            QtWidgets.QMessageBox.warning(self, "URL vacía", "Introduce un enlace de SoundCloud/YouTube")
            return

        output_dir = Path(self.output_label.text()) if not self.use_source_checkbox.isChecked() and self.output_label.text() else Path.home() / "Downloads"
        downloader = SoundCloudDownloader(SoundCloudCredentials(), output_dir)

        def task() -> None:
            try:
                target = downloader.download(url, output_dir, "mp3")
                QtCore.QMetaObject.invokeMethod(
                    self,
                    "_notify_download",
                    QtCore.Qt.ConnectionType.QueuedConnection,
                    QtCore.Q_ARG(str, target.name),
                    QtCore.Q_ARG(str, str(target.parent)),
                )
            except Exception as exc:  # pragma: no cover - red
                logger.exception("Error en descarga")
                QtCore.QMetaObject.invokeMethod(
                    self,
                    "_notify_download_error",
                    QtCore.Qt.ConnectionType.QueuedConnection,
                    QtCore.Q_ARG(str, str(exc)),
                )

        threading.Thread(target=task, daemon=True).start()

    @QtCore.pyqtSlot(str, str)
    def _notify_download(self, filename: str, folder: str) -> None:
        QtWidgets.QMessageBox.information(self, "Descarga completa", f"Archivo guardado en {folder}/{filename}")

    @QtCore.pyqtSlot(str)
    def _notify_download_error(self, message: str) -> None:
        QtWidgets.QMessageBox.critical(self, "Error", message)

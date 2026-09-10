# ============================================================
# KID ACID'S VINYLVAULT V3
# MP3 CONVERTER (BATCH)
#
# Zoekt WAV / FLAC / M4A / AIFF / OGG / WMA bestanden in een
# gekozen map (incl. submappen) en converteert ze naar MP3.
# Origineel blijft altijd bestaan.
# ============================================================

import os
from pathlib import Path

from PySide6.QtCore import Qt, Signal, QThread
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QFileDialog,
    QMessageBox,
    QListWidget,
    QListWidgetItem,
    QComboBox,
    QRadioButton,
    QButtonGroup,
    QProgressBar,
    QGroupBox,
    QCheckBox,
    QAbstractItemView,
)

try:
    from pydub import AudioSegment
    PYDUB_AVAILABLE = True
except ImportError:
    PYDUB_AVAILABLE = False


SUPPORTED_EXTENSIONS = {
    ".wav",
    ".flac",
    ".m4a",
    ".aiff",
    ".aif",
    ".ogg",
    ".wma",
}


def find_convertible_files(folder):

    results = []

    for root, dirs, files in os.walk(folder):

        for name in files:

            extension = Path(name).suffix.lower()

            if extension in SUPPORTED_EXTENSIONS:

                results.append(Path(root) / name)

    results.sort()

    return results


# ============================================================
# BACKGROUND WORKER (houdt de UI responsief tijdens batch)
# ============================================================

class ConversionWorker(QThread):

    file_started = Signal(int, str)
    file_finished = Signal(int, bool, str)
    all_finished = Signal(int, int)

    def __init__(
        self,
        files,
        bitrate_kbps,
        output_mode,
        output_folder=None,
    ):

        super().__init__()

        self.files = files
        self.bitrate_kbps = bitrate_kbps
        self.output_mode = output_mode
        self.output_folder = output_folder

        self._stop_requested = False

    def request_stop(self):

        self._stop_requested = True

    def build_output_path(self, source_path):

        source_path = Path(source_path)

        if self.output_mode == "custom" and self.output_folder:
            target_dir = Path(self.output_folder)
        else:
            target_dir = source_path.parent

        target_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        candidate = target_dir / (source_path.stem + ".mp3")

        counter = 2

        while candidate.exists():

            candidate = target_dir / f"{source_path.stem}_{counter}.mp3"

            counter += 1

        return candidate

    def run(self):

        success_count = 0
        fail_count = 0

        for index, source_path in enumerate(self.files):

            if self._stop_requested:
                break

            self.file_started.emit(
                index,
                str(source_path),
            )

            try:

                output_path = self.build_output_path(source_path)

                audio = AudioSegment.from_file(str(source_path))

                audio.export(
                    str(output_path),
                    format="mp3",
                    bitrate=f"{self.bitrate_kbps}k",
                )

                success_count += 1

                self.file_finished.emit(
                    index,
                    True,
                    str(output_path),
                )

            except Exception as exc:

                fail_count += 1

                self.file_finished.emit(
                    index,
                    False,
                    str(exc),
                )

        self.all_finished.emit(
            success_count,
            fail_count,
        )


# ============================================================
# CONVERTER DIALOG
# ============================================================

class MP3ConverterDialog(QDialog):

    def __init__(
        self,
        initial_folder=None,
        parent=None,
    ):

        super().__init__(parent)

        self.setWindowTitle("MP3 Converter (batch)")
        self.setMinimumSize(760, 620)

        self.source_folder = None
        self.found_files = []
        self.worker = None

        self.build_ui()
        self.apply_style()

        if initial_folder:
            self.load_folder(initial_folder)

    # ========================================================
    # BUILD UI
    # ========================================================

    def build_ui(self):

        layout = QVBoxLayout(self)

        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)

        # ----------------------------------------------------
        # MAP KIEZEN
        # ----------------------------------------------------

        folder_row = QHBoxLayout()

        self.folder_label = QLabel("Geen map geselecteerd")

        self.folder_label.setStyleSheet(
            "QLabel { color: #ffffff; font-weight: bold; }"
        )

        self.folder_label.setWordWrap(True)

        folder_row.addWidget(self.folder_label, 1)

        browse_button = QPushButton("[ MAP SELECTEREN ]")

        browse_button.clicked.connect(self.browse_folder)

        folder_row.addWidget(browse_button)

        layout.addLayout(folder_row)

        info_label = QLabel(
            "Zoekt automatisch (incl. submappen) naar: "
            "WAV, FLAC, M4A, AIFF, OGG, WMA"
        )

        info_label.setStyleSheet("QLabel { color: #999999; }")

        layout.addWidget(info_label)

        # ----------------------------------------------------
        # BESTANDENLIJST
        # ----------------------------------------------------

        list_group = QGroupBox("GEVONDEN BESTANDEN")

        list_layout = QVBoxLayout(list_group)

        self.file_list = QListWidget()

        self.file_list.setSelectionMode(
            QAbstractItemView.SelectionMode.NoSelection
        )

        list_layout.addWidget(self.file_list)

        select_row = QHBoxLayout()

        select_all_button = QPushButton("[ ALLES SELECTEREN ]")

        select_all_button.clicked.connect(
            lambda: self.set_all_checked(True)
        )

        select_row.addWidget(select_all_button)

        select_none_button = QPushButton("[ NIETS SELECTEREN ]")

        select_none_button.clicked.connect(
            lambda: self.set_all_checked(False)
        )

        select_row.addWidget(select_none_button)

        select_row.addStretch()

        self.count_label = QLabel("0 bestanden gevonden")

        select_row.addWidget(self.count_label)

        list_layout.addLayout(select_row)

        layout.addWidget(list_group, 1)

        # ----------------------------------------------------
        # OPTIES
        # ----------------------------------------------------

        options_group = QGroupBox("OPTIES")

        options_layout = QVBoxLayout(options_group)

        bitrate_row = QHBoxLayout()

        bitrate_row.addWidget(QLabel("Kwaliteit (bitrate):"))

        self.bitrate_combo = QComboBox()

        self.bitrate_combo.addItems(
            ["128 kbps", "192 kbps", "256 kbps", "320 kbps"]
        )

        self.bitrate_combo.setCurrentIndex(3)

        bitrate_row.addWidget(self.bitrate_combo)

        bitrate_row.addStretch()

        options_layout.addLayout(bitrate_row)

        output_row = QHBoxLayout()

        self.output_group = QButtonGroup(self)

        self.same_folder_radio = QRadioButton(
            "Zelfde map als origineel bestand"
        )

        self.same_folder_radio.setChecked(True)

        self.output_group.addButton(self.same_folder_radio)

        output_row.addWidget(self.same_folder_radio)

        self.custom_folder_radio = QRadioButton(
            "Aparte map:"
        )

        self.output_group.addButton(self.custom_folder_radio)

        output_row.addWidget(self.custom_folder_radio)

        self.output_folder_label = QLabel("(geen map gekozen)")

        self.output_folder_label.setStyleSheet(
            "QLabel { color: #999999; }"
        )

        output_row.addWidget(self.output_folder_label, 1)

        output_folder_button = QPushButton("[ KIEZEN ]")

        output_folder_button.clicked.connect(
            self.browse_output_folder
        )

        output_row.addWidget(output_folder_button)

        options_layout.addLayout(output_row)

        layout.addWidget(options_group)

        # ----------------------------------------------------
        # VOORTGANG + KNOPPEN
        # ----------------------------------------------------

        self.progress_bar = QProgressBar()

        self.progress_bar.setValue(0)

        layout.addWidget(self.progress_bar)

        self.status_label = QLabel("")

        self.status_label.setWordWrap(True)

        layout.addWidget(self.status_label)

        button_row = QHBoxLayout()

        button_row.addStretch()

        self.convert_button = QPushButton(
            "[ ⇄ CONVERTEER GESELECTEERDE BESTANDEN ]"
        )

        self.convert_button.setMinimumHeight(42)

        self.convert_button.clicked.connect(self.start_conversion)

        button_row.addWidget(self.convert_button)

        self.stop_button = QPushButton("[ STOP ]")

        self.stop_button.setEnabled(False)

        self.stop_button.clicked.connect(self.stop_conversion)

        button_row.addWidget(self.stop_button)

        layout.addLayout(button_row)

    # ========================================================
    # STYLE
    # ========================================================

    def apply_style(self):

        self.setStyleSheet(
            """
            QDialog {
                background-color: #151515;
                color: #ffffff;
            }

            QGroupBox {
                color: #ffffff;
                border: 1px solid #55466d;
                border-radius: 8px;
                margin-top: 10px;
                padding: 12px;
                font-weight: bold;
            }

            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 6px;
                color: #d84b91;
            }

            QLabel {
                color: #bbbbbb;
            }

            QListWidget {
                background-color: #1c1726;
                color: #ffffff;
                border: 1px solid #55466d;
                border-radius: 5px;
            }

            QComboBox {
                background-color: #1c1726;
                color: #ffffff;
                border: 1px solid #55466d;
                border-radius: 5px;
                padding: 4px;
            }

            QRadioButton {
                color: #ffffff;
            }

            QProgressBar {
                background-color: #1c1726;
                color: #ffffff;
                border: 1px solid #55466d;
                border-radius: 5px;
                text-align: center;
            }

            QProgressBar::chunk {
                background-color: #d84b91;
                border-radius: 4px;
            }

            QPushButton {
                background-color: #252525;
                color: #ffffff;
                border: 1px solid #55466d;
                border-radius: 5px;
                padding: 7px 12px;
            }

            QPushButton:hover {
                background-color: #352d46;
                border: 1px solid #d84b91;
            }

            QPushButton:pressed {
                background-color: #d84b91;
            }

            QPushButton:disabled {
                color: #777777;
                border: 1px solid #3a3a3a;
            }
            """
        )

        self.convert_button.setStyleSheet(
            """
            QPushButton {
                background-color: #234d23;
                color: #ffffff;
                border: 1px solid #3d7a3d;
                border-radius: 5px;
                padding: 10px 16px;
                font-weight: bold;
            }

            QPushButton:hover {
                background-color: #316831;
            }

            QPushButton:pressed {
                background-color: #1b3b1b;
            }

            QPushButton:disabled {
                background-color: #2a2a2a;
                color: #777777;
                border: 1px solid #3a3a3a;
            }
            """
        )

    # ========================================================
    # FOLDER SELECTION
    # ========================================================

    def browse_folder(self):

        folder = QFileDialog.getExistingDirectory(
            self,
            "Kies een map om te scannen",
        )

        if folder:
            self.load_folder(folder)

    def load_folder(self, folder):

        folder_path = Path(folder)

        if not folder_path.exists():

            QMessageBox.warning(
                self,
                "Map niet gevonden",
                f"Kon deze map niet vinden:\n\n{folder_path}",
            )

            return

        self.source_folder = str(folder_path)

        self.folder_label.setText(str(folder_path))

        self.found_files = find_convertible_files(folder_path)

        self.file_list.clear()

        for file_path in self.found_files:

            item = QListWidgetItem(
                str(file_path.relative_to(folder_path))
            )

            item.setFlags(
                item.flags() | Qt.ItemFlag.ItemIsUserCheckable
            )

            item.setCheckState(Qt.CheckState.Checked)

            self.file_list.addItem(item)

        self.count_label.setText(
            f"{len(self.found_files)} bestanden gevonden"
        )

        self.status_label.setText("")

        self.progress_bar.setValue(0)

        self.progress_bar.setMaximum(
            max(len(self.found_files), 1)
        )

        if not self.found_files:

            QMessageBox.information(
                self,
                "Niets gevonden",
                "Er zijn geen WAV / FLAC / M4A / AIFF / OGG / WMA "
                "bestanden gevonden in deze map (of submappen).",
            )

    def browse_output_folder(self):

        folder = QFileDialog.getExistingDirectory(
            self,
            "Kies uitvoermap",
        )

        if folder:

            self.custom_output_folder = folder

            self.output_folder_label.setText(folder)

            self.custom_folder_radio.setChecked(True)

    def set_all_checked(self, checked):

        state = (
            Qt.CheckState.Checked
            if checked
            else Qt.CheckState.Unchecked
        )

        for row in range(self.file_list.count()):

            self.file_list.item(row).setCheckState(state)

    # ========================================================
    # CONVERSION
    # ========================================================

    def start_conversion(self):

        if not PYDUB_AVAILABLE:

            QMessageBox.critical(
                self,
                "Pydub ontbreekt",
                (
                    "Voor het converteren is de Python-bibliotheek 'pydub' nodig, "
                    "en moet ffmpeg geinstalleerd zijn.\n\n"
                    "Installeer met:\n"
                    "python -m pip install pydub\n\n"
                    "En zorg dat ffmpeg.exe beschikbaar is via je systeem-PATH "
                    "(download op https://ffmpeg.org/download.html)."
                ),
            )

            return

        selected_files = [
            self.found_files[row]
            for row in range(self.file_list.count())
            if self.file_list.item(row).checkState()
            == Qt.CheckState.Checked
        ]

        if not selected_files:

            QMessageBox.warning(
                self,
                "Niets geselecteerd",
                "Selecteer minstens één bestand om te converteren.",
            )

            return

        output_mode = (
            "custom"
            if self.custom_folder_radio.isChecked()
            else "same"
        )

        output_folder = getattr(
            self,
            "custom_output_folder",
            None,
        )

        if output_mode == "custom" and not output_folder:

            QMessageBox.warning(
                self,
                "Geen uitvoermap gekozen",
                "Kies eerst een aparte map, of kies 'Zelfde map als origineel'.",
            )

            return

        bitrate_kbps = int(
            self.bitrate_combo.currentText().split()[0]
        )

        self.progress_bar.setMaximum(len(selected_files))

        self.progress_bar.setValue(0)

        self.status_label.setText(
            f"Bezig met converteren (0 / {len(selected_files)})..."
        )

        self.convert_button.setEnabled(False)
        self.stop_button.setEnabled(True)

        self._selected_files_for_run = selected_files

        self.worker = ConversionWorker(
            files=selected_files,
            bitrate_kbps=bitrate_kbps,
            output_mode=output_mode,
            output_folder=output_folder,
        )

        self.worker.file_started.connect(self.on_file_started)
        self.worker.file_finished.connect(self.on_file_finished)
        self.worker.all_finished.connect(self.on_all_finished)

        self.worker.start()

    def stop_conversion(self):

        if self.worker is not None:

            self.worker.request_stop()

            self.stop_button.setEnabled(False)

            self.status_label.setText("Wordt gestopt na huidig bestand...")

    def on_file_started(self, index, path):

        name = Path(path).name

        self.status_label.setText(
            f"Bezig: {name} "
            f"({index + 1} / {len(self._selected_files_for_run)})"
        )

    def on_file_finished(self, index, success, message):

        self.progress_bar.setValue(index + 1)

    def on_all_finished(self, success_count, fail_count):

        self.convert_button.setEnabled(True)
        self.stop_button.setEnabled(False)

        if fail_count == 0:

            self.status_label.setText(
                f"Klaar! {success_count} bestand(en) succesvol geconverteerd."
            )

            QMessageBox.information(
                self,
                "Conversie voltooid",
                f"{success_count} bestand(en) succesvol geconverteerd naar MP3.",
            )

        else:

            self.status_label.setText(
                f"Klaar met fouten: {success_count} gelukt, {fail_count} mislukt."
            )

            QMessageBox.warning(
                self,
                "Conversie voltooid (met fouten)",
                (
                    f"{success_count} bestand(en) succesvol geconverteerd.\n"
                    f"{fail_count} bestand(en) zijn mislukt.\n\n"
                    "Controleer of ffmpeg correct is geinstalleerd en of de "
                    "bronbestanden niet beschadigd zijn."
                ),
            )

        self.worker = None

    # ========================================================
    # CLEANUP
    # ========================================================

    def closeEvent(self, event):

        if self.worker is not None and self.worker.isRunning():

            self.worker.request_stop()

            self.worker.wait(3000)

        super().closeEvent(event)

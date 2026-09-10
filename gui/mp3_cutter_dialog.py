# ============================================================
# KID ACID'S VINYLVAULT V3
# MP3 CUTTER
#
# Volledige editor: begin/eind afsnijden + stukken uit het
# midden verwijderen. Resultaat wordt als NIEUW bestand
# opgeslagen; het origineel blijft ongewijzigd.
# ============================================================

import os
import re
from pathlib import Path

from PySide6.QtCore import Qt, QUrl, Signal
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSlider,
    QListWidget,
    QListWidgetItem,
    QFileDialog,
    QMessageBox,
    QLineEdit,
    QGroupBox,
    QAbstractItemView,
)

try:
    from mutagen.mp3 import MP3
    MUTAGEN_AVAILABLE = True
except ImportError:
    MUTAGEN_AVAILABLE = False

try:
    from pydub import AudioSegment
    PYDUB_AVAILABLE = True
except ImportError:
    PYDUB_AVAILABLE = False


# ============================================================
# TIME HELPERS
# ============================================================

def format_time(ms):

    if ms is None or ms < 0:
        ms = 0

    total_seconds = ms / 1000.0
    minutes = int(total_seconds // 60)
    seconds = total_seconds - (minutes * 60)

    return f"{minutes:02d}:{seconds:06.3f}"


TIME_PATTERN = re.compile(
    r"^\s*(?:(\d+):)?(\d+(?:\.\d+)?)\s*$"
)


def parse_time_to_ms(text):
    """Accepts 'mm:ss.mmm', 'mm:ss', or plain seconds like '12.5'."""

    if text is None:
        return None

    match = TIME_PATTERN.match(str(text))

    if not match:
        return None

    minutes_part, seconds_part = match.groups()

    minutes = int(minutes_part) if minutes_part else 0
    seconds = float(seconds_part)

    return int(round((minutes * 60 + seconds) * 1000))


# ============================================================
# MP3 CUTTER DIALOG
# ============================================================

class MP3CutterDialog(QDialog):

    cut_completed = Signal(str)

    def __init__(
        self,
        initial_path=None,
        parent=None,
    ):

        super().__init__(parent)

        self.setWindowTitle("MP3 Cutter")
        self.setMinimumSize(760, 620)

        self.source_path = None
        self.duration_ms = 0
        self.middle_cuts = []

        self.audio_output = QAudioOutput()
        self.audio_output.setVolume(1.0)

        self.player = QMediaPlayer()
        self.player.setAudioOutput(self.audio_output)

        self.player.positionChanged.connect(
            self.on_position_changed
        )

        self.player.durationChanged.connect(
            self.on_duration_changed
        )

        self.player.playbackStateChanged.connect(
            self.on_playback_state_changed
        )

        self._slider_dragging = False

        self.build_ui()
        self.apply_style()

        if initial_path:
            self.load_file(initial_path)

    # ========================================================
    # BUILD UI
    # ========================================================

    def build_ui(self):

        layout = QVBoxLayout(self)

        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)

        # ----------------------------------------------------
        # FILE ROW
        # ----------------------------------------------------

        file_row = QHBoxLayout()

        self.file_label = QLabel("Geen bestand geladen")

        self.file_label.setStyleSheet(
            "QLabel { color: #ffffff; font-weight: bold; }"
        )

        self.file_label.setWordWrap(True)

        file_row.addWidget(self.file_label, 1)

        open_button = QPushButton("[ ANDER BESTAND OPENEN ]")

        open_button.clicked.connect(self.browse_file)

        file_row.addWidget(open_button)

        layout.addLayout(file_row)

        # ----------------------------------------------------
        # PLAYBACK
        # ----------------------------------------------------

        playback_group = QGroupBox("AFSPELEN / POSITIE ZOEKEN")

        playback_layout = QVBoxLayout(playback_group)

        controls_row = QHBoxLayout()

        self.play_button = QPushButton("[ ▶ PLAY ]")

        self.play_button.clicked.connect(self.toggle_play)

        controls_row.addWidget(self.play_button)

        self.position_label = QLabel("00:00.000")

        controls_row.addWidget(self.position_label)

        self.slider = QSlider(Qt.Orientation.Horizontal)

        self.slider.setRange(0, 0)

        self.slider.sliderPressed.connect(self._on_slider_pressed)
        self.slider.sliderReleased.connect(self._on_slider_released)
        self.slider.sliderMoved.connect(self._on_slider_moved)

        controls_row.addWidget(self.slider, 1)

        self.duration_label = QLabel("00:00.000")

        controls_row.addWidget(self.duration_label)

        playback_layout.addLayout(controls_row)

        layout.addWidget(playback_group)

        # ----------------------------------------------------
        # TRIM (BEHOUDEN BEREIK)
        # ----------------------------------------------------

        trim_group = QGroupBox("VOLLEDIGE SELECTIE (dit blijft behouden)")

        trim_layout = QHBoxLayout(trim_group)

        trim_layout.addWidget(QLabel("Start:"))

        self.trim_start_input = QLineEdit("00:00.000")

        self.trim_start_input.setMaximumWidth(110)

        trim_layout.addWidget(self.trim_start_input)

        start_now_button = QPushButton("[ NU ]")

        start_now_button.clicked.connect(
            lambda: self.set_field_to_current(self.trim_start_input)
        )

        trim_layout.addWidget(start_now_button)

        trim_layout.addSpacing(20)

        trim_layout.addWidget(QLabel("Einde:"))

        self.trim_end_input = QLineEdit("00:00.000")

        self.trim_end_input.setMaximumWidth(110)

        trim_layout.addWidget(self.trim_end_input)

        end_now_button = QPushButton("[ NU ]")

        end_now_button.clicked.connect(
            lambda: self.set_field_to_current(self.trim_end_input)
        )

        trim_layout.addWidget(end_now_button)

        end_full_button = QPushButton("[ EINDE BESTAND ]")

        end_full_button.clicked.connect(self.set_end_to_full_duration)

        trim_layout.addWidget(end_full_button)

        trim_layout.addStretch()

        layout.addWidget(trim_group)

        # ----------------------------------------------------
        # MIDDEN-STUKKEN VERWIJDEREN
        # ----------------------------------------------------

        cuts_group = QGroupBox("STUKKEN UIT HET MIDDEN VERWIJDEREN")

        cuts_layout = QVBoxLayout(cuts_group)

        add_row = QHBoxLayout()

        add_row.addWidget(QLabel("Van:"))

        self.cut_start_input = QLineEdit("00:00.000")

        self.cut_start_input.setMaximumWidth(110)

        add_row.addWidget(self.cut_start_input)

        cut_start_now_button = QPushButton("[ NU ]")

        cut_start_now_button.clicked.connect(
            lambda: self.set_field_to_current(self.cut_start_input)
        )

        add_row.addWidget(cut_start_now_button)

        add_row.addSpacing(20)

        add_row.addWidget(QLabel("Tot:"))

        self.cut_end_input = QLineEdit("00:00.000")

        self.cut_end_input.setMaximumWidth(110)

        add_row.addWidget(self.cut_end_input)

        cut_end_now_button = QPushButton("[ NU ]")

        cut_end_now_button.clicked.connect(
            lambda: self.set_field_to_current(self.cut_end_input)
        )

        add_row.addWidget(cut_end_now_button)

        add_cut_button = QPushButton("[ + TOEVOEGEN ]")

        add_cut_button.clicked.connect(self.add_middle_cut)

        add_row.addWidget(add_cut_button)

        add_row.addStretch()

        cuts_layout.addLayout(add_row)

        self.cuts_list = QListWidget()

        self.cuts_list.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection
        )

        self.cuts_list.setMaximumHeight(120)

        cuts_layout.addWidget(self.cuts_list)

        remove_row = QHBoxLayout()

        remove_row.addStretch()

        remove_cut_button = QPushButton("[ VERWIJDER GESELECTEERDE ]")

        remove_cut_button.clicked.connect(self.remove_selected_cut)

        remove_row.addWidget(remove_cut_button)

        cuts_layout.addLayout(remove_row)

        layout.addWidget(cuts_group)

        # ----------------------------------------------------
        # EXPORT
        # ----------------------------------------------------

        export_group = QGroupBox("RESULTAAT OPSLAAN")

        export_layout = QVBoxLayout(export_group)

        self.result_info_label = QLabel(
            "Laad eerst een MP3-bestand."
        )

        self.result_info_label.setWordWrap(True)

        export_layout.addWidget(self.result_info_label)

        export_row = QHBoxLayout()

        export_row.addStretch()

        self.export_button = QPushButton(
            "[ ✂ KNIPPEN EN OPSLAAN ALS NIEUW BESTAND ]"
        )

        self.export_button.setMinimumHeight(42)

        self.export_button.clicked.connect(self.export_result)

        export_row.addWidget(self.export_button)

        export_layout.addLayout(export_row)

        self.status_label = QLabel("")

        self.status_label.setWordWrap(True)

        export_layout.addWidget(self.status_label)

        layout.addWidget(export_group)

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

            QLineEdit {
                background-color: #1c1726;
                color: #ffffff;
                border: 1px solid #55466d;
                border-radius: 5px;
                padding: 5px;
            }

            QLineEdit:focus {
                border: 1px solid #d84b91;
            }

            QListWidget {
                background-color: #1c1726;
                color: #ffffff;
                border: 1px solid #55466d;
                border-radius: 5px;
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
            """
        )

        self.export_button.setStyleSheet(
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
            """
        )

    # ========================================================
    # FILE LOADING
    # ========================================================

    def browse_file(self):

        path, _ = QFileDialog.getOpenFileName(
            self,
            "MP3-bestand openen",
            "",
            "Audio (*.mp3 *.wav *.flac *.m4a);;Alle bestanden (*)",
        )

        if path:
            self.load_file(path)

    def load_file(self, path):

        file_path = Path(path).expanduser()

        if not file_path.exists():

            QMessageBox.warning(
                self,
                "Bestand niet gevonden",
                f"Kon dit bestand niet vinden:\n\n{file_path}",
            )

            return

        self.player.stop()

        self.source_path = str(file_path)

        self.middle_cuts = []

        self.cuts_list.clear()

        self.file_label.setText(file_path.name)

        # Duration via mutagen (direct, betrouwbaar), val terug op
        # Qt's durationChanged als mutagen niet beschikbaar is.

        duration_ms = 0

        if MUTAGEN_AVAILABLE and file_path.suffix.lower() == ".mp3":

            try:

                audio_info = MP3(str(file_path))

                duration_ms = int(audio_info.info.length * 1000)

            except Exception:

                duration_ms = 0

        self.duration_ms = duration_ms

        self.slider.setRange(0, max(duration_ms, 0))

        self.duration_label.setText(format_time(duration_ms))

        self.trim_start_input.setText(format_time(0))

        self.trim_end_input.setText(format_time(duration_ms))

        self.update_result_info()

        self.player.setSource(
            QUrl.fromLocalFile(self.source_path)
        )

        self.status_label.setText("")

    # ========================================================
    # PLAYBACK
    # ========================================================

    def toggle_play(self):

        if not self.source_path:
            return

        if self.player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.player.pause()
        else:
            self.player.play()

    def on_playback_state_changed(self, state):

        if state == QMediaPlayer.PlaybackState.PlayingState:
            self.play_button.setText("[ ❚❚ PAUSE ]")
        else:
            self.play_button.setText("[ ▶ PLAY ]")

    def on_position_changed(self, position):

        if not self._slider_dragging:
            self.slider.setValue(position)

        self.position_label.setText(format_time(position))

    def on_duration_changed(self, duration):

        # Qt's eigen duration kan afwijken/later binnenkomen;
        # gebruik het alleen als mutagen niets opleverde.

        if self.duration_ms <= 0 and duration > 0:

            self.duration_ms = duration

            self.slider.setRange(0, duration)

            self.duration_label.setText(format_time(duration))

            if not self.trim_end_input.text().strip() or \
                    parse_time_to_ms(self.trim_end_input.text()) == 0:

                self.trim_end_input.setText(format_time(duration))

    def _on_slider_pressed(self):

        self._slider_dragging = True

    def _on_slider_released(self):

        self._slider_dragging = False

        self.player.setPosition(self.slider.value())

    def _on_slider_moved(self, value):

        self.position_label.setText(format_time(value))

    def current_position_ms(self):

        return self.player.position()

    # ========================================================
    # FIELD HELPERS
    # ========================================================

    def set_field_to_current(self, field):

        field.setText(
            format_time(self.current_position_ms())
        )

    def set_end_to_full_duration(self):

        self.trim_end_input.setText(
            format_time(self.duration_ms)
        )

    # ========================================================
    # MIDDEN-STUKKEN BEHEER
    # ========================================================

    def add_middle_cut(self):

        if not self.source_path:

            QMessageBox.warning(
                self,
                "Geen bestand",
                "Laad eerst een MP3-bestand.",
            )

            return

        start_ms = parse_time_to_ms(self.cut_start_input.text())
        end_ms = parse_time_to_ms(self.cut_end_input.text())

        if start_ms is None or end_ms is None:

            QMessageBox.warning(
                self,
                "Ongeldige tijd",
                "Gebruik het formaat mm:ss.mmm (bijvoorbeeld 01:23.500) of gewoon seconden.",
            )

            return

        if end_ms <= start_ms:

            QMessageBox.warning(
                self,
                "Ongeldig bereik",
                "Het eindpunt moet na het startpunt liggen.",
            )

            return

        if start_ms < 0 or end_ms > self.duration_ms:

            QMessageBox.warning(
                self,
                "Buiten bereik",
                "Dit stuk valt buiten de lengte van het bestand.",
            )

            return

        for existing_start, existing_end in self.middle_cuts:

            if start_ms < existing_end and end_ms > existing_start:

                QMessageBox.warning(
                    self,
                    "Overlapt",
                    "Dit stuk overlapt met een reeds toegevoegd stuk.",
                )

                return

        self.middle_cuts.append((start_ms, end_ms))

        self.middle_cuts.sort(key=lambda pair: pair[0])

        self.refresh_cuts_list()

        self.update_result_info()

    def refresh_cuts_list(self):

        self.cuts_list.clear()

        for start_ms, end_ms in self.middle_cuts:

            item = QListWidgetItem(
                f"{format_time(start_ms)}  -  {format_time(end_ms)}"
                f"   ({format_time(end_ms - start_ms)} verwijderd)"
            )

            self.cuts_list.addItem(item)

    def remove_selected_cut(self):

        row = self.cuts_list.currentRow()

        if row < 0:
            return

        del self.middle_cuts[row]

        self.refresh_cuts_list()

        self.update_result_info()

    # ========================================================
    # RESULT PREVIEW INFO
    # ========================================================

    def compute_kept_segments(self):
        """Geeft een lijst van (start_ms, end_ms) bereiken die
        behouden blijven, in volgorde."""

        start_ms = parse_time_to_ms(self.trim_start_input.text())
        end_ms = parse_time_to_ms(self.trim_end_input.text())

        if start_ms is None or end_ms is None or end_ms <= start_ms:
            return None

        segments = []
        cursor = start_ms

        for cut_start, cut_end in self.middle_cuts:

            if cut_start <= cursor:

                cursor = max(cursor, cut_end)

                continue

            if cut_start >= end_ms:
                break

            segments.append(
                (cursor, min(cut_start, end_ms))
            )

            cursor = max(cursor, cut_end)

        if cursor < end_ms:

            segments.append((cursor, end_ms))

        segments = [
            (s, e) for s, e in segments if e > s
        ]

        return segments

    def update_result_info(self):

        if not self.source_path:

            self.result_info_label.setText(
                "Laad eerst een MP3-bestand."
            )

            return

        segments = self.compute_kept_segments()

        if not segments:

            self.result_info_label.setText(
                "Ongeldige selectie: er blijft niets over om op te slaan."
            )

            return

        total_kept = sum(end - start for start, end in segments)

        self.result_info_label.setText(
            f"Resultaat: {len(segments)} deel(en) behouden, "
            f"totale lengte {format_time(total_kept)}."
        )

    # ========================================================
    # EXPORT
    # ========================================================

    def build_output_path(self):

        source = Path(self.source_path)

        candidate = source.with_name(
            source.stem + "_cut" + source.suffix
        )

        counter = 2

        while candidate.exists():

            candidate = source.with_name(
                f"{source.stem}_cut{counter}{source.suffix}"
            )

            counter += 1

        return candidate

    def export_result(self):

        if not self.source_path:

            QMessageBox.warning(
                self,
                "Geen bestand",
                "Laad eerst een MP3-bestand.",
            )

            return

        if not PYDUB_AVAILABLE:

            QMessageBox.critical(
                self,
                "Pydub ontbreekt",
                (
                    "Voor het knippen is de Python-bibliotheek 'pydub' nodig, "
                    "en moet ffmpeg geinstalleerd zijn.\n\n"
                    "Installeer met:\n"
                    "python -m pip install pydub\n\n"
                    "En zorg dat ffmpeg.exe beschikbaar is via je systeem-PATH "
                    "(download op https://ffmpeg.org/download.html)."
                ),
            )

            return

        segments = self.compute_kept_segments()

        if not segments:

            QMessageBox.warning(
                self,
                "Ongeldige selectie",
                "Er blijft niets over om op te slaan met deze instellingen.",
            )

            return

        self.player.stop()

        self.status_label.setText("Bezig met knippen...")

        self.export_button.setEnabled(False)

        try:

            audio = AudioSegment.from_file(self.source_path)

            result = AudioSegment.empty()

            for start_ms, end_ms in segments:

                result += audio[start_ms:end_ms]

            output_path = self.build_output_path()

            result.export(
                str(output_path),
                format="mp3",
            )

        except Exception as exc:

            self.export_button.setEnabled(True)

            self.status_label.setText("")

            QMessageBox.critical(
                self,
                "Knippen mislukt",
                (
                    "Het bestand kon niet worden verwerkt.\n\n"
                    f"{exc}\n\n"
                    "Controleer of ffmpeg geinstalleerd en bereikbaar is via PATH."
                ),
            )

            return

        self.export_button.setEnabled(True)

        self.status_label.setText(
            f"Klaar! Nieuw bestand opgeslagen als:\n{output_path}"
        )

        QMessageBox.information(
            self,
            "Knippen voltooid",
            f"Het nieuwe bestand is opgeslagen als:\n\n{output_path}",
        )

        self.cut_completed.emit(str(output_path))

    # ========================================================
    # CLEANUP
    # ========================================================

    def closeEvent(self, event):

        self.player.stop()

        super().closeEvent(event)

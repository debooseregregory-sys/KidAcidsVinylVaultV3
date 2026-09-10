# ============================================================
# KID ACID'S VINYLVAULT V3
# BPM ANALYSATOR
#
# Loopt alle tracks in de database af, analyseert het BPM van
# de gekoppelde (voorkeurs-)MP3, slaat het op in tracks.bpm
# EN zet het ook in het Notities-veld (met een [BPM: ...] tag).
# ============================================================

import re
from pathlib import Path

from PySide6.QtCore import Qt, Signal, QThread
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QMessageBox,
    QListWidget,
    QListWidgetItem,
    QRadioButton,
    QButtonGroup,
    QProgressBar,
    QGroupBox,
)

from database.database import get_connection

try:
    import librosa
    LIBROSA_AVAILABLE = True
except ImportError:
    LIBROSA_AVAILABLE = False


BPM_TAG_PATTERN = re.compile(
    r"\[BPM:\s*[\d.]+\]"
)


# ============================================================
# BPM DETECTIE
# ============================================================

def estimate_bpm(path):
    """Schat het BPM van een audiobestand. Probeert meerdere
    librosa-API's, omdat die tussen versies is veranderd."""

    y, sr = librosa.load(
        path,
        sr=None,
        mono=True,
    )

    onset_env = librosa.onset.onset_strength(
        y=y,
        sr=sr,
    )

    tempo = None

    try:
        tempo = float(
            librosa.feature.tempo(
                onset_envelope=onset_env,
                sr=sr,
            )[0]
        )
    except AttributeError:
        pass

    if tempo is None:

        try:
            tempo = float(
                librosa.beat.tempo(
                    onset_envelope=onset_env,
                    sr=sr,
                )[0]
            )
        except AttributeError:
            pass

    if tempo is None:

        tempo_value, _ = librosa.beat.beat_track(
            onset_envelope=onset_env,
            sr=sr,
        )

        tempo = float(tempo_value)

    # Octaaf-correctie: BPM-detectie slaat soms de helft/dubbel aan.
    # Muziek onder 70 of boven 185 BPM is zeldzaam, dus corrigeren
    # we naar het meest waarschijnlijke bereik.

    while tempo < 70 and tempo > 0:
        tempo *= 2

    while tempo > 185:
        tempo /= 2

    return round(tempo, 1)


def merge_bpm_into_notes(existing_notes, bpm_value):

    tag = f"[BPM: {bpm_value}]"

    existing_notes = existing_notes or ""

    if BPM_TAG_PATTERN.search(existing_notes):

        return BPM_TAG_PATTERN.sub(
            tag,
            existing_notes,
            count=1,
        )

    stripped = existing_notes.strip()

    if stripped:
        return f"{tag}\n{stripped}"

    return tag


# ============================================================
# DATABASE HELPERS
# ============================================================

def get_analyzable_tracks(only_missing_bpm):
    """Geeft een lijst van tracks die een gekoppelde MP3 hebben,
    met release/track-info en het pad naar de voorkeurs-MP3."""

    connection = get_connection()

    try:

        query = """
            SELECT
                t.id AS track_id,
                t.position,
                t.artist AS track_artist,
                t.title AS track_title,
                t.bpm AS current_bpm,
                t.notes AS current_notes,
                r.artist AS release_artist,
                r.title AS release_title,
                m.path AS mp3_path,
                m.id AS mp3_id

            FROM tracks t

            INNER JOIN releases r
                ON r.id = t.release_id

            INNER JOIN track_mp3 tm
                ON tm.track_id = t.id

            INNER JOIN mp3_files m
                ON m.id = tm.mp3_id

            WHERE tm.is_preferred = 1
               OR tm.id = (
                    SELECT x.id
                    FROM track_mp3 x
                    WHERE x.track_id = t.id
                    ORDER BY x.is_preferred DESC, x.score DESC, x.id
                    LIMIT 1
               )

            GROUP BY t.id

            ORDER BY r.artist, r.title, t.position
        """

        rows = connection.execute(query).fetchall()

        results = []

        for row in rows:

            if only_missing_bpm and row["current_bpm"]:
                continue

            path = row["mp3_path"]

            if not path or not Path(path).exists():
                continue

            results.append(row)

        return results

    finally:

        connection.close()


def save_bpm_result(track_id, mp3_id, bpm_value, existing_notes):

    new_notes = merge_bpm_into_notes(
        existing_notes,
        bpm_value,
    )

    connection = get_connection()

    try:

        connection.execute(
            """
            UPDATE tracks
            SET bpm = ?,
                notes = ?
            WHERE id = ?
            """,
            (
                bpm_value,
                new_notes,
                track_id,
            ),
        )

        connection.execute(
            """
            UPDATE mp3_files
            SET bpm = ?
            WHERE id = ?
            """,
            (
                bpm_value,
                mp3_id,
            ),
        )

        connection.commit()

    finally:

        connection.close()


# ============================================================
# BACKGROUND WORKER
# ============================================================

class BPMAnalyzerWorker(QThread):

    track_started = Signal(int, str)
    track_finished = Signal(int, bool, str)
    all_finished = Signal(int, int)

    def __init__(self, tracks):

        super().__init__()

        self.tracks = tracks

        self._stop_requested = False

    def request_stop(self):

        self._stop_requested = True

    def run(self):

        success_count = 0
        fail_count = 0

        for index, row in enumerate(self.tracks):

            if self._stop_requested:
                break

            label = (
                f"{row['release_artist']} - {row['release_title']} "
                f"/ {row['position']} {row['track_title']}"
            )

            self.track_started.emit(index, label)

            try:

                bpm_value = estimate_bpm(row["mp3_path"])

                save_bpm_result(
                    row["track_id"],
                    row["mp3_id"],
                    bpm_value,
                    row["current_notes"],
                )

                success_count += 1

                self.track_finished.emit(
                    index,
                    True,
                    f"{bpm_value} BPM",
                )

            except Exception as exc:

                fail_count += 1

                self.track_finished.emit(
                    index,
                    False,
                    str(exc),
                )

        self.all_finished.emit(
            success_count,
            fail_count,
        )


# ============================================================
# BPM ANALYZER DIALOG
# ============================================================

class BPMAnalyzerDialog(QDialog):

    def __init__(self, parent=None):

        super().__init__(parent)

        self.setWindowTitle("BPM Analysator")
        self.setMinimumSize(760, 600)

        self.tracks = []
        self.worker = None

        self.build_ui()
        self.apply_style()

        self.scan_database()

    # ========================================================
    # BUILD UI
    # ========================================================

    def build_ui(self):

        layout = QVBoxLayout(self)

        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)

        intro_label = QLabel(
            "Analyseert het BPM van elke track met een gekoppelde MP3, "
            "en zet het resultaat zowel in het BPM-veld als in de "
            "Notities (bv. [BPM: 128.0])."
        )

        intro_label.setWordWrap(True)

        layout.addWidget(intro_label)

        # ----------------------------------------------------
        # OPTIES
        # ----------------------------------------------------

        options_group = QGroupBox("WELKE TRACKS?")

        options_layout = QVBoxLayout(options_group)

        self.mode_group = QButtonGroup(self)

        self.only_missing_radio = QRadioButton(
            "Alleen tracks zonder BPM"
        )

        self.only_missing_radio.setChecked(True)

        self.mode_group.addButton(self.only_missing_radio)

        options_layout.addWidget(self.only_missing_radio)

        self.all_tracks_radio = QRadioButton(
            "Alle tracks opnieuw analyseren (overschrijft bestaand BPM)"
        )

        self.mode_group.addButton(self.all_tracks_radio)

        options_layout.addWidget(self.all_tracks_radio)

        self.only_missing_radio.toggled.connect(
            lambda checked: self.scan_database() if checked else None
        )

        self.all_tracks_radio.toggled.connect(
            lambda checked: self.scan_database() if checked else None
        )

        layout.addWidget(options_group)

        # ----------------------------------------------------
        # LIJST
        # ----------------------------------------------------

        list_group = QGroupBox("TRACKS")

        list_layout = QVBoxLayout(list_group)

        self.track_list = QListWidget()

        list_layout.addWidget(self.track_list)

        self.count_label = QLabel("0 tracks gevonden")

        list_layout.addWidget(self.count_label)

        layout.addWidget(list_group, 1)

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

        self.start_button = QPushButton(
            "[ ♫ START ANALYSE ]"
        )

        self.start_button.setMinimumHeight(42)

        self.start_button.clicked.connect(self.start_analysis)

        button_row.addWidget(self.start_button)

        self.stop_button = QPushButton("[ STOP ]")

        self.stop_button.setEnabled(False)

        self.stop_button.clicked.connect(self.stop_analysis)

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

            QRadioButton {
                color: #ffffff;
            }

            QListWidget {
                background-color: #1c1726;
                color: #ffffff;
                border: 1px solid #55466d;
                border-radius: 5px;
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

        self.start_button.setStyleSheet(
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
    # SCAN DATABASE
    # ========================================================

    def scan_database(self):

        only_missing = self.only_missing_radio.isChecked()

        try:
            self.tracks = get_analyzable_tracks(only_missing)
        except Exception as exc:

            self.tracks = []

            QMessageBox.critical(
                self,
                "Database-fout",
                f"Kon de database niet doorzoeken.\n\n{exc}",
            )

        self.track_list.clear()

        for row in self.tracks:

            bpm_text = (
                f" (huidig: {row['current_bpm']})"
                if row["current_bpm"]
                else ""
            )

            item = QListWidgetItem(
                f"{row['release_artist']} - {row['release_title']} / "
                f"{row['position']} {row['track_title']}{bpm_text}"
            )

            self.track_list.addItem(item)

        self.count_label.setText(
            f"{len(self.tracks)} tracks gevonden"
        )

        self.progress_bar.setMaximum(
            max(len(self.tracks), 1)
        )

        self.progress_bar.setValue(0)

        self.status_label.setText("")

    # ========================================================
    # ANALYSIS
    # ========================================================

    def start_analysis(self):

        if not LIBROSA_AVAILABLE:

            QMessageBox.critical(
                self,
                "Librosa ontbreekt",
                (
                    "Voor BPM-analyse is de Python-bibliotheek 'librosa' nodig.\n\n"
                    "Installeer met:\n"
                    "python -m pip install librosa soundfile\n\n"
                    "Dit kan even duren bij de eerste installatie."
                ),
            )

            return

        if not self.tracks:

            QMessageBox.information(
                self,
                "Niets te doen",
                "Er zijn geen tracks gevonden om te analyseren.",
            )

            return

        self.progress_bar.setMaximum(len(self.tracks))

        self.progress_bar.setValue(0)

        self.status_label.setText(
            f"Bezig met analyseren (0 / {len(self.tracks)})..."
        )

        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)

        self.only_missing_radio.setEnabled(False)
        self.all_tracks_radio.setEnabled(False)

        self.worker = BPMAnalyzerWorker(self.tracks)

        self.worker.track_started.connect(self.on_track_started)
        self.worker.track_finished.connect(self.on_track_finished)
        self.worker.all_finished.connect(self.on_all_finished)

        self.worker.start()

    def stop_analysis(self):

        if self.worker is not None:

            self.worker.request_stop()

            self.stop_button.setEnabled(False)

            self.status_label.setText(
                "Wordt gestopt na huidige track..."
            )

    def on_track_started(self, index, label):

        self.status_label.setText(
            f"Bezig: {label} ({index + 1} / {len(self.tracks)})"
        )

    def on_track_finished(self, index, success, message):

        self.progress_bar.setValue(index + 1)

        item = self.track_list.item(index)

        if item is not None:

            prefix = "✓" if success else "✗"

            item.setText(f"{prefix}  {item.text()}  →  {message}")

    def on_all_finished(self, success_count, fail_count):

        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)

        self.only_missing_radio.setEnabled(True)
        self.all_tracks_radio.setEnabled(True)

        if fail_count == 0:

            self.status_label.setText(
                f"Klaar! {success_count} track(s) geanalyseerd."
            )

            QMessageBox.information(
                self,
                "Analyse voltooid",
                f"{success_count} track(s) succesvol geanalyseerd.",
            )

        else:

            self.status_label.setText(
                f"Klaar met fouten: {success_count} gelukt, {fail_count} mislukt."
            )

            QMessageBox.warning(
                self,
                "Analyse voltooid (met fouten)",
                (
                    f"{success_count} track(s) succesvol geanalyseerd.\n"
                    f"{fail_count} track(s) zijn mislukt.\n\n"
                    "Controleer of de bijbehorende MP3-bestanden nog "
                    "bestaan en niet beschadigd zijn."
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

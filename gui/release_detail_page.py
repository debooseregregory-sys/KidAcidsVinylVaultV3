import urllib.request
import os

# ============================================================
# KID ACID'S VINYLVAULT V3
# RELEASE DETAIL PAGE
#
# RELEASE + TRACK EDITOR
# ============================================================

from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QFrame,
    QMessageBox,
    QLineEdit,
    QFormLayout,
    QGroupBox,
    QFileDialog,
    QDialog,
    QDialogButtonBox,
    QTextEdit,
)

from database.database import (
    get_release_details,
    unlink_mp3_from_track,
    set_preferred_mp3,
    update_release,
)

from gui.mp3_search_dialog import MP3SearchDialog


# ============================================================
# TRACK EDIT DIALOG
# ============================================================

class TrackEditDialog(QDialog):

    def __init__(
        self,
        track,
        parent=None
    ):

        super().__init__(parent)

        self.track = track

        self.setWindowTitle(
            "Track bewerken"
        )

        self.setMinimumWidth(
            520
        )

        self.setStyleSheet(
            """
            QDialog {
                background-color: #151515;
                color: #ffffff;
            }

            QLabel {
                color: #bbbbbb;
            }

            QLineEdit,
            QTextEdit {
                background-color: #1c1726;
                color: #ffffff;
                border: 1px solid #55466d;
                border-radius: 5px;
                padding: 7px;
            }

            QLineEdit:focus,
            QTextEdit:focus {
                border: 1px solid #d84b91;
            }

            QPushButton {
                background-color: #252525;
                color: #ffffff;
                border: 1px solid #55466d;
                border-radius: 5px;
                padding: 7px 14px;
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

        self.build_ui()

    # ========================================================
    # BUILD
    # ========================================================

    def build_ui(self):

        layout = QVBoxLayout(
            self
        )

        layout.setContentsMargins(
            20,
            20,
            20,
            20
        )

        layout.setSpacing(
            12
        )

        title = QLabel(
            "TRACK BEWERKEN"
        )

        title.setStyleSheet(
            """
            QLabel {
                color: #ffffff;
                font-size: 20px;
                font-weight: bold;
            }
            """
        )

        layout.addWidget(
            title
        )

        form = QFormLayout()

        # ----------------------------------------------------
        # POSITION
        # ----------------------------------------------------

        self.edit_position = QLineEdit()

        self.edit_position.setText(
            str(
                self.track["position"]
                or ""
            )
        )

        self.edit_position.setPlaceholderText(
            "A1 / A2 / B1 / B2 / AA1 / BB1..."
        )

        form.addRow(
            "Positie:",
            self.edit_position
        )

        # ----------------------------------------------------
        # TITLE
        # ----------------------------------------------------

        self.edit_title = QLineEdit()

        self.edit_title.setText(
            str(
                self.track["title"]
                or ""
            )
        )

        form.addRow(
            "Titel:",
            self.edit_title
        )

        # ----------------------------------------------------
        # ARTIST
        # ----------------------------------------------------

        self.edit_artist = QLineEdit()

        self.edit_artist.setText(
            str(
                self.track["artist"]
                or ""
            )
        )

        form.addRow(
            "Artist:",
            self.edit_artist
        )

        # ----------------------------------------------------
        # GENRE
        # ----------------------------------------------------

        self.edit_genre = QLineEdit()

        self.edit_genre.setText(
            str(
                self.track["genre"]
                or ""
            )
        )

        form.addRow(
            "Genre:",
            self.edit_genre
        )

        # ----------------------------------------------------
        # BPM
        # ----------------------------------------------------

        self.edit_bpm = QLineEdit()

        bpm = self.track["bpm"]

        if bpm is not None:

            self.edit_bpm.setText(
                str(
                    bpm
                )
            )

        form.addRow(
            "BPM:",
            self.edit_bpm
        )

        # ----------------------------------------------------
        # DURATION
        # ----------------------------------------------------

        self.edit_duration = QLineEdit()

        duration = self.track["duration"]

        if duration is not None:

            self.edit_duration.setText(
                str(
                    duration
                )
            )

        form.addRow(
            "Duur seconden:",
            self.edit_duration
        )

        # ----------------------------------------------------
        # NOTES
        # ----------------------------------------------------

        self.edit_notes = QTextEdit()

        self.edit_notes.setMaximumHeight(
            100
        )

        self.edit_notes.setPlainText(
            str(
                self.track["notes"]
                or ""
            )
        )

        form.addRow(
            "Notities:",
            self.edit_notes
        )

        layout.addLayout(
            form
        )

        # ----------------------------------------------------
        # INFO
        # ----------------------------------------------------

        info = QLabel(
            "De MP3-koppelingen van deze track blijven behouden."
        )

        info.setStyleSheet(
            """
            QLabel {
                color: #9688aa;
                font-size: 12px;
            }
            """
        )

        layout.addWidget(
            info
        )

        # ----------------------------------------------------
        # BUTTONS
        # ----------------------------------------------------

        buttons = QDialogButtonBox()

        cancel = buttons.addButton(
            "Annuleren",
            QDialogButtonBox.ButtonRole.RejectRole
        )

        save = buttons.addButton(
            "Opslaan",
            QDialogButtonBox.ButtonRole.AcceptRole
        )

        cancel.clicked.connect(
            self.reject
        )

        save.clicked.connect(
            self.validate_and_accept
        )

        layout.addWidget(
            buttons
        )

    # ========================================================
    # VALIDATE
    # ========================================================

    def validate_and_accept(self):

        position = (
            self.edit_position.text()
            .strip()
            .upper()
        )

        title = (
            self.edit_title.text()
            .strip()
        )

        if not position:

            QMessageBox.warning(
                self,
                "Track",
                "Positie mag niet leeg zijn."
            )

            return

        if not title:

            QMessageBox.warning(
                self,
                "Track",
                "Titel mag niet leeg zijn."
            )

            return

        # ----------------------------------------------------
        # BPM
        # ----------------------------------------------------

        bpm_text = (
            self.edit_bpm.text()
            .strip()
        )

        bpm = None

        if bpm_text:

            try:

                bpm = float(
                    bpm_text.replace(
                        ",",
                        "."
                    )
                )

            except ValueError:

                QMessageBox.warning(
                    self,
                    "Ongeldige BPM",
                    "BPM moet een getal zijn."
                )

                return

        # ----------------------------------------------------
        # DURATION
        # ----------------------------------------------------

        duration_text = (
            self.edit_duration.text()
            .strip()
        )

        duration = 0

        if duration_text:

            try:

                duration = int(
                    duration_text
                )

            except ValueError:

                QMessageBox.warning(
                    self,
                    "Ongeldige duur",
                    "Duur moet een geheel getal in seconden zijn."
                )

                return

            if duration < 0:

                QMessageBox.warning(
                    self,
                    "Ongeldige duur",
                    "Duur kan niet negatief zijn."
                )

                return

        self.result_data = {
            "position": position,
            "title": title,
            "artist": (
                self.edit_artist.text()
                .strip()
            ),
            "genre": (
                self.edit_genre.text()
                .strip()
            ),
            "bpm": bpm,
            "duration": duration,
            "notes": (
                self.edit_notes.toPlainText()
                .strip()
            )
        }

        self.accept()


# ============================================================
# TRACK CARD
# ============================================================

class TrackCard(QFrame):

    play_mp3 = Signal(str)
    unlink_mp3_requested = Signal(int)
    mp3_linked = Signal()
    track_changed = Signal()

    def __init__(
        self,
        track_data,
        parent=None
    ):

        super().__init__(parent)

        self.track = track_data["track"]

        self.mp3s = track_data["mp3s"]

        self.build_ui()

    # ========================================================
    # BUILD UI
    # ========================================================

    def build_ui(self):

        self.setFrameShape(
            QFrame.Shape.StyledPanel
        )

        self.setStyleSheet(
            """
            QFrame {
                background-color: #171717;
                border: 1px solid #352d46;
                border-radius: 8px;
            }

            QLabel {
                background: transparent;
                border: none;
            }

            QPushButton {
                background-color: #252525;
                color: #ffffff;
                border: 1px solid #55466d;
                border-radius: 5px;
                padding: 7px 14px;
            }

            QPushButton:hover {
                background-color: #352d46;
                border: 1px solid #d84b91;
            }

            QPushButton:pressed {
                background-color: #55466d;
            }
            """
        )

        layout = QVBoxLayout(
            self
        )

        layout.setContentsMargins(
            18,
            14,
            18,
            14
        )

        layout.setSpacing(
            8
        )

        # ----------------------------------------------------
        # HEADER
        # ----------------------------------------------------

        header = QHBoxLayout()

        position = QLabel(
            str(
                self.track["position"]
                or ""
            )
        )

        position.setFixedWidth(
            55
        )

        position.setStyleSheet(
            """
            QLabel {
                color: #d84b91;
                font-size: 15px;
                font-weight: bold;
            }
            """
        )

        header.addWidget(
            position
        )

        title = QLabel(
            str(
                self.track["title"]
                or ""
            )
        )

        title.setStyleSheet(
            """
            QLabel {
                color: #ffffff;
                font-size: 17px;
                font-weight: bold;
            }
            """
        )

        title.setWordWrap(
            True
        )

        header.addWidget(
            title,
            1
        )

        duration = self.track["duration"]

        duration_text = ""

        if duration:

            try:

                seconds = int(
                    duration
                )

                minutes = seconds // 60

                secs = seconds % 60

                duration_text = (
                    f"{minutes}:{secs:02d}"
                )

            except (
                ValueError,
                TypeError
            ):

                duration_text = ""

        if duration_text:

            duration_label = QLabel(
                duration_text
            )

            duration_label.setStyleSheet(
                """
                QLabel {
                    color: #9688aa;
                    font-size: 12px;
                }
                """
            )

            header.addWidget(
                duration_label
            )

        bpm = self.track["bpm"]

        if bpm:

            try:

                bpm_text = (
                    f"{float(bpm):.1f} BPM"
                )

            except (
                ValueError,
                TypeError
            ):

                bpm_text = ""

            if bpm_text:

                bpm_label = QLabel(
                    bpm_text
                )

                bpm_label.setStyleSheet(
                    """
                    QLabel {
                        color: #9688aa;
                        font-size: 12px;
                        margin-left: 12px;
                    }
                    """
                )

                header.addWidget(
                    bpm_label
                )

        # ----------------------------------------------------
        # TRACK EDIT
        # ----------------------------------------------------

        edit_button = QPushButton(
            "[ TRACK BEWERKEN ]"
        )

        edit_button.setMinimumWidth(
            175
        )

        edit_button.clicked.connect(
            self.edit_track
        )

        header.addWidget(
            edit_button
        )

        # ----------------------------------------------------
        # TRACK DELETE
        # ----------------------------------------------------

        delete_button = QPushButton(
            "[ TRACK VERWIJDEREN ]"
        )

        delete_button.setMinimumWidth(
            190
        )

        delete_button.clicked.connect(
            self.delete_track
        )

        header.addWidget(
            delete_button
        )

        layout.addLayout(
            header
        )

        # ----------------------------------------------------
        # ARTIST
        # ----------------------------------------------------

        artist = QLabel(
            str(
                self.track["artist"]
                or ""
            )
        )

        artist.setStyleSheet(
            """
            QLabel {
                color: #aaaaaa;
                font-size: 13px;
            }
            """
        )

        layout.addWidget(
            artist
        )

        # ----------------------------------------------------
        # MP3
        # ----------------------------------------------------

        if not self.mp3s:

            self.build_no_mp3_section(
                layout
            )

        else:

            self.build_mp3_section(
                layout
            )

    # ========================================================
    # EDIT TRACK
    # ========================================================

    def edit_track(self):

        dialog = TrackEditDialog(
            self.track,
            self
        )

        if dialog.exec() != QDialog.DialogCode.Accepted:

            return

        data = dialog.result_data

        from database.database import get_connection

        connection = get_connection()

        try:

            connection.execute(
                """
                UPDATE tracks

                SET
                    position = ?,
                    artist = ?,
                    title = ?,
                    duration = ?,
                    bpm = ?,
                    genre = ?,
                    notes = ?

                WHERE id = ?
                """,
                (
                    data["position"],
                    data["artist"],
                    data["title"],
                    data["duration"],
                    data["bpm"],
                    data["genre"],
                    data["notes"],
                    self.track["id"]
                )
            )

            connection.commit()

        except Exception as exc:

            connection.rollback()

            QMessageBox.critical(
                self,
                "Track opslaan mislukt",
                (
                    "De track kon niet worden opgeslagen.\n\n"
                    f"{exc}"
                )
            )

            return

        finally:

            connection.close()

        self.track_changed.emit()

    # ========================================================
    # DELETE TRACK
    # ========================================================

    def delete_track(self):

        position = str(
            self.track["position"]
            or ""
        )

        title = str(
            self.track["title"]
            or ""
        )

        answer = QMessageBox.question(
            self,
            "Track verwijderen",
            (
                "Weet je zeker dat je deze track wilt verwijderen?\n\n"
                f"{position} - {title}\n\n"
                "De MP3-koppelingen van deze track worden "
                "ook verwijderd."
            ),
            QMessageBox.StandardButton.Yes
            | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if answer != QMessageBox.StandardButton.Yes:

            return

        from database.database import get_connection

        connection = get_connection()

        try:

            # ------------------------------------------------
            # Eerst alle koppelingen verwijderen
            # ------------------------------------------------

            connection.execute(
                """
                DELETE FROM track_mp3
                WHERE track_id = ?
                """,
                (
                    self.track["id"],
                )
            )

            # ------------------------------------------------
            # Daarna de track verwijderen
            # ------------------------------------------------

            connection.execute(
                """
                DELETE FROM tracks
                WHERE id = ?
                """,
                (
                    self.track["id"],
                )
            )

            connection.commit()

        except Exception as exc:

            connection.rollback()

            QMessageBox.critical(
                self,
                "Track verwijderen mislukt",
                (
                    "De track kon niet worden verwijderd.\n\n"
                    f"{exc}"
                )
            )

            return

        finally:

            connection.close()

        self.track_changed.emit()

    # ========================================================
    # NO MP3
    # ========================================================

    def build_no_mp3_section(
        self,
        layout
    ):

        row = QHBoxLayout()

        label = QLabel(
            "MP3 - Geen koppeling"
        )

        label.setStyleSheet(
            """
            QLabel {
                color: #cc6666;
                font-size: 13px;
                padding-top: 4px;
            }
            """
        )

        row.addWidget(
            label
        )

        row.addStretch()

        button = QPushButton(
            "[ ZOEK MP3 ]"
        )

        button.setMinimumWidth(
            180
        )

        button.clicked.connect(
            self.open_mp3_search
        )

        row.addWidget(
            button
        )

        layout.addLayout(
            row
        )

    # ========================================================
    # MP3 LIST
    # ========================================================

    def build_mp3_section(
        self,
        layout
    ):

        count = len(
            self.mp3s
        )

        mp3_title = QLabel(
            f"MP3 - {count} koppeling"
            + (
                "en"
                if count != 1
                else ""
            )
        )

        mp3_title.setStyleSheet(
            """
            QLabel {
                color: #77cc77;
                font-size: 13px;
                font-weight: bold;
                padding-top: 4px;
            }
            """
        )

        layout.addWidget(
            mp3_title
        )

        for mp3 in self.mp3s:

            self.build_single_mp3_row(
                layout,
                mp3
            )

        search_row = QHBoxLayout()

        search_row.addStretch()

        search_button = QPushButton(
            "[ + MP3 KOPPELEN ]"
        )

        search_button.setMinimumWidth(
            180
        )

        search_button.clicked.connect(
            self.open_mp3_search
        )

        search_row.addWidget(
            search_button
        )

        layout.addLayout(
            search_row
        )

    # ========================================================
    # SINGLE MP3 ROW
    # ========================================================

    def build_single_mp3_row(
        self,
        layout,
        mp3
    ):

        row = QHBoxLayout()

        filename = (
            mp3["filename"]
            or mp3["path"]
            or ""
        )

        file_label = QLabel(
            str(filename)
        )

        file_label.setStyleSheet(
            """
            QLabel {
                color: #c8bddb;
                font-size: 12px;
            }
            """
        )

        file_label.setWordWrap(
            True
        )

        row.addWidget(
            file_label,
            1
        )

        play_button = QPushButton(
            "[ PLAY MP3 ]"
        )

        play_button.setMinimumWidth(
            150
        )

        play_button.clicked.connect(
            lambda checked=False,
            path=mp3["path"]:
            self.play_mp3.emit(path)
        )

        row.addWidget(
            play_button
        )

        preferred_button = QPushButton(
            "[ VOORKEUR ]"
        )

        preferred_button.setMinimumWidth(
            150
        )

        if mp3["is_preferred"]:

            preferred_button.setText(
                "[ * VOORKEUR ]"
            )

            preferred_button.setStyleSheet(
                """
                QPushButton {
                    background-color: #3d3518;
                    color: #ffd966;
                    border: 1px solid #806f2f;
                    border-radius: 5px;
                    padding: 5px 8px;
                    font-weight: bold;
                }

                QPushButton:hover {
                    background-color: #54491f;
                }
                """
            )

        else:

            preferred_button.setStyleSheet(
                """
                QPushButton {
                    background-color: #252525;
                    color: #bbbbbb;
                    border: 1px solid #6d5a8a;
                    border-radius: 5px;
                    padding: 5px 8px;
                }

                QPushButton:hover {
                    background-color: #352d46;
                    color: #ffffff;
                }
                """
            )

        preferred_button.clicked.connect(
            lambda checked=False,
            link_id=mp3["link_id"]:
            self.set_preferred_mp3(
                link_id
            )
        )

        row.addWidget(
            preferred_button
        )

        unlink_button = QPushButton(
            "[ ONTKOPPEL MP3 ]"
        )

        unlink_button.setMinimumWidth(
            180
        )

        unlink_button.setStyleSheet(
            """
            QPushButton {
                background-color: #3a2020;
                color: #dd8888;
                border: 1px solid #663333;
                border-radius: 5px;
                padding: 5px 8px;
            }

            QPushButton:hover {
                background-color: #552828;
                color: #ffffff;
                border: 1px solid #cc6666;
            }
            """
        )

        unlink_button.clicked.connect(
            lambda checked=False,
            link_id=mp3["link_id"]:
            self.unlink_mp3_requested.emit(
                link_id
            )
        )

        row.addWidget(
            unlink_button
        )

        layout.addLayout(
            row
        )

    # ========================================================
    # SET PREFERRED
    # ========================================================

    def set_preferred_mp3(
        self,
        link_id
    ):

        try:

            set_preferred_mp3(
                self.track["id"],
                link_id
            )

        except Exception as exc:

            QMessageBox.critical(
                self,
                "Fout",
                (
                    "Voorkeurs-MP3 kon niet "
                    "worden ingesteld.\n\n"
                    + str(exc)
                )
            )

            return

        self.mp3_linked.emit()

    # ========================================================
    # OPEN MP3 SEARCH
    # ========================================================

    def open_mp3_search(self):

        dialog = MP3SearchDialog(
            self.track,
            self
        )

        dialog.mp3_selected.connect(
            self.link_selected_mp3
        )

        dialog.exec()

    # ========================================================
    # LINK MP3
    # ========================================================

    def link_selected_mp3(
        self,
        mp3_id,
        path
    ):

        from database.database import get_connection

        connection = get_connection()

        try:

            existing = connection.execute(
                """
                SELECT id
                FROM track_mp3

                WHERE track_id = ?
                  AND mp3_id = ?
                """,
                (
                    self.track["id"],
                    mp3_id
                )
            ).fetchone()

            if existing:

                QMessageBox.information(
                    self,
                    "MP3 al gekoppeld",
                    "Deze MP3 is al aan deze "
                    "track gekoppeld."
                )

                return

            preferred_exists = connection.execute(
                """
                SELECT id
                FROM track_mp3

                WHERE track_id = ?
                  AND is_preferred = 1

                LIMIT 1
                """,
                (
                    self.track["id"],
                )
            ).fetchone()

            is_preferred = (
                0
                if preferred_exists
                else 1
            )

            connection.execute(
                """
                INSERT INTO track_mp3
                (
                    track_id,
                    mp3_id,
                    score,
                    is_preferred,
                    manually_added
                )

                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    self.track["id"],
                    mp3_id,
                    100.0,
                    is_preferred,
                    1
                )
            )

            connection.commit()

        except Exception as error:

            connection.rollback()

            QMessageBox.critical(
                self,
                "Koppelen mislukt",
                (
                    "De MP3 kon niet worden "
                    "gekoppeld.\n\n"
                    f"{error}"
                )
            )

            return

        finally:

            connection.close()

        self.mp3_linked.emit()


# ============================================================
# SIDE HEADER
# ============================================================

class SideHeader(QFrame):

    def __init__(
        self,
        side,
        parent=None
    ):

        super().__init__(
            parent
        )

        layout = QHBoxLayout(
            self
        )

        layout.setContentsMargins(
            5,
            12,
            5,
            4
        )

        label = QLabel(
            side
        )

        label.setStyleSheet(
            """
            QLabel {
                color: #ffffff;
                font-size: 19px;
                font-weight: bold;
            }
            """
        )

        layout.addWidget(
            label
        )

        line = QFrame()

        line.setFrameShape(
            QFrame.Shape.HLine
        )

        line.setStyleSheet(
            """
            QFrame {
                color: #352d46;
            }
            """
        )

        layout.addWidget(
            line,
            1
        )


# ============================================================
# RELEASE DETAIL PAGE
# ============================================================

class ReleaseDetailPage(QWidget):

    back_requested = Signal()

    play_mp3 = Signal(str)

    def __init__(
        self,
        parent=None
    ):

        super().__init__(
            parent
        )

        self.release_id = None

        self.navigation_ids = []
        self.navigation_index = -1

        self.editing = False

        self.discogs_data = None

        self.build_ui()

    # ========================================================
    # BUILD UI
    # ========================================================

    # ========================================================
    # RELEASE NAVIGATION
    # ========================================================

    def set_navigation_ids(self, release_ids):

        self.navigation_ids = list(
            release_ids or []
        )

        if self.release_id in self.navigation_ids:

            self.navigation_index = (
                self.navigation_ids.index(
                    self.release_id
                )
            )

        else:

            self.navigation_index = -1

        self.update_navigation_buttons()

    # ========================================================
    # NAVIGATION BUTTON STATE
    # ========================================================

    def update_navigation_buttons(self):

        if not hasattr(
            self,
            "previous_button"
        ):
            return

        has_previous = (
            self.navigation_index > 0
        )

        has_next = (
            self.navigation_index >= 0
            and
            self.navigation_index
            < len(self.navigation_ids) - 1
        )

        self.previous_button.setEnabled(
            has_previous
        )

        self.next_button.setEnabled(
            has_next
        )

    # ========================================================
    # PREVIOUS RELEASE
    # ========================================================

    def go_previous_release(self):

        if self.navigation_index <= 0:
            return

        self.navigation_index -= 1

        release_id = (
            self.navigation_ids[
                self.navigation_index
            ]
        )

        self.load_release(
            release_id
        )

        self.update_navigation_buttons()

    # ========================================================
    # NEXT RELEASE
    # ========================================================

    def go_next_release(self):

        if self.navigation_index < 0:
            return

        if (
            self.navigation_index
            >= len(self.navigation_ids) - 1
        ):
            return

        self.navigation_index += 1

        release_id = (
            self.navigation_ids[
                self.navigation_index
            ]
        )

        self.load_release(
            release_id
        )

        self.update_navigation_buttons()

    def build_ui(self):

        main_layout = QVBoxLayout(
            self
        )

        main_layout.setContentsMargins(
            25,
            25,
            25,
            25
        )

        main_layout.setSpacing(
            14
        )

        # ====================================================
        # MODERN DARK / PINK INTERFACE
        # ====================================================

        self.setStyleSheet(
            """
            QWidget {
                background-color: #0f0f12;
                color: #f2f2f2;
            }

            QScrollArea {
                background-color: #0f0f12;
                border: none;
            }

            QScrollBar:vertical {
                background: #15151a;
                width: 12px;
                border-radius: 6px;
            }

            QScrollBar::handle:vertical {
                background: #d84b91;
                border-radius: 6px;
                min-height: 40px;
            }

            QScrollBar::handle:vertical:hover {
                background: #f05ca4;
            }

            QPushButton {
                background-color: #1d1d23;
                color: #f3effa;
                border: 1px solid #3a3a44;
                border-radius: 7px;
                padding: 8px 15px;
                font-weight: bold;
            }

            QPushButton:hover {
                background-color: #2b1a25;
                border: 1px solid #d84b91;
                color: #ffffff;
            }

            QPushButton:pressed {
                background-color: #d84b91;
                color: #ffffff;
            }

            QLineEdit {
                background-color: #18181d;
                color: #ffffff;
                border: 1px solid #383842;
                border-radius: 6px;
                padding: 8px;
            }

            QLineEdit:focus {
                border: 1px solid #d84b91;
            }

            QGroupBox {
                background-color: #141419;
                color: #f05ca4;
                border: 1px solid #383842;
                border-radius: 10px;
            }
            """
        )

        # ====================================================
        # TOP BAR
        # ====================================================

        top = QHBoxLayout()

        self.back_button = QPushButton(
            "[ TERUG ]"
        )

        self.back_button.setMinimumHeight(
            38
        )

        self.back_button.clicked.connect(
            self.back_requested.emit
        )

        top.addWidget(
            self.back_button
        )

        self.previous_button = QPushButton(
            "[ ◀ VORIGE ]"
        )

        self.previous_button.setMinimumHeight(
            38
        )

        self.previous_button.clicked.connect(
            self.go_previous_release
        )

        top.addWidget(
            self.previous_button
        )

        self.next_button = QPushButton(
            "[ VOLGENDE ▶ ]"
        )

        self.next_button.setMinimumHeight(
            38
        )

        self.next_button.clicked.connect(
            self.go_next_release
        )

        top.addWidget(
            self.next_button
        )

        top.addStretch()

        self.edit_button = QPushButton(
            "[ BEWERKEN ]"
        )

        self.edit_button.setMinimumHeight(
            38
        )

        self.edit_button.clicked.connect(
            self.toggle_edit_mode
        )

        top.addWidget(
            self.edit_button
        )

        main_layout.addLayout(
            top
        )

        # ====================================================
        # RELEASE INFO
        # ====================================================

        self.artist_label = QLabel()

        self.artist_label.setStyleSheet(
            """
            QLabel {
                color: #d84b91;
                font-size: 17px;
                font-weight: bold;
            }
            """
        )

        main_layout.addWidget(
            self.artist_label
        )

        self.title_label = QLabel()

        self.title_label.setStyleSheet(
            """
            QLabel {
                color: #ffffff;
                font-size: 32px;
                font-weight: bold;
                padding-bottom: 4px;
            }
            """
        )

        main_layout.addWidget(
            self.title_label
        )

        # ====================================================
        # EDITOR
        # ====================================================

        self.editor = QGroupBox(
            "RELEASEGEGEVENS"
        )

        self.editor.setVisible(
            False
        )

        self.editor.setStyleSheet(
            """
            QGroupBox {
                color: #ffffff;
                border: 1px solid #55466d;
                border-radius: 8px;
                margin-top: 8px;
                padding: 12px;
                font-weight: bold;
            }

            QLabel {
                color: #bbbbbb;
            }

            QLineEdit {
                background-color: #1c1726;
                color: #ffffff;
                border: 1px solid #55466d;
                border-radius: 5px;
                padding: 7px;
            }

            QLineEdit:focus {
                border: 1px solid #d84b91;
            }

            QPushButton {
                background-color: #252525;
                color: #ffffff;
                border: 1px solid #55466d;
                border-radius: 5px;
                padding: 7px 14px;
            }

            QPushButton:hover {
                background-color: #352d46;
                border: 1px solid #d84b91;
            }
            """
        )

        editor_layout = QVBoxLayout(
            self.editor
        )

        form = QFormLayout()

        # ----------------------------------------------------
        # ARTIST
        # ----------------------------------------------------

        self.edit_artist = QLineEdit()

        form.addRow(
            "Artist:",
            self.edit_artist
        )

        # ----------------------------------------------------
        # TITLE
        # ----------------------------------------------------

        self.edit_title = QLineEdit()

        form.addRow(
            "Titel:",
            self.edit_title
        )

        # ----------------------------------------------------
        # LABEL
        # ----------------------------------------------------

        self.edit_label = QLineEdit()

        form.addRow(
            "Label:",
            self.edit_label
        )

        # ----------------------------------------------------
        # CATALOG
        # ----------------------------------------------------

        self.edit_catalog = QLineEdit()

        form.addRow(
            "Catalogus:",
            self.edit_catalog
        )

        # ----------------------------------------------------
        # YEAR
        # ----------------------------------------------------

        self.edit_year = QLineEdit()

        form.addRow(
            "Jaar:",
            self.edit_year
        )

        # ----------------------------------------------------
        # GENRE
        # ----------------------------------------------------

        self.edit_genre = QLineEdit()

        form.addRow(
            "Genre:",
            self.edit_genre
        )

        # ----------------------------------------------------
        # STORAGE
        # ----------------------------------------------------

        self.edit_storage = QLineEdit()

        form.addRow(
            "Storage code:",
            self.edit_storage
        )

        # ----------------------------------------------------
        # DISCOGS
        # ----------------------------------------------------

        self.edit_discogs = QLineEdit()

        form.addRow(
            "Discogs ID:",
            self.edit_discogs
        )

        # ----------------------------------------------------
        # DISCOGS LINK
        # ----------------------------------------------------

        self.edit_discogs_link = QLineEdit()

        form.addRow(
            "Discogs link:",
            self.edit_discogs_link
        )

        # ----------------------------------------------------
        # COVER
        # ----------------------------------------------------

        cover_row = QHBoxLayout()

        self.edit_cover = QLineEdit()

        cover_row.addWidget(
            self.edit_cover,
            1
        )

        self.cover_button = QPushButton(
            "[ COVER KIEZEN ]"
        )

        self.cover_button.setMinimumWidth(
            180
        )

        self.cover_button.clicked.connect(
            self.choose_cover
        )

        cover_row.addWidget(
            self.cover_button
        )

        form.addRow(
            "Cover:",
            cover_row
        )

        # ----------------------------------------------------
        # COVER PREVIEW
        # ----------------------------------------------------

        self.cover_preview = QLabel(
            "GEEN COVER"
        )

        self.cover_preview.setFixedSize(
            180,
            180
        )

        self.cover_preview.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        self.cover_preview.setStyleSheet(
            """
            QLabel {
                background-color: #1c1726;
                color: #9688aa;
                border: 1px solid #55466d;
                border-radius: 6px;
            }
            """
        )

        form.addRow(
            "Preview:",
            self.cover_preview
        )

        # ----------------------------------------------------
        # NOTES
        # ----------------------------------------------------

        self.edit_notes = QLineEdit()

        form.addRow(
            "Notities:",
            self.edit_notes
        )

        editor_layout.addLayout(
            form
        )

        # ====================================================
        # DISCOGS BUTTONS
        # ====================================================

        discogs_row = QHBoxLayout()

        self.discogs_fetch_button = QPushButton(
            "[ DISCOGS OPHALEN ]"
        )

        self.discogs_fetch_button.clicked.connect(
            self.fetch_discogs
        )

        discogs_row.addWidget(
            self.discogs_fetch_button
        )

        self.discogs_take_button = QPushButton(
            "[ GEGEVENS OVERNEMEN ]"
        )

        self.discogs_take_button.setEnabled(
            False
        )

        self.discogs_take_button.clicked.connect(
            self.apply_discogs_data
        )

        discogs_row.addWidget(
            self.discogs_take_button
        )

        discogs_row.addStretch()

        editor_layout.addLayout(
            discogs_row
        )

        # ====================================================
        # SAVE
        # ====================================================

        save_row = QHBoxLayout()

        save_row.addStretch()

        self.cancel_button = QPushButton(
            "[ ANNULEREN ]"
        )

        self.cancel_button.clicked.connect(
            self.cancel_edit
        )

        save_row.addWidget(
            self.cancel_button
        )

        self.save_button = QPushButton(
            "[ OPSLAAN ]"
        )

        self.save_button.clicked.connect(
            self.save_release
        )

        save_row.addWidget(
            self.save_button
        )

        # ----------------------------------------------------
        # KLAAR
        # ----------------------------------------------------

        self.checked_button = QPushButton(
            "[ ✓ KLAAR ]"
        )

        self.checked_button.setMinimumWidth(
            140
        )

        self.checked_button.setStyleSheet(
            """
            QPushButton {
                background-color: #234d23;
                color: #ffffff;
                border: 1px solid #3d7a3d;
                border-radius: 5px;
                padding: 7px 14px;
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

        self.checked_button.clicked.connect(
            self.mark_release_checked
        )

        save_row.addWidget(
            self.checked_button
        )

        editor_layout.addLayout(
            save_row
        )

        main_layout.addWidget(
            self.editor
        )

        # ====================================================
        # INFO
        # ====================================================

        self.info_label = QLabel()

        self.info_label.setStyleSheet(
            """
            QLabel {
                color: #999999;
                font-size: 13px;
            }
            """
        )

        self.info_label.setWordWrap(
            True
        )

        main_layout.addWidget(
            self.info_label
        )

        # ====================================================
        # SEPARATOR
        # ====================================================

        line = QFrame()

        line.setFrameShape(
            QFrame.Shape.HLine
        )

        line.setStyleSheet(
            """
            QFrame {
                color: #352d46;
            }
            """
        )

        main_layout.addWidget(
            line
        )

        # ====================================================
        # TRACK TOEVOEGEN
        # ====================================================

        self.add_track_button = QPushButton(
            "[ + TRACK TOEVOEGEN ]"
        )

        self.add_track_button.setMinimumWidth(
            190
        )

        self.add_track_button.clicked.connect(
            self.add_track
        )

        main_layout.addWidget(
            self.add_track_button
        )

        # ====================================================
        # SCROLL
        # ====================================================

        self.scroll = QScrollArea()

        self.scroll.setWidgetResizable(
            True
        )

        self.scroll.setStyleSheet(
            """
            QScrollArea {
                border: none;
                background: transparent;
            }
            """
        )

        self.track_container = QWidget()

        self.track_layout = QVBoxLayout(
            self.track_container
        )

        self.track_layout.setContentsMargins(
            0,
            0,
            10,
            0
        )

        self.track_layout.setSpacing(
            8
        )

        self.track_layout.addStretch()

        self.scroll.setWidget(
            self.track_container
        )

        main_layout.addWidget(
            self.scroll,
            1
        )

    # ========================================================
    # LOAD RELEASE
    # ========================================================

    def load_release(
        self,
        release_id
    ):

        self.release_id = release_id

        self.editing = False

        self.editor.setVisible(
            False
        )

        self.edit_button.setText(
            "[ BEWERKEN ]"
        )

        data = get_release_details(
            release_id
        )

        if not data:

            self.artist_label.setText(
                "Release niet gevonden"
            )

            self.title_label.setText(
                ""
            )

            self.info_label.setText(
                ""
            )

            self.clear_tracks()

            return

        release = data["release"]

        self.artist_label.setText(
            str(
                release["artist"]
                or ""
            )
        )

        self.title_label.setText(
            str(
                release["title"]
                or ""
            )
        )

        info = []

        if release["label"]:

            info.append(
                str(
                    release["label"]
                )
            )

        if release["catalog"]:

            info.append(
                str(
                    release["catalog"]
                )
            )

        if release["year"]:

            info.append(
                str(
                    release["year"]
                )
            )

        if release["storage_code"]:

            info.append(
                f"Storage {release['storage_code']}"
            )

        if release["discogs"]:

            info.append(
                f"Discogs {release['discogs']}"
            )

        if release["genre"]:

            info.append(
                str(
                    release["genre"]
                )
            )

        self.info_label.setText(
            "  -  ".join(
                info
            )
        )

        # ----------------------------------------------------
        # EDITOR
        # ----------------------------------------------------

        self.fill_editor(
            release
        )

        # ----------------------------------------------------
        # TRACKS
        # ----------------------------------------------------

        self.clear_tracks()

        grouped = self.group_tracks(
            data["tracks"]
        )

        for side in (
            "A",
            "AA",
            "B",
            "BB"
        ):

            tracks = grouped.get(
                side,
                []
            )

            if not tracks:

                continue

            side_header = SideHeader(
                f"KANT {side}"
            )

            self.track_layout.insertWidget(
                self.track_layout.count() - 1,
                side_header
            )

            for track_data in tracks:

                self.add_track_card(
                    track_data
                )

        other_tracks = grouped.get(
            "OTHER",
            []
        )

        if other_tracks:

            side_header = SideHeader(
                "OVERIGE TRACKS"
            )

            self.track_layout.insertWidget(
                self.track_layout.count() - 1,
                side_header
            )

            for track_data in other_tracks:

                self.add_track_card(
                    track_data
                )

    # ========================================================
    # ADD TRACK CARD
    # ========================================================

    def add_track_card(
        self,
        track_data
    ):

        card = TrackCard(
            track_data
        )

        card.play_mp3.connect(
            self.play_mp3.emit
        )

        card.unlink_mp3_requested.connect(
            self.unlink_mp3
        )

        card.mp3_linked.connect(
            self.refresh_current_release
        )

        card.track_changed.connect(
            self.refresh_current_release
        )

        self.track_layout.insertWidget(
            self.track_layout.count() - 1,
            card
        )

    # ========================================================
    # FILL EDITOR
    # ========================================================

    def fill_editor(
        self,
        release
    ):

        self.edit_artist.setText(
            str(
                release["artist"]
                or ""
            )
        )

        self.edit_title.setText(
            str(
                release["title"]
                or ""
            )
        )

        self.edit_label.setText(
            str(
                release["label"]
                or ""
            )
        )

        self.edit_catalog.setText(
            str(
                release["catalog"]
                or ""
            )
        )

        self.edit_year.setText(
            str(
                release["year"]
                or ""
            )
        )

        self.edit_genre.setText(
            str(
                release["genre"]
                or ""
            )
        )

        self.edit_storage.setText(
            str(
                release["storage_code"]
                or ""
            )
        )

        self.edit_discogs.setText(
            str(
                release["discogs"]
                or ""
            )
        )

        self.edit_discogs_link.setText(
            str(
                release["discogs_link"]
                or ""
            )
        )

        self.edit_cover.setText(
            str(
                release["cover"]
                or ""
            )
        )

        self.update_cover_preview()

        self.edit_notes.setText(
            str(
                release["notes"]
                or ""
            )
        )

    # ========================================================
    # COVER PREVIEW
    # ========================================================

    def update_cover_preview(self):

        if not hasattr(
            self,
            "cover_preview"
        ):

            return

        cover = (
            self.edit_cover.text()
            .strip()
        )

        if not cover:

            self.cover_preview.clear()

            self.cover_preview.setText(
                "GEEN COVER"
            )

            return

        # ----------------------------------------------------
        # LOKALE COVER
        # ----------------------------------------------------

        if os.path.isfile(
            cover
        ):

            pixmap = QPixmap(
                cover
            )

            if not pixmap.isNull():

                self.cover_preview.setPixmap(
                    pixmap.scaled(
                        self.cover_preview.size(),
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation
                    )
                )

                return

        # ----------------------------------------------------
        # DISCOGS URL
        # ----------------------------------------------------

        if (
            cover.startswith("http://")
            or cover.startswith("https://")
        ):

            try:

                root = os.path.dirname(
                    os.path.dirname(
                        os.path.abspath(
                            __file__
                        )
                    )
                )

                covers_dir = os.path.join(
                    root,
                    "covers"
                )

                os.makedirs(
                    covers_dir,
                    exist_ok=True
                )

                local_path = os.path.join(
                    covers_dir,
                    f"release_{self.release_id}.jpg"
                )

                request = urllib.request.Request(
                    cover,
                    headers={
                        "User-Agent": "Mozilla/5.0"
                    }
                )

                with urllib.request.urlopen(
                    request,
                    timeout=20
                ) as response:

                    image_data = response.read()

                with open(
                    local_path,
                    "wb"
                ) as file:

                    file.write(
                        image_data
                    )

                pixmap = QPixmap(
                    local_path
                )

                if not pixmap.isNull():

                    self.edit_cover.setText(
                        local_path
                    )

                    self.cover_preview.setPixmap(
                        pixmap.scaled(
                            self.cover_preview.size(),
                            Qt.AspectRatioMode.KeepAspectRatio,
                            Qt.TransformationMode.SmoothTransformation
                        )
                    )

                    return

            except Exception as exc:

                print(
                    "Cover download fout:",
                    exc
                )

        # ----------------------------------------------------
        # GEEN COVER
        # ----------------------------------------------------

        self.cover_preview.clear()

        self.cover_preview.setText(
            "COVER NIET GEVONDEN"
        )

    # ========================================================
    # CHOOSE COVER
    # ========================================================

    def choose_cover(self):

        filename, _ = QFileDialog.getOpenFileName(
            self,
            "Cover kiezen",
            "",
            (
                "Afbeeldingen "
                "(*.jpg *.jpeg *.png *.webp);;"
                "Alle bestanden (*.*)"
            )
        )

        if not filename:

            return

        self.edit_cover.setText(
            filename
        )

        self.update_cover_preview()

    # ========================================================
    # EDIT MODE
    # ========================================================

    def toggle_edit_mode(self):

        if self.release_id is None:

            return

        self.editing = not self.editing

        self.editor.setVisible(
            self.editing
        )

        if self.editing:

            self.edit_button.setText(
                "[ BEWERKEN ACTIEF ]"
            )

        else:

            self.edit_button.setText(
                "[ BEWERKEN ]"
            )

    # ========================================================
    # CANCEL
    # ========================================================

    def cancel_edit(self):

        if self.release_id is None:

            return

        data = get_release_details(
            self.release_id
        )

        if data:

            self.fill_editor(
                data["release"]
            )

        self.discogs_data = None

        self.discogs_take_button.setEnabled(
            False
        )

        self.editing = False

        self.editor.setVisible(
            False
        )

        self.edit_button.setText(
            "[ BEWERKEN ]"
        )

    # ========================================================
    # FETCH DISCOGS
    # ========================================================

    def fetch_discogs(self):

        release_id = (
            self.edit_discogs.text()
            .strip()
        )

        if not release_id:

            QMessageBox.warning(
                self,
                "Discogs",
                "Vul eerst een Discogs Release ID in."
            )

            return

        try:

            from tools.discogs import (
                fetch_release_data
            )

            data = fetch_release_data(
                release_id
            )

        except Exception as exc:

            QMessageBox.critical(
                self,
                "Discogs fout",
                (
                    "Discogs release kon niet "
                    "worden opgehaald.\n\n"
                    f"{exc}"
                )
            )

            return

        if not data:

            QMessageBox.warning(
                self,
                "Discogs",
                "Discogs gaf geen releasegegevens terug."
            )

            return

        self.discogs_data = data

        message = (
            "DISCOGS RELEASE GEVONDEN\n\n"
            f"ID: {data.get('discogs', '')}\n"
            f"Artist: {data.get('artist', '')}\n"
            f"Title: {data.get('title', '')}\n"
            f"Label: {data.get('label', '')}\n"
            f"Catalog: {data.get('catalog', '')}\n"
            f"Year: {data.get('year') or ''}\n"
            f"Genre: {data.get('genre', '')}\n"
            f"Country: {data.get('country', '')}\n"
        )

        QMessageBox.information(
            self,
            "Discogs release gevonden",
            message
        )

        self.discogs_take_button.setEnabled(
            True
        )

    # ========================================================
    # APPLY DISCOGS DATA
    # ========================================================

    def apply_discogs_data(self):

        print(
            "DEBUG APPLY DISCOGS:",
            self.discogs_data
        )

        if not self.discogs_data:

            return

        data = self.discogs_data

        self.edit_artist.setText(
            str(
                data.get("artist")
                or ""
            )
        )

        self.edit_title.setText(
            str(
                data.get("title")
                or ""
            )
        )

        self.edit_label.setText(
            str(
                data.get("label")
                or ""
            )
        )

        self.edit_catalog.setText(
            str(
                data.get("catalog")
                or ""
            )
        )

        if data.get("year"):

            self.edit_year.setText(
                str(
                    data["year"]
                )
            )

        self.edit_genre.setText(
            str(
                data.get("genre")
                or ""
            )
        )

        self.edit_discogs.setText(
            str(
                data.get("discogs")
                or ""
            )
        )

        self.edit_discogs_link.setText(
            str(
                data.get("discogs_link")
                or ""
            )
        )

        if data.get("cover"):

            self.edit_cover.setText(
                str(
                    data["cover"]
                )
            )

            self.update_cover_preview()

        QMessageBox.information(
            self,
            "Discogs",
            (
                "Discogs-gegevens zijn overgenomen "
                "in de velden.\n\n"
                "De database is nog NIET gewijzigd."
            )
        )

    # ========================================================
    # MARK RELEASE AS CHECKED
    # ========================================================

    def mark_release_checked(self):

        if self.release_id is None:
            return

        try:

            from database.database import get_connection

            connection = get_connection()

            try:

                row = connection.execute(
                    "SELECT checked FROM releases WHERE id = ?",
                    (self.release_id,)
                ).fetchone()

                current = int(row[0] or 0) if row else 0

                new_value = 0 if current else 1

                connection.execute(
                    "UPDATE releases SET checked = ? WHERE id = ?",
                    (
                        new_value,
                        self.release_id
                    )
                )

                connection.commit()

            finally:

                connection.close()

        except Exception as error:

            QMessageBox.critical(
                self,
                "KLAAR opslaan mislukt",
                (
                    "De KLAAR-status kon niet worden opgeslagen.\n\n"
                    f"{error}"
                )
            )
            return

        self.update_checked_button(new_value)

    # ========================================================
    # UPDATE KLAAR BUTTON
    # ========================================================

    def update_checked_button(self, checked):

        if checked:

            self.checked_button.setText(
                "[ ✓ KLAAR - TERUGZETTEN ]"
            )

        else:

            self.checked_button.setText(
                "[ KLAAR - MARKEREN ]"
            )

    # ========================================================
    # SAVE RELEASE
    # ========================================================

    def save_release(self):

        if self.release_id is None:

            return

        artist = (
            self.edit_artist.text()
            .strip()
        )

        title = (
            self.edit_title.text()
            .strip()
        )

        label = (
            self.edit_label.text()
            .strip()
        )

        catalog = (
            self.edit_catalog.text()
            .strip()
        )

        year_text = (
            self.edit_year.text()
            .strip()
        )

        genre = (
            self.edit_genre.text()
            .strip()
        )

        storage_code = (
            self.edit_storage.text()
            .strip()
        )

        discogs = (
            self.edit_discogs.text()
            .strip()
        )

        discogs_link = (
            self.edit_discogs_link.text()
            .strip()
        )

        cover = (
            self.edit_cover.text()
            .strip()
        )

        notes = (
            self.edit_notes.text()
            .strip()
        )

        if not artist:

            QMessageBox.warning(
                self,
                "Opslaan",
                "Artist mag niet leeg zijn."
            )

            return

        if not title:

            QMessageBox.warning(
                self,
                "Opslaan",
                "Titel mag niet leeg zijn."
            )

            return

        # ----------------------------------------------------
        # YEAR
        # ----------------------------------------------------

        year = None

        if year_text:

            try:

                year = int(
                    year_text
                )

            except ValueError:

                QMessageBox.warning(
                    self,
                    "Ongeldig jaar",
                    "Het jaar moet een getal zijn."
                )

                return

            if year < 1800 or year > 2100:

                QMessageBox.warning(
                    self,
                    "Ongeldig jaar",
                    "Vul een geldig jaar in."
                )

                return

        # ----------------------------------------------------
        # SAVE
        # ----------------------------------------------------

        try:

            update_release(
                release_id=self.release_id,
                artist=artist,
                title=title,
                label=label,
                catalog=catalog,
                year=year,
                genre=genre,
                storage_code=storage_code,
                discogs=discogs,
                discogs_link=discogs_link,
                cover=cover,
                notes=notes
            )

        except Exception as exc:

            QMessageBox.critical(
                self,
                "Opslaan mislukt",
                (
                    "De release kon niet worden "
                    "opgeslagen.\n\n"
                    f"{exc}"
                )
            )

            return

        self.discogs_data = None

        self.discogs_take_button.setEnabled(
            False
        )

        QMessageBox.information(
            self,
            "Opgeslagen",
            "De releasegegevens zijn opgeslagen."
        )

        self.load_release(
            self.release_id
        )

    # ========================================================
    # ADD TRACK
    # ========================================================

    def add_track(self):

        if self.release_id is None:

            return

        new_track = {
            "position": "",
            "artist": "",
            "title": "",
            "genre": "",
            "bpm": None,
            "duration": 0,
            "notes": "",
        }

        dialog = TrackEditDialog(
            new_track,
            self
        )

        if dialog.exec() != QDialog.DialogCode.Accepted:

            return

        data = dialog.result_data

        position = (
            str(
                data["position"]
                or ""
            )
            .strip()
            .upper()
        )

        title = (
            str(
                data["title"]
                or ""
            )
            .strip()
        )

        if not position:

            QMessageBox.warning(
                self,
                "Track toevoegen",
                "Vul een positie in, bijvoorbeeld A1, A2 of B1."
            )

            return

        if not title:

            QMessageBox.warning(
                self,
                "Track toevoegen",
                "Vul een titel in."
            )

            return

        from database.database import get_connection

        connection = get_connection()

        try:

            # ------------------------------------------------
            # Controle op dubbele positie binnen dezelfde
            # release
            # ------------------------------------------------

            existing_position = connection.execute(
                """
                SELECT id
                FROM tracks
                WHERE release_id = ?
                  AND UPPER(TRIM(position)) = ?
                LIMIT 1
                """,
                (
                    self.release_id,
                    position
                )
            ).fetchone()

            if existing_position:

                answer = QMessageBox.question(
                    self,
                    "Positie bestaat al",
                    (
                        f"Er bestaat al een track met positie "
                        f"{position}.\n\n"
                        "Toch toevoegen?"
                    ),
                    QMessageBox.StandardButton.Yes
                    | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No
                )

                if answer != QMessageBox.StandardButton.Yes:

                    connection.close()

                    return

            connection.execute(
                """
                INSERT INTO tracks
                (
                    release_id,
                    position,
                    artist,
                    title,
                    duration,
                    bpm,
                    genre,
                    notes
                )
                VALUES
                (
                    ?,
                    ?,
                    ?,
                    ?,
                    ?,
                    ?,
                    ?,
                    ?
                )
                """,
                (
                    self.release_id,
                    position,
                    data["artist"],
                    title,
                    data["duration"],
                    data["bpm"],
                    data["genre"],
                    data["notes"],
                )
            )

            connection.commit()

        except Exception as exc:

            connection.rollback()

            QMessageBox.critical(
                self,
                "Track toevoegen mislukt",
                (
                    "De nieuwe track kon niet worden "
                    "toegevoegd.\n\n"
                    f"{exc}"
                )
            )

            return

        finally:

            connection.close()

        self.load_release(
            self.release_id
        )

        QMessageBox.information(
            self,
            "Track toegevoegd",
            (
                "De track is toegevoegd.\n\n"
                f"{position} - {title}"
            )
        )

    # ========================================================
    # REFRESH
    # ========================================================

    def refresh_current_release(self):

        if self.release_id is None:

            return

        self.load_release(
            self.release_id
        )

    # ========================================================
    # UNLINK MP3
    # ========================================================

    def unlink_mp3(
        self,
        link_id
    ):

        answer = QMessageBox.question(
            self,
            "MP3 ontkoppelen",
            (
                "Deze MP3-koppeling verwijderen?\n\n"
                "Het MP3-bestand zelf wordt NIET verwijderd."
            ),
            QMessageBox.StandardButton.Yes
            | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if answer != QMessageBox.StandardButton.Yes:

            return

        try:

            unlink_mp3_from_track(
                link_id
            )

        except Exception as exc:

            QMessageBox.critical(
                self,
                "Fout",
                (
                    "MP3 kon niet worden "
                    "ontkoppeld.\n\n"
                    + str(exc)
                )
            )

            return

        self.load_release(
            self.release_id
        )

    # ========================================================
    # GROUP TRACKS
    # ========================================================

    @staticmethod
    def group_tracks(
        tracks
    ):

        groups = {
            "A": [],
            "AA": [],
            "B": [],
            "BB": [],
            "OTHER": [],
        }

        for track_data in tracks:

            track = track_data["track"]

            position = (
                str(
                    track["position"]
                    or ""
                )
                .strip()
                .upper()
            )

            if position.startswith(
                "AA"
            ):

                groups["AA"].append(
                    track_data
                )

            elif position.startswith(
                "BB"
            ):

                groups["BB"].append(
                    track_data
                )

            elif position.startswith(
                "A"
            ):

                groups["A"].append(
                    track_data
                )

            elif position.startswith(
                "B"
            ):

                groups["B"].append(
                    track_data
                )

            else:

                groups["OTHER"].append(
                    track_data
                )

        for key in groups:

            groups[key].sort(
                key=lambda item:
                ReleaseDetailPage.position_sort_key(
                    item["track"]["position"]
                )
            )

        return groups

    # ========================================================
    # POSITION SORT
    # ========================================================

    @staticmethod
    def position_sort_key(
        position
    ):

        value = (
            str(position or "")
            .strip()
            .upper()
        )

        side_order = {
            "A": 0,
            "AA": 1,
            "B": 2,
            "BB": 3,
        }

        for side in (
            "AA",
            "BB",
            "A",
            "B"
        ):

            if value.startswith(
                side
            ):

                number = (
                    value[len(side):]
                    .strip()
                )

                try:

                    number_value = float(
                        number
                    )

                except (
                    ValueError,
                    TypeError
                ):

                    number_value = 9999

                return (
                    side_order[side],
                    number_value,
                    value
                )

        return (
            99,
            9999,
            value
        )

    # ========================================================
    # CLEAR TRACKS
    # ========================================================

    def clear_tracks(self):

        while (
            self.track_layout.count()
            > 1
        ):

            item = (
                self.track_layout.takeAt(
                    0
                )
            )

            widget = item.widget()

            if widget:

                widget.deleteLater()

    # ========================================================
    # END
    # ========================================================
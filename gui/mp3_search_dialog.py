# ============================================================
# KID ACID'S VINYLVAULT V3
# MP3 SEARCH / LINK DIALOG
# ============================================================

from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QFileDialog,
)

from database.database import get_connection


# ============================================================
# MP3 SEARCH DIALOG
# ============================================================

class MP3SearchDialog(QDialog):
    """
    Zoek een MP3 in de bestaande MP3-database.

    Mogelijkheden:
    - zoeken op artiest / titel
    - bestaande MP3 uit database selecteren
    - controleren of het opgeslagen bestand bestaat
    - rechtstreeks een MP3-bestand op D: kiezen
    - gekozen bestand aan de huidige vinyltrack koppelen
    """

    mp3_selected = Signal(int, str)

    def __init__(
        self,
        track,
        parent=None
    ):

        super().__init__(
            parent
        )

        self.track = track

        self.results = []

        self.selected_database_row = None

        self.build_ui()

        artist = str(
            track["artist"] or ""
        )

        title = str(
            track["title"] or ""
        )

        self.artist_edit.setText(
            artist
        )

        self.title_edit.setText(
            title
        )

        self.setWindowTitle(
            "MP3 zoeken"
        )

        self.resize(
            1050,
            700
        )

        self.search()

    # ========================================================
    # UI
    # ========================================================

    def build_ui(
        self
    ):

        self.setStyleSheet(
            """
            QDialog {
                background-color: #171717;
                color: #ffffff;
            }

            QLabel {
                color: #ffffff;
            }

            QLabel#dialogTitle {
                color: #ff69b4;
                font-size: 18px;
                font-weight: bold;
                padding-bottom: 8px;
            }

            QLabel#infoLabel {
                color: #aaaaaa;
                padding: 5px 0;
            }

            QLabel#statusLabel {
                color: #ff69b4;
                font-weight: bold;
                padding: 5px 0;
            }

            QLineEdit {
                background-color: #252525;
                color: #ffffff;
                border: 1px solid #444444;
                border-radius: 5px;
                padding: 8px;
            }

            QLineEdit:focus {
                border: 1px solid #ff69b4;
            }

            QListWidget {
                background-color: #111111;
                color: #ffffff;
                border: 1px solid #333333;
                border-radius: 5px;
                outline: none;
            }

            QListWidget::item {
                padding: 10px;
                border-bottom: 1px solid #292929;
            }

            QListWidget::item:hover {
                background-color: #2a1823;
            }

            QListWidget::item:selected {
                background-color: #713957;
                color: #ffffff;
            }

            QPushButton {
                background-color: #252525;
                color: #ffffff;
                border: 1px solid #444444;
                border-radius: 5px;
                padding: 8px 14px;
            }

            QPushButton:hover {
                background-color: #35202d;
                border: 1px solid #ff69b4;
                color: #ff69b4;
            }

            QPushButton:pressed {
                background-color: #51283f;
            }

            QPushButton:disabled {
                background-color: #202020;
                color: #666666;
                border: 1px solid #333333;
            }

            QPushButton#linkButton {
                background-color: #713957;
                color: #ffffff;
                border: 1px solid #ff69b4;
                font-weight: bold;
            }

            QPushButton#linkButton:hover {
                background-color: #984b74;
            }

            QPushButton#fileButton {
                background-color: #252525;
                color: #ff69b4;
                border: 1px solid #ff69b4;
                font-weight: bold;
            }

            QPushButton#fileButton:hover {
                background-color: #35202d;
            }
            """
        )

        layout = QVBoxLayout(
            self
        )

        layout.setContentsMargins(
            14,
            14,
            14,
            14
        )

        layout.setSpacing(
            8
        )

        # ====================================================
        # TITLE
        # ====================================================

        title_label = QLabel(
            f"MP3 zoeken voor: "
            f"{self.track['position']} — "
            f"{self.track['artist']} - "
            f"{self.track['title']}"
        )

        title_label.setObjectName(
            "dialogTitle"
        )

        layout.addWidget(
            title_label
        )

        # ====================================================
        # SEARCH ROW
        # ====================================================

        search_row = QHBoxLayout()

        search_row.setSpacing(
            6
        )

        self.artist_edit = QLineEdit()

        self.artist_edit.setPlaceholderText(
            "Artiest"
        )

        self.title_edit = QLineEdit()

        self.title_edit.setPlaceholderText(
            "Titel"
        )

        search_button = QPushButton(
            "🔎 Zoeken"
        )

        search_button.clicked.connect(
            self.search
        )

        self.artist_edit.returnPressed.connect(
            self.search
        )

        self.title_edit.returnPressed.connect(
            self.search
        )

        search_row.addWidget(
            self.artist_edit,
            1
        )

        search_row.addWidget(
            self.title_edit,
            1
        )

        search_row.addWidget(
            search_button
        )

        layout.addLayout(
            search_row
        )

        # ====================================================
        # INFO
        # ====================================================

        self.info_label = QLabel(
            "Zoeken in MP3-database..."
        )

        self.info_label.setObjectName(
            "infoLabel"
        )

        layout.addWidget(
            self.info_label
        )

        # ====================================================
        # RESULTS
        # ====================================================

        self.results_list = QListWidget()

        self.results_list.itemSelectionChanged.connect(
            self.selection_changed
        )

        self.results_list.itemDoubleClicked.connect(
            self.select_result
        )

        layout.addWidget(
            self.results_list,
            1
        )

        # ====================================================
        # STATUS
        # ====================================================

        self.status_label = QLabel(
            ""
        )

        self.status_label.setObjectName(
            "statusLabel"
        )

        layout.addWidget(
            self.status_label
        )

        # ====================================================
        # BUTTONS
        # ====================================================

        button_row = QHBoxLayout()

        # ----------------------------------------------------
        # DIRECT FILE
        # ----------------------------------------------------

        self.file_button = QPushButton(
            "📁 MP3 BESTAND KIEZEN"
        )

        self.file_button.setObjectName(
            "fileButton"
        )

        self.file_button.clicked.connect(
            self.choose_mp3_file
        )

        button_row.addWidget(
            self.file_button
        )

        button_row.addStretch()

        # ----------------------------------------------------
        # CANCEL
        # ----------------------------------------------------

        cancel_button = QPushButton(
            "Annuleren"
        )

        cancel_button.clicked.connect(
            self.reject
        )

        button_row.addWidget(
            cancel_button
        )

        # ----------------------------------------------------
        # LINK
        # ----------------------------------------------------

        self.link_button = QPushButton(
            "✓ MP3 KOPPELEN"
        )

        self.link_button.setObjectName(
            "linkButton"
        )

        self.link_button.setEnabled(
            False
        )

        self.link_button.clicked.connect(
            self.select_result
        )

        button_row.addWidget(
            self.link_button
        )

        layout.addLayout(
            button_row
        )

    # ========================================================
    # NORMALIZE
    # ========================================================

    @staticmethod
    def normalize(
        value
    ):

        value = str(
            value or ""
        )

        replacements = (
            "_",
            "-",
            "(",
            ")",
            "[",
            "]",
            "{",
            "}",
        )

        value = value.lower()

        for char in replacements:

            value = value.replace(
                char,
                " "
            )

        return " ".join(
            value.split()
        )

    # ========================================================
    # SEARCH
    # ========================================================

    def search(
        self
    ):

        artist = self.normalize(
            self.artist_edit.text()
        )

        title = self.normalize(
            self.title_edit.text()
        )

        self.results_list.clear()

        self.results = []

        self.selected_database_row = None

        self.link_button.setEnabled(
            False
        )

        if not artist and not title:

            self.info_label.setText(
                "Geef een artiest of titel op."
            )

            self.status_label.setText(
                ""
            )

            return

        connection = get_connection()

        try:

            rows = connection.execute(
                """
                SELECT
                    id,
                    artist,
                    title,
                    filename,
                    path
                FROM mp3_files
                ORDER BY
                    artist COLLATE NOCASE,
                    title COLLATE NOCASE,
                    filename COLLATE NOCASE
                """
            ).fetchall()

        finally:

            connection.close()

        scored = []

        for row in rows:

            mp3_artist = self.normalize(
                row["artist"]
            )

            mp3_title = self.normalize(
                row["title"]
            )

            filename = self.normalize(
                row["filename"]
            )

            score = 0

            # ------------------------------------------------
            # EXACT ARTIST + TITLE
            # ------------------------------------------------

            if artist and title:

                if (
                    mp3_artist == artist
                    and mp3_title == title
                ):

                    score = 1000

            # ------------------------------------------------
            # EXACT ARTIST + TITLE IN TITLE
            # ------------------------------------------------

            if score == 0 and artist and title:

                if (
                    mp3_artist == artist
                    and title in mp3_title
                ):

                    score = 850

            # ------------------------------------------------
            # EXACT TITLE + ARTIST IN ARTIST
            # ------------------------------------------------

            if score == 0 and artist and title:

                if (
                    mp3_title == title
                    and artist in mp3_artist
                ):

                    score = 825

            # ------------------------------------------------
            # ARTIST + TITLE IN FILENAME
            # ------------------------------------------------

            if score == 0 and artist and title:

                if (
                    artist in filename
                    and title in filename
                ):

                    score = 750

            # ------------------------------------------------
            # EXACT TITLE
            # ------------------------------------------------

            if score == 0 and title:

                if mp3_title == title:

                    score = 600

            # ------------------------------------------------
            # TITLE IN MP3 TITLE
            # ------------------------------------------------

            if score == 0 and title:

                if title in mp3_title:

                    score = 450

            # ------------------------------------------------
            # TITLE IN FILENAME
            # ------------------------------------------------

            if score == 0 and title:

                if title in filename:

                    score = 350

            # ------------------------------------------------
            # EXACT ARTIST
            # ------------------------------------------------

            if score == 0 and artist:

                if mp3_artist == artist:

                    score = 250

            # ------------------------------------------------
            # ARTIST IN MP3 ARTIST
            # ------------------------------------------------

            if score == 0 and artist:

                if artist in mp3_artist:

                    score = 150

            # ------------------------------------------------
            # ARTIST IN FILENAME
            # ------------------------------------------------

            if score == 0 and artist:

                if artist in filename:

                    score = 100

            if score > 0:

                scored.append(
                    (
                        score,
                        row
                    )
                )

        scored.sort(
            key=lambda x: (
                -x[0],
                str(
                    x[1]["artist"] or ""
                ).lower(),
                str(
                    x[1]["title"] or ""
                ).lower(),
                str(
                    x[1]["filename"] or ""
                ).lower(),
            )
        )

        limited = scored[:300]

        self.results = [
            row
            for score, row in limited
        ]

        # ====================================================
        # SHOW RESULTS
        # ====================================================

        for score, row in limited:

            artist_text = (
                row["artist"]
                or "Onbekende artiest"
            )

            title_text = (
                row["title"]
                or "Onbekende titel"
            )

            filename = (
                row["filename"]
                or ""
            )

            path = (
                row["path"]
                or ""
            )

            exists = False

            if path:

                try:

                    exists = Path(
                        path
                    ).exists()

                except Exception:

                    exists = False

            if exists:

                file_status = (
                    "✓ BESTAND BESTAAT"
                )

            else:

                file_status = (
                    "⚠ PAD BESTAAT NIET"
                )

            item = QListWidgetItem()

            item.setText(
                f"[{score}]  "
                f"{artist_text} — "
                f"{title_text}\n"
                f"    {filename}\n"
                f"    {path}\n"
                f"    {file_status}"
            )

            item.setData(
                Qt.ItemDataRole.UserRole,
                row["id"]
            )

            item.setData(
                Qt.ItemDataRole.UserRole + 1,
                path
            )

            item.setData(
                Qt.ItemDataRole.UserRole + 2,
                score
            )

            self.results_list.addItem(
                item
            )

        self.info_label.setText(
            f"{len(self.results)} kandidaten gevonden"
        )

        self.status_label.setText(
            "Selecteer de juiste MP3."
        )

    # ========================================================
    # SELECTION CHANGED
    # ========================================================

    def selection_changed(
        self
    ):

        item = self.results_list.currentItem()

        if item is None:

            self.selected_database_row = None

            self.link_button.setEnabled(
                False
            )

            self.status_label.setText(
                ""
            )

            return

        mp3_id = item.data(
            Qt.ItemDataRole.UserRole
        )

        path = item.data(
            Qt.ItemDataRole.UserRole + 1
        )

        self.selected_database_row = mp3_id

        self.link_button.setEnabled(
            True
        )

        if path:

            try:

                exists = Path(
                    path
                ).exists()

            except Exception:

                exists = False

        else:

            exists = False

        if exists:

            self.status_label.setText(
                "✓ Bestand bestaat — klaar om te koppelen."
            )

        else:

            self.status_label.setText(
                "⚠ Dit MP3-record heeft een oud/ontbrekend pad."
            )

    # ========================================================
    # CHOOSE MP3 FILE
    # ========================================================

    def choose_mp3_file(
        self
    ):

        start_folder = (
            r"D:\01. MP3's"
        )

        if not Path(
            start_folder
        ).exists():

            start_folder = str(
                Path.home()
            )

        filename, selected_filter = QFileDialog.getOpenFileName(
            self,
            "MP3-bestand kiezen",
            start_folder,
            "MP3 bestanden (*.mp3);;Alle bestanden (*.*)"
        )

        if not filename:

            return

        selected_path = Path(
            filename
        )

        if not selected_path.exists():

            QMessageBox.warning(
                self,
                "Bestand niet gevonden",
                (
                    "Het gekozen bestand bestaat niet:\n\n"
                    f"{selected_path}"
                )
            )

            return

        if selected_path.suffix.lower() != ".mp3":

            answer = QMessageBox.question(
                self,
                "Geen MP3",
                (
                    "Dit bestand heeft geen .mp3-extensie.\n\n"
                    "Toch gebruiken?"
                ),
                QMessageBox.StandardButton.Yes
                | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )

            if answer != QMessageBox.StandardButton.Yes:

                return

        # ====================================================
        # TRY TO FIND EXISTING DATABASE RECORD
        # ====================================================

        connection = get_connection()

        try:

            row = connection.execute(
                """
                SELECT
                    id,
                    artist,
                    title,
                    filename,
                    path
                FROM mp3_files
                WHERE path = ?
                LIMIT 1
                """,
                (
                    str(selected_path),
                )
            ).fetchone()

            if row is None:

                row = connection.execute(
                    """
                    SELECT
                        id,
                        artist,
                        title,
                        filename,
                        path
                    FROM mp3_files
                    WHERE filename = ?
                    LIMIT 1
                    """,
                    (
                        selected_path.name,
                    )
                ).fetchone()

        finally:

            connection.close()

        # ====================================================
        # EXISTING RECORD
        # ====================================================

        if row is not None:

            mp3_id = row["id"]

            # ------------------------------------------------
            # IMPORTANT:
            # Update old path when same file was moved.
            # ------------------------------------------------

            old_path = row["path"] or ""

            if old_path != str(
                selected_path
            ):

                connection = get_connection()

                try:

                    connection.execute(
                        """
                        UPDATE mp3_files
                        SET path = ?
                        WHERE id = ?
                        """,
                        (
                            str(selected_path),
                            mp3_id
                        )
                    )

                    connection.commit()

                finally:

                    connection.close()

            artist = (
                row["artist"]
                or ""
            )

            title = (
                row["title"]
                or selected_path.stem
            )

            answer = QMessageBox.question(
                self,
                "MP3 gevonden",
                (
                    "Deze MP3 bestaat al in de MP3-database.\n\n"
                    f"MP3 ID: {mp3_id}\n"
                    f"Bestand: {selected_path.name}\n\n"
                    f"Oude locatie:\n"
                    f"{old_path}\n\n"
                    f"Nieuwe locatie:\n"
                    f"{selected_path}\n\n"
                    "Deze MP3 koppelen aan de track?"
                ),
                QMessageBox.StandardButton.Yes
                | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.Yes
            )

            if answer != QMessageBox.StandardButton.Yes:

                return

            self.mp3_selected.emit(
                mp3_id,
                str(selected_path)
            )

            self.accept()

            return

        # ====================================================
        # NO DATABASE RECORD
        # ====================================================

        answer = QMessageBox.question(
            self,
            "Nieuwe MP3",
            (
                "Deze MP3 staat nog niet in de MP3-database.\n\n"
                f"{selected_path.name}\n\n"
                "Moet deze MP3 eerst aan de database "
                "worden toegevoegd en daarna gekoppeld?"
            ),
            QMessageBox.StandardButton.Yes
            | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes
        )

        if answer != QMessageBox.StandardButton.Yes:

            return

        # ====================================================
        # READ BASIC INFORMATION FROM FILENAME
        # ====================================================

        filename_stem = selected_path.stem

        detected_artist = ""
        detected_title = filename_stem

        if " - " in filename_stem:

            parts = filename_stem.split(
                " - ",
                1
            )

            detected_artist = parts[0].strip()

            detected_title = parts[1].strip()

        # ====================================================
        # INSERT NEW MP3 RECORD
        # ====================================================

        connection = get_connection()

        try:

            cursor = connection.execute(
                """
                INSERT INTO mp3_files
                (
                    artist,
                    title,
                    filename,
                    path
                )
                VALUES (?, ?, ?, ?)
                """,
                (
                    detected_artist,
                    detected_title,
                    selected_path.name,
                    str(selected_path)
                )
            )

            mp3_id = cursor.lastrowid

            connection.commit()

        except Exception as exc:

            connection.rollback()

            QMessageBox.critical(
                self,
                "MP3 toevoegen mislukt",
                (
                    "De MP3 kon niet aan de database "
                    "worden toegevoegd.\n\n"
                    f"{exc}"
                )
            )

            return

        finally:

            connection.close()

        QMessageBox.information(
            self,
            "MP3 toegevoegd",
            (
                "MP3 toegevoegd aan de database.\n\n"
                f"ID: {mp3_id}\n"
                f"Bestand: {selected_path.name}"
            )
        )

        self.mp3_selected.emit(
            mp3_id,
            str(selected_path)
        )

        self.accept()

    # ========================================================
    # SELECT RESULT
    # ========================================================

    def select_result(
        self,
        item=None
    ):

        # ----------------------------------------------------
        # QPushButton.clicked geeft een bool door.
        # Daarom controleren we of item werkelijk een item is.
        # ----------------------------------------------------

        if (
            item is None
            or not isinstance(
                item,
                QListWidgetItem
            )
        ):

            item = self.results_list.currentItem()

        if item is None:

            return

        mp3_id = item.data(
            Qt.ItemDataRole.UserRole
        )

        path = item.data(
            Qt.ItemDataRole.UserRole + 1
        )

        if not mp3_id:

            return

        row = None

        for candidate in self.results:

            if candidate["id"] == mp3_id:

                row = candidate

                break

        if row is None:

            return

        artist = (
            row["artist"]
            or ""
        )

        title = (
            row["title"]
            or ""
        )

        filename = (
            row["filename"]
            or ""
        )

        if not path:

            path = (
                row["path"]
                or ""
            )

        # ====================================================
        # CHECK FILE
        # ====================================================

        file_exists = False

        if path:

            try:

                file_exists = Path(
                    path
                ).exists()

            except Exception:

                file_exists = False

        # ====================================================
        # FILE EXISTS
        # ====================================================

        if file_exists:

            answer = QMessageBox.question(
                self,
                "MP3 koppelen",
                (
                    "Deze MP3 koppelen aan:\n\n"
                    f"{self.track['position']} — "
                    f"{self.track['artist']} - "
                    f"{self.track['title']}\n\n"
                    "MP3:\n"
                    f"{artist} - {title}\n\n"
                    f"Bestand:\n"
                    f"{filename}\n\n"
                    f"Pad:\n"
                    f"{path}\n\n"
                    "✓ Bestand bestaat\n\n"
                    "Doorgaan?"
                ),
                QMessageBox.StandardButton.Yes
                | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )

        # ====================================================
        # FILE DOES NOT EXIST
        # ====================================================

        else:

            answer = QMessageBox.warning(
                self,
                "Oud MP3-pad",
                (
                    "Deze MP3 staat in de database, "
                    "maar het opgeslagen pad bestaat niet meer.\n\n"
                    f"MP3:\n"
                    f"{filename}\n\n"
                    f"Oud pad:\n"
                    f"{path}\n\n"
                    "Je kunt deze koppeling wel maken, "
                    "maar hij zal pas kunnen afspelen "
                    "als het pad wordt hersteld.\n\n"
                    "Wil je toch koppelen?"
                ),
                QMessageBox.StandardButton.Yes
                | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )

        if answer != QMessageBox.StandardButton.Yes:

            return

        self.mp3_selected.emit(
            mp3_id,
            path
        )

        self.accept()
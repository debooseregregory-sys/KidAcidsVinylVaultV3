try:
    from gui.app_settings import match_mp3_minimum_score, discogs_match_mode
except ImportError:
    def discogs_match_mode():
        try:
            from PySide6.QtCore import QSettings
            mode = str(QSettings("Kid Acid", "MusicVault").value("discogs_match_mode", "Balanced") or "Balanced")
            return mode if mode in ("Strict", "Balanced", "Flexible") else "Balanced"
        except Exception:
            return "Balanced"

    def match_mp3_minimum_score():
        mode = discogs_match_mode()
        if mode == "Strict":
            return 750
        if mode == "Flexible":
            return 250
        return 450


# ============================================================
# KID ACID'S VINYLVAULT V3
# MP3 SEARCH / LINK DIALOG
# ============================================================

from pathlib import Path

from PySide6.QtCore import (
    Qt,
    Signal,
    Slot,
    QObject,
    QThread,
    QSettings,
)

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
# MP3 SEARCH WORKER
# ============================================================

class MP3SearchWorker(QObject):

    finished = Signal(object, int, int)
    error = Signal(str)

    def __init__(
        self,
        artist,
        title,
        search_folder,
    ):

        super().__init__()

        self.artist = artist
        self.title = title
        self.search_folder = search_folder

        self.cancelled = False

    def cancel(self):

        self.cancelled = True

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

    @Slot()
    def run(self):

        try:

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

            if self.cancelled:

                return

            scored = []

            # =================================================
            # SEARCH DATABASE
            # =================================================

            for row in rows:

                if self.cancelled:

                    return

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

                # ---------------------------------------------
                # EXACT ARTIST + TITLE
                # ---------------------------------------------

                if self.artist and self.title:

                    if (
                        mp3_artist == self.artist
                        and mp3_title == self.title
                    ):

                        score = 1000

                # ---------------------------------------------
                # EXACT ARTIST + TITLE IN TITLE
                # ---------------------------------------------

                if (
                    score == 0
                    and self.artist
                    and self.title
                ):

                    if (
                        mp3_artist == self.artist
                        and self.title in mp3_title
                    ):

                        score = 850

                # ---------------------------------------------
                # EXACT TITLE + ARTIST IN ARTIST
                # ---------------------------------------------

                if (
                    score == 0
                    and self.artist
                    and self.title
                ):

                    if (
                        mp3_title == self.title
                        and self.artist in mp3_artist
                    ):

                        score = 825

                # ---------------------------------------------
                # ARTIST + TITLE IN FILENAME
                # ---------------------------------------------

                if (
                    score == 0
                    and self.artist
                    and self.title
                ):

                    if (
                        self.artist in filename
                        and self.title in filename
                    ):

                        score = 750

                # ---------------------------------------------
                # EXACT TITLE
                # ---------------------------------------------

                if (
                    score == 0
                    and self.title
                ):

                    if mp3_title == self.title:

                        score = 600

                # ---------------------------------------------
                # TITLE IN MP3 TITLE
                # ---------------------------------------------

                if (
                    score == 0
                    and self.title
                ):

                    if self.title in mp3_title:

                        score = 450

                # ---------------------------------------------
                # TITLE IN FILENAME
                # ---------------------------------------------

                if (
                    score == 0
                    and self.title
                ):

                    if self.title in filename:

                        score = 350

                # ---------------------------------------------
                # EXACT ARTIST
                # ---------------------------------------------

                if (
                    score == 0
                    and self.artist
                ):

                    if mp3_artist == self.artist:

                        score = 250

                # ---------------------------------------------
                # ARTIST IN MP3 ARTIST
                # ---------------------------------------------

                if (
                    score == 0
                    and self.artist
                ):

                    if self.artist in mp3_artist:

                        score = 150

                # ---------------------------------------------
                # ARTIST IN FILENAME
                # ---------------------------------------------

                if (
                    score == 0
                    and self.artist
                ):

                    if self.artist in filename:

                        score = 100

                if score > 0:

                    scored.append(
                        (
                            score,
                            row
                        )
                    )

            # =================================================
            # SEARCH FOLDER
            # =================================================

            folder_matched = 0
            folder_scanned = 0

            if (
                self.search_folder
                and Path(
                    self.search_folder
                ).exists()
            ):

                known_paths = set()

                for extra_row in rows:

                    known_paths.add(
                        str(
                            extra_row["path"]
                            or ""
                        )
                    )

                for file_path in Path(
                    self.search_folder
                ).rglob(
                    "*.mp3"
                ):

                    if self.cancelled:

                        return

                    folder_scanned += 1

                    path_str = str(
                        file_path
                    )

                    if path_str in known_paths:

                        continue

                    fname_norm = self.normalize(
                        file_path.stem
                    )

                    folder_score = 0

                    if (
                        self.artist
                        and self.title
                        and self.artist in fname_norm
                        and self.title in fname_norm
                    ):

                        folder_score = 750

                    elif (
                        self.title
                        and self.title in fname_norm
                    ):

                        folder_score = 350

                    elif (
                        self.artist
                        and self.artist in fname_norm
                    ):

                        folder_score = 100

                    if folder_score > 0:

                        folder_row = {
                            "id": None,
                            "artist": "",
                            "title": "",
                            "filename": file_path.name,
                            "path": path_str,
                        }

                        folder_matched += 1

                        scored.append(
                            (
                                folder_score,
                                folder_row
                            )
                        )

            if self.cancelled:

                return

            min_score = match_mp3_minimum_score()

            before = len(
                scored
            )

            scored = [
                item
                for item in scored
                if (
                    item[0]
                    if isinstance(
                        item,
                        (list, tuple)
                    )
                    else 0
                ) >= min_score
            ]

            print(
                f"Match mode={discogs_match_mode()} "
                f"min_score={min_score} "
                f"kept {len(scored)}/{before}"
            )

            scored.sort(
                key=lambda x: (
                    -x[0],
                    str(
                        x[1]["artist"]
                        or ""
                    ).lower(),
                    str(
                        x[1]["title"]
                        or ""
                    ).lower(),
                    str(
                        x[1]["filename"]
                        or ""
                    ).lower(),
                )
            )

            limited = scored[:300]

            results = [
                row
                for score, row in limited
            ]

            self.finished.emit(
                limited,
                folder_scanned,
                folder_matched
            )

        except Exception as exc:

            self.error.emit(
                str(exc)
            )


# ============================================================
# MP3 SEARCH DIALOG
# ============================================================

class MP3SearchDialog(QDialog):

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

        self.search_folder = None

        self.search_thread = None

        self.search_worker = None

        settings = QSettings(
            "Kid Acid",
            "MusicVault"
        )

        self.search_folder = (
            settings.value(
                "mp3_search_folder",
                "",
                type=str
            )
            or None
        )

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

        self.search_button = QPushButton(
            "🔎 Zoeken"
        )

        self.search_button.clicked.connect(
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
            self.search_button
        )

        layout.addLayout(
            search_row
        )

        self.info_label = QLabel(
            "Zoeken in MP3-database..."
        )

        self.info_label.setObjectName(
            "infoLabel"
        )

        layout.addWidget(
            self.info_label
        )

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

        self.status_label = QLabel(
            ""
        )

        self.status_label.setObjectName(
            "statusLabel"
        )

        layout.addWidget(
            self.status_label
        )

        button_row = QHBoxLayout()

        self.file_button = QPushButton(
            "ðŸ“ MP3 BESTAND KIEZEN"
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

        self.folder_button = QPushButton(
            "Zoek in map..."
        )

        self.folder_button.setObjectName(
            "fileButton"
        )

        self.folder_button.clicked.connect(
            self.choose_search_folder
        )

        button_row.addWidget(
            self.folder_button
        )

        button_row.addStretch()

        cancel_button = QPushButton(
            "Annuleren"
        )

        cancel_button.clicked.connect(
            self.reject
        )

        button_row.addWidget(
            cancel_button
        )

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
    # CHOOSE SEARCH FOLDER
    # ========================================================

    def choose_search_folder(
        self
    ):

        settings = QSettings(
            "Kid Acid",
            "MusicVault"
        )

        start = (
            self.search_folder
            or settings.value(
                "mp3_search_folder",
                r"D:\01. MP3's",
                type=str
            )
        )

        if not Path(
            start
        ).exists():

            start = str(
                Path.home()
            )

        folder = QFileDialog.getExistingDirectory(
            self,
            "Map kiezen om te doorzoeken",
            start
        )

        if not folder:

            return

        self.search_folder = folder

        settings.setValue(
            "mp3_search_folder",
            folder
        )

        self.search()

    # ========================================================
    # SEARCH
    # ========================================================

    def search(
        self
    ):

        if (
            self.search_thread is not None
            and self.search_thread.isRunning()
        ):

            return

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

        self.info_label.setText(
            "MP3's zoeken..."
        )

        self.status_label.setText(
            "Bezig met zoeken — de interface blijft beschikbaar."
        )

        self.search_button.setText(
            "⏳ Bezig..."
        )
        self.search_button.setEnabled(
            False
        )

        self.folder_button.setEnabled(
            False
        )

        self.file_button.setEnabled(
            False
        )

        self.search_thread = QThread()

        self.search_worker = MP3SearchWorker(
            artist,
            title,
            self.search_folder
        )

        self.search_worker.moveToThread(
            self.search_thread
        )

        self.search_thread.started.connect(
            self.search_worker.run
        )

        self.search_worker.finished.connect(
            self.search_finished
        )

        self.search_worker.error.connect(
            self.search_error
        )

        self.search_worker.finished.connect(
            self.search_thread.quit
        )

        self.search_worker.error.connect(
            self.search_thread.quit
        )

        self.search_thread.finished.connect(
            self.worker_finished
        )

        self.search_thread.finished.connect(
            self.search_worker.deleteLater
        )

        self.search_thread.finished.connect(
            self.search_thread.deleteLater
        )

        self.search_thread.start()

    # ========================================================
    # SEARCH FINISHED
    # ========================================================

    @Slot(object, int, int)
    def search_finished(
        self,
        limited,
        folder_scanned,
        folder_matched
    ):

        self.results = [
            row
            for score, row in limited
        ]

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
            (
                f"Zoeken klaar. "
                f"{folder_scanned} MP3-bestanden in map gecontroleerd."
            )
        )

    # ========================================================
    # SEARCH ERROR
    # ========================================================

    @Slot(str)
    def search_error(
        self,
        message
    ):

        self.info_label.setText(
            "Zoeken mislukt."
        )

        self.status_label.setText(
            message
        )

        QMessageBox.critical(
            self,
            "MP3 zoeken mislukt",
            (
                "Er is een fout opgetreden tijdens "
                "het zoeken naar MP3-bestanden.\n\n"
                f"{message}"
            )
        )

    # ========================================================
    # WORKER FINISHED
    # ========================================================

    @Slot()
    def worker_finished(
        self
    ):

        self.search_button.setText(
            "🔎 Zoeken"
        )
        self.search_button.setEnabled(
            True
        )

        self.folder_button.setEnabled(
            True
        )

        self.file_button.setEnabled(
            True
        )

        self.search_worker = None

        self.search_thread = None

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

        if row is not None:

            mp3_id = row["id"]

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
    # ENSURE MP3 RECORD
    # ========================================================

    def _ensure_mp3_record(
        self,
        selected_path
    ):

        connection = get_connection()

        try:

            row = connection.execute(
                "SELECT id FROM mp3_files WHERE path = ? LIMIT 1",
                (
                    str(selected_path),
                )
            ).fetchone()

        finally:

            connection.close()

        if row is not None:

            return row["id"]

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

            return None

        finally:

            connection.close()

        return mp3_id

    # ========================================================
    # SELECT RESULT
    # ========================================================

    def select_result(
        self,
        item=None
    ):

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

            if path:

                mp3_id = self._ensure_mp3_record(
                    Path(path)
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

        file_exists = False

        if path:

            try:

                file_exists = Path(
                    path
                ).exists()

            except Exception:

                file_exists = False

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

    # ========================================================
    # CLOSE
    # ========================================================

    def closeEvent(
        self,
        event
    ):

        if (
            self.search_worker is not None
            and self.search_thread is not None
            and self.search_thread.isRunning()
        ):

            self.search_worker.cancel()

            self.search_thread.quit()

            self.search_thread.wait()

        event.accept()

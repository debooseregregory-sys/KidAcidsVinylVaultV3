# ============================================================
# KID ACID'S VINYLVAULT V3
# MP3 SEARCH / LINK DIALOG
# ============================================================

from pathlib import Path

from PySide6.QtCore import Qt, Signal, QObject, QThread
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


class DiskSearchWorker(QObject):
    """
    Doorzoekt een map naar .mp3-bestanden op een aparte thread, zodat de
    GUI niet bevriest. Kan op elk moment gestopt worden via cancel().
    """

    finished = Signal(list, bool)  # (kandidaten, was_gestopt)
    error = Signal(str)

    def __init__(self, root, artist, title, score_fn):
        super().__init__()
        self.root = root
        self.artist = artist
        self.title = title
        self.score_fn = score_fn
        self._cancelled = False

    def cancel(self):
        self._cancelled = True

    def run(self):
        candidates = []
        wanted_path_set = set()

        try:
            for path in self.root.rglob("*.mp3"):
                if self._cancelled:
                    break

                if not path.is_file():
                    continue

                path_key = str(path).casefold()
                if path_key in wanted_path_set:
                    continue
                wanted_path_set.add(path_key)

                filename_stem = path.stem
                detected_artist = ""
                detected_title = filename_stem

                if " - " in filename_stem:
                    parts = filename_stem.split(" - ", 1)
                    detected_artist = parts[0].strip()
                    detected_title = parts[1].strip()

                score = self.score_fn(
                    self.artist, self.title,
                    detected_artist, detected_title, path.name
                )

                if score > 0:
                    candidates.append((score, path, detected_artist, detected_title))

        except Exception as exc:
            self.error.emit(str(exc))
            return

        self.finished.emit(candidates, self._cancelled)


class MP3SearchDialog(QDialog):
    """
    Zoek MP3's in de database én rechtstreeks op een schijf/map.

    Een bestand dat nog niet in mp3_files staat kan vanuit een
    schijfzoekresultaat rechtstreeks aan de database worden toegevoegd
    en daarna aan de huidige vinyltrack worden gekoppeld.
    """

    mp3_selected = Signal(int, str)

    # Negatieve IDs worden uitsluitend intern gebruikt voor gevonden
    # bestanden die nog geen database-record hebben.
    DISK_ID_BASE = -1

    def __init__(self, track, parent=None):
        super().__init__(parent)

        self.track = track
        self.results = []
        self.selected_database_row = None
        self.selected_disk_path = None

        self._search_thread = None
        self._search_worker = None

        self.build_ui()

        self.artist_edit.setText(str(track["artist"] or ""))
        self.title_edit.setText(str(track["title"] or ""))

        self.setWindowTitle("MP3 zoeken")
        self.resize(1050, 700)

        # Geen automatische zoekactie meer bij openen: de gebruiker moet
        # zelf op 'Zoeken' of 'ZOEK IN PAD' drukken.

    # ========================================================
    # UI
    # ========================================================

    def build_ui(self):
        self.setStyleSheet("""
            QDialog { background-color: #171717; color: #ffffff; }
            QLabel { color: #ffffff; }
            QLabel#dialogTitle {
                color: #ff69b4; font-size: 18px; font-weight: bold;
                padding-bottom: 8px;
            }
            QLabel#infoLabel { color: #aaaaaa; padding: 5px 0; }
            QLabel#statusLabel {
                color: #ff69b4; font-weight: bold; padding: 5px 0;
            }
            QLineEdit {
                background-color: #252525; color: #ffffff;
                border: 1px solid #444444; border-radius: 5px; padding: 8px;
            }
            QLineEdit:focus { border: 1px solid #ff69b4; }
            QListWidget {
                background-color: #111111; color: #ffffff;
                border: 1px solid #333333; border-radius: 5px; outline: none;
            }
            QListWidget::item {
                padding: 10px; border-bottom: 1px solid #292929;
            }
            QListWidget::item:hover { background-color: #2a1823; }
            QListWidget::item:selected {
                background-color: #713957; color: #ffffff;
            }
            QPushButton {
                background-color: #252525; color: #ffffff;
                border: 1px solid #444444; border-radius: 5px;
                padding: 8px 14px;
            }
            QPushButton:hover {
                background-color: #35202d; border: 1px solid #ff69b4;
                color: #ff69b4;
            }
            QPushButton:pressed { background-color: #51283f; }
            QPushButton:disabled {
                background-color: #202020; color: #666666;
                border: 1px solid #333333;
            }
            QPushButton#linkButton {
                background-color: #713957; color: #ffffff;
                border: 1px solid #ff69b4; font-weight: bold;
            }
            QPushButton#linkButton:hover { background-color: #984b74; }
            QPushButton#fileButton {
                background-color: #252525; color: #ff69b4;
                border: 1px solid #ff69b4; font-weight: bold;
            }
            QPushButton#fileButton:hover { background-color: #35202d; }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(8)

        title_label = QLabel(
            f"MP3 zoeken voor: {self.track['position']} — "
            f"{self.track['artist']} - {self.track['title']}"
        )
        title_label.setObjectName("dialogTitle")
        layout.addWidget(title_label)

        search_row = QHBoxLayout()
        search_row.setSpacing(6)

        self.artist_edit = QLineEdit()
        self.artist_edit.setPlaceholderText("Artiest")

        self.title_edit = QLineEdit()
        self.title_edit.setPlaceholderText("Titel")

        search_button = QPushButton("🔎 Zoeken")
        search_button.clicked.connect(self.search)
        self.artist_edit.returnPressed.connect(self.search)
        self.title_edit.returnPressed.connect(self.search)

        search_row.addWidget(self.artist_edit, 1)
        search_row.addWidget(self.title_edit, 1)
        search_row.addWidget(search_button)
        layout.addLayout(search_row)

        # ----------------------------------------------------
        # SEARCH PATH
        # ----------------------------------------------------

        path_row = QHBoxLayout()
        path_row.setSpacing(6)

        self.search_path_edit = QLineEdit()
        self.search_path_edit.setPlaceholderText(
            "Zoekpad (optioneel) — bv. D:\\01. MP3's"
        )
        self.search_path_edit.setText(r"D:\01. MP3's")

        path_button = QPushButton("📂 PAD KIEZEN")
        path_button.clicked.connect(self.choose_search_path)

        self.disk_search_button = QPushButton("🔎 ZOEK IN PAD")
        self.disk_search_button.setObjectName("fileButton")
        self.disk_search_button.clicked.connect(self.search_disk)

        self.stop_search_button = QPushButton("⏹ STOP")
        self.stop_search_button.setObjectName("fileButton")
        self.stop_search_button.clicked.connect(self.stop_disk_search)
        self.stop_search_button.setEnabled(False)
        self.stop_search_button.setVisible(False)

        path_row.addWidget(self.search_path_edit, 1)
        path_row.addWidget(path_button)
        path_row.addWidget(self.disk_search_button)
        path_row.addWidget(self.stop_search_button)
        layout.addLayout(path_row)

        self.info_label = QLabel(
            "Klaar om te zoeken. Vul artiest/titel in en druk op 'Zoeken', "
            "of gebruik 'ZOEK IN PAD' voor een schijf."
        )
        self.info_label.setObjectName("infoLabel")
        layout.addWidget(self.info_label)

        self.results_list = QListWidget()
        self.results_list.itemSelectionChanged.connect(self.selection_changed)
        self.results_list.itemDoubleClicked.connect(self.select_result)
        layout.addWidget(self.results_list, 1)

        self.status_label = QLabel("")
        self.status_label.setObjectName("statusLabel")
        layout.addWidget(self.status_label)

        button_row = QHBoxLayout()

        self.file_button = QPushButton("📁 MP3 BESTAND KIEZEN")
        self.file_button.setObjectName("fileButton")
        self.file_button.clicked.connect(self.choose_mp3_file)
        button_row.addWidget(self.file_button)

        button_row.addStretch()

        cancel_button = QPushButton("Annuleren")
        cancel_button.clicked.connect(self.reject)
        button_row.addWidget(cancel_button)

        self.link_button = QPushButton("✓ MP3 KOPPELEN")
        self.link_button.setObjectName("linkButton")
        self.link_button.setEnabled(False)
        self.link_button.clicked.connect(self.select_result)
        button_row.addWidget(self.link_button)

        layout.addLayout(button_row)

    # ========================================================
    # NORMALIZE / SCORE
    # ========================================================

    @staticmethod
    def normalize(value):
        value = str(value or "").lower()
        for char in ("_", "-", "(", ")", "[", "]", "{", "}"):
            value = value.replace(char, " ")
        return " ".join(value.split())

    def score_values(self, artist, title, filename):
        """Gebruik dezelfde rangorde als de oorspronkelijke databasezoeker."""
        artist = self.normalize(artist)
        title = self.normalize(title)
        mp3_artist = self.normalize(artist if artist else "")
        mp3_title = self.normalize(title if title else "")
        filename = self.normalize(filename)

        # Deze methode wordt alleen voor een al opgebouwde candidate gebruikt;
        # de echte waarden worden daarom door score_candidate aangeleverd.
        return 0

    def score_candidate(self, wanted_artist, wanted_title,
                        candidate_artist, candidate_title, filename):
        artist = self.normalize(wanted_artist)
        title = self.normalize(wanted_title)
        mp3_artist = self.normalize(candidate_artist)
        mp3_title = self.normalize(candidate_title)
        filename = self.normalize(filename)

        score = 0

        if artist and title and mp3_artist == artist and mp3_title == title:
            score = 1000
        elif artist and title and mp3_artist == artist and title in mp3_title:
            score = 850
        elif artist and title and mp3_title == title and artist in mp3_artist:
            score = 825
        elif artist and title and artist in filename and title in filename:
            score = 750
        elif title and mp3_title == title:
            score = 600
        elif title and title in mp3_title:
            score = 450
        elif title and title in filename:
            score = 350
        elif artist and mp3_artist == artist:
            score = 250
        elif artist and artist in mp3_artist:
            score = 150
        elif artist and artist in filename:
            score = 100

        return score

    # ========================================================
    # DATABASE SEARCH
    # ========================================================

    def search(self):
        artist = self.normalize(self.artist_edit.text())
        title = self.normalize(self.title_edit.text())

        self.results_list.clear()
        self.results = []
        self.selected_database_row = None
        self.selected_disk_path = None
        self.link_button.setEnabled(False)

        if not artist and not title:
            self.info_label.setText("Geef een artiest of titel op.")
            self.status_label.setText("")
            return

        connection = get_connection()
        try:
            rows = connection.execute("""
                SELECT id, artist, title, filename, path
                FROM mp3_files
                ORDER BY artist COLLATE NOCASE,
                         title COLLATE NOCASE,
                         filename COLLATE NOCASE
            """).fetchall()
        finally:
            connection.close()

        scored = []
        for row in rows:
            score = self.score_candidate(
                artist, title,
                row["artist"], row["title"], row["filename"]
            )
            if score > 0:
                scored.append((score, row))

        scored.sort(key=lambda x: (
            -x[0],
            str(x[1]["artist"] or "").lower(),
            str(x[1]["title"] or "").lower(),
            str(x[1]["filename"] or "").lower(),
        ))

        limited = scored[:300]
        self.results = [row for score, row in limited]

        self._add_database_results(limited)

        self.info_label.setText(
            f"{len(self.results)} kandidaten gevonden in MP3-database"
        )
        self.status_label.setText(
            "Database-resultaten. Gebruik 'ZOEK IN PAD' om ook de schijf te doorzoeken."
        )

    def _add_database_results(self, scored):
        for score, row in scored:
            artist_text = row["artist"] or "Onbekende artiest"
            title_text = row["title"] or "Onbekende titel"
            filename = row["filename"] or ""
            path = row["path"] or ""

            try:
                exists = bool(path) and Path(path).exists()
            except Exception:
                exists = False

            file_status = "✓ BESTAND BESTAAT" if exists else "⚠ PAD BESTAAT NIET"

            item = QListWidgetItem(
                f"[{score}]  {artist_text} — {title_text}\n"
                f"    {filename}\n"
                f"    {path}\n"
                f"    {file_status}"
            )
            item.setData(Qt.ItemDataRole.UserRole, row["id"])
            item.setData(Qt.ItemDataRole.UserRole + 1, path)
            item.setData(Qt.ItemDataRole.UserRole + 2, score)
            item.setData(Qt.ItemDataRole.UserRole + 3, "database")
            self.results_list.addItem(item)

    # ========================================================
    # DIALOOG SLUITEN
    # ========================================================

    def _stop_and_wait_for_search(self):
        """Stopt een eventueel lopende schijf-scan en wacht tot de
        achtergrondthread echt gestopt is, zodat Qt niet crasht bij het
        sluiten van de dialoog."""
        if self._search_worker is not None:
            self._search_worker.cancel()
        if self._search_thread is not None:
            self._search_thread.quit()
            self._search_thread.wait(3000)

    def closeEvent(self, event):
        self._stop_and_wait_for_search()
        super().closeEvent(event)

    def reject(self):
        self._stop_and_wait_for_search()
        super().reject()

    def accept(self):
        self._stop_and_wait_for_search()
        super().accept()

    # ========================================================
    # FILESYSTEM SEARCH
    # ========================================================

    def choose_search_path(self):
        current = self.search_path_edit.text().strip()
        start_folder = current if Path(current).is_dir() else str(Path.home())

        folder = QFileDialog.getExistingDirectory(
            self,
            "MP3 zoekmap kiezen",
            start_folder
        )

        if folder:
            self.search_path_edit.setText(folder)
            self.info_label.setText(
                "Map gekozen. Druk op 'ZOEK IN PAD' om te starten."
            )

    def search_disk(self):
        artist = self.normalize(self.artist_edit.text())
        title = self.normalize(self.title_edit.text())
        raw_path = self.search_path_edit.text().strip().strip('"')

        self.results_list.clear()
        self.results = []
        self.selected_database_row = None
        self.selected_disk_path = None
        self.link_button.setEnabled(False)

        if not artist and not title:
            self.info_label.setText("Geef een artiest of titel op.")
            self.status_label.setText("")
            return

        if not raw_path:
            QMessageBox.warning(self, "Geen zoekpad", "Geef eerst een map op.")
            return

        root = Path(raw_path)
        if not root.is_dir():
            QMessageBox.warning(
                self,
                "Map niet gevonden",
                f"Deze map bestaat niet:\n\n{root}"
            )
            return

        if self._search_thread is not None:
            # Er loopt al een scan; negeer een dubbele klik.
            return

        self.info_label.setText(f"Schijf wordt doorzocht: {root}")
        self.status_label.setText("Even geduld — MP3-bestanden worden gezocht...")

        self._pending_artist = artist
        self._pending_title = title

        self.disk_search_button.setEnabled(False)
        self.stop_search_button.setEnabled(True)
        self.stop_search_button.setVisible(True)

        self._search_thread = QThread(self)
        self._search_worker = DiskSearchWorker(
            root, artist, title, self.score_candidate
        )
        self._search_worker.moveToThread(self._search_thread)

        self._search_thread.started.connect(self._search_worker.run)
        self._search_worker.finished.connect(self._on_disk_search_finished)
        self._search_worker.error.connect(self._on_disk_search_error)
        self._search_worker.finished.connect(self._search_thread.quit)
        self._search_worker.error.connect(self._search_thread.quit)
        self._search_thread.finished.connect(self._cleanup_search_thread)

        self._search_thread.start()

    def stop_disk_search(self):
        if self._search_worker is not None:
            self._search_worker.cancel()
        self.status_label.setText("Zoeken wordt gestopt...")
        self.stop_search_button.setEnabled(False)

    def _cleanup_search_thread(self):
        self._search_thread = None
        self._search_worker = None
        self.disk_search_button.setEnabled(True)
        self.stop_search_button.setEnabled(False)
        self.stop_search_button.setVisible(False)

    def _on_disk_search_error(self, message):
        QMessageBox.critical(
            self,
            "Zoeken mislukt",
            f"De map kon niet volledig worden doorzocht.\n\n{message}"
        )
        self.info_label.setText("Zoeken mislukt.")
        self.status_label.setText("")

    def _on_disk_search_finished(self, candidates, was_cancelled):
        candidates.sort(key=lambda x: (
            -x[0],
            x[1].name.casefold(),
            str(x[1]).casefold(),
        ))

        limited = candidates[:500]
        self.results = []

        # Toon filesystem-resultaten. Deze krijgen een negatieve interne ID.
        for index, (score, path, detected_artist, detected_title) in enumerate(limited):
            internal_id = self.DISK_ID_BASE - index

            # Als het bestand al in de DB staat, markeer dat zichtbaar.
            connection = get_connection()
            try:
                db_row = connection.execute(
                    "SELECT id, artist, title, filename, path "
                    "FROM mp3_files WHERE path = ? LIMIT 1",
                    (str(path),)
                ).fetchone()
            finally:
                connection.close()

            if db_row is not None:
                display_artist = db_row["artist"] or detected_artist or "Onbekende artiest"
                display_title = db_row["title"] or detected_title or "Onbekende titel"
                db_status = "✓ STAAT AL IN DATABASE"
            else:
                display_artist = detected_artist or "Onbekende artiest"
                display_title = detected_title or "Onbekende titel"
                db_status = "＋ NOG NIET IN DATABASE"

            item = QListWidgetItem(
                f"[{score}]  {display_artist} — {display_title}\n"
                f"    {path.name}\n"
                f"    {path}\n"
                f"    ✓ BESTAND GEVONDEN  |  {db_status}"
            )
            item.setData(Qt.ItemDataRole.UserRole, internal_id)
            item.setData(Qt.ItemDataRole.UserRole + 1, str(path))
            item.setData(Qt.ItemDataRole.UserRole + 2, score)
            item.setData(Qt.ItemDataRole.UserRole + 3, "disk")
            item.setData(Qt.ItemDataRole.UserRole + 4, db_row["id"] if db_row else None)
            item.setData(Qt.ItemDataRole.UserRole + 5, detected_artist)
            item.setData(Qt.ItemDataRole.UserRole + 6, detected_title)
            self.results_list.addItem(item)

        stopped_note = " — gestopt door gebruiker" if was_cancelled else ""
        self.info_label.setText(
            f"{len(limited)} MP3-bestanden gevonden op schijf "
            f"(van maximaal 500 weergegeven){stopped_note}"
        )
        self.status_label.setText(
            "Selecteer een bestand. Een nieuw bestand wordt bij koppelen automatisch aan de database toegevoegd."
        )

    # ========================================================
    # SELECTION
    # ========================================================

    def selection_changed(self):
        item = self.results_list.currentItem()
        if item is None:
            self.selected_database_row = None
            self.selected_disk_path = None
            self.link_button.setEnabled(False)
            self.status_label.setText("")
            return

        source = item.data(Qt.ItemDataRole.UserRole + 3)
        path = item.data(Qt.ItemDataRole.UserRole + 1) or ""

        if source == "disk":
            db_id = item.data(Qt.ItemDataRole.UserRole + 4)
            self.selected_database_row = db_id
            self.selected_disk_path = path
            self.link_button.setEnabled(bool(path))

            if db_id:
                self.status_label.setText(
                    "✓ Bestand bestaat en staat al in de database — klaar om te koppelen."
                )
            else:
                self.status_label.setText(
                    "✓ Bestand gevonden op schijf — nog niet in database. Koppelen voegt het automatisch toe."
                )
            return

        mp3_id = item.data(Qt.ItemDataRole.UserRole)
        self.selected_database_row = mp3_id
        self.selected_disk_path = None
        self.link_button.setEnabled(bool(mp3_id))

        try:
            exists = bool(path) and Path(path).exists()
        except Exception:
            exists = False

        self.status_label.setText(
            "✓ Bestand bestaat — klaar om te koppelen."
            if exists
            else "⚠ Dit MP3-record heeft een oud/ontbrekend pad."
        )

    # ========================================================
    # DIRECT FILE
    # ========================================================

    def choose_mp3_file(self):
        start_folder = r"D:\01. MP3's"
        if not Path(start_folder).exists():
            start_folder = str(Path.home())

        filename, _ = QFileDialog.getOpenFileName(
            self,
            "MP3-bestand kiezen",
            start_folder,
            "MP3 bestanden (*.mp3);;Alle bestanden (*.*)"
        )

        if not filename:
            return

        selected_path = Path(filename)
        if not selected_path.exists():
            QMessageBox.warning(
                self,
                "Bestand niet gevonden",
                f"Het gekozen bestand bestaat niet:\n\n{selected_path}"
            )
            return

        if selected_path.suffix.lower() != ".mp3":
            answer = QMessageBox.question(
                self,
                "Geen MP3",
                "Dit bestand heeft geen .mp3-extensie.\n\nToch gebruiken?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            if answer != QMessageBox.StandardButton.Yes:
                return

        self.link_file_path(selected_path)

    def link_file_path(self, selected_path):
        connection = get_connection()
        try:
            row = connection.execute(
                "SELECT id, artist, title, filename, path FROM mp3_files "
                "WHERE path = ? LIMIT 1",
                (str(selected_path),)
            ).fetchone()

            if row is None:
                row = connection.execute(
                    "SELECT id, artist, title, filename, path FROM mp3_files "
                    "WHERE filename = ? LIMIT 1",
                    (selected_path.name,)
                ).fetchone()
        finally:
            connection.close()

        if row is not None:
            mp3_id = row["id"]
            old_path = row["path"] or ""

            if old_path != str(selected_path):
                connection = get_connection()
                try:
                    connection.execute(
                        "UPDATE mp3_files SET path = ? WHERE id = ?",
                        (str(selected_path), mp3_id)
                    )
                    connection.commit()
                finally:
                    connection.close()

            answer = QMessageBox.question(
                self,
                "MP3 gevonden",
                f"Deze MP3 bestaat al in de MP3-database.\n\n"
                f"MP3 ID: {mp3_id}\n"
                f"Bestand: {selected_path.name}\n\n"
                f"Pad:\n{selected_path}\n\n"
                "Deze MP3 koppelen aan de track?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.Yes
            )
            if answer != QMessageBox.StandardButton.Yes:
                return

            self.mp3_selected.emit(mp3_id, str(selected_path))
            self.accept()
            return

        answer = QMessageBox.question(
            self,
            "Nieuwe MP3",
            f"Deze MP3 staat nog niet in de MP3-database.\n\n"
            f"{selected_path.name}\n\n"
            "De MP3 wordt eerst aan de database toegevoegd en daarna gekoppeld.\n\n"
            "Doorgaan?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes
        )
        if answer != QMessageBox.StandardButton.Yes:
            return

        filename_stem = selected_path.stem
        detected_artist = ""
        detected_title = filename_stem
        if " - " in filename_stem:
            parts = filename_stem.split(" - ", 1)
            detected_artist = parts[0].strip()
            detected_title = parts[1].strip()

        connection = get_connection()
        try:
            cursor = connection.execute(
                "INSERT INTO mp3_files (artist, title, filename, path) "
                "VALUES (?, ?, ?, ?)",
                (detected_artist, detected_title,
                 selected_path.name, str(selected_path))
            )
            mp3_id = cursor.lastrowid
            connection.commit()
        except Exception as exc:
            connection.rollback()
            QMessageBox.critical(
                self,
                "MP3 toevoegen mislukt",
                f"De MP3 kon niet aan de database worden toegevoegd.\n\n{exc}"
            )
            return
        finally:
            connection.close()

        self.mp3_selected.emit(mp3_id, str(selected_path))
        self.accept()

    # ========================================================
    # SELECT RESULT
    # ========================================================

    def select_result(self, item=None):
        if item is None or not isinstance(item, QListWidgetItem):
            item = self.results_list.currentItem()

        if item is None:
            return

        source = item.data(Qt.ItemDataRole.UserRole + 3)
        path = item.data(Qt.ItemDataRole.UserRole + 1) or ""

        # ----------------------------------------------------
        # SCHIJFRESULTAAT
        # ----------------------------------------------------
        if source == "disk":
            if not path:
                return

            disk_path = Path(path)
            if not disk_path.exists():
                QMessageBox.warning(
                    self,
                    "Bestand niet gevonden",
                    f"Het bestand bestaat niet meer:\n\n{disk_path}"
                )
                return

            existing_id = item.data(Qt.ItemDataRole.UserRole + 4)
            if existing_id:
                self.mp3_selected.emit(existing_id, str(disk_path))
                self.accept()
                return

            # Nieuw bestand: gebruik exact hetzelfde insert-mechanisme als
            # bij 'MP3 BESTAND KIEZEN'.
            self.link_file_path(disk_path)
            return

        # ----------------------------------------------------
        # DATABASERESULTAAT
        # ----------------------------------------------------
        mp3_id = item.data(Qt.ItemDataRole.UserRole)
        if not mp3_id:
            return

        row = None
        for candidate in self.results:
            if candidate["id"] == mp3_id:
                row = candidate
                break

        if row is None:
            return

        artist = row["artist"] or ""
        title = row["title"] or ""
        filename = row["filename"] or ""
        if not path:
            path = row["path"] or ""

        try:
            file_exists = bool(path) and Path(path).exists()
        except Exception:
            file_exists = False

        if file_exists:
            answer = QMessageBox.question(
                self,
                "MP3 koppelen",
                f"Deze MP3 koppelen aan:\n\n"
                f"{self.track['position']} — {self.track['artist']} - {self.track['title']}\n\n"
                f"MP3:\n{artist} - {title}\n\n"
                f"Bestand:\n{filename}\n\n"
                f"Pad:\n{path}\n\n"
                "✓ Bestand bestaat\n\nDoorgaan?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
        else:
            answer = QMessageBox.warning(
                self,
                "Oud MP3-pad",
                f"Deze MP3 staat in de database, maar het opgeslagen pad bestaat niet meer.\n\n"
                f"MP3:\n{filename}\n\n"
                f"Oud pad:\n{path}\n\n"
                "Je kunt deze koppeling wel maken, maar hij zal pas kunnen afspelen "
                "als het pad wordt hersteld.\n\nWil je toch koppelen?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )

        if answer != QMessageBox.StandardButton.Yes:
            return

        self.mp3_selected.emit(mp3_id, path)
        self.accept()

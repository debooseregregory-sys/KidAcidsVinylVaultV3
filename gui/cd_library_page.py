# ============================================================
# KID ACID'S VINYLVAULT V3
# CD LIBRARY
# ============================================================

from PySide6.QtCore import Signal, Qt, QTimer
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
    QMessageBox, QInputDialog, QFileDialog,
)

from database.cd_database import (
    get_cd_releases,
    ensure_cd_schema,
    save_cd_discogs_tracks,
)
from database.database import get_connection
from tools.discogs import fetch_release_data
from gui.cd_track_editor import CDTrackEditorDialog


class CDLibraryPage(QWidget):
    cd_selected = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.all_rows = []
        self.search_timer = QTimer(self)
        self.search_timer.setSingleShot(True)
        self.search_timer.setInterval(160)
        self.search_timer.timeout.connect(self._apply_pending_search)
        self._pending_search = ""
        self.build_ui()
        self.load_releases()

    def build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(25, 25, 25, 25)
        root.setSpacing(12)

        title = QLabel("VINYLVAULT CD LIBRARY")
        title.setStyleSheet("QLabel { color:#fff; font-size:28px; font-weight:bold; }")
        root.addWidget(title)

        subtitle = QLabel("Je volledige CD-collectie")
        subtitle.setStyleSheet("QLabel { color:#888; font-size:14px; }")
        root.addWidget(subtitle)

        search_row = QHBoxLayout()
        self.search = QLineEdit()
        self.search.setPlaceholderText("Zoek artiest, titel, type, label of catalogus...")
        self.search.setMinimumHeight(42)
        self.search.textChanged.connect(self._schedule_search)
        search_row.addWidget(self.search, 1)

        refresh = QPushButton("VERNIEUW")
        refresh.setMinimumHeight(42)
        refresh.clicked.connect(self.load_releases)
        search_row.addWidget(refresh)
        root.addLayout(search_row)

        self.status = QLabel("CD's laden...")
        self.status.setStyleSheet("QLabel { color:#aaa; font-size:13px; }")
        root.addWidget(self.status)

        self.table = QTableWidget(0, 7)
        self.table.setHorizontalHeaderLabels([
            "ID", "ARTIST", "RELEASE", "TYPE", "LABEL", "CATALOG", "YEAR"
        ])
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.setSortingEnabled(True)
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(34)
        self.table.cellDoubleClicked.connect(self._open_selected)
        self.table.setStyleSheet("""
            QTableWidget { background:#101010; alternate-background-color:#171717;
                color:#eee; gridline-color:#292929; border:1px solid #303030;
                selection-background-color:#383838; selection-color:#fff; font-size:13px; }
            QTableWidget::item { padding:6px; border:none; }
            QHeaderView::section { background:#202020; color:#fff; padding:9px;
                border:none; border-right:1px solid #303030; border-bottom:1px solid #444;
                font-weight:bold; font-size:12px; }
            QLineEdit { background:#181818; color:#fff; border:1px solid #383838;
                border-radius:4px; padding:8px 12px; font-size:14px; }
            QLineEdit:focus { border:1px solid #666; }
            QPushButton { background:#222; color:#fff; border:1px solid #3a3a3a;
                border-radius:4px; padding:8px 16px; font-weight:bold; }
            QPushButton:hover { background:#303030; }
        """)

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)
        root.addWidget(self.table, 1)

        button_row = QHBoxLayout()
        button_row.setSpacing(10)

        open_button = QPushButton("OPEN CD")
        open_button.setMinimumHeight(42)
        open_button.clicked.connect(self.open_selected)
        button_row.addWidget(open_button)

        discogs_button = QPushButton("DISCOGS KOPPELEN")
        discogs_button.setMinimumHeight(42)
        discogs_button.clicked.connect(self.link_selected_discogs)
        button_row.addWidget(discogs_button)

        manual_button = QPushButton("+ CD HANDMATIG")
        manual_button.setMinimumHeight(42)
        manual_button.clicked.connect(self.add_manual_cd)
        button_row.addWidget(manual_button)

        tracks_button = QPushButton("TRACKS BEWERKEN")
        tracks_button.setMinimumHeight(42)
        tracks_button.clicked.connect(self.edit_selected_tracks)
        button_row.addWidget(tracks_button)

        delete_button = QPushButton("VERWIJDER CD")
        delete_button.setMinimumHeight(42)
        delete_button.clicked.connect(self.delete_selected)
        button_row.addWidget(delete_button)

        root.addLayout(button_row)

    def load_releases(self):
        try:
            ensure_cd_schema()
            self.all_rows = get_cd_releases()
            self.display_releases(self.all_rows)
        except Exception as error:
            QMessageBox.critical(self, "Database fout", f"De CD Library kon niet worden geladen.\n\n{error}")

    def display_releases(self, rows):
        self.table.setSortingEnabled(False)
        self.table.setRowCount(0)
        for r, row in enumerate(rows):
            self.table.insertRow(r)
            values = [row["id"], row["artist"], row["title"], row["media_type"], row["label"], row["catalog"], row["year"] or ""]
            for c, value in enumerate(values):
                item = QTableWidgetItem(str(value or "------------"))
                item.setToolTip(str(value or ""))
                item.setTextAlignment(
                    Qt.AlignmentFlag.AlignCenter if c in (0, 3, 6)
                    else Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
                )
                self.table.setItem(r, c, item)
            self.table.setRowHeight(r, 34)
        self.table.setSortingEnabled(True)
        self.status.setText(f"{len(rows)} CD's")

    def _schedule_search(self, text):
        self._pending_search = text
        self.search_timer.start()

    def _apply_pending_search(self):
        text = self._pending_search.strip().lower()
        if not text:
            self.display_releases(self.all_rows)
            return
        filtered = []
        for row in self.all_rows:
            values = [row[k] for k in ("id", "artist", "title", "media_type", "label", "catalog", "year")]
            if text in " ".join("" if v is None else str(v) for v in values).lower():
                filtered.append(row)
        self.display_releases(filtered)

    def _open_selected(self, row, column):
        self._emit_selected(row)

    def open_selected(self):
        selected = self.table.selectionModel().selectedRows()
        if not selected:
            QMessageBox.information(self, "Geen CD geselecteerd", "Selecteer eerst een CD.")
            return
        self._emit_selected(selected[0].row())

    def _selected_release_id(self):
        selected = self.table.selectionModel().selectedRows()
        if not selected:
            QMessageBox.information(self, "Geen CD geselecteerd", "Selecteer eerst een CD.")
            return None
        item = self.table.item(selected[0].row(), 0)
        if item is None:
            return None
        try:
            return int(item.text())
        except ValueError:
            return None

    def _selected_row_data(self, release_id):
        return next((r for r in self.all_rows if int(r["id"]) == int(release_id)), None)

    def edit_selected_tracks(self):
        release_id = self._selected_release_id()
        if release_id is None:
            return
        row = self._selected_row_data(release_id)
        if row is None:
            QMessageBox.warning(self, "CD niet gevonden", "De geselecteerde CD bestaat niet meer in de database.")
            return
        dialog = CDTrackEditorDialog(
            release_id,
            artist=str(row["artist"] or ""),
            title=str(row["title"] or ""),
            parent=self,
        )
        if dialog.exec() == dialog.DialogCode.Accepted:
            QMessageBox.information(
                self,
                "Tracks opgeslagen",
                f"De tracklist van {row['artist']} — {row['title']} is opgeslagen."
            )

    def add_manual_cd(self):
        artist, ok = QInputDialog.getText(self, "CD handmatig toevoegen", "Artiest:", text="")
        if not ok:
            return
        artist = artist.strip()
        if not artist:
            QMessageBox.warning(self, "Ontbrekende artiest", "Vul een artiest in.")
            return

        title, ok = QInputDialog.getText(self, "CD handmatig toevoegen", "Titel:", text="")
        if not ok:
            return
        title = title.strip()
        if not title:
            QMessageBox.warning(self, "Ontbrekende titel", "Vul een titel in.")
            return

        label, ok = QInputDialog.getText(self, "CD handmatig toevoegen", "Label:")
        if not ok:
            return
        catalog, ok = QInputDialog.getText(self, "CD handmatig toevoegen", "Catalogusnummer:")
        if not ok:
            return
        year_text, ok = QInputDialog.getText(self, "CD handmatig toevoegen", "Jaar:")
        if not ok:
            return
        genre, ok = QInputDialog.getText(self, "CD handmatig toevoegen", "Genre:")
        if not ok:
            return
        notes, ok = QInputDialog.getMultiLineText(self, "CD handmatig toevoegen", "Notities:")
        if not ok:
            return

        cover = ""
        choose_cover = QMessageBox.question(
            self, "Cover", "Wil je een lokale coverafbeelding toevoegen?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes,
        )
        if choose_cover == QMessageBox.StandardButton.Yes:
            cover, _ = QFileDialog.getOpenFileName(
                self, "Kies CD-cover", "",
                "Afbeeldingen (*.jpg *.jpeg *.png *.webp *.bmp);;Alle bestanden (*.*)",
            )

        year = None
        if year_text.strip():
            try:
                year = int(year_text.strip())
            except ValueError:
                QMessageBox.warning(self, "Ongeldig jaar", "Het jaar moet een nummer zijn. De CD wordt zonder jaar opgeslagen.")

        connection = get_connection()
        try:
            ensure_cd_schema(connection)
            try:
                cursor = connection.execute(
                    """
                    INSERT INTO cd_releases
                        (artist, title, media_type, label, catalog, year, genre,
                         discogs, discogs_link, cover, notes, checked)
                    VALUES (?, ?, 'CD', ?, ?, ?, ?, '', '', ?, ?, 0)
                    """,
                    (artist, title, label.strip(), catalog.strip(), year, genre.strip(), cover.strip(), notes.strip()),
                )
                connection.commit()
                new_id = cursor.lastrowid
            except Exception as error:
                connection.rollback()
                if "UNIQUE" in str(error).upper():
                    QMessageBox.warning(self, "CD bestaat al", f"Deze CD bestaat al:\n\n{artist} — {title}")
                    return
                raise
        finally:
            connection.close()

        self.load_releases()
        QMessageBox.information(self, "CD toegevoegd", f"{artist} — {title}\n\nCD ID: {new_id}\n\nDe CD staat nu in de CD Library.")

    def delete_selected(self):
        release_id = self._selected_release_id()
        if release_id is None:
            return

        row = self._selected_row_data(release_id)
        if row is None:
            QMessageBox.warning(self, "CD niet gevonden", "De geselecteerde CD bestaat niet meer in de database.")
            return

        artist = str(row["artist"] or "Onbekend")
        title = str(row["title"] or "(geen titel)")
        answer = QMessageBox.warning(
            self,
            "CD verwijderen",
            f"Wil je deze CD definitief verwijderen?\n\n{artist} — {title}\n\n"
            "De CD en de bijbehorende CD-tracks worden verwijderd. Deze actie kan niet ongedaan worden gemaakt.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return

        connection = get_connection()
        try:
            ensure_cd_schema(connection)
            connection.execute("DELETE FROM cd_tracks WHERE cd_release_id = ?", (release_id,))
            connection.execute("DELETE FROM cd_releases WHERE id = ?", (release_id,))
            connection.commit()
        except Exception as error:
            connection.rollback()
            QMessageBox.critical(self, "Verwijderen mislukt", f"De CD kon niet worden verwijderd.\n\n{error}")
            return
        finally:
            connection.close()

        self.load_releases()
        QMessageBox.information(self, "CD verwijderd", f"{artist} — {title}\n\nDe CD is verwijderd uit de CD Library.")

    def link_selected_discogs(self):
        release_id = self._selected_release_id()
        if release_id is None:
            return

        row = self._selected_row_data(release_id)
        if row is None:
            QMessageBox.warning(self, "CD niet gevonden", "De geselecteerde CD bestaat niet meer in de database.")
            return

        current_discogs = str(row["discogs"] or "").strip()
        prompt = "Discogs Release ID:"
        if current_discogs:
            prompt += f"\n(huidig: {current_discogs})"

        discogs_id, ok = QInputDialog.getText(self, "CD aan Discogs koppelen", prompt, text=current_discogs)
        if not ok:
            return

        discogs_id = discogs_id.strip()
        if not discogs_id.isdigit():
            QMessageBox.warning(self, "Ongeldig Discogs ID", "Een Discogs Release ID moet een nummer zijn.")
            return

        try:
            data = fetch_release_data(discogs_id)
            release = data["release"]
            release_artist = data["artist"] or str(row["artist"] or "")
            release_title = data["title"] or str(row["title"] or "")

            connection = get_connection()
            try:
                connection.execute(
                    """
                    UPDATE cd_releases
                    SET artist = ?, title = ?, label = ?, catalog = ?, year = ?,
                        genre = ?, discogs = ?, discogs_link = ?, cover = ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                    """,
                    (release_artist, release_title, data["label"], data["catalog"], data["year"], data["genre"], data["discogs"], data["discogs_link"], data["cover"], release_id),
                )
                connection.commit()
            finally:
                connection.close()

            track_count = save_cd_discogs_tracks(release_id, release)
            self.load_releases()
            QMessageBox.information(self, "Discogs gekoppeld", f"{release_artist} — {release_title}\n\nDiscogs ID: {discogs_id}\nTracks geïmporteerd: {track_count}")
        except Exception as error:
            QMessageBox.critical(self, "Discogs fout", f"De CD kon niet aan Discogs worden gekoppeld.\n\n{error}")

    def _emit_selected(self, row):
        item = self.table.item(row, 0)
        if item is not None:
            try:
                self.cd_selected.emit(int(item.text()))
            except ValueError:
                pass

# ============================================================
# KID ACID'S VINYLVAULT V3
# CD TRACK EDITOR
# ============================================================

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QInputDialog,
    QMessageBox, QFileDialog,
)

from database.cd_database import get_cd_tracks, replace_cd_tracks


class CDTrackEditorDialog(QDialog):
    """Manual editor for a CD tracklist, including optional MP3 links."""

    def __init__(self, cd_release_id, artist="", title="", parent=None):
        super().__init__(parent)
        self.cd_release_id = int(cd_release_id)
        self.setWindowTitle(f"CD TRACKS — {artist} — {title}")
        self.resize(1050, 560)
        self.build_ui()
        self.load_tracks()

    def build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(10)

        heading = QLabel("TRACKS BEWERKEN")
        heading.setStyleSheet("font-size:20px; font-weight:900; color:#fff;")
        root.addWidget(heading)

        info = QLabel(
            "Voeg tracks toe, pas ze aan of verwijder ze. Je kunt per track ook een bestaand MP3-bestand uit je MP3-map koppelen."
        )
        info.setWordWrap(True)
        info.setStyleSheet("color:#999; font-size:12px;")
        root.addWidget(info)

        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(["#", "POSITIE", "ARTIST", "TITEL", "DUUR", "MP3"])
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)
        self.table.doubleClicked.connect(self.edit_selected)
        root.addWidget(self.table, 1)

        buttons = QHBoxLayout()
        self.add_button = QPushButton("+ TRACK")
        self.add_button.clicked.connect(self.add_track)
        buttons.addWidget(self.add_button)

        self.mp3_button = QPushButton("MP3 KOPPELEN")
        self.mp3_button.clicked.connect(self.link_selected_mp3)
        buttons.addWidget(self.mp3_button)

        self.clear_mp3_button = QPushButton("MP3 LOSKOPPELEN")
        self.clear_mp3_button.clicked.connect(self.clear_selected_mp3)
        buttons.addWidget(self.clear_mp3_button)

        self.edit_button = QPushButton("BEWERK TRACK")
        self.edit_button.clicked.connect(self.edit_selected)
        buttons.addWidget(self.edit_button)

        self.delete_button = QPushButton("VERWIJDER TRACK")
        self.delete_button.clicked.connect(self.delete_selected)
        buttons.addWidget(self.delete_button)

        buttons.addStretch()
        cancel = QPushButton("ANNULEREN")
        cancel.clicked.connect(self.reject)
        buttons.addWidget(cancel)

        save = QPushButton("OPSLAAN")
        save.clicked.connect(self.save_tracks)
        buttons.addWidget(save)
        root.addLayout(buttons)

        self.setStyleSheet("""
            QDialog { background:#0b0b0f; color:#f5f5f7; }
            QLabel { color:#f5f5f7; }
            QTableWidget { background:#101014; alternate-background-color:#17171d;
                color:#eee; gridline-color:#292933; border:1px solid #30303a;
                selection-background-color:#38383f; }
            QHeaderView::section { background:#202027; color:#fff; padding:8px;
                border:none; border-right:1px solid #30303a; font-weight:800; }
            QPushButton { background:#18181f; color:#fff; border:1px solid #30303a;
                border-radius:7px; padding:8px 14px; font-weight:800; }
            QPushButton:hover { background:#24242c; }
        """)

    def load_tracks(self):
        self.table.setRowCount(0)
        for track in get_cd_tracks(self.cd_release_id):
            self._append_row(
                position=track[2],
                artist=track[4],
                title=track[5],
                duration=track[6],
                mp3_path=track[8] if len(track) > 8 else "",
            )

    def _append_row(self, position="", artist="", title="", duration="", mp3_path=""):
        row = self.table.rowCount()
        self.table.insertRow(row)
        display_mp3 = Path(mp3_path).name if mp3_path else ""
        values = [row + 1, position, artist, title, duration, display_mp3]
        for column, value in enumerate(values):
            item = QTableWidgetItem(str(value or ""))
            if column == 0:
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            if column == 5 and mp3_path:
                item.setToolTip(mp3_path)
                item.setData(Qt.ItemDataRole.UserRole, mp3_path)
            self.table.setItem(row, column, item)
        self.table.setRowHeight(row, 34)

    def _selected_row(self):
        selected = self.table.selectionModel().selectedRows()
        return selected[0].row() if selected else None

    def add_track(self):
        position, ok = QInputDialog.getText(self, "Track toevoegen", "Positie:", text="")
        if not ok:
            return
        artist, ok = QInputDialog.getText(self, "Track toevoegen", "Artist:", text="")
        if not ok:
            return
        title, ok = QInputDialog.getText(self, "Track toevoegen", "Titel:", text="")
        if not ok:
            return
        if not title.strip():
            QMessageBox.warning(self, "Titel ontbreekt", "Een track moet een titel hebben.")
            return
        duration, ok = QInputDialog.getText(self, "Track toevoegen", "Duur:", text="")
        if not ok:
            return
        self._append_row(position.strip(), artist.strip(), title.strip(), duration.strip(), "")

        # Select the newly added row so MP3 KOPPELEN can be used immediately.
        self.table.selectRow(self.table.rowCount() - 1)
        self.link_selected_mp3(optional=True)

    def link_selected_mp3(self, optional=False):
        row = self._selected_row()
        if row is None:
            if not optional:
                QMessageBox.information(self, "Geen track geselecteerd", "Selecteer eerst de track waaraan je een MP3 wilt koppelen.")
            return

        current_item = self.table.item(row, 5)
        current_path = current_item.data(Qt.ItemDataRole.UserRole) if current_item else ""
        start_dir = str(Path(r"D:\01. MP3's")) if Path(r"D:\01. MP3's").exists() else ""
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Kies MP3 voor deze track",
            start_dir,
            "MP3 bestanden (*.mp3);;Alle bestanden (*.*)",
        )
        if not path:
            return

        item = self.table.item(row, 5)
        if item is None:
            item = QTableWidgetItem()
            self.table.setItem(row, 5, item)
        item.setText(Path(path).name)
        item.setToolTip(path)
        item.setData(Qt.ItemDataRole.UserRole, path)

    def clear_selected_mp3(self):
        row = self._selected_row()
        if row is None:
            QMessageBox.information(self, "Geen track geselecteerd", "Selecteer eerst een track.")
            return
        item = self.table.item(row, 5)
        if item is not None:
            item.setText("")
            item.setToolTip("")
            item.setData(Qt.ItemDataRole.UserRole, "")

    def edit_selected(self):
        row = self._selected_row()
        if row is None:
            QMessageBox.information(self, "Geen track geselecteerd", "Selecteer eerst een track.")
            return

        fields = [("Positie", 1), ("Artist", 2), ("Titel", 3), ("Duur", 4)]
        for label, column in fields:
            current = self.table.item(row, column).text() if self.table.item(row, column) else ""
            value, ok = QInputDialog.getText(self, "Track bewerken", f"{label}:", text=current)
            if not ok:
                return
            if label == "Titel" and not value.strip():
                QMessageBox.warning(self, "Titel ontbreekt", "Een track moet een titel hebben.")
                return
            self.table.item(row, column).setText(value.strip())

    def delete_selected(self):
        row = self._selected_row()
        if row is None:
            QMessageBox.information(self, "Geen track geselecteerd", "Selecteer eerst een track.")
            return
        title = self.table.item(row, 3).text() if self.table.item(row, 3) else ""
        answer = QMessageBox.question(
            self, "Track verwijderen", f"Wil je deze track verwijderen?\n\n{title}",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        self.table.removeRow(row)
        for index in range(self.table.rowCount()):
            self.table.item(index, 0).setText(str(index + 1))

    def save_tracks(self):
        tracks = []
        for row in range(self.table.rowCount()):
            title = self.table.item(row, 3).text().strip() if self.table.item(row, 3) else ""
            if not title:
                QMessageBox.warning(self, "Ongeldige track", f"Track {row + 1} heeft geen titel.")
                return
            mp3_item = self.table.item(row, 5)
            mp3_path = mp3_item.data(Qt.ItemDataRole.UserRole) if mp3_item else ""
            tracks.append({
                "position": self.table.item(row, 1).text().strip(),
                "track_order": row + 1,
                "artist": self.table.item(row, 2).text().strip(),
                "title": title,
                "duration": self.table.item(row, 4).text().strip(),
                "discogs_track_id": "",
                "mp3_path": str(mp3_path or "").strip(),
            })

        try:
            replace_cd_tracks(self.cd_release_id, tracks)
        except Exception as error:
            QMessageBox.critical(self, "Opslaan mislukt", f"De tracks konden niet worden opgeslagen.\n\n{error}")
            return

        self.accept()

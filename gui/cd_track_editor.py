# ============================================================
# KID ACID'S VINYLVAULT V3
# CD TRACK EDITOR
# ============================================================

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QInputDialog,
    QMessageBox,
)

from database.cd_database import get_cd_tracks, replace_cd_tracks


class CDTrackEditorDialog(QDialog):
    """Manual editor for the complete tracklist of one CD release."""

    def __init__(self, cd_release_id, artist="", title="", parent=None):
        super().__init__(parent)
        self.cd_release_id = int(cd_release_id)
        self.setWindowTitle(f"CD TRACKS — {artist} — {title}")
        self.resize(820, 520)
        self.build_ui()
        self.load_tracks()

    def build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(10)

        heading = QLabel("TRACKS BEWERKEN")
        heading.setStyleSheet("font-size:20px; font-weight:900; color:#fff;")
        root.addWidget(heading)

        info = QLabel("Voeg tracks toe, pas ze aan of verwijder ze. Discogs-tracks kunnen hier ook handmatig worden aangepast.")
        info.setWordWrap(True)
        info.setStyleSheet("color:#999; font-size:12px;")
        root.addWidget(info)

        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["#", "POSITIE", "ARTIST", "TITEL", "DUUR"])
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self.table.doubleClicked.connect(self.edit_selected)
        root.addWidget(self.table, 1)

        buttons = QHBoxLayout()
        self.add_button = QPushButton("+ TRACK")
        self.add_button.clicked.connect(self.add_track)
        buttons.addWidget(self.add_button)

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
            )

    def _append_row(self, position="", artist="", title="", duration=""):
        row = self.table.rowCount()
        self.table.insertRow(row)
        values = [row + 1, position, artist, title, duration]
        for column, value in enumerate(values):
            item = QTableWidgetItem(str(value or ""))
            if column == 0:
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
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
        self._append_row(position.strip(), artist.strip(), title.strip(), duration.strip())

    def edit_selected(self):
        row = self._selected_row()
        if row is None:
            QMessageBox.information(self, "Geen track geselecteerd", "Selecteer eerst een track.")
            return

        fields = [
            ("Positie", 1),
            ("Artist", 2),
            ("Titel", 3),
            ("Duur", 4),
        ]
        for label, column in fields:
            current = self.table.item(row, column).text() if self.table.item(row, column) else ""
            if label == "Titel":
                value, ok = QInputDialog.getText(self, "Track bewerken", f"{label}:", text=current)
                if not ok:
                    return
                if not value.strip():
                    QMessageBox.warning(self, "Titel ontbreekt", "Een track moet een titel hebben.")
                    return
            else:
                value, ok = QInputDialog.getText(self, "Track bewerken", f"{label}:", text=current)
                if not ok:
                    return
            self.table.item(row, column).setText(value.strip())

    def delete_selected(self):
        row = self._selected_row()
        if row is None:
            QMessageBox.information(self, "Geen track geselecteerd", "Selecteer eerst een track.")
            return
        title = self.table.item(row, 3).text() if self.table.item(row, 3) else ""
        answer = QMessageBox.question(
            self,
            "Track verwijderen",
            f"Wil je deze track verwijderen?\n\n{title}",
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
            tracks.append({
                "position": self.table.item(row, 1).text().strip(),
                "track_order": row + 1,
                "artist": self.table.item(row, 2).text().strip(),
                "title": title,
                "duration": self.table.item(row, 4).text().strip(),
                "discogs_track_id": "",
            })

        try:
            replace_cd_tracks(self.cd_release_id, tracks)
        except Exception as error:
            QMessageBox.critical(self, "Opslaan mislukt", f"De tracks konden niet worden opgeslagen.\n\n{error}")
            return

        self.accept()

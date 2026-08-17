from pathlib import Path

from PySide6.QtCore import Qt, QTimer, Signal, QAbstractTableModel, QModelIndex
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QComboBox, QTableView, QDialog, QFormLayout, QDialogButtonBox,
    QMessageBox, QTextEdit,
)

from database.database import get_connection

try:
    from mutagen.id3 import ID3, ID3NoHeaderError, TIT2, TPE1, TALB, TCON, TDRC, TRCK, TPOS, TCOM, TPE2, COMM
    from mutagen.mp3 import MP3
    MUTAGEN_AVAILABLE = True
except ImportError:
    MUTAGEN_AVAILABLE = False


class MP3TableModel(QAbstractTableModel):
    HEADERS = ["Artist", "Title", "Album", "Year", "BPM", "Pad", "Koppeling"]

    def __init__(self, rows=None, parent=None):
        super().__init__(parent)
        self.rows = rows or []

    def rowCount(self, parent=QModelIndex()):
        return 0 if parent.isValid() else len(self.rows)

    def columnCount(self, parent=QModelIndex()):
        return 0 if parent.isValid() else len(self.HEADERS)

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid() or index.row() >= len(self.rows):
            return None
        row = self.rows[index.row()]
        if role == Qt.ItemDataRole.DisplayRole:
            return str(row[index.column()] or "")
        if role == Qt.ItemDataRole.ToolTipRole:
            return str(row[7] or "") if index.column() in (0, 1, 2, 5) else None
        return None

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if role != Qt.ItemDataRole.DisplayRole:
            return None
        if orientation == Qt.Orientation.Horizontal:
            return self.HEADERS[section]
        return str(section + 1)

    def set_rows(self, rows):
        self.beginResetModel()
        self.rows = rows
        self.endResetModel()


class MetadataDialog(QDialog):
    def __init__(self, row, parent=None):
        super().__init__(parent)
        self.row = row
        self.setWindowTitle("MP3 Metadata Builder")
        self.resize(620, 430)

        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.artist = QLineEdit(str(row[1] or ""))
        self.title = QLineEdit(str(row[2] or ""))
        self.album = QLineEdit(str(row[3] or ""))
        self.year = QLineEdit(str(row[4] or ""))
        self.bpm = QLineEdit(str(row[5] or ""))
        self.track = QLineEdit(str(row[6] or ""))
        self.disc = QLineEdit(str(row[7] or ""))
        self.album_artist = QLineEdit(str(row[8] or ""))
        self.composer = QLineEdit(str(row[9] or ""))
        self.genre = QLineEdit(str(row[10] or ""))
        self.comment = QTextEdit(str(row[11] or ""))
        self.comment.setFixedHeight(75)

        form.addRow("Artist:", self.artist)
        form.addRow("Title:", self.title)
        form.addRow("Album:", self.album)
        form.addRow("Year:", self.year)
        form.addRow("BPM:", self.bpm)
        form.addRow("Track:", self.track)
        form.addRow("Disc:", self.disc)
        form.addRow("Album Artist:", self.album_artist)
        form.addRow("Composer:", self.composer)
        form.addRow("Genre:", self.genre)
        form.addRow("Comment:", self.comment)
        layout.addLayout(form)

        self.status = QLabel(f"Bestand: {row[0]}")
        self.status.setWordWrap(True)
        layout.addWidget(self.status)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Cancel | QDialogButtonBox.StandardButton.Save
        )
        buttons.accepted.connect(self.save)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def save(self):
        if not MUTAGEN_AVAILABLE:
            QMessageBox.warning(
                self,
                "Mutagen ontbreekt",
                "Installeer eerst Mutagen:\n\npython -m pip install mutagen",
            )
            return

        path = str(self.row[0])
        if not Path(path).exists():
            QMessageBox.warning(self, "Bestand ontbreekt", path)
            return

        try:
            try:
                tags = ID3(path)
            except ID3NoHeaderError:
                tags = ID3()

            def text(v):
                return str(v).strip()

            tags.delall("TPE1")
            tags.add(TPE1(encoding=3, text=text(self.artist.text())))
            tags.delall("TIT2")
            tags.add(TIT2(encoding=3, text=text(self.title.text())))
            tags.delall("TALB")
            tags.add(TALB(encoding=3, text=text(self.album.text())))
            tags.delall("TCON")
            tags.add(TCON(encoding=3, text=text(self.genre.text())))
            tags.delall("TDRC")
            if text(self.year.text()):
                tags.add(TDRC(encoding=3, text=text(self.year.text())))
            tags.delall("TRCK")
            if text(self.track.text()):
                tags.add(TRCK(encoding=3, text=text(self.track.text())))
            tags.delall("TPOS")
            if text(self.disc.text()):
                tags.add(TPOS(encoding=3, text=text(self.disc.text())))
            tags.delall("TPE2")
            if text(self.album_artist.text()):
                tags.add(TPE2(encoding=3, text=text(self.album_artist.text())))
            tags.delall("TCOM")
            if text(self.composer.text()):
                tags.add(TCOM(encoding=3, text=text(self.composer.text())))
            tags.delall("COMM")
            if text(self.comment.toPlainText()):
                tags.add(COMM(encoding=3, lang="eng", desc="", text=text(self.comment.toPlainText())))
            tags.save(path, v2_version=3)

            try:
                audio = MP3(path)
                db_bpm = float(self.bpm.text()) if text(self.bpm.text()) else None
            except Exception:
                db_bpm = None

            conn = get_connection()
            try:
                conn.execute(
                    "UPDATE mp3_files SET artist=?, title=?, album=?, year=?, genre=?, bpm=?, updated_at=CURRENT_TIMESTAMP WHERE path=?",
                    (text(self.artist.text()), text(self.title.text()), text(self.album.text()), int(self.year.text()) if text(self.year.text()) else None, text(self.genre.text()), db_bpm, path),
                )
                conn.commit()
            finally:
                conn.close()

            self.accept()
        except Exception as exc:
            QMessageBox.critical(self, "Metadata opslaan mislukt", str(exc))


class MP3LibraryPage(QWidget):
    play_mp3 = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.rows = []
        self.filtered_rows = []
        self.build_ui()
        self.load_data()

    def build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 22, 24, 20)
        root.setSpacing(12)

        title = QLabel("MP3 LIBRARY")
        title.setStyleSheet("font-size: 25px; font-weight: 900; color: #ffffff;")
        root.addWidget(title)

        tools = QHBoxLayout()
        self.search = QLineEdit()
        self.search.setPlaceholderText("Zoek artiest, titel, album, bestandsnaam…")
        tools.addWidget(self.search, 1)

        self.filter = QComboBox()
        self.filter.addItems(["Alle MP3's", "Aan vinyl gekoppeld", "Niet gekoppeld"])
        tools.addWidget(self.filter)

        self.refresh = QPushButton("VERVERS")
        tools.addWidget(self.refresh)
        root.addLayout(tools)

        self.info = QLabel("0 MP3's")
        self.info.setStyleSheet("color: #9b9ba6;")
        root.addWidget(self.info)

        self.table = QTableView()
        self.model = MP3TableModel(parent=self.table)
        self.table.setModel(self.model)
        self.table.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableView.SelectionMode.SingleSelection)
        self.table.setAlternatingRowColors(False)
        self.table.setSortingEnabled(False)
        self.table.doubleClicked.connect(self.play_selected)
        self.table.setColumnWidth(0, 190)
        self.table.setColumnWidth(1, 260)
        self.table.setColumnWidth(2, 220)
        root.addWidget(self.table, 1)

        actions = QHBoxLayout()
        self.play_button = QPushButton("▶ PLAY")
        self.meta_button = QPushButton("METADATA BEWERKEN")
        actions.addWidget(self.play_button)
        actions.addWidget(self.meta_button)
        actions.addStretch()
        root.addLayout(actions)

        self.search_timer = QTimer(self)
        self.search_timer.setSingleShot(True)
        self.search_timer.setInterval(180)
        self.search_timer.timeout.connect(self.apply_filter)
        self.search.textChanged.connect(lambda _: self.search_timer.start())
        self.filter.currentIndexChanged.connect(self.apply_filter)
        self.refresh.clicked.connect(self.load_data)
        self.play_button.clicked.connect(self.play_selected)
        self.meta_button.clicked.connect(self.edit_selected_metadata)

        self.setStyleSheet("""
            QWidget { background: #0b0b0f; color: #f2f2f5; }
            QLineEdit, QComboBox, QPushButton { background: #18181f; color: #fff; border: 1px solid #30303a; border-radius: 6px; padding: 8px 10px; }
            QPushButton:hover { border-color: #d84b91; background: #24242c; }
            QTableView { background: #0f0f14; border: 1px solid #25252d; gridline-color: #202028; }
            QTableView::item { padding: 6px; }
            QHeaderView::section { background: #18181f; color: #aaaaaf; padding: 7px; border: none; }
        """)

    def load_data(self):
        conn = get_connection()
        try:
            self.rows = conn.execute(
                """
                SELECT m.path, m.artist, m.title, m.album, m.year, m.bpm,
                       m.genre,
                       CASE WHEN EXISTS (SELECT 1 FROM track_mp3 tm WHERE tm.mp3_id=m.id) THEN 1 ELSE 0 END AS linked,
                       COALESCE((SELECT r.artist || ' - ' || r.title || ' / ' || t.position || ' ' || t.title
                                 FROM track_mp3 tm JOIN tracks t ON t.id=tm.track_id JOIN releases r ON r.id=t.release_id
                                 WHERE tm.mp3_id=m.id ORDER BY tm.id LIMIT 1), '') AS vinyl_link
                FROM mp3_files m
                ORDER BY m.artist COLLATE NOCASE, m.title COLLATE NOCASE, m.path COLLATE NOCASE
                """
            ).fetchall()
        finally:
            conn.close()
        self.apply_filter()

    def apply_filter(self):
        text = self.search.text().strip().casefold()
        mode = self.filter.currentIndex()
        rows = []
        for row in self.rows:
            linked = int(row[7] or 0)
            if mode == 1 and not linked:
                continue
            if mode == 2 and linked:
                continue
            hay = " ".join(str(x or "") for x in (row[0], row[1], row[2], row[3], row[4], row[6])).casefold()
            if text and text not in hay:
                continue
            display = (row[0], row[1], row[2], row[3], row[4], row[5], "VINYL" if linked else "LOS", row[8])
            rows.append(display)
        self.filtered_rows = rows
        self.model.set_rows(rows)
        self.info.setText(f"{len(rows)} van {len(self.rows)} MP3's")

    def selected_row(self):
        indexes = self.table.selectionModel().selectedRows()
        if not indexes:
            return None
        return self.model.rows[indexes[0].row()]

    def play_selected(self, *_args):
        row = self.selected_row()
        if row is None:
            return
        path = str(row[0] or "")
        if path and Path(path).exists():
            self.play_mp3.emit(path)
        else:
            QMessageBox.warning(self, "Bestand ontbreekt", path)

    def edit_selected_metadata(self, *_args):
        row = self.selected_row()
        if row is None:
            return
        if not MUTAGEN_AVAILABLE:
            QMessageBox.information(self, "Metadata Builder", "Installeer Mutagen met:\n\npython -m pip install mutagen")
            return
        path = str(row[0])
        if not Path(path).exists():
            QMessageBox.warning(self, "Bestand ontbreekt", path)
            return
        try:
            tags = ID3(path)
            def first(key):
                value = tags.get(key)
                if value is None:
                    return ""
                return str(value[0]) if hasattr(value, "__getitem__") and not isinstance(value, str) else str(value)
            dialog_row = (
                path, first("TPE1"), first("TIT2"), first("TALB"), first("TDRC"),
                first("TBPM"), first("TRCK"), first("TPOS"), first("TPE2"), first("TCOM"),
                first("TCON"), first("COMM::eng")
            )
        except Exception:
            dialog_row = (path, row[1], row[2], row[3], row[4], row[5], "", "", "", "", row[6], "")
        dialog = MetadataDialog(dialog_row, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.load_data()

from pathlib import Path
import sqlite3

BASE = Path(__file__).resolve().parents[2]
DB = BASE / "data" / "vinylvault.db"
TARGET = BASE / "gui" / "mp3_library_page.py"


def ensure_db():
    conn = sqlite3.connect(DB)
    try:
        cols = {row[1] for row in conn.execute("PRAGMA table_info(mp3_files)").fetchall()}
        if "metadata_checked" not in cols:
            conn.execute("ALTER TABLE mp3_files ADD COLUMN metadata_checked INTEGER NOT NULL DEFAULT 0")
        if "metadata_checked_at" not in cols:
            conn.execute("ALTER TABLE mp3_files ADD COLUMN metadata_checked_at TEXT")
        conn.commit()
    finally:
        conn.close()


def replace_once(text, old, new, label):
    if old not in text:
        raise RuntimeError(f"Kan patroon niet vinden: {label}")
    return text.replace(old, new, 1)


ensure_db()
text = TARGET.read_text(encoding="utf-8-sig")

# Add QBrush/QColor for row highlighting.
text = replace_once(
    text,
    "from PySide6.QtCore import Qt, QTimer, Signal, QAbstractTableModel, QModelIndex\n",
    "from PySide6.QtCore import Qt, QTimer, Signal, QAbstractTableModel, QModelIndex\nfrom PySide6.QtGui import QColor, QBrush\n",
    "QtGui imports",
)

# Extend headers with explicit progress status.
text = replace_once(
    text,
    '    HEADERS = ["Artist", "Title", "Album", "Year", "BPM", "Pad", "Koppeling"]\n',
    '    HEADERS = ["Artist", "Title", "Album", "Year", "BPM", "Pad", "Koppeling", "Metadata"]\n',
    "headers",
)

# Highlight completed rows; keep the entire row visibly yellow.
needle = '''        if role == Qt.ItemDataRole.DisplayRole:\n            return str(row[index.column()] or "")\n        if role == Qt.ItemDataRole.ToolTipRole:\n'''
replacement = '''        if role == Qt.ItemDataRole.DisplayRole:\n            return str(row[index.column()] or "")\n        if role == Qt.ItemDataRole.BackgroundRole and len(row) > 8 and int(row[8] or 0) == 1:\n            return QBrush(QColor("#4a3d16"))\n        if role == Qt.ItemDataRole.ForegroundRole and len(row) > 8 and int(row[8] or 0) == 1:\n            return QBrush(QColor("#ffe89a"))\n        if role == Qt.ItemDataRole.ToolTipRole:\n'''
text = replace_once(text, needle, replacement, "row highlight")

# Add a metadata-progress filter directly after the vinyl-link filter.
needle = '''        self.filter = QComboBox()\n        self.filter.addItems(["Alle MP3's", "Aan vinyl gekoppeld", "Niet gekoppeld"])\n        tools.addWidget(self.filter)\n'''
replacement = '''        self.filter = QComboBox()\n        self.filter.addItems(["Alle MP3's", "Aan vinyl gekoppeld", "Niet gekoppeld"])\n        tools.addWidget(self.filter)\n\n        self.metadata_filter = QComboBox()\n        self.metadata_filter.addItems(["Metadata: Alles", "Metadata: Klaar", "Metadata: Niet gedaan"])\n        tools.addWidget(self.metadata_filter)\n'''
text = replace_once(text, needle, replacement, "metadata filter")

# Make action buttons more visible and keep them at the bottom.
needle = '''        actions = QHBoxLayout()\n        self.play_button = QPushButton("▶ PLAY")\n        self.meta_button = QPushButton("METADATA BEWERKEN")\n        actions.addWidget(self.play_button)\n        actions.addWidget(self.meta_button)\n        actions.addStretch()\n        root.addLayout(actions)\n'''
replacement = '''        actions = QHBoxLayout()\n        self.play_button = QPushButton("▶ PLAY")\n        self.meta_button = QPushButton("✎ METADATA BEWERKEN")\n        self.open_folder_button = QPushButton("📁 OPEN MAP")\n        self.refresh_button = QPushButton("⟳ VERVERS")\n\n        self.play_button.setMinimumHeight(42)\n        self.meta_button.setMinimumHeight(42)\n        self.open_folder_button.setMinimumHeight(42)\n        self.refresh_button.setMinimumHeight(42)\n\n        actions.addWidget(self.play_button)\n        actions.addWidget(self.meta_button)\n        actions.addWidget(self.open_folder_button)\n        actions.addWidget(self.refresh_button)\n        actions.addStretch()\n        root.addLayout(actions)\n'''
text = replace_once(text, needle, replacement, "action bar")

# Reuse refresh button if the old name exists; otherwise connect the new one.
text = replace_once(
    text,
    '        self.refresh.clicked.connect(self.load_data)\n        self.play_button.clicked.connect(self.play_selected)\n',
    '        self.refresh.clicked.connect(self.load_data)\n        self.refresh_button.clicked.connect(self.load_data)\n        self.play_button.clicked.connect(self.play_selected)\n        self.metadata_filter.currentIndexChanged.connect(self.apply_filter)\n',
    "signals",
)

# Update SQL to include metadata progress.
text = replace_once(
    text,
    '''                SELECT m.path, m.artist, m.title, m.album, m.year, m.bpm,\n                       m.genre,\n''',
    '''                SELECT m.path, m.artist, m.title, m.album, m.year, m.bpm,\n                       m.genre,\n''',
    "sql anchor",
)
text = replace_once(
    text,
    '''                       COALESCE((SELECT r.artist || ' - ' || r.title || ' / ' || t.position || ' ' || t.title\n                                 FROM track_mp3 tm JOIN tracks t ON t.id=tm.track_id JOIN releases r ON r.id=t.release_id\n                                 WHERE tm.mp3_id=m.id ORDER BY tm.id LIMIT 1), '') AS vinyl_link\n''',
    '''                       COALESCE((SELECT r.artist || ' - ' || r.title || ' / ' || t.position || ' ' || t.title\n                                 FROM track_mp3 tm JOIN tracks t ON t.id=tm.track_id JOIN releases r ON r.id=t.release_id\n                                 WHERE tm.mp3_id=m.id ORDER BY tm.id LIMIT 1), '') AS vinyl_link,\n                       COALESCE(m.metadata_checked, 0) AS metadata_checked\n''',
    "sql metadata field",
)

# Apply metadata filter without making completed rows disappear from the default view.
needle = '''            linked = int(row[7] or 0)\n            if mode == 1 and not linked:\n                continue\n            if mode == 2 and linked:\n                continue\n            hay = " ".join(str(x or "") for x in (row[0], row[1], row[2], row[3], row[4], row[6])).casefold()\n'''
replacement = '''            linked = int(row[7] or 0)\n            metadata_checked = int(row[9] or 0) if len(row) > 9 else 0\n            if mode == 1 and not linked:\n                continue\n            if mode == 2 and linked:\n                continue\n            meta_mode = self.metadata_filter.currentIndex()\n            if meta_mode == 1 and not metadata_checked:\n                continue\n            if meta_mode == 2 and metadata_checked:\n                continue\n            hay = " ".join(str(x or "") for x in (row[0], row[1], row[2], row[3], row[4], row[6])).casefold()\n'''
text = replace_once(text, needle, replacement, "metadata filtering")

# Keep path as an internal field at the end, not as Artist.
needle = '            display = (row[0], row[1], row[2], row[3], row[4], row[5], "VINYL" if linked else "LOS", row[8])\n'
replacement = '            display = (row[1], row[2], row[3], row[4], row[5], row[0], "VINYL" if linked else "LOS", row[8], metadata_checked, row[0])\n'
text = replace_once(text, needle, replacement, "display mapping")

# Selection path must use the internal final field.
needle = '''        path = str(row[0] or "")\n        if path and Path(path).exists():\n            self.play_mp3.emit(path)\n'''
replacement = '''        path = str(row[9] or "")\n        if path and Path(path).exists():\n            self.play_mp3.emit(path)\n'''
text = replace_once(text, needle, replacement, "play path")

# Metadata editor path must use internal final field.
needle = '''        path = str(row[0])\n        if not Path(path).exists():\n'''
replacement = '''        path = str(row[9] or "")\n        if not Path(path).exists():\n'''
text = replace_once(text, needle, replacement, "editor path")

# Make metadata column visible and show a clear status label.
needle = '''        self.table.setColumnWidth(0, 190)\n        self.table.setColumnWidth(1, 260)\n        self.table.setColumnWidth(2, 220)\n'''
replacement = '''        self.table.setColumnWidth(0, 190)\n        self.table.setColumnWidth(1, 260)\n        self.table.setColumnWidth(2, 220)\n        self.table.setColumnWidth(3, 80)\n        self.table.setColumnWidth(4, 90)\n        self.table.setColumnWidth(5, 420)\n        self.table.setColumnWidth(6, 90)\n        self.table.setColumnWidth(7, 130)\n'''
text = replace_once(text, needle, replacement, "column widths")

# Mark saved MP3 as checked. Replace the existing UPDATE with metadata_checked fields.
needle = '''                    "UPDATE mp3_files SET artist=?, title=?, album=?, year=?, genre=?, bpm=?, updated_at=CURRENT_TIMESTAMP WHERE path=?",\n                    (text(self.artist.text()), text(self.title.text()), text(self.album.text()), int(self.year.text()) if text(self.year.text()) else None, text(self.genre.text()), db_bpm, path),\n'''
replacement = '''                    """\n                    UPDATE mp3_files\n                    SET artist=?, title=?, album=?, year=?, genre=?, bpm=?,\n                        metadata_checked=1, metadata_checked_at=CURRENT_TIMESTAMP,\n                        updated_at=CURRENT_TIMESTAMP\n                    WHERE path=?\n                    """,\n                    (text(self.artist.text()), text(self.title.text()), text(self.album.text()), int(self.year.text()) if text(self.year.text()) else None, text(self.genre.text()), db_bpm, path),\n'''
text = replace_once(text, needle, replacement, "save progress")

# Ensure save does not cause the current row to vanish; refresh while preserving filter.
text = replace_once(
    text,
    '''        if dialog.exec() == QDialog.DialogCode.Accepted:\n            self.load_data()\n''',
    '''        if dialog.exec() == QDialog.DialogCode.Accepted:\n            # Refresh data but do not change the active filter. Default is Metadata: Alles.\n            self.load_data()\n''',
    "post-save refresh",
)

# Add explicit status text through the model display without changing visible data order.
needle = '''        if role == Qt.ItemDataRole.DisplayRole:\n            return str(row[index.column()] or "")\n'''
replacement = '''        if role == Qt.ItemDataRole.DisplayRole:\n            if index.column() == 7 and len(row) > 8:\n                return "✓ KLAAR" if int(row[8] or 0) == 1 else "NIET GEDAAN"\n            return str(row[index.column()] or "")\n'''
text = replace_once(text, needle, replacement, "status display")

TARGET.write_text(text, encoding="utf-8")
print("MP3 Library progress/actions fix toegepast.")

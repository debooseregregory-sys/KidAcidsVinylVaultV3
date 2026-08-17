from pathlib import Path

BASE = Path(__file__).resolve().parents[2]
TARGET = BASE / 'gui' / 'mp3_library_page.py'
text = TARGET.read_text(encoding='utf-8-sig')

# Make the database remember whether the user actually completed the metadata dialog.
db_insert = '''\n\n# MP3 metadata progress helper\ndef ensure_mp3_metadata_progress():\n    conn = get_connection()\n    try:\n        cols = {row[1] for row in conn.execute("PRAGMA table_info(mp3_files)").fetchall()}\n        if "metadata_checked" not in cols:\n            conn.execute("ALTER TABLE mp3_files ADD COLUMN metadata_checked INTEGER NOT NULL DEFAULT 0")\n        if "metadata_checked_at" not in cols:\n            conn.execute("ALTER TABLE mp3_files ADD COLUMN metadata_checked_at TEXT")\n        conn.commit()\n    finally:\n        conn.close()\n'''
if 'def ensure_mp3_metadata_progress()' not in text:
    marker = 'try:\n'
    # place after imports/try block by inserting before first class
    p = text.find('\n\nclass MP3TableModel')
    text = text[:p] + db_insert + text[p:]

# Ensure the dialog keeps its row/path.
needle = 'class MetadataDialog(QDialog):\n    def __init__(self, row, parent=None):\n        super().__init__(parent)\n'
if needle in text and '        self.row = row\n' not in text[text.find(needle):text.find(needle)+400]:
    text = text.replace(needle, needle + '        self.row = row\n', 1)

# Replace table model with status-aware model, keeping the hidden real path at row[8].
start = text.find('class MP3TableModel(QAbstractTableModel):')
end = text.find('\n\nclass MetadataDialog(QDialog):', start)
model = r'''class MP3TableModel(QAbstractTableModel):
    HEADERS = ["Artist", "Title", "Album", "Year", "BPM", "Pad", "Koppeling", "Metadata"]

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
        if role == Qt.ItemDataRole.BackgroundRole and int(row[9] or 0) == 1:
            from PySide6.QtGui import QColor
            return QColor("#4a3d08")
        if role == Qt.ItemDataRole.ForegroundRole and int(row[9] or 0) == 1:
            from PySide6.QtGui import QColor
            return QColor("#ffe08a")
        if role == Qt.ItemDataRole.ToolTipRole:
            return str(row[8] or "") if index.column() == 5 else None
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
'''
if start >= 0 and end >= 0:
    text = text[:start] + model + text[end:]

# Ensure page initializes progress status before loading.
text = text.replace('        self.rows = []\n        self.filtered_rows = []\n        self.build_ui()\n        self.load_data()', '        self.rows = []\n        self.filtered_rows = []\n        self.metadata_status_by_path = {}\n        ensure_mp3_metadata_progress()\n        self.build_ui()\n        self.load_data()', 1)

# Add explicit metadata filter.
needle = '        self.filter = QComboBox()\n        self.filter.addItems(["Alle MP3\'s", "Aan vinyl gekoppeld", "Niet gekoppeld"])\n        tools.addWidget(self.filter)'
if needle in text and 'self.metadata_filter = QComboBox()' not in text:
    repl = needle + '''\n\n        self.metadata_filter = QComboBox()\n        self.metadata_filter.addItems(["Metadata: Alles", "Metadata: KLAAR", "Metadata: NIET GEDAAN"])\n        tools.addWidget(self.metadata_filter)'''
    text = text.replace(needle, repl, 1)

# Connect the new filter.
text = text.replace('        self.filter.currentIndexChanged.connect(self.apply_filter)\n', '        self.filter.currentIndexChanged.connect(self.apply_filter)\n        self.metadata_filter.currentIndexChanged.connect(self.apply_filter)\n', 1)

# Replace load_data with a single query and single status query. Avoid per-row DB queries.
ls = text.find('    def load_data(self):')
le = text.find('\n    def apply_filter(self):', ls)
load_block = r'''    def load_data(self):
        conn = get_connection()
        try:
            self.rows = conn.execute(
                """
                SELECT m.path, m.artist, m.title, m.album, m.year, m.bpm,
                       m.genre,
                       EXISTS(SELECT 1 FROM track_mp3 tm WHERE tm.mp3_id=m.id) AS linked,
                       COALESCE((SELECT r.artist || ' - ' || r.title || ' / ' || t.position || ' ' || t.title
                                 FROM track_mp3 tm
                                 JOIN tracks t ON t.id=tm.track_id
                                 JOIN releases r ON r.id=t.release_id
                                 WHERE tm.mp3_id=m.id
                                 ORDER BY tm.id LIMIT 1), '') AS vinyl_link,
                       COALESCE(m.metadata_checked, 0) AS metadata_checked
                FROM mp3_files m
                ORDER BY m.artist COLLATE NOCASE, m.title COLLATE NOCASE, m.path COLLATE NOCASE
                """
            ).fetchall()
        finally:
            conn.close()

        self.metadata_status_by_path = {str(row[0]): int(row[9] or 0) for row in self.rows}
        self.apply_filter()
'''
if ls >= 0 and le >= 0:
    text = text[:ls] + load_block + text[le:]

# Replace apply_filter; display row has hidden path at index 8 and checked at index 9.
fs = text.find('    def apply_filter(self):')
fe = text.find('\n    def selected_row(self):', fs)
filter_block = r'''    def apply_filter(self):
        query = self.search.text().strip().casefold()
        link_mode = self.filter.currentIndex()
        meta_mode = self.metadata_filter.currentIndex() if hasattr(self, "metadata_filter") else 0
        rows = []

        for row in self.rows:
            linked = int(row[7] or 0)
            checked = int(row[9] or 0)

            if link_mode == 1 and not linked:
                continue
            if link_mode == 2 and linked:
                continue
            if meta_mode == 1 and not checked:
                continue
            if meta_mode == 2 and checked:
                continue

            hay = " ".join(str(x or "") for x in (row[0], row[1], row[2], row[3], row[4], row[6])).casefold()
            if query and query not in hay:
                continue

            rows.append((
                row[1], row[2], row[3], row[4], row[5],
                row[0], "VINYL" if linked else "LOS", row[8], row[0], checked
            ))

        self.filtered_rows = rows
        self.model.set_rows(rows)
        total = len(self.rows)
        done = sum(1 for row in self.rows if int(row[9] or 0) == 1)
        todo = total - done
        self.info.setText(f"{len(rows)} zichtbaar  |  {done} KLAAR  |  {todo} NIET GEDAAN  |  totaal {total} MP3's")
'''
if fs >= 0 and fe >= 0:
    text = text[:fs] + filter_block + text[fe:]

# Use hidden path in play/edit methods.
text = text.replace('        path = str(row[0] or "")\n        if path and Path(path).exists():', '        path = str(row[8] or "")\n        if path and Path(path).exists():', 1)
text = text.replace('        path = str(row[0])\n        if not Path(path).exists():', '        path = str(row[8] or "")\n        if not Path(path).exists():', 1)

# Mark as checked only after successful save, while preserving existing metadata DB update.
old = '''                conn.execute(
                    "UPDATE mp3_files SET artist=?, title=?, album=?, year=?, genre=?, bpm=?, updated_at=CURRENT_TIMESTAMP WHERE path=?",
                    (text(self.artist.text()), text(self.title.text()), text(self.album.text()), int(self.year.text()) if text(self.year.text()) else None, text(self.genre.text()), db_bpm, path),
                )
                conn.commit()'''
new = '''                conn.execute(
                    "UPDATE mp3_files SET artist=?, title=?, album=?, year=?, genre=?, bpm=?, metadata_checked=1, metadata_checked_at=CURRENT_TIMESTAMP, updated_at=CURRENT_TIMESTAMP WHERE path=?",
                    (text(self.artist.text()), text(self.title.text()), text(self.album.text()), int(self.year.text()) if text(self.year.text()) else None, text(self.genre.text()), db_bpm, self.path),
                )
                conn.commit()'''
text = text.replace(old, new, 1)

# Reload after save, but do not hide the just-finished file.
old_reload = '        if dialog.exec() == QDialog.DialogCode.Accepted:\n            self.load_data()'
new_reload = '        if dialog.exec() == QDialog.DialogCode.Accepted:\n            if hasattr(self, "metadata_filter"):\n                self.metadata_filter.blockSignals(True)\n                self.metadata_filter.setCurrentIndex(0)\n                self.metadata_filter.blockSignals(False)\n            self.load_data()'
text = text.replace(old_reload, new_reload, 1)

TARGET.write_text(text, encoding='utf-8-sig')
print('MP3 progress/filter/yellow fix applied')

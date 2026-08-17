from pathlib import Path

BASE = Path(__file__).resolve().parents[2]
TARGET = BASE / "gui" / "mp3_library_page.py"

text = TARGET.read_text(encoding="utf-8-sig")

# Add BackgroundRole support without changing existing display logic.
old = """        if role == Qt.ItemDataRole.DisplayRole:\n            return str(row[index.column()] or \"\")\n        if role == Qt.ItemDataRole.ToolTipRole:\n            return str(row[7] or \"\") if index.column() in (0, 1, 2, 5) else None\n        return None\n"""
new = """        if role == Qt.ItemDataRole.DisplayRole:\n            return str(row[index.column()] or \"\")\n        if role == Qt.ItemDataRole.ToolTipRole:\n            return str(row[-1] or \"\") if index.column() in (0, 1, 2, 5) else None\n        if role == Qt.ItemDataRole.BackgroundRole:\n            if len(row) > 1 and str(row[-2]) == \"KLAAR\":\n                from PySide6.QtGui import QBrush, QColor\n                return QBrush(QColor(82, 67, 18))\n        return None\n"""
if old in text:
    text = text.replace(old, new, 1)

# Add a status column to headers, preserving all existing columns.
old = '    HEADERS = ["Artist", "Title", "Album", "Year", "BPM", "Pad", "Koppeling"]'
new = '    HEADERS = ["Artist", "Title", "Album", "Year", "BPM", "Pad", "Koppeling", "Metadata"]'
if old in text:
    text = text.replace(old, new, 1)

# Create a small persistent status table automatically. This avoids altering mp3_files.
needle = '    def load_data(self):\n        conn = get_connection()\n'
replacement = '''    def load_data(self):\n        conn = get_connection()\n        try:\n            conn.execute(\n                """\n                CREATE TABLE IF NOT EXISTS mp3_metadata_status (\n                    path TEXT PRIMARY KEY,\n                    checked INTEGER NOT NULL DEFAULT 0,\n                    checked_at TEXT\n                )\n                """\n            )\n            conn.commit()\n        finally:\n            conn.close()\n\n        conn = get_connection()\n'''
if needle in text and 'CREATE TABLE IF NOT EXISTS mp3_metadata_status' not in text:
    text = text.replace(needle, replacement, 1)

# Extend every display tuple with metadata status while keeping the real path first
# internally for existing PLAY/EDIT logic.
old = '            display = (row[0], row[1], row[2], row[3], row[4], row[5], "VINYL" if linked else "LOS", row[8])\n'
new = '''            # Progress is stored separately from the MP3 metadata itself.\n            status_conn = get_connection()\n            try:\n                checked = status_conn.execute(\n                    "SELECT checked FROM mp3_metadata_status WHERE path=?",\n                    (str(row[0]),),\n                ).fetchone()\n            finally:\n                status_conn.close()\n            status = "KLAAR" if checked and int(checked[0] or 0) else "NIET GEDAAN"\n            display = (row[1], row[2], row[3], row[4], row[5], row[0], "VINYL" if linked else "LOS", status, row[8])\n'''
if old in text:
    text = text.replace(old, new, 1)

# Fix play_selected to use hidden path at index 5.
text = text.replace('        path = str(row[0] or "")\n        if path and Path(path).exists():', '        path = str(row[5] or "")\n        if path and Path(path).exists():', 1)

# Fix edit_selected_metadata to use hidden path at index 5.
text = text.replace('        path = str(row[0])\n        if not Path(path).exists():', '        path = str(row[5])\n        if not Path(path).exists():', 1)

# Search should include the actual visible metadata and path.
text = text.replace('            hay = " ".join(str(x or "") for x in (row[0], row[1], row[2], row[3], row[4], row[6])).casefold()', '            hay = " ".join(str(x or "") for x in (row[0], row[1], row[2], row[3], row[4], row[6])).casefold()', 1)

# Add metadata filter alongside existing Vinyl filters.
old = '        self.filter.addItems(["Alle MP3\'s", "Aan vinyl gekoppeld", "Niet gekoppeld"])'
new = '        self.filter.addItems(["Alle MP3\'s", "Aan vinyl gekoppeld", "Niet gekoppeld", "Metadata: Alles", "Metadata: KLAAR", "Metadata: NIET GEDAAN"])'
if old in text:
    text = text.replace(old, new, 1)

# Apply metadata filter without hiding saved rows from the default view.
old = '''            if mode == 1 and not linked:\n                continue\n            if mode == 2 and linked:\n                continue\n            hay = " ".join(str(x or "") for x in (row[0], row[1], row[2], row[3], row[4], row[6])).casefold()\n'''
new = '''            if mode == 1 and not linked:\n                continue\n            if mode == 2 and linked:\n                continue\n\n            status_conn = get_connection()\n            try:\n                checked = status_conn.execute(\n                    "SELECT checked FROM mp3_metadata_status WHERE path=?",\n                    (str(row[0]),),\n                ).fetchone()\n            finally:\n                status_conn.close()\n            is_done = bool(checked and int(checked[0] or 0))\n            if mode == 4 and not is_done:\n                continue\n            if mode == 5 and is_done:\n                continue\n\n            hay = " ".join(str(x or "") for x in (row[0], row[1], row[2], row[3], row[4], row[6])).casefold()\n'''
if old in text:
    text = text.replace(old, new, 1)

# If index changes because the filter is in use, keep the default filter on Alles MP3s.
text = text.replace('        self.info.setText(f"{len(rows)} van {len(self.rows)} MP3\'s")', '        self.info.setText(f"{len(rows)} van {len(self.rows)} MP3\'s")', 1)

# Mark metadata as checked after a successful dialog save. The separate status table
# keeps progress even when tags are later edited again.
old = '''        dialog = MetadataDialog(dialog_row, self)\n        if dialog.exec() == QDialog.DialogCode.Accepted:\n            self.load_data()\n'''
new = '''        dialog = MetadataDialog(dialog_row, self)\n        if dialog.exec() == QDialog.DialogCode.Accepted:\n            conn = get_connection()\n            try:\n                conn.execute(\n                    "INSERT INTO mp3_metadata_status(path, checked, checked_at) VALUES(?, 1, CURRENT_TIMESTAMP) "\n                    "ON CONFLICT(path) DO UPDATE SET checked=1, checked_at=CURRENT_TIMESTAMP",\n                    (path,),\n                )\n                conn.commit()\n            finally:\n                conn.close()\n            self.load_data()\n'''
if old in text:
    text = text.replace(old, new, 1)

# Put the action buttons in a non-collapsing minimum-height row.
marker = '        actions = QHBoxLayout()\n        self.play_button = QPushButton("▶ PLAY")\n'
if marker in text and 'actions.setContentsMargins(0, 8, 0, 0)' not in text:
    text = text.replace(marker, '        actions = QHBoxLayout()\n        actions.setContentsMargins(0, 8, 0, 0)\n        actions.setSpacing(10)\n        self.play_button = QPushButton("▶ PLAY")\n', 1)

# Ensure enough space for the bottom action bar.
marker = '        root.addLayout(actions)\n\n        self.search_timer = QTimer(self)'
if marker in text and 'root.addSpacing(4)' not in text:
    text = text.replace('        root.addLayout(actions)\n\n        self.search_timer = QTimer(self)', '        root.addLayout(actions)\n        root.addSpacing(4)\n\n        self.search_timer = QTimer(self)', 1)

TARGET.write_text(text, encoding="utf-8-sig")
print("MP3 voortgangsweergave toegepast:")
print("- statuskolom KLAAR / NIET GEDAAN")
print("- gele statusregel voor KLAAR")
print("- metadatafilters")
print("- verborgen echt MP3-pad behouden voor PLAY/EDIT")
print("- voortgang opgeslagen in mp3_metadata_status")

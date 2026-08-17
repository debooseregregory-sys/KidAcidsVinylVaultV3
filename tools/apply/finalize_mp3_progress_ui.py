from pathlib import Path
import sqlite3

BASE = Path(__file__).resolve().parents[2]
TARGET = BASE / "gui" / "mp3_library_page.py"
DB = BASE / "data" / "vinylvault.db"

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

text = TARGET.read_text(encoding="utf-8-sig")

# Remove old broken metadata_filter lines completely.
text = "\n".join(line for line in text.splitlines() if "metadata_filter" not in line) + "\n"

# QColor for yellow finished rows.
core_import = "from PySide6.QtCore import Qt, QTimer, Signal, QAbstractTableModel, QModelIndex\n"
if "from PySide6.QtGui import QColor" not in text and core_import in text:
    text = text.replace(core_import, core_import + "from PySide6.QtGui import QColor\n", 1)

# Replace table model with status-aware model.
start = text.find("class MP3TableModel(QAbstractTableModel):")
end = text.find("\n\nclass MetadataDialog(QDialog):", start)
if start < 0 or end < 0:
    raise RuntimeError("MP3TableModel block niet gevonden")

model = '''class MP3TableModel(QAbstractTableModel):
    HEADERS = ["Artist", "Title", "Album", "Year", "BPM", "Pad", "Koppeling", "STATUS"]

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
            return QColor("#4a3d08")
        if role == Qt.ItemDataRole.ForegroundRole and int(row[9] or 0) == 1:
            return QColor("#ffe08a")
        if role == Qt.ItemDataRole.ToolTipRole:
            if index.column() == 5:
                return str(row[8] or "")
            if index.column() == 7:
                return "Metadata gecontroleerd" if int(row[9] or 0) == 1 else "Metadata nog niet gecontroleerd"
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
text = text[:start] + model + text[end:]

if "self.metadata_progress_mode =" not in text:
    text = text.replace("        self.filtered_rows = []\n", "        self.filtered_rows = []\n        self.metadata_progress_mode = \"all\"\n", 1)

# Add explicit status buttons after existing Vinyl/linked filter.
needle = '        self.filter = QComboBox()\n        self.filter.addItems(["Alle MP3\'s", "Aan vinyl gekoppeld", "Niet gekoppeld"])\n        tools.addWidget(self.filter)\n\n'
if needle not in text:
    raise RuntimeError("bestaande MP3 filter niet gevonden")

buttons = '''        self.filter = QComboBox()\n        self.filter.addItems(["Alle MP3's", "Aan vinyl gekoppeld", "Niet gekoppeld"])\n        tools.addWidget(self.filter)\n\n        status_label = QLabel("METADATA:")\n        status_label.setStyleSheet("color:#9b9ba6; font-weight:bold;")\n        tools.addWidget(status_label)\n\n        self.all_button = QPushButton("ALLES")\n        self.done_button = QPushButton("✓ KLAAR")\n        self.todo_button = QPushButton("NIET GEDAAN")\n        tools.addWidget(self.all_button)\n        tools.addWidget(self.done_button)\n        tools.addWidget(self.todo_button)\n\n'''
text = text.replace(needle, buttons, 1)

# Wire explicit status buttons.
wire_needle = '        self.filter.currentIndexChanged.connect(self.apply_filter)\n'
if wire_needle not in text:
    raise RuntimeError("filter connect niet gevonden")
wire = wire_needle + '''        self.all_button.clicked.connect(lambda: self.set_metadata_mode("all"))\n        self.done_button.clicked.connect(lambda: self.set_metadata_mode("done"))\n        self.todo_button.clicked.connect(lambda: self.set_metadata_mode("todo"))\n'''
text = text.replace(wire_needle, wire, 1)

# Add status map + mode method before apply_filter.
old_marker = '        self.apply_filter()\n\n    def apply_filter(self):\n'
new_marker = '''        try:\n            conn2 = get_connection()\n            try:\n                status_rows = conn2.execute("SELECT path, metadata_checked FROM mp3_files").fetchall()\n                self.metadata_status_by_path = {str(r[0]): int(r[1] or 0) for r in status_rows}\n            finally:\n                conn2.close()\n        except Exception:\n            self.metadata_status_by_path = {}\n\n        self.apply_filter()\n\n    def set_metadata_mode(self, mode):\n        self.metadata_progress_mode = mode\n        self.apply_filter()\n\n    def apply_filter(self):\n'''
if old_marker not in text:
    raise RuntimeError("load_data/apply_filter overgang niet gevonden")
text = text.replace(old_marker, new_marker, 1)

# Replace apply_filter body.
start = text.find("    def apply_filter(self):")
end = text.find("\n    def selected_row(self):", start)
if start < 0 or end < 0:
    raise RuntimeError("apply_filter block niet gevonden")
apply_block = '''    def apply_filter(self):\n        text_filter = self.search.text().strip().casefold()\n        mode = self.filter.currentIndex()\n        rows = []\n\n        for row in self.rows:\n            linked = int(row[7] or 0)\n            checked = int(getattr(self, "metadata_status_by_path", {}).get(str(row[0]), 0))\n\n            if mode == 1 and not linked:\n                continue\n            if mode == 2 and linked:\n                continue\n            if self.metadata_progress_mode == "done" and not checked:\n                continue\n            if self.metadata_progress_mode == "todo" and checked:\n                continue\n\n            hay = " ".join(str(x or "") for x in (row[0], row[1], row[2], row[3], row[4], row[6])).casefold()\n            if text_filter and text_filter not in hay:\n                continue\n\n            rows.append((\n                row[1], row[2], row[3], row[4], row[5], row[0],\n                "VINYL" if linked else "LOS",\n                "✓ KLAAR" if checked else "NIET GEDAAN",\n                row[8], checked,\n            ))\n\n        self.filtered_rows = rows\n        self.model.set_rows(rows)\n\n        status_map = getattr(self, "metadata_status_by_path", {})\n        done = sum(1 for value in status_map.values() if value == 1)\n        total = len(self.rows)\n        todo = max(0, total - done)\n        self.info.setText(f"{len(rows)} zichtbaar | {done} KLAAR | {todo} NIET GEDAAN | totaal {total} MP3's")\n'''
text = text[:start] + apply_block + text[end:]

# Hidden real path now lives at row[8].
text = text.replace('        path = str(row[0] or "")\n        if path and Path(path).exists():', '        path = str(row[8] or "")\n        if path and Path(path).exists():', 1)
text = text.replace('        path = str(row[0])\n        if not Path(path).exists():', '        path = str(row[8] or "")\n        if not Path(path).exists():', 1)

# Mark as checked only after a successful metadata save.
save_needle = '                conn.commit()\n            finally:\n                conn.close()'
if save_needle in text:
    save_repl = '''                conn.execute(\n                    "UPDATE mp3_files SET metadata_checked=1, metadata_checked_at=CURRENT_TIMESTAMP WHERE path=?",\n                    (path,),\n                )\n                conn.commit()\n            finally:\n                conn.close()'''
    text = text.replace(save_needle, save_repl, 1)

TARGET.write_text(text, encoding="utf-8-sig")
print("Definitieve MP3 status UI toegepast")

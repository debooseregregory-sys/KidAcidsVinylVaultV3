from pathlib import Path

BASE = Path(__file__).resolve().parents[2]
TARGET = BASE / "gui" / "mp3_library_page.py"

text = TARGET.read_text(encoding="utf-8-sig")

# Qt painting imports.
old = "from PySide6.QtCore import Qt, QTimer, Signal, QAbstractTableModel, QModelIndex\n"
new = old + "from PySide6.QtGui import QColor, QBrush\n"
if "from PySide6.QtGui import QColor, QBrush" not in text:
    if old not in text:
        raise RuntimeError("QtCore importregel niet gevonden")
    text = text.replace(old, new, 1)

# Add visual status to table model. The internal status flag is the final tuple item.
needle = '''        if role == Qt.ItemDataRole.DisplayRole:\n            return str(row[index.column()] or "")\n'''
replacement = '''        if role == Qt.ItemDataRole.DisplayRole:\n            return str(row[index.column()] or "")\n\n        if role == Qt.ItemDataRole.BackgroundRole and int(row[-1] or 0) == 1:\n            return QBrush(QColor("#5a4b00"))\n\n        if role == Qt.ItemDataRole.ForegroundRole and int(row[-1] or 0) == 1:\n            return QBrush(QColor("#fff4b0"))\n'''
if "Qt.ItemDataRole.BackgroundRole" not in text:
    if needle not in text:
        raise RuntimeError("MP3TableModel display-regel niet gevonden")
    text = text.replace(needle, replacement, 1)

# Extend the data query with the explicit review status.
old_select = '''                       m.genre,\n                       CASE WHEN EXISTS (SELECT 1 FROM track_mp3 tm WHERE tm.mp3_id=m.id) THEN 1 ELSE 0 END AS linked,\n'''
new_select = '''                       m.genre,\n                       CASE WHEN EXISTS (SELECT 1 FROM track_mp3 tm WHERE tm.mp3_id=m.id) THEN 1 ELSE 0 END AS linked,\n                       COALESCE(m.metadata_checked, 0) AS metadata_checked,\n'''
if "AS metadata_checked" not in text:
    if old_select not in text:
        raise RuntimeError("MP3 SELECT-blok niet gevonden")
    text = text.replace(old_select, new_select, 1)

# Preserve the path while exposing status as the final internal field.
old_display = '''            display = (row[0], row[1], row[2], row[3], row[4], row[5], "VINYL" if linked else "LOS", row[8])\n'''
new_display = '''            # Visible columns: Artist, Title, Album, Year, BPM, Pad, Koppeling.\n            # Internal final value is metadata_checked and is used only for highlighting.\n            display = (row[1], row[2], row[3], row[4], row[5], row[0], "VINYL" if linked else "LOS", row[8], row[9])\n'''
if old_display in text:
    text = text.replace(old_display, new_display, 1)
else:
    raise RuntimeError("MP3 display-tuple niet gevonden; geen wijziging uitgevoerd")

# Fix selected-row path to the hidden Pad column (index 5).
text = text.replace('        path = str(row[0] or "")\n        if path and Path(path).exists():', '        path = str(row[5] or "")\n        if path and Path(path).exists():', 1)
text = text.replace('        path = str(row[0])\n        if not Path(path).exists():', '        path = str(row[5] or "")\n        if not Path(path).exists():', 1)

# Mark metadata as checked after successful tag/database save.
needle_save = '''                conn.commit()\n            finally:\n                conn.close()\n\n            self.accept()\n'''
replacement_save = '''                conn.execute(\n                    "UPDATE mp3_files SET metadata_checked=1, metadata_checked_at=CURRENT_TIMESTAMP WHERE path=?",\n                    (path,),\n                )\n                conn.commit()\n            finally:\n                conn.close()\n\n            self.accept()\n'''
if "metadata_checked=1" not in text:
    if needle_save not in text:
        raise RuntimeError("Metadata save-commit blok niet gevonden")
    text = text.replace(needle_save, replacement_save, 1)

# Add status counter in the info line without changing the existing filters.
old_info = '        self.info.setText(f"{len(rows)} van {len(self.rows)} MP3\'s")\n'
new_info = '''        checked = sum(1 for row in self.rows if int(row[9] or 0) == 1)\n        todo = len(self.rows) - checked\n        self.info.setText(f"{len(rows)} van {len(self.rows)} MP3's | KLAAR: {checked} | TE DOEN: {todo}")\n'''
if old_info in text:
    text = text.replace(old_info, new_info, 1)

TARGET.write_text(text, encoding="utf-8")
print("MP3 metadata-status toegevoegd.")
print("KLAAR-bestanden worden geel gemarkeerd.")
print("Opslaan markeert metadata_checked=1.")

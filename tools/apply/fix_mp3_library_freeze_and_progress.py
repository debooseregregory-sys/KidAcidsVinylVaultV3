from pathlib import Path

BASE = Path(__file__).resolve().parents[2]
TARGET = BASE / 'gui' / 'mp3_library_page.py'

text = TARGET.read_text(encoding='utf-8-sig')

# Add status-aware table model roles without touching the metadata editor.
old_model_start = text.find('class MP3TableModel(QAbstractTableModel):')
old_model_end = text.find('\n\nclass MetadataDialog(QDialog):', old_model_start)
if old_model_start < 0 or old_model_end < 0:
    raise RuntimeError('MP3TableModel block niet gevonden')

model_block = r'''class MP3TableModel(QAbstractTableModel):
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
        if role == Qt.ItemDataRole.ToolTipRole and index.column() == 5:
            return str(row[8] or "")
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
text = text[:old_model_start] + model_block + text[old_model_end:]

# Add metadata status filter.
needle = '        self.filter.addItems(["Alle MP3\'s", "Aan vinyl gekoppeld", "Niet gekoppeld"])'
if needle in text and 'self.metadata_filter' not in text:
    replacement = needle + '''\n\n        self.metadata_filter = QComboBox()\n        self.metadata_filter.addItems(["Metadata: Alles", "Metadata: KLAAR", "Metadata: NIET GEDAAN"])\n        tools.addWidget(self.metadata_filter)'''
    text = text.replace(needle, replacement, 1)
    text = text.replace(
        '        self.filter.currentIndexChanged.connect(self.apply_filter)',
        '        self.filter.currentIndexChanged.connect(self.apply_filter)\n        self.metadata_filter.currentIndexChanged.connect(self.apply_filter)',
        1,
    )

# Load the status map once, instead of doing status work per row.
text = text.replace(
    '        finally:\n            conn.close()\n        self.apply_filter()',
    '''        finally:\n            conn.close()\n\n        self.metadata_status_by_path = {}\n        try:\n            conn2 = get_connection()\n            try:\n                status_rows = conn2.execute(\n                    "SELECT path, COALESCE(metadata_checked, 0) FROM mp3_files"\n                ).fetchall()\n                self.metadata_status_by_path = {str(r[0]): int(r[1] or 0) for r in status_rows}\n            finally:\n                conn2.close()\n        except Exception:\n            pass\n\n        self.apply_filter()''',
    1,
)

start = text.find('    def apply_filter(self):')
end = text.find('\n    def selected_row(self):', start)
if start < 0 or end < 0:
    raise RuntimeError('apply_filter block niet gevonden')

apply_block = r'''    def apply_filter(self):
        text_filter = self.search.text().strip().casefold()
        mode = self.filter.currentIndex()
        metadata_mode = self.metadata_filter.currentIndex() if hasattr(self, "metadata_filter") else 0
        rows = []

        for row in self.rows:
            linked = int(row[7] or 0)
            checked = int(getattr(self, "metadata_status_by_path", {}).get(str(row[0]), 0))

            if mode == 1 and not linked:
                continue
            if mode == 2 and linked:
                continue
            if metadata_mode == 1 and not checked:
                continue
            if metadata_mode == 2 and checked:
                continue

            hay = " ".join(str(x or "") for x in (row[0], row[1], row[2], row[3], row[4], row[6])).casefold()
            if text_filter and text_filter not in hay:
                continue

            rows.append((
                row[1], row[2], row[3], row[4], row[5], row[0],
                "VINYL" if linked else "LOS", row[8], row[0], checked,
            ))

        self.filtered_rows = rows
        self.model.set_rows(rows)

        total = len(self.rows)
        done = sum(1 for p in getattr(self, "metadata_status_by_path", {}).values() if p == 1)
        todo = total - done
        self.info.setText(f"{len(rows)} zichtbaar | {done} KLAAR | {todo} NIET GEDAAN | totaal {total} MP3's")
'''
text = text[:start] + apply_block + text[end:]

# Hidden real path after visible-column reorder.
text = text.replace(
    '        path = str(row[0] or "")\n        if path and Path(path).exists():',
    '        path = str(row[8] or "")\n        if path and Path(path).exists():',
    1,
)
text = text.replace(
    '        path = str(row[0])\n        if not Path(path).exists():',
    '        path = str(row[8] or "")\n        if not Path(path).exists():',
    1,
)

# Mark checked only after successful metadata save.
text = text.replace(
    '                conn.commit()\n            finally:\n                conn.close()\n\n            self.accept()',
    '''                conn.execute(\n                    "UPDATE mp3_files SET metadata_checked=1, metadata_checked_at=CURRENT_TIMESTAMP WHERE path=?",\n                    (path,),\n                )\n                conn.commit()\n            finally:\n                conn.close()\n\n            self.accept()''',
    1,
)

# Prevent a just-finished row from disappearing if user was viewing 'NIET GEDAAN'.
text = text.replace(
    '        if dialog.exec() == QDialog.DialogCode.Accepted:\n            self.load_data()',
    '''        if dialog.exec() == QDialog.DialogCode.Accepted:\n            if hasattr(self, "metadata_filter"):\n                self.metadata_filter.blockSignals(True)\n                self.metadata_filter.setCurrentIndex(0)\n                self.metadata_filter.blockSignals(False)\n            self.load_data()''',
    1,
)

TARGET.write_text(text, encoding='utf-8-sig')
print('MP3 Library freeze/progress fix toegepast')

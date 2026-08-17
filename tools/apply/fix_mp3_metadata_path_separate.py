from pathlib import Path

BASE = Path(__file__).resolve().parents[2]
TARGET = BASE / "gui" / "mp3_library_page.py"

text = TARGET.read_text(encoding="utf-8-sig")

old = '''    def selected_row(self):
        indexes = self.table.selectionModel().selectedRows()
        if not indexes:
            return None
        return self.model.rows[indexes[0].row()]
'''

new = '''    def selected_row(self):
        indexes = self.table.selectionModel().selectedRows()
        if not indexes:
            return None

        row = self.model.rows[indexes[0].row()]

        # Visible table columns are:
        # 0 artist, 1 title, 2 album, 3 year, 4 bpm, 5 pad, 6 koppeling.
        # The real MP3 path is deliberately stored separately at index 7.
        return row

    def selected_path(self):
        row = self.selected_row()
        if row is None:
            return ""
        return str(row[7] or "")
'''

if old not in text:
    raise SystemExit("selected_row block not found")
text = text.replace(old, new, 1)

old2 = '''    def play_selected(self, *_args):
        row = self.selected_row()
        if row is None:
            return
        path = str(row[0] or "")
        if path and Path(path).exists():
            self.play_mp3.emit(path)
        else:
            QMessageBox.warning(self, "Bestand ontbreekt", path)
'''

new2 = '''    def play_selected(self, *_args):
        path = self.selected_path()
        if not path:
            return
        if Path(path).exists():
            self.play_mp3.emit(path)
        else:
            QMessageBox.warning(self, "Bestand ontbreekt", path)
'''

if old2 not in text:
    raise SystemExit("play_selected block not found")
text = text.replace(old2, new2, 1)

old3 = '''    def edit_selected_metadata(self, *_args):
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
'''

new3 = '''    def edit_selected_metadata(self, *_args):
        row = self.selected_row()
        if row is None:
            return
        if not MUTAGEN_AVAILABLE:
            QMessageBox.information(
                self,
                "Metadata Builder",
                "Installeer Mutagen met:\n\npython -m pip install mutagen",
            )
            return

        path = self.selected_path()
        if not path:
            return
        if not Path(path).exists():
            QMessageBox.warning(self, "Bestand ontbreekt", path)
            return

        # MetadataDialog reads the REAL ID3 tags from the file itself.
        dialog = MetadataDialog((path,), self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.load_data()
'''

if old3 not in text:
    raise SystemExit("edit_selected_metadata block not found")
text = text.replace(old3, new3, 1)

TARGET.write_text(text, encoding="utf-8")
print("MP3 Library: real MP3 path is now kept separately from visible columns.")
print("PLAY and METADATA BEWERKEN use the real path again.")

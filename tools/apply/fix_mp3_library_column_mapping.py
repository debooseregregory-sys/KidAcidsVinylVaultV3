from pathlib import Path

BASE = Path(__file__).resolve().parents[2]
TARGET = BASE / "gui" / "mp3_library_page.py"

text = TARGET.read_text(encoding="utf-8-sig")

old = '''            display = (row[0], row[1], row[2], row[3], row[4], row[5], "VINYL" if linked else "LOS", row[8])
            rows.append(display)
'''
new = '''            # Display order must match HEADERS exactly.
            # Keep the real filesystem path separately inside the tuple
            # so the visible columns never become shifted.
            display = (
                row[1],                         # Artist
                row[2],                         # Title
                row[3],                         # Album
                row[4],                         # Year
                row[5],                         # BPM
                row[0],                         # Pad / filesystem path
                "VINYL" if linked else "LOS", # Koppeling
                row[8],                         # hidden/tooltip vinyl link
            )
            rows.append(display)
'''
if old not in text:
    raise RuntimeError("apply_filter display-blok niet gevonden")
text = text.replace(old, new, 1)

old_play = '''        path = str(row[0] or "")
        if path and Path(path).exists():
            self.play_mp3.emit(path)
'''
new_play = '''        path = str(row[5] or "")
        if path and Path(path).exists():
            self.play_mp3.emit(path)
'''
if old_play not in text:
    raise RuntimeError("play_selected-pad niet gevonden")
text = text.replace(old_play, new_play, 1)

old_edit = '''        path = str(row[0])
        if not Path(path).exists():
            QMessageBox.warning(self, "Bestand ontbreekt", path)
            return
        try:
            tags = ID3(path)
'''
new_edit = '''        path = str(row[5] or "")
        if not Path(path).exists():
            QMessageBox.warning(self, "Bestand ontbreekt", path)
            return
        try:
            tags = ID3(path)
'''
if old_edit not in text:
    raise RuntimeError("edit_selected_metadata-pad niet gevonden")
text = text.replace(old_edit, new_edit, 1)

old_fallback = '''            dialog_row = (path, row[1], row[2], row[3], row[4], row[5], "", "", "", "", row[6], "")
'''
new_fallback = '''            dialog_row = (path, row[0], row[1], row[2], row[3], row[4], "", "", "", "", "", "")
'''
if old_fallback in text:
    text = text.replace(old_fallback, new_fallback, 1)

TARGET.write_text(text, encoding="utf-8")
print("MP3 LIBRARY: kolommen correct uitgelijnd.")
print("Artist/Title/Album/Year/BPM tonen nu de juiste databasevelden.")
print("Pad blijft apart beschikbaar en wordt niet meer als Artist getoond.")

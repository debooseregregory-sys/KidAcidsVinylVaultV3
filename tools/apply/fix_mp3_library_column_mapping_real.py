from pathlib import Path

BASE = Path(__file__).resolve().parents[2]
TARGET = BASE / "gui" / "mp3_library_page.py"

text = TARGET.read_text(encoding="utf-8-sig")

old = '''            display = (row[0], row[1], row[2], row[3], row[4], row[5], "VINYL" if linked else "LOS", row[8])\n            rows.append(display)'''

new = '''            # Database row:\n            # 0=path, 1=artist, 2=title, 3=album, 4=year,\n            # 5=bpm, 6=genre, 7=linked, 8=vinyl_link.\n            # Table order must be: Artist, Title, Album, Year, BPM, Pad, Koppeling.\n            display = (\n                row[1],\n                row[2],\n                row[3],\n                row[4],\n                row[5],\n                row[0],\n                "VINYL" if linked else "LOS",\n                row[8],\n            )\n            rows.append(display)'''

if old not in text:
    raise RuntimeError("MP3 Library display-mapping niet gevonden")

text = text.replace(old, new, 1)

# selected_row / play_selected must continue using the path at display column 5.
old_play = '''        path = str(row[0] or "")\n        if path and Path(path).exists():\n            self.play_mp3.emit(path)\n        else:\n            QMessageBox.warning(self, "Bestand ontbreekt", path)'''

new_play = '''        path = str(row[5] or "")\n        if path and Path(path).exists():\n            self.play_mp3.emit(path)\n        else:\n            QMessageBox.warning(self, "Bestand ontbreekt", path)'''

if old_play in text:
    text = text.replace(old_play, new_play, 1)

old_meta = '''        path = str(row[0])\n        if not Path(path).exists():\n            QMessageBox.warning(self, "Bestand ontbreekt", path)\n            return\n        try:\n            tags = ID3(path)'''

new_meta = '''        path = str(row[5])\n        if not Path(path).exists():\n            QMessageBox.warning(self, "Bestand ontbreekt", path)\n            return\n        try:\n            tags = ID3(path)'''

if old_meta in text:
    text = text.replace(old_meta, new_meta, 1)

TARGET.write_text(text, encoding="utf-8")
print("MP3 LIBRARY KOLOMMAPPING HERSTELD")
print("Artist/Title/Album/Year/BPM/Pad/Koppeling staan nu in de juiste volgorde.")
print("PLAY en METADATA BEWERKEN gebruiken opnieuw het pad uit kolom 5 (Pad).")

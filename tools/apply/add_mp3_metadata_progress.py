from pathlib import Path

BASE = Path(__file__).resolve().parents[2]
TARGET = BASE / "gui" / "mp3_library_page.py"

text = TARGET.read_text(encoding="utf-8-sig")

# Add a persistent progress column to mp3_files.
old_load = '''                self.rows = conn.execute(\n                """\n                SELECT m.path, m.artist, m.title, m.album, m.year, m.bpm,\n                       m.genre,\n                       CASE WHEN EXISTS (SELECT 1 FROM track_mp3 tm WHERE tm.mp3_id=m.id) THEN 1 ELSE 0 END AS linked,\n                       COALESCE((SELECT r.artist || ' - ' || r.title || ' / ' || t.position || ' ' || t.title\n                                 FROM track_mp3 tm JOIN tracks t ON t.id=tm.track_id JOIN releases r ON r.id=t.release_id\n                                 WHERE tm.mp3_id=m.id ORDER BY tm.id LIMIT 1), '') AS vinyl_link\n                FROM mp3_files m\n                ORDER BY m.artist COLLATE NOCASE, m.title COLLATE NOCASE, m.path COLLATE NOCASE\n                """\n            ).fetchall()'''

new_load = '''                self.rows = conn.execute(\n                """\n                SELECT m.path, m.artist, m.title, m.album, m.year, m.bpm,\n                       m.genre,\n                       CASE WHEN EXISTS (SELECT 1 FROM track_mp3 tm WHERE tm.mp3_id=m.id) THEN 1 ELSE 0 END AS linked,\n                       COALESCE((SELECT r.artist || ' - ' || r.title || ' / ' || t.position || ' ' || t.title\n                                 FROM track_mp3 tm JOIN tracks t ON t.id=tm.track_id JOIN releases r ON r.id=t.release_id\n                                 WHERE tm.mp3_id=m.id ORDER BY tm.id LIMIT 1), '') AS vinyl_link,\n                       COALESCE(m.metadata_checked, 0) AS metadata_checked\n                FROM mp3_files m\n                ORDER BY m.artist COLLATE NOCASE, m.title COLLATE NOCASE, m.path COLLATE NOCASE\n                """\n            ).fetchall()'''

if old_load in text:
    text = text.replace(old_load, new_load, 1)

# Add metadata status filter if the filter currently has only three items.
old_filter = 'self.filter.addItems(["Alle MP3\'s", "Aan vinyl gekoppeld", "Niet gekoppeld"])'
new_filter = 'self.filter.addItems(["Alle MP3\'s", "Aan vinyl gekoppeld", "Niet gekoppeld", "Metadata KLAAR", "Metadata NIET GEDAAN"])'
if old_filter in text:
    text = text.replace(old_filter, new_filter, 1)

# Add a progress label beside the total count.
old_info = '''        self.info = QLabel("0 MP3\'s")\n        self.info.setStyleSheet("color: #9b9ba6;")\n        root.addWidget(self.info)'''
new_info = '''        self.info = QLabel("0 MP3\'s")\n        self.info.setStyleSheet("color: #9b9ba6;")\n        root.addWidget(self.info)\n\n        self.progress = QLabel("Metadata: 0 klaar | 0 te doen")\n        self.progress.setStyleSheet("color: #d84b91; font-weight: bold;")\n        root.addWidget(self.progress)'''
if old_info in text:
    text = text.replace(old_info, new_info, 1)

# Filter handling: keep the existing vinyl filters and add metadata filters.
old_mode = '''            if mode == 1 and not linked:\n                continue\n            if mode == 2 and linked:\n                continue'''
new_mode = '''            metadata_checked = int(row[9] or 0)\n            if mode == 1 and not linked:\n                continue\n            if mode == 2 and linked:\n                continue\n            if mode == 3 and not metadata_checked:\n                continue\n            if mode == 4 and metadata_checked:\n                continue'''
if old_mode in text:
    text = text.replace(old_mode, new_mode, 1)

# Keep the hidden path as the last field, and add metadata state as a final hidden field.
old_display = '''            display = (row[1], row[2], row[3], row[4], row[5], row[0], "VINYL" if linked else "LOS", row[8])'''
new_display = '''            display = (row[1], row[2], row[3], row[4], row[5], row[0], "VINYL" if linked else "LOS", row[8], metadata_checked)'''
if old_display in text:
    text = text.replace(old_display, new_display, 1)

# If a prior mapping fix used a different display tuple, handle that too.
old_display2 = '''            display = (row[1], row[2], row[3], row[4], row[5], row[0], "VINYL" if linked else "LOS", row[8])'''
if old_display2 in text:
    text = text.replace(old_display2, new_display, 1)

# Update progress text after filtering.
old_set = '''        self.info.setText(f"{len(rows)} van {len(self.rows)} MP3's")'''
new_set = '''        self.info.setText(f"{len(rows)} van {len(self.rows)} MP3's")\n        checked_total = sum(1 for item in self.rows if int(item[9] or 0))\n        self.progress.setText(\n            f"Metadata: {checked_total} klaar | {len(self.rows) - checked_total} te doen"\n        )'''
if old_set in text:
    text = text.replace(old_set, new_set, 1)

# selected_row remains compatible: path is display column 5.
# Metadata save: mark the exact file as checked after successful tag/database save.
needle = '''                conn.execute(\n                    "UPDATE mp3_files SET artist=?, title=?, album=?, year=?, genre=?, bpm=?, updated_at=CURRENT_TIMESTAMP WHERE path=?",'''
if needle in text:
    replacement = '''                conn.execute(\n                    "UPDATE mp3_files SET artist=?, title=?, album=?, year=?, genre=?, bpm=?, metadata_checked=1, metadata_checked_at=CURRENT_TIMESTAMP, updated_at=CURRENT_TIMESTAMP WHERE path=?",'''
    text = text.replace(needle, replacement, 1)

# Fallback: if the current save SQL is a multiline variant, inject fields into it.
text = text.replace(
    'SET artist=?, title=?, album=?, year=?, genre=?, bpm=?,\n                        updated_at=CURRENT_TIMESTAMP',
    'SET artist=?, title=?, album=?, year=?, genre=?, bpm=?,\n                        metadata_checked=1, metadata_checked_at=CURRENT_TIMESTAMP,\n                        updated_at=CURRENT_TIMESTAMP',
    1,
)

TARGET.write_text(text, encoding="utf-8")
print("Metadata voortgang toegevoegd aan MP3 Library.")
print("Nieuwe filters: Metadata KLAAR / Metadata NIET GEDAAN.")
print("Opslaan in Metadata Builder markeert het bestand als KLAAR.")

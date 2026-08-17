from pathlib import Path
import re

BASE = Path(__file__).resolve().parents[2]
TARGET = BASE / 'gui' / 'mp3_showcase_page.py'

text = TARGET.read_text(encoding='utf-8-sig')
text = text.replace('from PySide6.QtWidgets import (\n', 'from PySide6.QtWidgets import (\n')

if 'metadata_checked' not in text:
    text = text.replace('            m.genre,\n', '            m.genre,\n                    COALESCE(m.metadata_checked, 0),\n', 1)

if 'self.metadata_status_label' not in text:
    needle = '        self.discogs_label = QLabel("Discogs: -")\n'
    insert = '        self.metadata_status_label = QLabel("Metadata: NIET GEDAAN")\n        self.metadata_status_label.setStyleSheet("color:#9b9ba6;font-size:12px;font-weight:bold;")\n        info.addWidget(self.metadata_status_label)\n\n'
    text = text.replace(needle, insert + needle, 1)

show = '        (\n            path,\n            artist,\n            title,\n            album,\n            year,\n            bpm,\n            genre,\n            release_artist,\n            release_title,\n            discogs_id,\n            release_cover,\n        ) = row\n'
if show in text:
    text = text.replace(show, '        (\n            path, artist_db, title_db, album_db, year_db, bpm_db, genre_db,\n            metadata_checked, release_artist, release_title, discogs_id, release_cover,\n        ) = row\n', 1)

if 'def read_showcase_tags' not in text:
    marker = '    def show_item(self, row):\n'
    helper = '''    def read_showcase_tags(self, path):\n        result = {\n            "artist":"", "title":"", "album":"", "year":"", "bpm":"",\n            "track":"", "disc":"", "album_artist":"", "composer":"",\n            "genre":"", "comment":""\n        }\n        if not MUTAGEN_AVAILABLE or not Path(path).exists():\n            return result\n        try:\n            tags = ID3(path)\n            def first(key):\n                frame = tags.get(key)\n                if frame is None:\n                    return ""\n                try:\n                    vals = getattr(frame, "text", None)\n                    if vals:\n                        return str(vals[0]).strip()\n                except Exception:\n                    pass\n                return str(frame).strip()\n            for key, name in (("TPE1","artist"),("TIT2","title"),("TALB","album"),("TDRC","year"),("TBPM","bpm"),("TRCK","track"),("TPOS","disc"),("TPE2","album_artist"),("TCOM","composer"),("TCON","genre")):\n                result[name] = first(key)\n            vals=[]\n            for frame in tags.getall("COMM"):\n                try:\n                    vals.extend(str(v).strip() for v in frame.text if str(v).strip())\n                except Exception:\n                    pass\n            result["comment"] = " | ".join(dict.fromkeys(vals))\n        except Exception:\n            pass\n        return result\n\n'''
    text = text.replace(marker, helper + marker, 1)

old_assign = '        artist = str(artist or "").strip() or "Onbekende artiest"\n        title = str(title or "").strip() or Path(str(path)).stem\n        album = str(album or "").strip()\n'
new_assign = '''        tags = self.read_showcase_tags(str(path))\n        artist = tags["artist"] or str(artist_db or "").strip() or "Onbekende artiest"\n        title = tags["title"] or str(title_db or "").strip() or Path(str(path)).stem\n        album = tags["album"] or str(album_db or "").strip()\n        year = tags["year"] or str(year_db or "").strip()\n        bpm = tags["bpm"] or str(bpm_db or "").strip()\n        genre = tags["genre"] or str(genre_db or "").strip()\n'''
text = text.replace(old_assign, new_assign, 1)

text = text.replace('            self.discogs_label.setText("Discogs: geen releasekoppeling")\n', '            self.discogs_label.setText("Discogs: geen releasekoppeling")\n\n        if int(metadata_checked or 0) == 1:\n            self.metadata_status_label.setText("Metadata: ✓ KLAAR")\n            self.metadata_status_label.setStyleSheet("color:#ffe08a;font-size:12px;font-weight:bold;")\n        else:\n            self.metadata_status_label.setText("Metadata: NIET GEDAAN")\n            self.metadata_status_label.setStyleSheet("color:#9b9ba6;font-size:12px;font-weight:bold;")\n', 1)

text = text.replace('        self.load_comment(str(path))\n', '        self.load_comment(str(path), tags.get("comment", ""))\n', 1)
text = text.replace('    def load_comment(self, path):\n        self.comment_label.clear()\n        if not MUTAGEN_AVAILABLE or not Path(path).exists():\n            return\n        try:\n            tags = ID3(path)\n            comments = tags.getall("COMM")\n', '    def load_comment(self, path, supplied_comment=""):\n        self.comment_label.clear()\n        if supplied_comment:\n            self.comment_label.setText("Comment: " + supplied_comment)\n            return\n        if not MUTAGEN_AVAILABLE or not Path(path).exists():\n            return\n        try:\n            tags = ID3(path)\n            comments = tags.getall("COMM")\n', 1)

# fix duplicate tuple indices in load_files caused by metadata field insertion
text = text.replace('            elif not unique[path][9] and row[9]:\n', '            elif not unique[path][10] and row[10]:\n', 1)
text = text.replace('            ) = row\n\n        artist =', '            ) = row\n\n        artist =', 1)

TARGET.write_text(text, encoding='utf-8-sig')
print('MP3 Showcase metadata-bron en status bijgewerkt')

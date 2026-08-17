from pathlib import Path
import re

p = Path('gui/mp3_showcase_page.py')
s = p.read_text(encoding='utf-8-sig')

# Add metadata_checked to SQL if not already present.
if 'm.metadata_checked' not in s:
    s = s.replace(
        '                    COALESCE(r.cover, \'\')\n',
        '                    COALESCE(r.cover, \'\'),\n                    COALESCE(m.metadata_checked, 0)\n',
        1,
    )

# Replace the row unpacking in show_item to include status.
s = s.replace(
'''        (\n            path,\n            artist,\n            title,\n            album,\n            year,\n            bpm,\n            genre,\n            release_artist,\n            release_title,\n            discogs_id,\n            release_cover,\n        ) = row\n''',
'''        (\n            path,\n            artist,\n            title,\n            album,\n            year,\n            bpm,\n            genre,\n            release_artist,\n            release_title,\n            discogs_id,\n            release_cover,\n            metadata_checked,\n        ) = row\n''',
1,
)

# Add a dedicated metadata status label next to Discogs label.
if 'self.metadata_status_label' not in s:
    target = '''        self.discogs_label = QLabel("Discogs: -")\n'''
    replacement = '''        self.discogs_label = QLabel("Discogs: -")\n'''
    s = s.replace(target, replacement, 1)
    anchor = '''        info.addWidget(self.discogs_label)\n\n        self.comment_label = QLabel("")\n'''
    repl = '''        info.addWidget(self.discogs_label)\n\n        self.metadata_status_label = QLabel("Metadata: -")\n        self.metadata_status_label.setStyleSheet(\n            "color:#8fd694;font-size:13px;font-weight:800;"\n        )\n        info.addWidget(self.metadata_status_label)\n\n        self.comment_label = QLabel("")\n'''
    s = s.replace(anchor, repl, 1)

# Make the Showcase read real ID3 tags as the authoritative display source.
if 'def read_tags_for_showcase' not in s:
    marker = '    def load_cover(self, path, release_cover):\n'
    method = '''    def read_tags_for_showcase(self, path):\n        result = {\n            "artist": "",\n            "title": "",\n            "album": "",\n            "year": "",\n            "bpm": "",\n            "track": "",\n            "disc": "",\n            "album_artist": "",\n            "composer": "",\n            "genre": "",\n        }\n        if not MUTAGEN_AVAILABLE or not Path(path).exists():\n            return result\n        try:\n            tags = ID3(path)\n            mapping = {\n                "artist": "TPE1",\n                "title": "TIT2",\n                "album": "TALB",\n                "year": "TDRC",\n                "bpm": "TBPM",\n                "track": "TRCK",\n                "disc": "TPOS",\n                "album_artist": "TPE2",\n                "composer": "TCOM",\n                "genre": "TCON",\n            }\n            for key, frame_id in mapping.items():\n                frame = tags.get(frame_id)\n                if frame is None:\n                    continue\n                values = getattr(frame, "text", None)\n                if values:\n                    result[key] = str(values[0]).strip()\n        except Exception:\n            pass\n        return result\n\n'''
    if marker in s:
        s = s.replace(marker, method + marker, 1)

# Insert tag override and metadata status immediately after show_item row unpacking.
if 'tags = self.read_tags_for_showcase' not in s:
    anchor = '''        artist = str(artist or "").strip() or "Onbekende artiest"\n'''
    repl = '''        tags = self.read_tags_for_showcase(str(path))\n\n        artist = tags["artist"] or str(artist or "").strip() or "Onbekende artiest"\n        title = tags["title"] or str(title or "").strip() or Path(str(path)).stem\n        album = tags["album"] or str(album or "").strip()\n        year = tags["year"] or year\n        bpm = tags["bpm"] or bpm\n        genre = tags["genre"] or genre\n\n        if int(metadata_checked or 0) == 1:\n            self.metadata_status_label.setText("Metadata: ✓ KLAAR")\n            self.metadata_status_label.setStyleSheet(\n                "color:#ffe08a;font-size:13px;font-weight:900;"\n            )\n        else:\n            self.metadata_status_label.setText("Metadata: NIET GEDAAN")\n            self.metadata_status_label.setStyleSheet(\n                "color:#ff9f9f;font-size:13px;font-weight:800;"\n            )\n\n'''
    s = s.replace(anchor, repl, 1)
    # Remove the old immediately following normalization lines, because repl already normalizes them.
    s = s.replace('        title = str(title or "").strip() or Path(str(path)).stem\n        album = str(album or "").strip()\n\n', '', 1)

# Clear metadata label on empty showcase.
if 'self.metadata_status_label.setText("Metadata: -")' not in s:
    s = s.replace(
        '        self.discogs_label.setText("Discogs: -")\n',
        '        self.discogs_label.setText("Discogs: -")\n        if hasattr(self, "metadata_status_label"):\n            self.metadata_status_label.setText("Metadata: -")\n',
        1,
    )

p.write_text(s, encoding='utf-8-sig')
print('MP3 Showcase bijgewerkt: echte ID3-tags + metadata status.')

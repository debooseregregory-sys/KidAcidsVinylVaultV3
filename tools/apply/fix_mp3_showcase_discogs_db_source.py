from pathlib import Path
import re

p = Path("gui/mp3_showcase_page.py")
text = p.read_text(encoding="utf-8-sig")

# Ensure the Showcase has access to Path and the DB fields it needs.

# Replace the SELECT inside load_files() with a version that reads the
# MP3's own persisted Discogs fields first, while keeping vinyl release
# information as a fallback/display context.
load_pattern = re.compile(
    r'(    def load_files\(self\):.*?rows = conn\.execute\("""\n)(.*?)(\n                """\)\.fetchall\(\))',
    re.S,
)

m = load_pattern.search(text)
if not m:
    raise SystemExit("load_files() SQL block not found")

new_sql = '''                SELECT
                    m.path,
                    m.artist,
                    m.title,
                    m.album,
                    m.year,
                    m.bpm,
                    m.genre,
                    COALESCE(m.discogs_id, ''),
                    COALESCE(m.discogs_link, ''),
                    COALESCE(m.cover, ''),
                    COALESCE(r.artist, ''),
                    COALESCE(r.title, ''),
                    COALESCE(r.discogs, ''),
                    COALESCE(r.cover, '')
                FROM mp3_files m
                LEFT JOIN track_mp3 tm ON tm.mp3_id = m.id
                LEFT JOIN tracks t ON t.id = tm.track_id
                LEFT JOIN releases r ON r.id = t.release_id
                ORDER BY m.artist COLLATE NOCASE,
                         m.title COLLATE NOCASE,
                         m.path COLLATE NOCASE'''

text = text[:m.start(2)] + new_sql + text[m.end(2):]

# Replace the row unpacking in show_item().
unpack_pattern = re.compile(
    r'(    def show_item\(self, row\):\n\s*)\(.*?\n\s*\) = row',
    re.S,
)

um = unpack_pattern.search(text)
if not um:
    raise SystemExit("show_item() row unpacking not found")

new_unpack = '''        (
            path,
            artist,
            title,
            album,
            year,
            bpm,
            genre,
            stored_discogs_id,
            stored_discogs_link,
            stored_cover,
            release_artist,
            release_title,
            release_discogs_id,
            release_cover,
        ) = row'''

text = text[:um.start(0)] + um.group(1) + new_unpack + text[um.end(0):]

# Replace the beginning of the display logic so persisted MP3 Discogs wins.
logic_marker = '        artist = str(artist or "").strip() or "Onbekende artiest"\n'
if logic_marker not in text:
    raise SystemExit("show_item() display marker not found")

replacement = '''        artist = str(artist or "").strip() or "Onbekende artiest"
        title = str(title or "").strip() or Path(str(path)).stem
        album = str(album or "").strip()

        persisted_discogs_id = str(stored_discogs_id or "").strip()
        persisted_discogs_link = str(stored_discogs_link or "").strip()
        persisted_cover = str(stored_cover or "").strip()

        if persisted_discogs_id:
            active_discogs_id = persisted_discogs_id
        else:
            active_discogs_id = str(release_discogs_id or "").strip()

        active_cover = ""
        if persisted_cover and Path(persisted_cover).exists():
            active_cover = persisted_cover
        elif release_cover and Path(str(release_cover)).exists():
            active_cover = str(release_cover)

'''

# Remove the immediately following old artist/title/album assignments too.
after = text.index(logic_marker)
old_prefix_end = after + len(logic_marker)
rest = text[old_prefix_end:]
old_title = '        title = str(title or "").strip() or Path(str(path)).stem\n'
old_album = '        album = str(album or "").strip()\n'
if rest.startswith(old_title + old_album):
    old_prefix_end += len(old_title + old_album)

text = text[:after] + replacement + text[old_prefix_end:]

# Replace release and Discogs display sections.
old_discogs = re.compile(
    r'        if discogs_id:\n.*?        self\.load_cover\(str\(path\), str\(release_cover or ""\)\)\n',
    re.S,
)
dm = old_discogs.search(text)
if not dm:
    raise SystemExit("Discogs display block not found")

new_display = '''        if active_discogs_id:
            if persisted_discogs_link:
                self.discogs_label.setText(
                    f"Discogs: opgehaald en opgeslagen | ID {active_discogs_id}"
                )
            else:
                self.discogs_label.setText(
                    f"Discogs release ID: {active_discogs_id}"
                )
        else:
            self.discogs_label.setText("Discogs: geen releasekoppeling")

        self.load_cover(str(path), active_cover)
'''

text = text[:dm.start()] + new_display + text[dm.end():]

# Make the cover size responsive without rebuilding the whole UI.
# Use a minimum size and resize the pixmap to the actual label size.
text = text.replace(
    '        self.cover.setFixedSize(340, 340)\n',
    '        self.cover.setMinimumSize(180, 180)\n        self.cover.setMaximumSize(420, 420)\n        self.cover.setSizePolicy(\n            self.cover.sizePolicy().horizontalPolicy(),\n            self.cover.sizePolicy().verticalPolicy(),\n        )\n',
    1,
)

# load_cover() currently always scales to 340x340. Use the current label size.
text = text.replace(
    '                                340,\n                                340,\n',
    '                                max(120, self.cover.width() - 4),\n                                max(120, self.cover.height() - 4),\n',
)

# Add a responsive resizeEvent that switches body orientation.
if 'def resizeEvent(self, event):' not in text:
    marker = '    def load_files(self):\n'
    method = '''    def resizeEvent(self, event):
        super().resizeEvent(event)
        if not hasattr(self, "body_layout"):
            return

        # Rebuild the main body orientation for narrow windows so the
        # controls never overlap the cover.
        if self.width() < 950:
            self.body_layout.setDirection(QBoxLayout.Direction.TopToBottom)
        else:
            self.body_layout.setDirection(QBoxLayout.Direction.LeftToRight)

'''
    # Ensure the required imports exist.
    text = text.replace(
        '    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,\n',
        '    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QBoxLayout,\n',
        1,
    )
    body_marker = '        body = QHBoxLayout()\n        body.setSpacing(20)\n'
    if body_marker in text:
        text = text.replace(
            body_marker,
            '        body = QHBoxLayout()\n        self.body_layout = body\n        body.setSpacing(20)\n',
            1,
        )
    text = text.replace(marker, method + marker, 1)

p.write_text(text, encoding="utf-8-sig")
print("OK: MP3 Showcase gebruikt nu opgeslagen MP3-Discogsgegevens en responsive cover/layout.")

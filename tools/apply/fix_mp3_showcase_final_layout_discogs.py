from pathlib import Path
import re

p = Path("gui/mp3_showcase_page.py")
text = p.read_text(encoding="utf-8-sig")

# ------------------------------------------------------------
# Imports: QBoxLayout for responsive layout direction.
# ------------------------------------------------------------
text = text.replace(
    "QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,\n",
    "QWidget, QVBoxLayout, QHBoxLayout, QBoxLayout, QLabel, QLineEdit, QPushButton,\n",
    1,
)

# ------------------------------------------------------------
# Build UI: keep references to body/top and make them dynamic.
# ------------------------------------------------------------
text = text.replace(
    "        body = QHBoxLayout()\n        body.setSpacing(20)\n",
    "        self.body = QBoxLayout(QBoxLayout.Direction.LeftToRight)\n        self.body.setSpacing(20)\n",
    1,
)
text = text.replace("        body.addWidget(self.list)\n", "        self.body.addWidget(self.list)\n", 1)
text = text.replace("        top = QHBoxLayout()\n        top.setSpacing(22)\n", "        self.top = QBoxLayout(QBoxLayout.Direction.LeftToRight)\n        self.top.setSpacing(22)\n", 1)
text = text.replace("        top.addWidget(self.cover, 0, Qt.AlignmentFlag.AlignTop)\n", "        self.top.addWidget(self.cover, 0, Qt.AlignmentFlag.AlignTop)\n", 1)
text = text.replace("        top.addLayout(info, 1)\n        cl.addLayout(top)\n", "        self.top.addLayout(info, 1)\n        cl.addLayout(self.top)\n", 1)
text = text.replace("        body.addWidget(card, 1)\n        root.addLayout(body, 1)\n", "        self.body.addWidget(card, 1)\n        root.addLayout(self.body, 1)\n", 1)

# Make cover start smaller and scalable.
text = text.replace(
    "        self.cover.setFixedSize(340, 340)\n",
    "        self.cover.setMinimumSize(180, 180)\n        self.cover.setMaximumSize(340, 340)\n        self.cover.setSizePolicy(\n            self.cover.sizePolicy().horizontalPolicy(),\n            self.cover.sizePolicy().verticalPolicy(),\n        )\n",
    1,
)

# The generated SizePolicy call above is not ideal on PySide6; replace with explicit policy.
text = text.replace(
    "        self.cover.setSizePolicy(\n            self.cover.sizePolicy().horizontalPolicy(),\n            self.cover.sizePolicy().verticalPolicy(),\n        )\n",
    "        from PySide6.QtWidgets import QSizePolicy\n        self.cover.setSizePolicy(\n            QSizePolicy.Policy.Preferred,\n            QSizePolicy.Policy.Preferred,\n        )\n",
    1,
)

# ------------------------------------------------------------
# SQL: load persisted Discogs ID/link/cover from mp3_files.
# ------------------------------------------------------------
sql_old = """                    m.genre,\n                    COALESCE(r.artist, ''),\n                    COALESCE(r.title, ''),\n                    COALESCE(r.discogs, ''),\n                    COALESCE(r.cover, '')\n"""
sql_new = """                    m.genre,\n                    COALESCE(m.discogs_id, ''),\n                    COALESCE(m.discogs_link, ''),\n                    COALESCE(m.cover, ''),\n                    COALESCE(r.artist, ''),\n                    COALESCE(r.title, ''),\n                    COALESCE(r.discogs, ''),\n                    COALESCE(r.cover, '')\n"""
if "COALESCE(m.discogs_id" not in text and sql_old in text:
    text = text.replace(sql_old, sql_new, 1)

# ------------------------------------------------------------
# Row unpack: support either old or new query shape.
# ------------------------------------------------------------
old_unpack = """            release_artist,\n            release_title,\n            discogs_id,\n            release_cover,\n        ) = row\n"""
new_unpack = """            stored_discogs_id,\n            stored_discogs_link,\n            stored_cover,\n            release_artist,\n            release_title,\n            discogs_id,\n            release_cover,\n        ) = row\n"""
if "stored_discogs_id" not in text and old_unpack in text:
    text = text.replace(old_unpack, new_unpack, 1)

# If the query already contains persisted fields but unpack does not, patch that too.
if "stored_discogs_id" not in text and "COALESCE(m.discogs_id" in text and old_unpack in text:
    text = text.replace(old_unpack, new_unpack, 1)

# ------------------------------------------------------------
# show_item: prefer persisted MP3 Discogs data and cover.
# ------------------------------------------------------------
show_anchor = '        album = str(album or "").strip()\n\n'
if "stored_discogs_id" in text and "stored_cover and Path(stored_cover).exists()" not in text:
    block = '''        # Persisted MP3 Discogs data is authoritative for the MP3 Showcase.\n        if stored_discogs_id:\n            discogs_id = stored_discogs_id\n\n        if stored_cover and Path(str(stored_cover)).exists():\n            release_cover = stored_cover\n\n'''
    if show_anchor in text:
        text = text.replace(show_anchor, show_anchor + block, 1)

# Replace Discogs display text.
discogs_old = '''        if discogs_id:\n            self.discogs_label.setText(\n                f"Discogs release ID: {discogs_id}"\n            )\n        else:\n            self.discogs_label.setText("Discogs: geen releasekoppeling")\n'''
discogs_new = '''        if stored_discogs_id:\n            self.discogs_label.setText(\n                f"Discogs: opgehaald en opgeslagen • Release {stored_discogs_id}"\n            )\n            if stored_discogs_link:\n                self.discogs_label.setToolTip(stored_discogs_link)\n        elif discogs_id:\n            self.discogs_label.setText(\n                f"Discogs release ID: {discogs_id}"\n            )\n        else:\n            self.discogs_label.setText("Discogs: geen gegevens opgeslagen")\n'''
if discogs_old in text:
    text = text.replace(discogs_old, discogs_new, 1)

# ------------------------------------------------------------
# Cover loader: allow persisted cover path and make scaling dynamic.
# ------------------------------------------------------------
text = text.replace(
    "    def load_cover(self, path, release_cover):\n",
    "    def load_cover(self, path, release_cover):\n",
    1,
)
text = text.replace(
    "                                340,\n                                340,\n",
    "                                max(180, min(self.cover.width() - 8, self.cover.height() - 8)),\n                                max(180, min(self.cover.width() - 8, self.cover.height() - 8)),\n",
    2,
)

# ------------------------------------------------------------
# Add responsive resizeEvent before clear_showcase().
# ------------------------------------------------------------
if "    def resizeEvent(self, event):" not in text:
    marker = "    def clear_showcase(self):\n"
    resize_method = '''    def resizeEvent(self, event):\n        super().resizeEvent(event)\n\n        narrow = self.width() < 950\n\n        if hasattr(self, "body"):\n            self.body.setDirection(\n                QBoxLayout.Direction.TopToBottom\n                if narrow\n                else QBoxLayout.Direction.LeftToRight\n            )\n\n        if hasattr(self, "top"):\n            self.top.setDirection(\n                QBoxLayout.Direction.TopToBottom\n                if narrow\n                else QBoxLayout.Direction.LeftToRight\n            )\n\n        size = 240 if narrow else 340\n        self.cover.setMaximumSize(size, size)\n        self.cover.setMinimumSize(180, 180)\n\n        if self.current_index >= 0 and self.current_index < len(self.visible_items):\n            try:\n                row = self.visible_items[self.current_index]\n                self.load_cover(str(row[0]), str(row[-1] or ""))\n            except Exception:\n                pass\n\n'''
    if marker not in text:
        raise SystemExit("clear_showcase() not found")
    text = text.replace(marker, resize_method + marker, 1)

p.write_text(text, encoding="utf-8-sig")
print("OK: MP3 Showcase cover + Discogs status + responsive layout gefixt.")
''
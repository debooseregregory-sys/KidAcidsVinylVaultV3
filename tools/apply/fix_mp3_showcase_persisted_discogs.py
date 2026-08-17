from pathlib import Path

p = Path("gui/mp3_showcase_page.py")
text = p.read_text(encoding="utf-8-sig")

old_select = '''                    m.genre,\n                    COALESCE(r.artist, ''),\n                    COALESCE(r.title, ''),\n                    COALESCE(r.discogs, ''),\n                    COALESCE(r.cover, '')\n'''

new_select = '''                    m.genre,\n                    COALESCE(m.discogs_id, ''),\n                    COALESCE(m.discogs_link, ''),\n                    COALESCE(m.cover, ''),\n                    COALESCE(r.artist, ''),\n                    COALESCE(r.title, ''),\n                    COALESCE(r.discogs, ''),\n                    COALESCE(r.cover, '')\n'''

if old_select in text and "COALESCE(m.discogs_id" not in text:
    text = text.replace(old_select, new_select, 1)

old_unpack = '''            genre,\n            release_artist,\n            release_title,\n            discogs_id,\n            release_cover,\n        ) = row\n'''

new_unpack = '''            genre,\n            stored_discogs_id,\n            stored_discogs_link,\n            stored_cover,\n            release_artist,\n            release_title,\n            release_discogs_id,\n            release_cover,\n        ) = row\n'''

if old_unpack in text and "stored_discogs_id" not in text:
    text = text.replace(old_unpack, new_unpack, 1)

old_discogs = '''        if discogs_id:\n            self.discogs_label.setText(\n                f"Discogs release ID: {discogs_id}"\n            )\n        else:\n            self.discogs_label.setText("Discogs: geen releasekoppeling")\n\n        self.load_cover(str(path), str(release_cover or ""))\n'''

new_discogs = '''        # MP3-specifieke Discogs-opslag heeft voorrang op de vinyl-release.\n        persisted_id = str(stored_discogs_id or "").strip()\n        persisted_link = str(stored_discogs_link or "").strip()\n\n        if persisted_id:\n            if persisted_link:\n                self.discogs_label.setText(\n                    f"Discogs: opgehaald en opgeslagen  |  ID {persisted_id}"\n                )\n            else:\n                self.discogs_label.setText(\n                    f"Discogs: opgeslagen  |  ID {persisted_id}"\n                )\n        elif release_discogs_id:\n            self.discogs_label.setText(\n                f"Discogs release ID: {release_discogs_id}"\n            )\n        else:\n            self.discogs_label.setText("Discogs: geen releasekoppeling")\n\n        cover_source = (\n            str(stored_cover or "").strip()\n            if str(stored_cover or "").strip()\n            else str(release_cover or "")\n        )\n\n        self.load_cover(str(path), cover_source)\n'''

if old_discogs in text:
    text = text.replace(old_discogs, new_discogs, 1)

# Make the existing load_cover parameter represent either MP3-persisted or release cover.
# No functional change needed there: it already accepts a local file path.

p.write_text(text, encoding="utf-8-sig")
print("OK: MP3 Showcase gebruikt nu opgeslagen Discogs-ID/link/cover als primaire bron.")

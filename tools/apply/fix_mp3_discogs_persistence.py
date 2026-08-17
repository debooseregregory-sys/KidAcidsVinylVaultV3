from pathlib import Path
import re
import urllib.request

ROOT = Path(__file__).resolve().parents[2]
DB_SCRIPT = ROOT / "tools" / "apply" / "fix_mp3_discogs_persistence.py"
LIB = ROOT / "gui" / "mp3_library_page.py"
SHOW = ROOT / "gui" / "mp3_showcase_page.py"


def patch_library():
    text = LIB.read_text(encoding="utf-8-sig")

    # 1. Ensure extra imports needed by persisted Discogs covers.
    if "import urllib.request" not in text:
        text = text.replace("from pathlib import Path\n", "from pathlib import Path\nimport urllib.request\n", 1)

    # 2. Extend the existing progress/schema helper.
    marker = '        if "metadata_checked_at" not in cols:\n            conn.execute("ALTER TABLE mp3_files ADD COLUMN metadata_checked_at TEXT")\n'
    if marker in text and '"discogs_id"' not in text[text.find(marker):text.find(marker) + 1200]:
        extra = '''        if "discogs_id" not in cols:\n            conn.execute("ALTER TABLE mp3_files ADD COLUMN discogs_id TEXT")\n        if "discogs_link" not in cols:\n            conn.execute("ALTER TABLE mp3_files ADD COLUMN discogs_link TEXT")\n        if "cover" not in cols:\n            conn.execute("ALTER TABLE mp3_files ADD COLUMN cover TEXT")\n        if "album_artist" not in cols:\n            conn.execute("ALTER TABLE mp3_files ADD COLUMN album_artist TEXT")\n        if "composer" not in cols:\n            conn.execute("ALTER TABLE mp3_files ADD COLUMN composer TEXT")\n        if "track" not in cols:\n            conn.execute("ALTER TABLE mp3_files ADD COLUMN track TEXT")\n        if "disc" not in cols:\n            conn.execute("ALTER TABLE mp3_files ADD COLUMN disc TEXT")\n'''
        text = text.replace(marker, marker + extra, 1)

    # 3. Add a helper method to MetadataDialog for cover download and DB persistence.
    if "def persist_discogs_release(self, conn, path):" not in text:
        anchor = "    def save(self):\n"
        helper = '''    def persist_discogs_release(self, conn, path):\n        release = getattr(self, "release", None)\n        if not release:\n            return\n\n        release_id = str(release.get("id") or "").strip()\n        release_link = str(release.get("uri") or release.get("resource_url") or "").strip()\n        if release_id and release_link and not release_link.startswith("http"):\n            release_link = "https://www.discogs.com/release/" + release_id\n\n        cover_path = ""\n        images = release.get("images") or []\n        if images:\n            image_url = str(images[0].get("uri") or images[0].get("uri150") or "").strip()\n            if image_url:\n                covers_dir = ROOT / "covers"\n                covers_dir.mkdir(exist_ok=True)\n                target = covers_dir / f"mp3_release_{release_id}.jpg"\n                try:\n                    if not target.exists():\n                        urllib.request.urlretrieve(image_url, target)\n                    if target.exists():\n                        cover_path = str(target)\n                except Exception:\n                    pass\n\n        conn.execute(\n            """\n            UPDATE mp3_files\n            SET discogs_id=?, discogs_link=?, cover=?,\n                album_artist=?, composer=?, track=?, disc=?,\n                updated_at=CURRENT_TIMESTAMP\n            WHERE path=?\n            """,\n            (\n                release_id,\n                release_link,\n                cover_path,\n                str(self.album_artist.text()).strip(),\n                str(self.composer.text()).strip(),\n                str(self.track.text()).strip(),\n                str(self.disc.text()).strip(),\n                path,\n            ),\n        )\n\n'''
        if anchor not in text:
            raise SystemExit("Could not find MetadataDialog.save()")
        text = text.replace(anchor, helper + anchor, 1)

    # 4. Call the helper after the normal DB UPDATE and before commit.
    call_anchor = '                conn.execute(\n                    "UPDATE mp3_files SET metadata_checked=1, metadata_checked_at=CURRENT_TIMESTAMP WHERE path=?",\n                    (path,),\n                )\n                conn.commit()\n'
    if call_anchor in text and 'self.persist_discogs_release(conn, path)' not in text:
        replacement = call_anchor.replace(
            '                conn.commit()\n',
            '                self.persist_discogs_release(conn, path)\n                conn.commit()\n',
        )
        text = text.replace(call_anchor, replacement, 1)

    LIB.write_text(text, encoding="utf-8-sig")


def patch_showcase():
    text = SHOW.read_text(encoding="utf-8-sig")

    if "def load_persisted_mp3_info(self, path):" not in text:
        anchor = "    def show_item(self, row):\n"
        helper = '''    def load_persisted_mp3_info(self, path):\n        result = {\n            "discogs_id": "",\n            "discogs_link": "",\n            "cover": "",\n            "metadata_checked": 0,\n            "album_artist": "",\n            "composer": "",\n            "track": "",\n            "disc": "",\n        }\n        try:\n            conn = get_connection()\n            try:\n                row = conn.execute(\n                    """\n                    SELECT discogs_id, discogs_link, cover,\n                           COALESCE(metadata_checked, 0),\n                           album_artist, composer, track, disc\n                    FROM mp3_files\n                    WHERE path=?\n                    LIMIT 1\n                    """,\n                    (path,),\n                ).fetchone()\n            finally:\n                conn.close()\n            if row:\n                result.update({\n                    "discogs_id": str(row[0] or ""),\n                    "discogs_link": str(row[1] or ""),\n                    "cover": str(row[2] or ""),\n                    "metadata_checked": int(row[3] or 0),\n                    "album_artist": str(row[4] or ""),\n                    "composer": str(row[5] or ""),\n                    "track": str(row[6] or ""),\n                    "disc": str(row[7] or ""),\n                })\n        except Exception:\n            pass\n        return result\n\n'''
        if anchor not in text:
            raise SystemExit("Could not find MP3ShowcasePage.show_item()")
        text = text.replace(anchor, helper + anchor, 1)

    # 1. Load persistence at the start of show_item.
    marker = '        album = str(album or "").strip()\n\n'
    if marker in text and 'persisted = self.load_persisted_mp3_info(str(path))' not in text:
        extra = '''        persisted = self.load_persisted_mp3_info(str(path))\n\n        if persisted["album_artist"]:\n            album_artist = persisted["album_artist"]\n        else:\n            album_artist = ""\n\n        if persisted["composer"]:\n            composer = persisted["composer"]\n        else:\n            composer = ""\n\n'''
        text = text.replace(marker, marker + extra, 1)

    # 2. Add a visible status label if not already present.
    if "self.metadata_status_label" not in text:
        anchor = '        self.discogs_label = QLabel("Discogs: -")\n'
        if anchor not in text:
            raise SystemExit("Could not find Showcase Discogs label")
        status_block = '''        self.metadata_status_label = QLabel("Metadata: -")\n        self.metadata_status_label.setWordWrap(True)\n        self.metadata_status_label.setStyleSheet(\n            "color:#aaaab3;font-size:12px;font-weight:bold;"\n        )\n        info.addWidget(self.metadata_status_label)\n\n'''
        text = text.replace(anchor, status_block + anchor, 1)

    # 3. Use persisted Discogs values before falling back to the release join.
    discogs_marker = '        if discogs_id:\n            self.discogs_label.setText(\n                f"Discogs release ID: {discogs_id}"\n            )\n'
    if discogs_marker in text:
        old = discogs_marker
        new = '''        stored_discogs_id = persisted["discogs_id"]\n        stored_discogs_link = persisted["discogs_link"]\n        if stored_discogs_id:\n            discogs_id = stored_discogs_id\n\n        if discogs_id:\n            self.discogs_label.setText(\n                f"Discogs release ID: {discogs_id}"\n            )\n        else:\n            self.discogs_label.setText("Discogs: geen releasekoppeling")\n\n        if persisted["metadata_checked"]:\n            self.metadata_status_label.setText("Metadata: ✓ KLAAR")\n            self.metadata_status_label.setStyleSheet(\n                "color:#ffe08a;font-size:12px;font-weight:bold;"\n            )\n        else:\n            self.metadata_status_label.setText("Metadata: NIET GEDAAN")\n            self.metadata_status_label.setStyleSheet(\n                "color:#777783;font-size:12px;font-weight:bold;"\n            )\n'''
        text = text.replace(old, new, 1)

    # 4. Ensure persisted cover is tried before release cover.
    cover_call = '        self.load_cover(str(path), str(release_cover or ""))\n'
    if cover_call in text:
        text = text.replace(
            cover_call,
            '        persisted_cover = persisted["cover"]\n        self.load_cover(str(path), persisted_cover or str(release_cover or ""))\n',
            1,
        )

    # 5. Extend metadata line with stored album artist/composer/track/disc.
    meta_marker = '        self.meta_label.setText(\n            "  •  ".join(meta) if meta else "Geen aanvullende metadata"\n        )\n'
    if meta_marker in text and 'album_artist:' not in text:
        replacement = '''        if album_artist:\n            meta.append(f"Album Artist: {album_artist}")\n        if composer:\n            meta.append(f"Composer: {composer}")\n        if persisted["track"]:\n            meta.append(f"Track: {persisted[\"track\"]}")\n        if persisted["disc"]:\n            meta.append(f"Disc: {persisted[\"disc\"]}")\n\n        self.meta_label.setText(\n            "  •  ".join(meta) if meta else "Geen aanvullende metadata"\n        )\n'''
        text = text.replace(meta_marker, replacement, 1)

    # 6. Clear metadata status on empty page.
    clear_marker = '        self.discogs_label.setText("Discogs: -")\n'
    if clear_marker in text and 'self.metadata_status_label.setText("Metadata: -")' not in text:
        text = text.replace(clear_marker, clear_marker + '        self.metadata_status_label.setText("Metadata: -")\n', 1)

    SHOW.write_text(text, encoding="utf-8-sig")


def main():
    if not LIB.exists():
        raise SystemExit(f"Missing {LIB}")
    if not SHOW.exists():
        raise SystemExit(f"Missing {SHOW}")
    patch_library()
    patch_showcase()
    print("MP3 Discogs persistence + cover support toegevoegd.")
    print("Database-kolommen: discogs_id, discogs_link, cover, album_artist, composer, track, disc")
    print("De eerstvolgende keer dat je een metadata-editor opslaat, worden Discogs en cover permanent bewaard.")


if __name__ == "__main__":
    main()

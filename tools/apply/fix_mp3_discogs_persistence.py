from pathlib import Path
import urllib.request

ROOT = Path(__file__).resolve().parents[2]
LIB = ROOT / "gui" / "mp3_library_page.py"
SHOW = ROOT / "gui" / "mp3_showcase_page.py"

COLUMNS = {
    "metadata_checked": "INTEGER NOT NULL DEFAULT 0",
    "metadata_checked_at": "TEXT",
    "discogs_id": "TEXT",
    "discogs_link": "TEXT",
    "cover": "TEXT",
    "album_artist": "TEXT",
    "composer": "TEXT",
    "track": "TEXT",
    "disc": "TEXT",
}


def patch_library():
    text = LIB.read_text(encoding="utf-8-sig")

    if "import urllib.request" not in text:
        text = text.replace(
            "from pathlib import Path\n",
            "from pathlib import Path\nimport urllib.request\n",
            1,
        )

    # Make the existing schema helper add every column we need.
    helper_anchor = "def ensure_mp3_metadata_progress():\n"
    if helper_anchor in text:
        start = text.index(helper_anchor)
        next_class = text.find("\n\nclass ", start)
        if next_class == -1:
            next_class = len(text)
        helper = text[start:next_class]
        if "PRAGMA table_info(mp3_files)" in helper:
            add_lines = []
            for name, definition in COLUMNS.items():
                if f'"{name}" not in cols' not in helper:
                    add_lines.append(
                        f'        if "{name}" not in cols:\n'
                        f'            conn.execute("ALTER TABLE mp3_files ADD COLUMN {name} {definition}")\n'
                    )
            if add_lines:
                marker = "        conn.commit()\n"
                helper = helper.replace(marker, "".join(add_lines) + marker, 1)
                text = text[:start] + helper + text[next_class:]

    # Add a persistence helper that is self-contained and does not depend on a
    # previous migration having run.
    if "def persist_discogs_release(self, conn, path):" not in text:
        anchor = "    def save(self):\n"
        helper = '''    def persist_discogs_release(self, conn, path):
        # Ensure required columns exist even when an older DB is opened.
        existing = {row[1] for row in conn.execute("PRAGMA table_info(mp3_files)").fetchall()}
        for name, definition in {
            "discogs_id": "TEXT",
            "discogs_link": "TEXT",
            "cover": "TEXT",
            "album_artist": "TEXT",
            "composer": "TEXT",
            "track": "TEXT",
            "disc": "TEXT",
        }.items():
            if name not in existing:
                conn.execute(
                    f"ALTER TABLE mp3_files ADD COLUMN {name} {definition}"
                )

        release = getattr(self, "release", None)
        if not release:
            return

        release_id = str(release.get("id") or "").strip()
        release_link = (
            f"https://www.discogs.com/release/{release_id}"
            if release_id else ""
        )

        cover_path = ""
        images = release.get("images") or []
        if images:
            image_url = str(
                images[0].get("uri")
                or images[0].get("uri150")
                or ""
            ).strip()
            if image_url and release_id:
                covers_dir = ROOT / "covers"
                covers_dir.mkdir(exist_ok=True)
                target = covers_dir / f"mp3_release_{release_id}.jpg"
                try:
                    if not target.exists():
                        request = urllib.request.Request(
                            image_url,
                            headers={"User-Agent": "KidAcidsVinylVault/3.0"},
                        )
                        with urllib.request.urlopen(request, timeout=20) as response:
                            target.write_bytes(response.read())
                    if target.exists() and target.stat().st_size > 0:
                        cover_path = str(target)
                except Exception:
                    pass

        conn.execute(
            """
            UPDATE mp3_files
            SET discogs_id=?, discogs_link=?, cover=?,
                album_artist=?, composer=?, track=?, disc=?,
                updated_at=CURRENT_TIMESTAMP
            WHERE path=?
            """,
            (
                release_id,
                release_link,
                cover_path,
                str(self.album_artist.text()).strip(),
                str(self.composer.text()).strip(),
                str(self.track.text()).strip(),
                str(self.disc.text()).strip(),
                path,
            ),
        )

'''
        if anchor not in text:
            raise SystemExit("MetadataDialog.save() not found")
        text = text.replace(anchor, helper + anchor, 1)

    # Call persistence immediately before commit wherever metadata_checked is updated.
    if "self.persist_discogs_release(conn, path)" not in text:
        marker = "                conn.commit()\n"
        pos = text.find(marker, text.find("def save(self):"))
        if pos == -1:
            raise SystemExit("Could not find MetadataDialog commit")
        text = text[:pos] + "                self.persist_discogs_release(conn, path)\n" + text[pos:]

    LIB.write_text(text, encoding="utf-8-sig")


def patch_showcase():
    text = SHOW.read_text(encoding="utf-8-sig")

    if "def load_persisted_mp3_info(self, path):" not in text:
        anchor = "    def show_item(self, row):\n"
        helper = '''    def load_persisted_mp3_info(self, path):
        result = {
            "discogs_id": "",
            "discogs_link": "",
            "cover": "",
            "metadata_checked": 0,
            "album_artist": "",
            "composer": "",
            "track": "",
            "disc": "",
        }
        try:
            conn = get_connection()
            try:
                existing = {row[1] for row in conn.execute("PRAGMA table_info(mp3_files)").fetchall()}
                required = [
                    "discogs_id", "discogs_link", "cover",
                    "metadata_checked", "album_artist", "composer", "track", "disc",
                ]
                if all(column in existing for column in required):
                    row = conn.execute(
                        """
                        SELECT discogs_id, discogs_link, cover,
                               COALESCE(metadata_checked, 0),
                               album_artist, composer, track, disc
                        FROM mp3_files
                        WHERE path=?
                        LIMIT 1
                        """,
                        (path,),
                    ).fetchone()
                else:
                    row = None
            finally:
                conn.close()

            if row:
                result.update({
                    "discogs_id": str(row[0] or ""),
                    "discogs_link": str(row[1] or ""),
                    "cover": str(row[2] or ""),
                    "metadata_checked": int(row[3] or 0),
                    "album_artist": str(row[4] or ""),
                    "composer": str(row[5] or ""),
                    "track": str(row[6] or ""),
                    "disc": str(row[7] or ""),
                })
        except Exception:
            pass
        return result

'''
        if anchor not in text:
            raise SystemExit("MP3ShowcasePage.show_item() not found")
        text = text.replace(anchor, helper + anchor, 1)

    marker = '        album = str(album or "").strip()\n\n'
    if marker in text and "persisted = self.load_persisted_mp3_info(str(path))" not in text:
        text = text.replace(
            marker,
            marker + '        persisted = self.load_persisted_mp3_info(str(path))\n\n',
            1,
        )

    if "self.metadata_status_label" not in text:
        anchor = '        self.discogs_label = QLabel("Discogs: -")\n'
        if anchor not in text:
            raise SystemExit("Showcase Discogs label not found")
        block = '''        self.metadata_status_label = QLabel("Metadata: -")
        self.metadata_status_label.setWordWrap(True)
        self.metadata_status_label.setStyleSheet(
            "color:#aaaab3;font-size:12px;font-weight:bold;"
        )
        info.addWidget(self.metadata_status_label)

'''
        text = text.replace(anchor, block + anchor, 1)

    # Prefer persisted Discogs ID and cover.
    marker = '        if discogs_id:\n'
    first = text.find(marker, text.find("def show_item(self, row):"))
    if first != -1 and "stored_discogs_id = persisted[\"discogs_id\"]" not in text:
        insertion = '''        stored_discogs_id = persisted["discogs_id"]
        if stored_discogs_id:
            discogs_id = stored_discogs_id

        if persisted["metadata_checked"]:
            self.metadata_status_label.setText("Metadata: ✓ KLAAR")
            self.metadata_status_label.setStyleSheet(
                "color:#ffe08a;font-size:12px;font-weight:bold;"
            )
        else:
            self.metadata_status_label.setText("Metadata: NIET GEDAAN")
            self.metadata_status_label.setStyleSheet(
                "color:#777783;font-size:12px;font-weight:bold;"
            )

'''
        text = text[:first] + insertion + text[first:]

    cover_call = '        self.load_cover(str(path), str(release_cover or ""))\n'
    if cover_call in text and "persisted_cover = persisted[\"cover\"]" not in text:
        text = text.replace(
            cover_call,
            '        persisted_cover = persisted["cover"]\n'
            '        self.load_cover(str(path), persisted_cover or str(release_cover or ""))\n',
            1,
        )

    # Show stored auxiliary fields.
    marker = '        self.meta_label.setText(\n'
    if marker in text and "Album Artist:" not in text:
        extra = '''        if persisted["album_artist"]:
            meta.append(f"Album Artist: {persisted['album_artist']}")
        if persisted["composer"]:
            meta.append(f"Composer: {persisted['composer']}")
        if persisted["track"]:
            meta.append(f"Track: {persisted['track']}")
        if persisted["disc"]:
            meta.append(f"Disc: {persisted['disc']}")

'''
        text = text.replace(marker, extra + marker, 1)

    SHOW.write_text(text, encoding="utf-8-sig")


def main():
    patch_library()
    patch_showcase()
    print("OK: MP3 Discogs-ID, Discogs-link, cover en metadata-status worden persistent opgeslagen.")
    print("Nieuwe opslag gebeurt zodra je in Metadata Builder opnieuw OPSLAAN gebruikt.")


if __name__ == "__main__":
    main()

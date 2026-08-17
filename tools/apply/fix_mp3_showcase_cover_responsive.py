from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LIB = ROOT / "gui" / "mp3_library_page.py"
SHOW = ROOT / "gui" / "mp3_showcase_page.py"


def add_library_persistence(text: str) -> str:
    if "import urllib.request" not in text:
        text = text.replace("from pathlib import Path\n", "from pathlib import Path\nimport urllib.request\n", 1)

    if "ROOT = Path(__file__).resolve().parents[1]" not in text and "ROOT = Path(__file__).resolve().parents[2]" not in text:
        marker = "\n\nclass MP3TableModel"
        if marker in text:
            text = text.replace(marker, "\n\nROOT = Path(__file__).resolve().parents[1]\n" + marker, 1)

    if "def ensure_mp3_discogs_columns():" not in text:
        marker = "\n\nclass MP3TableModel"
        helper = '''\n\ndef ensure_mp3_discogs_columns():\n    conn = get_connection()\n    try:\n        cols = {row[1] for row in conn.execute("PRAGMA table_info(mp3_files)").fetchall()}\n        for name in ("discogs_id", "discogs_link", "cover"):\n            if name not in cols:\n                conn.execute(f"ALTER TABLE mp3_files ADD COLUMN {name} TEXT")\n        conn.commit()\n    finally:\n        conn.close()\n'''
        if marker not in text:
            raise SystemExit("Kan MP3TableModel niet vinden in mp3_library_page.py")
        text = text.replace(marker, helper + marker, 1)

    if "self.release = None" not in text:
        marker = '        self.setWindowTitle("MP3 Metadata Builder")\n'
        if marker in text:
            text = text.replace(marker, marker + "        self.release = None\n", 1)

    if "def persist_discogs_release(self, path):" not in text:
        marker = "    def save(self):\n"
        helper = '''    def persist_discogs_release(self, path):\n        release = getattr(self, "release", None)\n        if not release:\n            return\n\n        release_id = str(release.get("id") or "").strip()\n        if not release_id:\n            return\n\n        discogs_link = str(\n            release.get("uri")\n            or release.get("resource_url")\n            or ""\n        ).strip()\n        if not discogs_link.startswith("http"):\n            discogs_link = f"https://www.discogs.com/release/{release_id}"\n\n        cover_path = ""\n        images = release.get("images") or []\n        image_url = ""\n        if images and isinstance(images[0], dict):\n            image_url = str(\n                images[0].get("uri")\n                or images[0].get("uri150")\n                or ""\n            ).strip()\n\n        if image_url:\n            covers = ROOT / "covers"\n            covers.mkdir(parents=True, exist_ok=True)\n            target = covers / f"mp3_release_{release_id}.jpg"\n            try:\n                if not target.exists():\n                    urllib.request.urlretrieve(image_url, str(target))\n                if target.exists():\n                    cover_path = str(target)\n            except Exception:\n                cover_path = ""\n\n        ensure_mp3_discogs_columns()\n        conn = get_connection()\n        try:\n            conn.execute(\n                "UPDATE mp3_files SET discogs_id=?, discogs_link=?, cover=?, updated_at=CURRENT_TIMESTAMP WHERE path=?",\n                (release_id, discogs_link, cover_path, path),\n            )\n            conn.commit()\n        finally:\n            conn.close()\n\n'''
        if marker not in text:
            raise SystemExit("MetadataDialog.save() niet gevonden")
        text = text.replace(marker, helper + marker, 1)

    if "self.persist_discogs_release(path)" not in text:
        marker = "            self.accept()\n"
        if marker not in text:
            raise SystemExit("MetadataDialog.accept() niet gevonden")
        text = text.replace(
            marker,
            "            self.persist_discogs_release(path)\n\n" + marker,
            1,
        )

    if "ensure_mp3_discogs_columns()\n        self.build_ui()" not in text:
        marker = "        self.build_ui()\n"
        if marker in text:
            text = text.replace(marker, "        ensure_mp3_discogs_columns()\n" + marker, 1)

    return text


def add_showcase_persistence_and_responsive(text: str) -> str:
    if "def load_persisted_metadata(self, path):" not in text:
        marker = "    def show_item(self, row):\n"
        helper = '''    def load_persisted_metadata(self, path):\n        result = {\n            "discogs_id": "",\n            "discogs_link": "",\n            "cover": "",\n        }\n\n        try:\n            conn = get_connection()\n            try:\n                cols = {row[1] for row in conn.execute("PRAGMA table_info(mp3_files)").fetchall()}\n                if "discogs_id" not in cols:\n                    return result\n                row = conn.execute(\n                    "SELECT COALESCE(discogs_id,''), COALESCE(discogs_link,''), COALESCE(cover,'') FROM mp3_files WHERE path=? LIMIT 1",\n                    (path,),\n                ).fetchone()\n            finally:\n                conn.close()\n\n            if row:\n                result["discogs_id"] = str(row[0] or "").strip()\n                result["discogs_link"] = str(row[1] or "").strip()\n                result["cover"] = str(row[2] or "").strip()\n        except Exception:\n            pass\n\n        return result\n\n'''
        if marker not in text:
            raise SystemExit("MP3ShowcasePage.show_item() niet gevonden")
        text = text.replace(marker, helper + marker, 1)

    # Ensure persisted is defined before use.
    marker = '        album = str(album or "").strip()\n\n'
    if marker in text and '        persisted = self.load_persisted_metadata(str(path))\n' not in text:
        text = text.replace(
            marker,
            marker + '        persisted = self.load_persisted_metadata(str(path))\n',
            1,
        )

    # Persisted Discogs values take precedence over Vinyl-linked release data.
    marker = '        if release_title:\n'
    if marker in text and 'stored_discogs_id = persisted["discogs_id"]' not in text:
        block = '''        stored_discogs_id = persisted["discogs_id"]\n        if stored_discogs_id:\n            discogs_id = stored_discogs_id\n\n        if persisted["cover"] and Path(persisted["cover"]).exists():\n            release_cover = persisted["cover"]\n\n'''
        text = text.replace(marker, block + marker, 1)

    # Use persisted cover in existing cover loader call.
    old = '        self.load_cover(str(path), str(release_cover or ""))\n'
    if old in text:
        text = text.replace(
            old,
            '        self.load_cover(str(path), str(persisted["cover"] or release_cover or ""))\n',
            1,
        )

    # Display persisted Discogs link when available.
    old = '''        if discogs_id:\n            self.discogs_label.setText(\n                f"Discogs release ID: {discogs_id}"\n            )\n        else:\n            self.discogs_label.setText("Discogs: geen releasekoppeling")\n'''
    if old in text and 'stored_discogs_link' not in text:
        new = '''        stored_discogs_link = persisted["discogs_link"]\n        if discogs_id:\n            label = f"Discogs release ID: {discogs_id}"\n            if stored_discogs_link:\n                label += f"  •  {stored_discogs_link}"\n            self.discogs_label.setText(label)\n        else:\n            self.discogs_label.setText("Discogs: geen releasekoppeling")\n'''
        text = text.replace(old, new, 1)

    # Make the body layout responsive.
    if 'self.body_layout = body' not in text:
        text = text.replace(
            '        body = QHBoxLayout()\n        body.setSpacing(20)\n',
            '        body = QHBoxLayout()\n        body.setSpacing(20)\n        self.body_layout = body\n',
            1,
        )

    text = text.replace(
        '        self.list.setMinimumWidth(360)\n',
        '        self.list.setMinimumWidth(0)\n        self.list.setMinimumHeight(260)\n',
        1,
    )

    text = text.replace(
        '        self.cover.setFixedSize(340, 340)\n',
        '        self.cover.setMinimumSize(180, 180)\n        self.cover.setMaximumSize(340, 340)\n',
        1,
    )

    if '    def resizeEvent(self, event):\n' not in text:
        marker = '    def load_files(self):\n'
        method = '''    def resizeEvent(self, event):\n        super().resizeEvent(event)\n\n        if not hasattr(self, "body_layout"):\n            return\n\n        compact = self.width() < 1100\n        direction = (\n            self.body_layout.Direction.TopToBottom\n            if compact\n            else self.body_layout.Direction.LeftToRight\n        )\n        self.body_layout.setDirection(direction)\n\n        available = max(180, min(340, int(self.width() * (0.32 if not compact else 0.55))))\n        self.cover.setFixedSize(available, available)\n\n'''
        if marker not in text:
            raise SystemExit("load_files() niet gevonden in Showcase")
        text = text.replace(marker, method + marker, 1)

    return text


def main():
    if not LIB.exists():
        raise SystemExit(f"Niet gevonden: {LIB}")
    if not SHOW.exists():
        raise SystemExit(f"Niet gevonden: {SHOW}")

    lib_text = LIB.read_text(encoding="utf-8-sig")
    show_text = SHOW.read_text(encoding="utf-8-sig")

    LIB.write_text(add_library_persistence(lib_text), encoding="utf-8-sig")
    SHOW.write_text(add_showcase_persistence_and_responsive(show_text), encoding="utf-8-sig")

    print("OK: MP3 Discogs/cover persistentie en responsive Showcase toegevoegd.")


if __name__ == "__main__":
    main()

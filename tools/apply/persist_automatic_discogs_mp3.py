from pathlib import Path
import urllib.request

ROOT = Path(__file__).resolve().parents[2]
LIB = ROOT / "gui" / "mp3_library_page.py"
SHOW = ROOT / "gui" / "mp3_showcase_page.py"


def add_imports(text):
    if "import urllib.request" not in text:
        text = text.replace(
            "from pathlib import Path\n",
            "from pathlib import Path\nimport urllib.request\n",
            1,
        )
    return text


def add_schema_helper(text):
    if "def ensure_mp3_discogs_columns():" in text:
        return text

    marker = "\n\nclass MP3TableModel"
    helper = '''\n\ndef ensure_mp3_discogs_columns():\n    conn = get_connection()\n    try:\n        cols = {row[1] for row in conn.execute("PRAGMA table_info(mp3_files)").fetchall()}\n        additions = {\n            "discogs_id": "TEXT",\n            "discogs_link": "TEXT",\n            "cover": "TEXT",\n        }\n        for name, kind in additions.items():\n            if name not in cols:\n                conn.execute(f"ALTER TABLE mp3_files ADD COLUMN {name} {kind}")\n        conn.commit()\n    finally:\n        conn.close()\n'''
    if marker not in text:
        raise SystemExit("Cannot find MP3TableModel marker")
    return text.replace(marker, helper + marker, 1)


def add_dialog_helper(text):
    if "def persist_discogs_release(self, conn, path):" in text:
        return text

    marker = "    def save(self):\n"
    helper = '''    def persist_discogs_release(self, conn, path):\n        release = getattr(self, "release", None)\n        if not release:\n            return\n\n        release_id = str(release.get("id") or "").strip()\n        if not release_id:\n            return\n\n        discogs_link = str(release.get("uri") or "").strip()\n        if not discogs_link.startswith("http"):\n            discogs_link = f"https://www.discogs.com/release/{release_id}"\n\n        cover_path = ""\n        images = release.get("images") or []\n        image_url = ""\n        if images and isinstance(images[0], dict):\n            image_url = str(\n                images[0].get("uri")\n                or images[0].get("uri150")\n                or ""\n            ).strip()\n\n        if image_url:\n            covers = ROOT / "covers"\n            covers.mkdir(parents=True, exist_ok=True)\n            target = covers / f"mp3_release_{release_id}.jpg"\n            try:\n                if not target.exists():\n                    urllib.request.urlretrieve(image_url, str(target))\n                if target.exists():\n                    cover_path = str(target)\n            except Exception:\n                pass\n\n        conn.execute(\n            """\n            UPDATE mp3_files\n            SET discogs_id=?, discogs_link=?, cover=?, updated_at=CURRENT_TIMESTAMP\n            WHERE path=?\n            """,\n            (release_id, discogs_link, cover_path, path),\n        )\n\n'''
    if marker not in text:
        raise SystemExit("Cannot find MetadataDialog.save()")
    return text.replace(marker, helper + marker, 1)


def call_dialog_helper(text):
    marker = "            self.accept()\n"
    if "self.persist_discogs_release(conn, path)" in text:
        return text
    # Put the persistence call immediately before accept, after the normal DB transaction.
    if marker not in text:
        raise SystemExit("Cannot find MetadataDialog.accept()")
    return text.replace(
        marker,
        "            ensure_mp3_discogs_columns()\n            self.persist_discogs_release(conn, path)\n            conn.commit()\n\n" + marker,
        1,
    )


def patch_library():
    text = LIB.read_text(encoding="utf-8-sig")
    text = add_imports(text)
    text = add_schema_helper(text)
    text = add_dialog_helper(text)
    text = call_dialog_helper(text)
    # Ensure columns on page construction as well.
    init_marker = "        self.build_ui()\n"
    if "ensure_mp3_discogs_columns()\n        self.build_ui()" not in text:
        text = text.replace(init_marker, "        ensure_mp3_discogs_columns()\n" + init_marker, 1)
    LIB.write_text(text, encoding="utf-8-sig")


def patch_showcase():
    text = SHOW.read_text(encoding="utf-8-sig")

    if "def ensure_mp3_discogs_columns()" not in text:
        marker = "\n\nclass MP3ShowcasePage"
        helper = '''\n\ndef ensure_mp3_discogs_columns():\n    conn = get_connection()\n    try:\n        cols = {row[1] for row in conn.execute("PRAGMA table_info(mp3_files)").fetchall()}\n        for name, kind in (("discogs_id", "TEXT"), ("discogs_link", "TEXT"), ("cover", "TEXT")):\n            if name not in cols:\n                conn.execute(f"ALTER TABLE mp3_files ADD COLUMN {name} {kind}")\n        conn.commit()\n    finally:\n        conn.close()\n'''
        if marker not in text:
            raise SystemExit("Cannot find MP3ShowcasePage marker")
        text = text.replace(marker, helper + marker, 1)

    # Add persisted columns to load_files SELECT if absent.
    select_marker = "                    m.genre,\n                    COALESCE(r.artist, ''),"
    select_new = "                    m.genre,\n                    COALESCE(m.discogs_id, ''),\n                    COALESCE(m.discogs_link, ''),\n                    COALESCE(m.cover, ''),\n                    COALESCE(r.artist, ''),"
    if select_marker in text and "COALESCE(m.discogs_id" not in text:
        text = text.replace(select_marker, select_new, 1)

    # The existing row unpacking needs to match the new three fields.
    old_unpack = '''            release_artist,\n            release_title,\n            discogs_id,\n            release_cover,\n        ) = row\n'''
    new_unpack = '''            stored_discogs_id,\n            stored_discogs_link,\n            stored_cover,\n            release_artist,\n            release_title,\n            discogs_id,\n            release_cover,\n        ) = row\n'''
    if old_unpack in text and "stored_discogs_id" not in text:
        text = text.replace(old_unpack, new_unpack, 1)

    # Prefer persisted Discogs values and cover.
    marker = '        if release_title:\n'
    if marker in text and 'if stored_discogs_id:' not in text:
        block = '''        if stored_discogs_id:\n            discogs_id = stored_discogs_id\n\n        if stored_cover and Path(stored_cover).exists():\n            release_cover = stored_cover\n\n'''
        text = text.replace(marker, block + marker, 1)

    # Ensure columns are ready when the showcase is created.
    init_marker = "        self.build_ui()\n"
    if "ensure_mp3_discogs_columns()\n        self.build_ui()" not in text:
        text = text.replace(init_marker, "        ensure_mp3_discogs_columns()\n" + init_marker, 1)

    SHOW.write_text(text, encoding="utf-8-sig")


def main():
    if not LIB.exists():
        raise SystemExit(f"Missing {LIB}")
    if not SHOW.exists():
        raise SystemExit(f"Missing {SHOW}")
    patch_library()
    patch_showcase()
    print("OK: automatische + handmatige Discogs MP3-opslag toegevoegd.")
    print("OK: Discogs cover wordt lokaal bewaard en door de Showcase gebruikt.")


if __name__ == "__main__":
    main()

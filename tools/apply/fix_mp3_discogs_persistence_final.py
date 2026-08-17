from pathlib import Path
import re
import urllib.request

ROOT = Path(__file__).resolve().parents[2]
LIB = ROOT / "gui" / "mp3_library_page.py"
SHOW = ROOT / "gui" / "mp3_showcase_page.py"


def add_import(text):
    if "import urllib.request" not in text:
        text = text.replace("from pathlib import Path\n", "from pathlib import Path\nimport urllib.request\n", 1)
    return text


def ensure_columns_helper(text):
    if "def ensure_mp3_discogs_columns():" in text:
        return text
    marker = "\n\nclass MP3TableModel"
    helper = '''\n\ndef ensure_mp3_discogs_columns():\n    conn = get_connection()\n    try:\n        cols = {row[1] for row in conn.execute("PRAGMA table_info(mp3_files)").fetchall()}\n        additions = {\n            "discogs_id": "TEXT",\n            "discogs_link": "TEXT",\n            "cover": "TEXT",\n        }\n        for name, kind in additions.items():\n            if name not in cols:\n                conn.execute(f"ALTER TABLE mp3_files ADD COLUMN {name} {kind}")\n        conn.commit()\n    finally:\n        conn.close()\n'''
    if marker not in text:
        raise SystemExit("Kan MP3TableModel niet vinden")
    return text.replace(marker, helper + marker, 1)


def add_persist_method(text):
    if "def persist_discogs_release(self, path):" in text:
        return text
    marker = "    def save(self):"
    method = '''    def persist_discogs_release(self, path):\n        release = getattr(self, "release", None)\n        if not release:\n            return\n\n        release_id = str(release.get("id") or "").strip()\n        if not release_id:\n            return\n\n        discogs_link = str(release.get("uri") or "").strip()\n        if not discogs_link.startswith("http"):\n            discogs_link = f"https://www.discogs.com/release/{release_id}"\n\n        cover_path = ""\n        images = release.get("images") or []\n        if images and isinstance(images[0], dict):\n            image_url = str(images[0].get("uri") or images[0].get("uri150") or "").strip()\n            if image_url:\n                covers = ROOT / "covers"\n                covers.mkdir(parents=True, exist_ok=True)\n                target = covers / f"mp3_release_{release_id}.jpg"\n                try:\n                    if not target.exists():\n                        urllib.request.urlretrieve(image_url, str(target))\n                    if target.exists():\n                        cover_path = str(target)\n                except Exception:\n                    pass\n\n        ensure_mp3_discogs_columns()\n        conn = get_connection()\n        try:\n            conn.execute(\n                "UPDATE mp3_files SET discogs_id=?, discogs_link=?, cover=?, updated_at=CURRENT_TIMESTAMP WHERE path=?",\n                (release_id, discogs_link, cover_path, path),\n            )\n            conn.commit()\n        finally:\n            conn.close()\n\n'''
    if marker not in text:
        raise SystemExit("MetadataDialog.save() niet gevonden")
    return text.replace(marker, method + marker, 1)


def add_save_call(text):
    if "self.persist_discogs_release(path)" in text:
        return text
    marker = "            self.accept()"
    if marker not in text:
        raise SystemExit("MetadataDialog.accept() niet gevonden")
    return text.replace(marker, "            self.persist_discogs_release(path)\n\n" + marker, 1)


def patch_library():
    text = LIB.read_text(encoding="utf-8-sig")
    text = add_import(text)
    text = ensure_columns_helper(text)
    text = add_persist_method(text)
    text = add_save_call(text)
    # Initialise schema whenever page is created.
    init = "        self.build_ui()\n"
    if "ensure_mp3_discogs_columns()\n        self.build_ui()" not in text:
        text = text.replace(init, "        ensure_mp3_discogs_columns()\n" + init, 1)
    LIB.write_text(text, encoding="utf-8-sig")


def add_showcase_helper(text):
    if "def load_persisted_mp3_info(self, path):" in text:
        return text
    marker = "    def show_item(self, row):"
    helper = '''    def load_persisted_mp3_info(self, path):\n        result = {\n            "discogs_id": "",\n            "discogs_link": "",\n            "cover": "",\n            "metadata_checked": 0,\n        }\n        try:\n            conn = get_connection()\n            try:\n                cols = {row[1] for row in conn.execute("PRAGMA table_info(mp3_files)").fetchall()}\n                if "discogs_id" not in cols:\n                    conn.close()\n                    return result\n                row = conn.execute(\n                    "SELECT discogs_id, discogs_link, cover, COALESCE(metadata_checked,0) FROM mp3_files WHERE path=? LIMIT 1",\n                    (path,),\n                ).fetchone()\n            finally:\n                try:\n                    conn.close()\n                except Exception:\n                    pass\n            if row:\n                result.update({\n                    "discogs_id": str(row[0] or ""),\n                    "discogs_link": str(row[1] or ""),\n                    "cover": str(row[2] or ""),\n                    "metadata_checked": int(row[3] or 0),\n                })\n        except Exception:\n            pass\n        return result\n\n'''
    if marker not in text:
        raise SystemExit("MP3ShowcasePage.show_item() niet gevonden")
    return text.replace(marker, helper + marker, 1)


def patch_showcase():
    text = SHOW.read_text(encoding="utf-8-sig")
    # Guarantee the schema exists before Showcase queries it.
    if "def ensure_mp3_discogs_columns():" not in text:
        marker = "\n\nclass MP3ShowcasePage"
        helper = '''\n\ndef ensure_mp3_discogs_columns():\n    conn = get_connection()\n    try:\n        cols = {row[1] for row in conn.execute("PRAGMA table_info(mp3_files)").fetchall()}\n        for name in ("discogs_id", "discogs_link", "cover"):\n            if name not in cols:\n                conn.execute(f"ALTER TABLE mp3_files ADD COLUMN {name} TEXT")\n        conn.commit()\n    finally:\n        conn.close()\n'''
        if marker not in text:
            raise SystemExit("MP3ShowcasePage marker niet gevonden")
        text = text.replace(marker, helper + marker, 1)

    text = add_showcase_helper(text)

    # Ensure persisted is created immediately after show_item unpacking.
    show_match = re.search(r"(    def show_item\(self, row\):\n)(.*?)(\n        artist = str\(artist or \\\"\\\"\).strip\(\) or \\\"Onbekende artiest\\\"\n)", text, re.S)
    if show_match and "persisted = self.load_persisted_mp3_info(str(path))" not in show_match.group(0):
        replacement = show_match.group(1) + show_match.group(2) + "\n        persisted = self.load_persisted_mp3_info(str(path))\n" + show_match.group(3)
        text = text[:show_match.start()] + replacement + text[show_match.end():]

    # Fallback for slightly different whitespace/code versions: insert before the first artist normalisation.
    if "persisted = self.load_persisted_mp3_info(str(path))" not in text:
        marker = '        artist = str(artist or "").strip() or "Onbekende artiest"'
        if marker in text:
            text = text.replace(marker, '        persisted = self.load_persisted_mp3_info(str(path))\n\n' + marker, 1)

    # Prefer the persisted Discogs id/cover.
    if 'stored_discogs_id = persisted["discogs_id"]' not in text:
        marker = '        if release_title:'
        if marker in text:
            block = '''        stored_discogs_id = persisted["discogs_id"]\n        stored_discogs_link = persisted["discogs_link"]\n        stored_cover = persisted["cover"]\n\n        if stored_discogs_id:\n            discogs_id = stored_discogs_id\n        if stored_cover and Path(stored_cover).exists():\n            release_cover = stored_cover\n\n'''
            text = text.replace(marker, block + marker, 1)

    # Add a visible persistence indicator if it does not exist.
    if "self.metadata_status_label" not in text:
        marker = '        self.discogs_label = QLabel("Discogs: -")\n'
        if marker in text:
            block = '''        self.metadata_status_label = QLabel("Metadata: -")\n        self.metadata_status_label.setWordWrap(True)\n        self.metadata_status_label.setStyleSheet("color:#777783;font-size:12px;font-weight:bold;")\n        info.addWidget(self.metadata_status_label)\n'''
            text = text.replace(marker, block + marker, 1)

    # Add status text right before the release section.
    if 'self.metadata_status_label.setText("Metadata: ✓ KLAAR")' not in text:
        marker = '        if release_title:'
        if marker in text:
            block = '''        if persisted["metadata_checked"]:\n            self.metadata_status_label.setText("Metadata: ✓ KLAAR")\n            self.metadata_status_label.setStyleSheet("color:#ffe08a;font-size:12px;font-weight:bold;")\n        else:\n            self.metadata_status_label.setText("Metadata: NIET GEDAAN")\n            self.metadata_status_label.setStyleSheet("color:#777783;font-size:12px;font-weight:bold;")\n\n'''
            text = text.replace(marker, block + marker, 1)

    # Use stored cover before release cover.
    old_cover = '        self.load_cover(str(path), str(release_cover or ""))\n'
    if old_cover in text:
        text = text.replace(old_cover, '        self.load_cover(str(path), stored_cover or str(release_cover or ""))\n', 1)

    # Ensure persisted columns before Showcase page construction.
    init = "        self.build_ui()\n"
    if "ensure_mp3_discogs_columns()\n        self.build_ui()" not in text:
        text = text.replace(init, "        ensure_mp3_discogs_columns()\n" + init, 1)

    SHOW.write_text(text, encoding="utf-8-sig")


def main():
    if not LIB.exists():
        raise SystemExit(f"Ontbreekt: {LIB}")
    if not SHOW.exists():
        raise SystemExit(f"Ontbreekt: {SHOW}")
    patch_library()
    patch_showcase()
    print("OK: automatische en handmatige Discogs-opslag gekoppeld.")
    print("OK: Discogs-cover wordt lokaal opgeslagen en door de Showcase gebruikt.")
    print("OK: Showcase initialiseert persisted metadata correct.")


if __name__ == "__main__":
    main()

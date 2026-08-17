from pathlib import Path
import re

TARGET = Path("gui/mp3_duplicate_cleaner.py")
text = TARGET.read_text(encoding="utf-8-sig")

# Ensure re is imported.
if "import re" not in text:
    text = text.replace("import hashlib\n", "import hashlib\nimport re\n", 1)

# Make the worker stoppable.
if "def request_stop(self):" not in text:
    needle = "    def run(self):\n"
    replacement = "    def request_stop(self):\n        self.requestInterruption()\n\n    def run(self):\n"
    if needle in text:
        text = text.replace(needle, replacement, 1)

# Stop checks inside the main file loop and before expensive hashing.
text = text.replace(
    "            for row in rows:\n                mp3_id, path, artist, title, album, year, checked, linked = row\n",
    "            for row in rows:\n                if self.isInterruptionRequested():\n                    return\n                mp3_id, path, artist, title, album, year, checked, linked = row\n",
    1,
)
text = text.replace(
    "                for item in candidates:\n                    path = item[1]\n",
    "                for item in candidates:\n                    if self.isInterruptionRequested():\n                        return\n                    path = item[1]\n",
    1,
)

# Add a track-key helper if the file does not have one.
if "def _duplicate_track_key" not in text:
    marker = "class HashWorker(QThread):\n"
    helper = '''def _duplicate_track_key(artist, title):\n    def norm(value):\n        value = str(value or "").casefold()\n        value = re.sub(r"\\[[^\\]]*\\]", " ", value)\n        value = re.sub(r"\\([^)]*\\)", " ", value)\n        value = re.sub(r"\\s+", " ", value).strip()\n        return value\n    a = norm(artist)\n    t = norm(title)\n    return f"{a}|||{t}" if a and t else ""\n\n\n'''
    if marker in text:
        text = text.replace(marker, helper + marker, 1)

# Extend finished_scan groups with likely duplicates based on artist/title.
needle = "            self.finished_scan.emit(groups)\n"
if needle in text and "MOGELIJK DUBBEL" not in text:
    replacement = '''            # Also report likely duplicate tracks based on artist + title.\n            by_track = {}\n            for row in rows:\n                key = _duplicate_track_key(row[2], row[3])\n                if key:\n                    by_track.setdefault(key, []).append(row)\n\n            for key, members in by_track.items():\n                if len(members) > 1:\n                    groups.append({\n                        "sha256": "",\n                        "size": members[0][5] if len(members[0]) > 5 else 0,\n                        "kind": "track",\n                        "files": members,\n                    })\n\n            self.finished_scan.emit(groups)\n'''
    text = text.replace(needle, replacement, 1)

# Replace the old summary so zero results are explicit.
old_summary = '        self.summary.setText(\n            f"{len(groups)} dubbele groepen gevonden • {duplicate_files} overtollige bestanden"\n        )\n'
if old_summary in text:
    new_summary = '''        if not groups:\n            self.summary.setText("Geen dubbele MP3's gevonden.")\n        else:\n            self.summary.setText(\n                f"{len(groups)} dubbele groepen gevonden • {duplicate_files} overtollige bestanden"\n            )\n'''
    text = text.replace(old_summary, new_summary, 1)

# Show track duplicates with a clear header when group kind is present.
text = text.replace(
    '            header = QListWidgetItem(\n                f"DUBBEL GROEP {group_index}  •  {len(members)} IDENTIEKE BESTANDEN  •  {group[\'size\']:,} bytes"\n            )\n',
    '            kind = group.get("kind", "exact")\n            prefix = "MOGELIJK DUBBEL" if kind == "track" else "EXACT DUBBEL"\n            header = QListWidgetItem(\n                f"{prefix}  •  GROEP {group_index}  •  {len(members)} BESTANDEN"\n            )\n',
    1,
)

# Make closeEvent wait for the worker before destroying it.
if "def closeEvent(self, event):" not in text:
    marker = "    def delete_selected(self):\n"
    close_method = '''    def closeEvent(self, event):\n        worker = getattr(self, "worker", None)\n        if worker is not None and worker.isRunning():\n            try:\n                worker.request_stop()\n            except Exception:\n                try:\n                    worker.requestInterruption()\n                except Exception:\n                    pass\n            worker.wait(10000)\n        event.accept()\n\n'''
    if marker in text:
        text = text.replace(marker, close_method + marker, 1)

TARGET.write_text(text, encoding="utf-8-sig")
print("OK: duplicate cleaner patched for visible results and safe thread shutdown.")

from pathlib import Path
import re

p = Path("gui/mp3_duplicate_cleaner.py")
text = p.read_text(encoding="utf-8-sig")

# Replace the HashWorker with a worker that detects both exact file duplicates
# and likely track duplicates based on normalized artist/title/album data.
start = text.find("class HashWorker(QThread):")
end = text.find("\n\nclass MP3DuplicateCleaner", start)
if start == -1 or end == -1:
    raise SystemExit("HashWorker block not found")

worker = r'''class HashWorker(QThread):
    progress = Signal(int, int)
    finished_scan = Signal(list)
    failed = Signal(str)

    @staticmethod
    def normalize(value):
        value = str(value or "").strip().casefold()
        value = re.sub(r"\s+", " ", value)
        value = re.sub(r"[\[\(]\s*(original|extended|radio|club|remix|mix)\s*[\]\)]", "", value)
        return value.strip(" -_")

    def run(self):
        try:
            conn = get_connection()
            try:
                rows = conn.execute(
                    """
                    SELECT
                        m.id,
                        m.path,
                        m.artist,
                        m.title,
                        m.album,
                        m.year,
                        COALESCE(m.metadata_checked, 0),
                        EXISTS(
                            SELECT 1 FROM track_mp3 tm WHERE tm.mp3_id = m.id
                        ),
                        m.filesize,
                        m.duration,
                        m.bitrate
                    FROM mp3_files m
                    ORDER BY m.artist COLLATE NOCASE,
                             m.title COLLATE NOCASE,
                             m.path COLLATE NOCASE
                    """
                ).fetchall()
            finally:
                conn.close()

            total = len(rows)
            processed = 0
            candidates = []

            for row in rows:
                mp3_id, path, artist, title, album, year, checked, linked, filesize, duration, bitrate = row
                path_obj = Path(str(path or ""))
                if not path_obj.is_file():
                    processed += 1
                    self.progress.emit(processed, total)
                    continue

                candidates.append(
                    (mp3_id, str(path_obj), artist, title, album, year,
                     checked, linked, filesize, duration, bitrate)
                )
                processed += 1
                self.progress.emit(processed, total)

            by_track = {}
            by_hash = {}

            for item in candidates:
                key = (
                    self.normalize(item[2]),
                    self.normalize(item[3]),
                    str(item[9] or "").strip(),
                )
                if key[0] or key[1]:
                    by_track.setdefault(key, []).append(item)

                # Exact-content hash is kept as an additional strong signal.
                h = hashlib.sha256()
                try:
                    with open(item[1], "rb") as fh:
                        while True:
                            chunk = fh.read(1024 * 1024)
                            if not chunk:
                                break
                            h.update(chunk)
                    by_hash.setdefault(h.hexdigest(), []).append(item)
                except OSError:
                    pass

            groups = []
            seen_group_paths = set()

            # First show exact byte-for-byte duplicates.
            for sha256, members in by_hash.items():
                if len(members) < 2:
                    continue
                groups.append({
                    "kind": "exact",
                    "key": sha256,
                    "sha256": sha256,
                    "size": int(members[0][8] or 0),
                    "files": members,
                })
                seen_group_paths.update(x[1] for x in members)

            # Then show same-track candidates even when tags/bitrate/cover differ.
            for key, members in by_track.items():
                if len(members) < 2:
                    continue
                paths = {x[1] for x in members}
                if paths.issubset(seen_group_paths):
                    continue
                groups.append({
                    "kind": "track",
                    "key": "|".join(key),
                    "sha256": "",
                    "size": int(members[0][8] or 0),
                    "files": members,
                })

            self.finished_scan.emit(groups)
        except Exception as exc:
            self.failed.emit(str(exc))
'''

text = text[:start] + worker + text[end:]

# Make headers explain whether the group is exact or a track duplicate.
old = '''            header = QListWidgetItem(
                f"DUBBEL GROEP {group_index}  •  {len(members)} IDENTIEKE BESTANDEN  •  {group['size']:,} bytes"
            )
'''
new = '''            if group.get("kind") == "exact":
                group_type = "EXACT DUBBEL"
            else:
                group_type = "MOGELIJK DUBBELE TRACK"

            header = QListWidgetItem(
                f"DUBBEL GROEP {group_index}  •  {group_type}  •  {len(members)} BESTANDEN"
            )
'''
text = text.replace(old, new, 1)

# Summary should distinguish exact duplicates and track candidates.
old_summary = '''        self.summary.setText(
            f"{len(groups)} dubbele groepen gevonden • {duplicate_files} overtollige bestanden"
        )
'''
new_summary = '''        exact_count = sum(1 for group in groups if group.get("kind") == "exact")
        track_count = sum(1 for group in groups if group.get("kind") == "track")
        self.summary.setText(
            f"{exact_count} exacte dubbele groepen • "
            f"{track_count} dubbele track-kandidaten • "
            f"{duplicate_files} overtollige bestanden"
        )
'''
text = text.replace(old_summary, new_summary, 1)

p.write_text(text, encoding="utf-8-sig")
print("OK: duplicate cleaner toont nu exacte dubbels én dubbele track-kandidaten.")

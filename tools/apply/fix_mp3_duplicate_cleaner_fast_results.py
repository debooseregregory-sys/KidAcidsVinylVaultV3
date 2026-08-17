from pathlib import Path
import re

p = Path("gui/mp3_duplicate_cleaner.py")
text = p.read_text(encoding="utf-8-sig")

pattern = re.compile(r"    def run\(self\):.*?(?=\n\nclass MP3DuplicateCleaner)", re.S)

replacement = '''    def run(self):
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
            candidates = []

            for processed, row in enumerate(rows, 1):
                if self.isInterruptionRequested():
                    return

                (
                    mp3_id, path, artist, title, album, year,
                    checked, linked, filesize, duration, bitrate,
                ) = row

                path_text = str(path or "")
                if not Path(path_text).is_file():
                    self.progress.emit(processed, total)
                    continue

                candidates.append(
                    (
                        mp3_id, path_text, artist, title, album, year,
                        checked, linked, filesize, duration, bitrate,
                    )
                )
                self.progress.emit(processed, total)

            # First find likely duplicate tracks quickly. Do NOT hash the
            # entire MP3 library before showing anything.
            by_track = {}
            for item in candidates:
                artist = self.normalize(item[2])
                title = self.normalize(item[3])
                if not artist or not title:
                    continue

                try:
                    duration = float(item[9]) if item[9] not in (None, "") else None
                except (TypeError, ValueError):
                    duration = None

                by_track.setdefault((artist, title), []).append((item, duration))

            groups = []
            seen_ids = set()

            for key, members in by_track.items():
                if len(members) < 2:
                    continue

                # Split by duration so different remixes/edits are less likely
                # to be mixed together. Missing durations remain in the group.
                duration_groups = []
                for item, duration in members:
                    placed = False
                    for group in duration_groups:
                        reference = group[0][1]
                        if duration is None or reference is None or abs(duration - reference) <= 2.0:
                            group.append((item, duration))
                            placed = True
                            break
                    if not placed:
                        duration_groups.append([(item, duration)])

                for duration_group in duration_groups:
                    if len(duration_group) < 2:
                        continue

                    files = [item for item, _ in duration_group]
                    ids = {int(item[0]) for item in files}
                    if ids.issubset(seen_ids):
                        continue

                    groups.append({
                        "kind": "track",
                        "key": "|||".join(key),
                        "sha256": "",
                        "size": int(files[0][8] or 0),
                        "files": files,
                    })
                    seen_ids.update(ids)

            # Now calculate SHA-256 only for the candidate files. This keeps
            # the UI responsive while still marking truly identical files.
            for group in groups:
                members = group["files"]
                by_hash = {}
                for item in members:
                    if self.isInterruptionRequested():
                        return
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
                        continue

                exact = next(
                    (members_for_hash for members_for_hash in by_hash.values() if len(members_for_hash) > 1),
                    None,
                )
                if exact:
                    group["kind"] = "exact"
                    group["sha256"] = hashlib.sha256(
                        Path(exact[0][1]).read_bytes()
                    ).hexdigest() if Path(exact[0][1]).is_file() else ""

            self.finished_scan.emit(groups)
        except Exception as exc:
            self.failed.emit(str(exc))
'''

new_text, count = pattern.subn(replacement, text, count=1)
if count != 1:
    raise SystemExit("HashWorker.run() niet gevonden")

p.write_text(new_text, encoding="utf-8-sig")
print("OK: duplicate scanner toont track-dubbels eerst en hasht alleen kandidaten.")

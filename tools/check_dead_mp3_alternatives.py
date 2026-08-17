from pathlib import Path
import re
import sqlite3
import unicodedata

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "vinylvault.db"


def norm(value):
    value = value or ""
    value = unicodedata.normalize("NFKD", str(value))
    value = value.encode("ascii", "ignore").decode("ascii")
    value = value.lower()
    value = value.replace("_", " ")
    value = re.sub(r"[^a-z0-9]+", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def score(target_artist, target_title, row):
    ta = norm(target_artist)
    tt = norm(target_title)
    ra = norm(row["artist"])
    rt = norm(row["title"])
    fn = norm(Path(row["path"]).stem)
    value = 0
    if ta and ra == ta:
        value += 60
    elif ta and ta in ra or ra and ra in ta:
        value += 35
    if tt and rt == tt:
        value += 70
    elif tt and tt in rt or rt and rt in tt:
        value += 40
    combined = f"{ra} {rt}".strip()
    target = f"{ta} {tt}".strip()
    if target and target in fn:
        value += 25
    if tt and tt in fn:
        value += 15
    return value


def main():
    if not DB_PATH.exists():
        raise SystemExit(f"Database niet gevonden: {DB_PATH}")

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(
            """
            SELECT
                tm.id AS link_id,
                tm.mp3_id,
                t.id AS track_id,
                t.artist AS track_artist,
                t.title AS track_title,
                r.id AS release_id,
                r.artist AS release_artist,
                r.title AS release_title,
                m.path AS dead_path,
                m.filename AS dead_filename,
                m.artist AS dead_artist,
                m.title AS dead_title
            FROM track_mp3 tm
            JOIN tracks t ON t.id = tm.track_id
            JOIN releases r ON r.id = t.release_id
            JOIN mp3_files m ON m.id = tm.mp3_id
            WHERE m.path LIKE '%21. Discogs Database%'
              AND tm.id IN (
                    SELECT tm2.id
                    FROM track_mp3 tm2
                    JOIN mp3_files m2 ON m2.id = tm2.mp3_id
                    WHERE m2.path NOT LIKE ''
                )
            """
        ).fetchall()

        dead = []
        for row in rows:
            if Path(row["dead_path"]).exists():
                continue
            dead.append(row)

        print("=" * 110)
        print("VINYLVAULT - ALTERNATIEVEN VOOR DODE MP3-KOPPELINGEN")
        print("=" * 110)
        print(f"Dode koppelingen onderzocht : {len(dead)}")

        all_mp3 = conn.execute(
            """
            SELECT id, path, filename, artist, title, album
            FROM mp3_files
            WHERE path IS NOT NULL AND path <> ''
            """
        ).fetchall()

        for row in dead:
            print("\n" + "-" * 110)
            print(
                f"RELEASE {row['release_id']} | {row['release_artist']} - {row['release_title']} | "
                f"TRACK {row['track_id']} | {row['track_artist'] or ''} / {row['track_title'] or ''}"
            )
            print(f"DODE MP3 : {row['dead_filename']} | {row['dead_path']}")

            candidates = []
            target_artist = row["track_artist"] or row["release_artist"] or ""
            target_title = row["track_title"] or row["dead_title"] or Path(row["dead_filename"] or row["dead_path"]).stem

            for candidate in all_mp3:
                if candidate["id"] == row["mp3_id"]:
                    continue
                if not Path(candidate["path"]).exists():
                    continue
                s = score(target_artist, target_title, candidate)
                if s >= 60:
                    candidates.append((s, candidate))

            candidates.sort(key=lambda item: (-item[0], item[1]["path"].lower()))

            if not candidates:
                print("ALTERNATIEVEN : GEEN")
                continue

            print(f"ALTERNATIEVEN : {len(candidates)}")
            for s, candidate in candidates[:10]:
                print(
                    f"  SCORE {s:3d} | MP3 {candidate['id']} | "
                    f"{candidate['artist']} - {candidate['title']} | {candidate['filename']} | {candidate['path']}"
                )

        print("\n" + "=" * 110)
        print("DATABASE GEWIJZIGD : NEE")
        print("=" * 110)
    finally:
        conn.close()


if __name__ == "__main__":
    main()

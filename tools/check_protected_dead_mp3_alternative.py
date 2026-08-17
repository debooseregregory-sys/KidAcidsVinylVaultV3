from pathlib import Path
import sqlite3
import unicodedata

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "vinylvault.db"
MP3_ROOT = Path(r"D:\01. MP3's")

TARGET_LINK_ID = 3245


def norm(value):
    value = unicodedata.normalize("NFKC", value or "")
    return " ".join(value.replace("–", "-").replace("—", "-").split()).casefold()


def main():
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    try:
        row = con.execute(
            """
            SELECT
                tm.id AS link_id,
                tm.mp3_id,
                t.id AS track_id,
                t.position,
                t.artist AS track_artist,
                t.title AS track_title,
                r.id AS release_id,
                r.artist AS release_artist,
                r.title AS release_title,
                m.path,
                m.filename,
                m.artist AS mp3_artist,
                m.title AS mp3_title,
                m.duration
            FROM track_mp3 tm
            JOIN tracks t ON t.id = tm.track_id
            JOIN releases r ON r.id = t.release_id
            JOIN mp3_files m ON m.id = tm.mp3_id
            WHERE tm.id = ?
            """,
            (TARGET_LINK_ID,),
        ).fetchone()

        if not row:
            raise SystemExit(f"Link {TARGET_LINK_ID} niet gevonden")

        print("=" * 100)
        print("VINYLVAULT - BESCHERMDE DODE MP3-LINK")
        print("=" * 100)
        print(f"Release : {row['release_id']} | {row['release_artist']} - {row['release_title']}")
        print(f"Track   : {row['track_id']} | {row['position']} {row['track_title']}")
        print(f"MP3     : {row['filename']}")
        print(f"Pad     : {row['path']}")
        print(f"Duur    : {row['duration']}")
        print()

        candidates = []
        for path in MP3_ROOT.rglob("*.mp3"):
            if not path.is_file():
                continue
            filename = path.name
            if norm(filename) == norm(row['filename']):
                candidates.append((path, "EXACTE BESTANDSNAAM"))
                continue
            if norm(row['title']) and norm(row['title']) in norm(filename):
                candidates.append((path, "TITEL IN BESTANDSNAAM"))

        unique = []
        seen = set()
        for path, reason in candidates:
            key = str(path).casefold()
            if key not in seen:
                seen.add(key)
                unique.append((path, reason))

        print("KANDIDATEN OP SCHIJF:", len(unique))
        for path, reason in unique[:100]:
            print(f"  {reason}: {path}")

        print()
        print("DATABASE GEWIJZIGD : NEE")
        print("=" * 100)
    finally:
        con.close()


if __name__ == "__main__":
    main()

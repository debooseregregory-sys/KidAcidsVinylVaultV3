from pathlib import Path
import sqlite3
import unicodedata
import re

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "vinylvault.db"
MP3_ROOT = Path(r"D:\01. MP3's")
TARGET_LINK_ID = 3245


def norm(value):
    value = unicodedata.normalize("NFKD", value or "").encode("ascii", "ignore").decode("ascii")
    value = value.replace("–", "-").replace("—", "-")
    value = re.sub(r"[^a-z0-9]+", " ", value.casefold())
    return " ".join(value.split())


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
        print(f"Duur    : {row['duration'] or 0}")
        print()

        target_filename = norm(row['filename'])
        target_title = norm(row['track_title'])
        target_artist = norm(row['track_artist'] or row['release_artist'])

        candidates = []
        for path in MP3_ROOT.rglob("*.mp3"):
            if not path.is_file():
                continue
            n = norm(path.name)
            score = 0
            reason = []
            if n == target_filename:
                score = 100
                reason.append("EXACTE BESTANDSNAAM")
            else:
                if target_title and target_title in n:
                    score += 55
                    reason.append("TITEL")
                if target_artist and target_artist in n:
                    score += 35
                    reason.append("ARTIST")
                title_tokens = [x for x in target_title.split() if len(x) >= 3]
                hits = sum(1 for x in title_tokens if x in n)
                if hits:
                    score += min(10, hits * 2)
                    reason.append(f"{hits} TITELTOKENS")
            if score > 0:
                candidates.append((score, ", ".join(reason), path))

        candidates.sort(key=lambda x: (-x[0], str(x[2]).lower()))

        print("KANDIDATEN OP SCHIJF:", len(candidates))
        for score, reason, path in candidates[:100]:
            print(f"  SCORE {score:3d} | {reason:25s} | {path}")

        print()
        print("DATABASE GEWIJZIGD : NEE")
        print("=" * 100)
    finally:
        con.close()


if __name__ == "__main__":
    main()

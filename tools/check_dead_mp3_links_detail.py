from pathlib import Path
import sqlite3

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "vinylvault.db"
MP3_ROOT = Path(r"D:\01. MP3's")


def main():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(
            """
            SELECT
                tm.id AS link_id,
                tm.track_id,
                tm.mp3_id,
                tm.score,
                tm.is_preferred,
                tm.manually_added,
                r.id AS release_id,
                r.artist AS release_artist,
                r.title AS release_title,
                r.checked,
                t.position,
                t.artist AS track_artist,
                t.title AS track_title,
                m.path,
                m.filename
            FROM track_mp3 tm
            JOIN tracks t ON t.id = tm.track_id
            JOIN releases r ON r.id = t.release_id
            JOIN mp3_files m ON m.id = tm.mp3_id
            ORDER BY r.artist COLLATE NOCASE, r.title COLLATE NOCASE, t.position, tm.id
            """
        ).fetchall()

        by_track = {}
        dead = []
        for row in rows:
            exists = Path(row["path"]).exists()
            by_track.setdefault(row["track_id"], []).append((row, exists))
            if not exists:
                dead.append(row)

        print("=" * 100)
        print("VINYLVAULT - DETAIL OVER DE LAATSTE DODE MP3-KOPPELINGEN")
        print("=" * 100)
        print(f"Dode koppelingen gevonden : {len(dead)}")
        print()

        for row in dead:
            print(
                f"RELEASE {row['release_id']} | {row['release_artist']} - {row['release_title']} | "
                f"TRACK {row['track_id']} | {row['position']} {row['track_title']}"
            )
            print(f"  DODE LINK : {row['link_id']} | MP3 {row['mp3_id']} | {row['path']}")
            print(f"  checked   : {row['checked']} | preferred={row['is_preferred']} | manual={row['manually_added']} | score={row['score']}")

            siblings = by_track.get(row["track_id"], [])
            valid_siblings = [item[0] for item in siblings if item[1]]
            other_dead = [item[0] for item in siblings if not item[1] and item[0]["link_id"] != row["link_id"]]

            if valid_siblings:
                print(f"  ANDERE GELDIGE KOPPELINGEN : {len(valid_siblings)}")
                for item in valid_siblings:
                    print(
                        f"    MP3 {item['mp3_id']} | preferred={item['is_preferred']} | "
                        f"manual={item['manually_added']} | {item['path']}"
                    )
            else:
                print("  ANDERE GELDIGE KOPPELINGEN : 0")

            if other_dead:
                print(f"  ANDERE DODE KOPPELINGEN     : {len(other_dead)}")

            print("-" * 100)

        print()
        print("DATABASE GEWIJZIGD : NEE")
        print("=" * 100)
    finally:
        conn.close()


if __name__ == "__main__":
    main()

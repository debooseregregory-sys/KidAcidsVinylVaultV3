from pathlib import Path
import sqlite3
from collections import Counter

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "vinylvault.db"


def norm_year(value):
    try:
        y = int(value)
        return y if 1900 <= y <= 2100 else None
    except (TypeError, ValueError):
        return None


def main():
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    try:
        releases = con.execute(
            """
            SELECT id, artist, title
            FROM releases
            WHERE year IS NULL OR year = 0
            ORDER BY artist COLLATE NOCASE, title COLLATE NOCASE, id
            """
        ).fetchall()

        reliable = []
        mixed = []
        none = []

        for r in releases:
            rows = con.execute(
                """
                SELECT DISTINCT m.year
                FROM tracks t
                JOIN track_mp3 tm ON tm.track_id = t.id
                JOIN mp3_files m ON m.id = tm.mp3_id
                WHERE t.release_id = ? AND m.year IS NOT NULL AND m.year != 0
                """,
                (r['id'],),
            ).fetchall()
            years = sorted({norm_year(x['year']) for x in rows if norm_year(x['year'])})
            if len(years) == 1:
                reliable.append((r['id'], r['artist'], r['title'], years[0]))
            elif len(years) > 1:
                mixed.append((r['id'], r['artist'], r['title'], years))
            else:
                none.append((r['id'], r['artist'], r['title']))

        print("=" * 78)
        print("VINYLVAULT - BRONNEN VOOR ONTBREKEND JAAR")
        print("=" * 78)
        print(f"Releases zonder jaar        : {len(releases)}")
        print(f"1 betrouwbaar MP3-jaar      : {len(reliable)}")
        print(f"Meerdere verschillende jaren: {len(mixed)}")
        print(f"Geen MP3-jaar beschikbaar  : {len(none)}")
        print("Database gewijzigd          : NEE")
        print("=" * 78)
        print("VOORBEELDEN BETROUWBAAR")
        for item in reliable[:30]:
            print(f"{item[0]} | {item[1]} - {item[2]} | JAAR={item[3]}")
        print("=" * 78)
        print("VOORBEELDEN GEMENGD")
        for item in mixed[:20]:
            print(f"{item[0]} | {item[1]} - {item[2]} | JAREN={','.join(map(str,item[3]))}")

    finally:
        con.close()


if __name__ == "__main__":
    main()

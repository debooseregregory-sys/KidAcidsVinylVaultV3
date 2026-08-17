from pathlib import Path
import sqlite3

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "vinylvault.db"
OUT_DIR = BASE_DIR / "reports"
OUT_FILE = OUT_DIR / "mp3_link_coverage.txt"


def main():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(
            """
            SELECT
                t.id AS track_id,
                t.release_id,
                t.position,
                t.artist,
                t.title,
                COUNT(tm.id) AS total_links,
                SUM(CASE WHEN m.id IS NOT NULL AND (m.path IS NOT NULL) THEN 1 ELSE 0 END) AS existing_rows
            FROM tracks t
            LEFT JOIN track_mp3 tm ON tm.track_id = t.id
            LEFT JOIN mp3_files m ON m.id = tm.mp3_id
            GROUP BY t.id
            ORDER BY t.release_id, t.id
            """
        ).fetchall()

        only_missing = []
        mixed = []
        no_links = []
        has_valid = []

        for r in rows:
            total = int(r["total_links"] or 0)
            valid = int(r["existing_rows"] or 0)
            if total == 0:
                no_links.append(r)
            elif valid == 0:
                only_missing.append(r)
            elif valid < total:
                mixed.append(r)
            else:
                has_valid.append(r)

        OUT_DIR.mkdir(parents=True, exist_ok=True)
        with OUT_FILE.open("w", encoding="utf-8") as f:
            f.write("VINYLVAULT - MP3 LINK COVERAGE\n")
            f.write("=" * 72 + "\n\n")
            f.write(f"Tracks totaal       : {len(rows)}\n")
            f.write(f"Tracks zonder link  : {len(no_links)}\n")
            f.write(f"Tracks alleen oud   : {len(only_missing)}\n")
            f.write(f"Tracks gemengd      : {len(mixed)}\n")
            f.write(f"Tracks volledig OK  : {len(has_valid)}\n\n")

            f.write("TRACKS MET ALLEEN ONGELDIGE LINKS\n")
            f.write("-" * 72 + "\n")
            for r in only_missing:
                f.write(f"{r['track_id']};{r['release_id']};{r['position'] or ''};{r['artist'] or ''};{r['title'] or ''};{r['total_links']}\n")

            f.write("\nTRACKS MET ZOWEL GELDIGE ALS ONGELDIGE LINKS\n")
            f.write("-" * 72 + "\n")
            for r in mixed:
                f.write(f"{r['track_id']};{r['release_id']};{r['position'] or ''};{r['artist'] or ''};{r['title'] or ''};links={r['total_links']};geldig={r['existing_rows']}\n")

        print("=" * 72)
        print("VINYLVAULT - MP3 LINK COVERAGE")
        print("=" * 72)
        print(f"Tracks totaal      : {len(rows)}")
        print(f"Zonder MP3-link    : {len(no_links)}")
        print(f"Alleen oude links  : {len(only_missing)}")
        print(f"Gemengde links     : {len(mixed)}")
        print(f"Volledig geldig    : {len(has_valid)}")
        print(f"Rapport            : {OUT_FILE}")
        print("Database gewijzigd : NEE")
        print("=" * 72)
    finally:
        conn.close()


if __name__ == "__main__":
    main()

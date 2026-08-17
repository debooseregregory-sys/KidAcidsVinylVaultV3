from pathlib import Path
import sqlite3
from collections import Counter

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "vinylvault.db"
MP3_ROOT = Path(r"D:\01. MP3's")
REPORT_DIR = BASE_DIR / "reports"
REPORT_FILE = REPORT_DIR / "missing_mp3_paths.txt"


def main():
    if not DB_PATH.exists():
        raise SystemExit(f"Database niet gevonden: {DB_PATH}")

    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row

    try:
        rows = connection.execute(
            """
            SELECT
                tm.id AS link_id,
                tm.track_id,
                t.position,
                t.artist AS track_artist,
                t.title AS track_title,
                m.path,
                m.filename,
                r.id AS release_id,
                r.artist AS release_artist,
                r.title AS release_title
            FROM track_mp3 tm
            JOIN tracks t ON t.id = tm.track_id
            JOIN mp3_files m ON m.id = tm.mp3_id
            JOIN releases r ON r.id = t.release_id
            ORDER BY r.id, t.id, tm.id
            """
        ).fetchall()

        missing = []
        existing = []
        folder_counts = Counter()

        for row in rows:
            raw_path = (row["path"] or "").strip()
            path = Path(raw_path)

            if path.exists():
                existing.append(row)
                continue

            missing.append(row)
            try:
                rel = path.relative_to(MP3_ROOT)
                folder = rel.parent.as_posix() or "."
            except ValueError:
                folder = "<buiten D:\\01. MP3's>"
            except Exception:
                folder = "<onbekende map>"
            folder_counts[folder] += 1

        REPORT_DIR.mkdir(parents=True, exist_ok=True)
        with REPORT_FILE.open("w", encoding="utf-8") as handle:
            handle.write("VINYLVAULT - ONTBREKENDE MP3 PADEN\n")
            handle.write("=" * 78 + "\n\n")
            handle.write(f"Totaal track_mp3 koppelingen : {len(rows)}\n")
            handle.write(f"Bestaand bestand             : {len(existing)}\n")
            handle.write(f"Bestand ontbreekt             : {len(missing)}\n\n")
            handle.write("ONTBREKENDE PADEN PER MAP\n")
            handle.write("-" * 78 + "\n")
            for folder, count in folder_counts.most_common():
                handle.write(f"{count:6d}  {folder}\n")

            handle.write("\nDETAILS\n")
            handle.write("-" * 78 + "\n")
            for row in missing:
                handle.write(
                    f"[{row['release_id']}] {row['release_artist']} - {row['release_title']} | "
                    f"{row['position'] or '?'} {row['track_title'] or '[GEEN TITEL]'}\n"
                )
                handle.write(f"  MP3: {row['filename'] or '[GEEN NAAM]'}\n")
                handle.write(f"  Pad: {row['path'] or '[GEEN PAD]'}\n\n")

        print("=" * 78)
        print("VINYLVAULT - MP3 PADEN CONTROLE")
        print("=" * 78)
        print(f"Track_MP3 koppelingen : {len(rows)}")
        print(f"Bestand bestaat       : {len(existing)}")
        print(f"Bestand ontbreekt     : {len(missing)}")
        print("\nONTBREKENDE BESTANDEN PER MAP:")
        for folder, count in folder_counts.most_common(20):
            print(f"  {count:6d}  {folder}")
        print(f"\nRapport: {REPORT_FILE}")
        print("Database gewijzigd: NEE")
        print("=" * 78)

    finally:
        connection.close()


if __name__ == "__main__":
    main()

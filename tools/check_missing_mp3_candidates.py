from pathlib import Path
import sqlite3
import unicodedata
import re

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "vinylvault.db"
MP3_ROOT = Path(r"D:\01. MP3's")

TARGETS = [
    "Slam - Positive Education.mp3",
    "Aphex  Twin - Flap Head.mp3",
    "7 PM â€“ Our Minds (Original).mp3",
]


def norm(value):
    value = unicodedata.normalize("NFKC", str(value or ""))
    value = value.replace("–", "-").replace("—", "-").replace("â€“", "-")
    value = value.replace("’", "'").replace("“", '"').replace("”", '"')
    value = re.sub(r"\s+", " ", value).strip().lower()
    return value


def main():
    print("=" * 90)
    print("VINYLVAULT - MP3 KANDIDATENCONTROLE")
    print("=" * 90)
    print(f"MP3 root: {MP3_ROOT}")

    if not MP3_ROOT.exists():
        raise SystemExit(f"MP3 map niet gevonden: {MP3_ROOT}")

    files = [p for p in MP3_ROOT.rglob("*.mp3") if p.is_file()]
    print(f"MP3 bestanden gevonden: {len(files)}")
    print()

    db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row
    try:
        rows = db.execute(
            """
            SELECT r.id AS release_id, r.artist, r.title AS release_title,
                   t.id AS track_id, t.position, t.title AS track_title,
                   m.path AS stored_path
            FROM track_mp3 tm
            JOIN tracks t ON t.id = tm.track_id
            JOIN releases r ON r.id = t.release_id
            JOIN mp3_files m ON m.id = tm.mp3_id
            WHERE m.path LIKE '%21. Discogs Database%'
               OR m.path LIKE '%23. Discogs Database%'
            ORDER BY r.id, t.id
            """
        ).fetchall()

        for row in rows:
            if row["track_title"]:
                expected = row["track_title"]
                print(f"Track {row['track_id']}: {row['artist']} / {expected}")

        print("\nSPECIFIEKE BESTANDSNAAM-KANDIDATEN")
        print("-" * 90)
        for target in TARGETS:
            nt = norm(target)
            candidates = [p for p in files if norm(p.name) == nt]
            fuzzy = [p for p in files if norm(Path(p).stem) == norm(Path(target).stem)]
            print(f"\nTARGET: {target}")
            print(f"exacte kandidaten: {len(candidates)}")
            for p in candidates[:20]:
                print(f"  {p}")
            if not candidates:
                print(f"fuzzy kandidaten: {len(fuzzy)}")
                for p in fuzzy[:20]:
                    print(f"  {p}")

        print("\nDATABASE GEWIJZIGD: NEE")
        print("=" * 90)
    finally:
        db.close()


if __name__ == "__main__":
    main()

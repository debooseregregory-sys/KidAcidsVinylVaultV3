from pathlib import Path
import shutil
import sqlite3
from datetime import datetime

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "vinylvault.db"
MP3_ROOT = Path(r"D:\01. MP3's")
OLD_FOLDER = "23. Discogs Database"
NEW_FOLDER = "21. Discogs Database"


def main():
    old_dir = MP3_ROOT / OLD_FOLDER
    new_dir = MP3_ROOT / NEW_FOLDER

    if old_dir.exists():
        raise SystemExit(f"STOP: map 23 bestaat nog: {old_dir}")
    if not new_dir.exists():
        raise SystemExit(f"STOP: map 21 niet gevonden: {new_dir}")
    if not DB_PATH.exists():
        raise SystemExit(f"Database niet gevonden: {DB_PATH}")

    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row

    try:
        rows = connection.execute(
            "SELECT id, path FROM mp3_files WHERE path LIKE ? ORDER BY id",
            (f"%{OLD_FOLDER}%",),
        ).fetchall()

        print("=" * 72)
        print("VINYLVAULT - MP3 PADEN 23 -> 21")
        print("=" * 72)
        print(f"Databasepaden gevonden : {len(rows)}")

        if not rows:
            print("Geen oude databasepaden gevonden. Niets te wijzigen.")
            return

        missing = []
        for row in rows:
            new_path = Path(str(row["path"]).replace(OLD_FOLDER, NEW_FOLDER))
            if not new_path.exists():
                missing.append((row["id"], new_path))

        print(f"Bestanden gevonden      : {len(rows) - len(missing)}")
        print(f"Bestanden niet gevonden : {len(missing)}")

        backup_dir = BASE_DIR / "reports" / "db_backups"
        backup_dir.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = backup_dir / f"vinylvault_before_23_to_21_{stamp}.db"
        shutil.copy2(DB_PATH, backup_path)

        for row in rows:
            new_path = str(row["path"]).replace(OLD_FOLDER, NEW_FOLDER)
            connection.execute(
                "UPDATE mp3_files SET path = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (new_path, row["id"]),
            )

        connection.commit()

        remaining = connection.execute(
            "SELECT COUNT(*) FROM mp3_files WHERE path LIKE ?",
            (f"%{OLD_FOLDER}%",),
        ).fetchone()[0]

        print(f"Database aangepast      : {len(rows)}")
        print(f"Oude paden over         : {remaining}")
        print(f"Backup                   : {backup_path}")
        print("track_mp3 gewijzigd      : NEE")
        print("scores gewijzigd        : NEE")
        print("preferred gewijzigd     : NEE")
        print("releases gewijzigd      : NEE")

        if missing:
            print()
            print("LET OP: deze 3 databasepaden verwijzen naar bestanden die niet in map 21 gevonden zijn:")
            for mp3_id, new_path in missing:
                print(f"  MP3 {mp3_id}: {new_path}")

        print("=" * 72)

    finally:
        connection.close()


if __name__ == "__main__":
    main()

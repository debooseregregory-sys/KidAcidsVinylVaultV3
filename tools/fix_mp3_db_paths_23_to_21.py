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
        raise SystemExit(
            f"STOP: oude map bestaat nog: {old_dir}\n"
            "Verwijder/verplaats de map 23 eerst."
        )

    if not new_dir.exists():
        raise SystemExit(f"STOP: nieuwe map niet gevonden: {new_dir}")

    if not DB_PATH.exists():
        raise SystemExit(f"Database niet gevonden: {DB_PATH}")

    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row

    try:
        rows = connection.execute(
            """
            SELECT id, path
            FROM mp3_files
            WHERE path LIKE ?
            ORDER BY id
            """,
            (f"%{OLD_FOLDER}%",),
        ).fetchall()

        print("=" * 72)
        print("VINYLVAULT - MP3 PADEN 23 -> 21")
        print("=" * 72)
        print(f"Oude databasepaden : {len(rows)}")
        print("Oude map bestaat   : NEE")
        print("Nieuwe map bestaat : JA")
        print()

        if not rows:
            print("Geen databasepaden naar 23 gevonden.")
            return

        missing_files = []
        for row in rows:
            old_path = Path(row["path"])
            new_path = Path(str(old_path).replace(OLD_FOLDER, NEW_FOLDER))
            if not new_path.exists():
                missing_files.append((row["id"], old_path, new_path))

        print(f"Nieuwe bestanden gevonden : {len(rows) - len(missing_files)}")
        print(f"Nieuwe bestanden ontbreken: {len(missing_files)}")

        if missing_files:
            print()
            print("STOP: er zijn databasepaden waarvoor het bestand niet in 21 staat.")
            for link_id, old_path, new_path in missing_files[:50]:
                print(f"  MP3 {link_id}: {new_path}")
            if len(missing_files) > 50:
                print(f"  ... en nog {len(missing_files) - 50}")
            return

        backup_dir = BASE_DIR / "reports" / "db_backups"
        backup_dir.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = backup_dir / f"vinylvault_before_23_to_21_{stamp}.db"
        shutil.copy2(DB_PATH, backup_path)

        updates = 0
        for row in rows:
            new_path = str(row["path"]).replace(OLD_FOLDER, NEW_FOLDER)
            connection.execute(
                "UPDATE mp3_files SET path = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (new_path, row["id"]),
            )
            updates += 1

        connection.commit()

        remaining = connection.execute(
            "SELECT COUNT(*) FROM mp3_files WHERE path LIKE ?",
            (f"%{OLD_FOLDER}%",),
        ).fetchone()[0]

        print()
        print(f"Database aangepast          : {updates}")
        print(f"Oude paden over             : {remaining}")
        print(f"Backup                      : {backup_path}")
        print("Koppelingstabellen gewijzigd: NEE")
        print("track_mp3 scores gewijzigd  : NEE")
        print("preferred-status gewijzigd  : NEE")
        print("=" * 72)

    finally:
        connection.close()


if __name__ == "__main__":
    main()

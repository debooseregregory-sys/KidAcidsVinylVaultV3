from pathlib import Path
from datetime import datetime
import shutil
import sqlite3
import sys

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "vinylvault.db"
MP3_ROOT = Path(r"D:\01. MP3's")
OLD_DIR = MP3_ROOT / "23. Discogs Database"
NEW_DIR = MP3_ROOT / "21. Discogs Database"
BACKUP_DIR = BASE_DIR / "data" / "backup"


def main():
    print("=" * 78)
    print("VINYLVAULT - MP3 MAP 23 -> 21 HERSTEL")
    print("=" * 78)
    print(f"OUD : {OLD_DIR}")
    print(f"NIEUW: {NEW_DIR}")
    print()

    if not DB_PATH.exists():
        raise SystemExit(f"Database niet gevonden: {DB_PATH}")

    if not MP3_ROOT.exists():
        raise SystemExit(f"MP3-hoofdmap niet gevonden: {MP3_ROOT}")

    if not OLD_DIR.exists():
        raise SystemExit(f"Bronmap bestaat niet: {OLD_DIR}")

    if NEW_DIR.exists():
        raise SystemExit(
            "Doelmap bestaat al. Ik wijzig niets om overschrijven te voorkomen.\n"
            f"Doel: {NEW_DIR}"
        )

    files_in_old = [p for p in OLD_DIR.rglob("*") if p.is_file()]
    print(f"Bestanden in 23: {len(files_in_old)}")

    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row

    try:
        rows = connection.execute(
            """
            SELECT DISTINCT
                m.id,
                m.path,
                r.id AS release_id,
                r.artist,
                r.title,
                r.checked
            FROM mp3_files m
            JOIN track_mp3 tm ON tm.mp3_id = m.id
            JOIN tracks t ON t.id = tm.track_id
            JOIN releases r ON r.id = t.release_id
            WHERE m.path LIKE ?
            ORDER BY r.checked DESC, r.id, m.id
            """,
            (str(OLD_DIR) + r"\%",),
        ).fetchall()

        all_path_rows = connection.execute(
            "SELECT id, path FROM mp3_files WHERE path LIKE ?",
            (str(OLD_DIR) + r"\%",),
        ).fetchall()

        print(f"Database-paden naar 23: {len(all_path_rows)}")
        print(f"Gekoppelde releases: {len(rows)}")
        checked_ids = sorted({row['release_id'] for row in rows if int(row['checked'] or 0) == 1})
        unchecked_ids = sorted({row['release_id'] for row in rows if int(row['checked'] or 0) == 0})
        print(f"Daarvan KLAAR : {len(checked_ids)} releases")
        print(f"Daarvan niet-KLAAR: {len(unchecked_ids)} releases")
        print()

        print("Backup database maken...")
        BACKUP_DIR.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = BACKUP_DIR / f"vinylvault_before_mp3_23_to_21_{stamp}.db"
        shutil.copy2(DB_PATH, backup_path)
        print(f"Backup: {backup_path}")
        print()

        print("Map hernoemen...")
        OLD_DIR.rename(NEW_DIR)
        print(f"OK: {OLD_DIR.name} -> {NEW_DIR.name}")

        updated = 0
        try:
            for row in all_path_rows:
                old_path = Path(row["path"])
                try:
                    relative = old_path.relative_to(OLD_DIR)
                except ValueError:
                    old_text = str(row["path"])
                    old_prefix = str(OLD_DIR)
                    if old_text.startswith(old_prefix):
                        relative_text = old_text[len(old_prefix):].lstrip("\\/")
                        new_path = NEW_DIR / relative_text
                    else:
                        continue
                else:
                    new_path = NEW_DIR / relative

                connection.execute(
                    "UPDATE mp3_files SET path = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                    (str(new_path), row["id"]),
                )
                updated += 1

            connection.commit()
        except Exception:
            connection.rollback()
            raise

        missing_now = connection.execute(
            """
            SELECT COUNT(*)
            FROM mp3_files
            WHERE path LIKE ?
            """,
            (str(OLD_DIR) + r"\%",),
        ).fetchone()[0]

        new_db_paths = connection.execute(
            "SELECT COUNT(*) FROM mp3_files WHERE path LIKE ?",
            (str(NEW_DIR) + r"\%",),
        ).fetchone()[0]

        existing_new_files = 0
        for row in connection.execute(
            "SELECT path FROM mp3_files WHERE path LIKE ?",
            (str(NEW_DIR) + r"\%",),
        ).fetchall():
            if Path(row[0]).exists():
                existing_new_files += 1

        print()
        print("=" * 78)
        print("HERSTEL VOLTOOID")
        print("=" * 78)
        print(f"Map hernoemd        : JA")
        print(f"Database paden     : {updated}")
        print(f"Oude paden over    : {missing_now}")
        print(f"Nieuwe DB-paden    : {new_db_paths}")
        print(f"Bestaande bestanden: {existing_new_files}")
        print(f"Backup              : {backup_path}")
        print("Database gewijzigd  : JA")
        print("=" * 78)

        if new_db_paths != existing_new_files:
            print("WAARSCHUWING: niet elk aangepast databasepad bestaat fysiek op schijf.")
            print("De database is wel veilig geback-upt vóór de wijziging.")

    except Exception:
        connection.close()
        print()
        print("FOUT: wijziging mislukt. Controleer de backup en mapstatus.")
        raise
    finally:
        try:
            connection.close()
        except Exception:
            pass


if __name__ == "__main__":
    main()

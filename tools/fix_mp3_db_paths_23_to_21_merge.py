from pathlib import Path
import shutil
import sqlite3
from datetime import datetime

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "vinylvault.db"
ROOT = Path(r"D:\01. MP3's")
OLD = "23. Discogs Database"
NEW = "21. Discogs Database"


def main():
    old_dir = ROOT / OLD
    new_dir = ROOT / NEW
    if old_dir.exists():
        raise SystemExit(f"STOP: map 23 bestaat nog: {old_dir}")
    if not new_dir.exists():
        raise SystemExit(f"STOP: map 21 bestaat niet: {new_dir}")

    c = sqlite3.connect(DB_PATH)
    c.row_factory = sqlite3.Row
    try:
        rows = c.execute("SELECT id, path FROM mp3_files WHERE path LIKE ? ORDER BY id", (f"%{OLD}%",)).fetchall()
        print("=" * 80)
        print("VINYLVAULT - VEILIGE MP3 PADEN 23 -> 21")
        print("=" * 80)
        print(f"23-records : {len(rows)}")

        missing = []
        normal = []
        merges = []
        for row in rows:
            old_path = str(row["path"])
            new_path = old_path.replace(OLD, NEW)
            if not Path(new_path).exists():
                missing.append((row["id"], old_path, new_path))
                continue
            existing = c.execute("SELECT id FROM mp3_files WHERE path = ? AND id <> ?", (new_path, row["id"])).fetchone()
            if existing:
                old_id = row["id"]
                new_id = existing["id"]
                old_links = c.execute("SELECT COUNT(*) FROM track_mp3 WHERE mp3_id = ?", (old_id,)).fetchone()[0]
                new_links = c.execute("SELECT COUNT(*) FROM track_mp3 WHERE mp3_id = ?", (new_id,)).fetchone()[0]
                merges.append((old_id, new_id, old_links, new_links, old_path, new_path))
            else:
                normal.append((row["id"], new_path))

        print(f"Normale updates : {len(normal)}")
        print(f"Conflicten      : {len(merges)}")
        print(f"Ontbrekend      : {len(missing)}")
        for item in merges:
            print(f"MERGE {item[0]} -> {item[1]} | links oud={item[2]} nieuw={item[3]} | {item[5]}")
        for item in missing:
            print(f"ONTBREEKT {item[0]} | {item[2]}")

        backup_dir = BASE_DIR / "reports" / "db_backups"
        backup_dir.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup = backup_dir / f"vinylvault_before_23_to_21_merge_{stamp}.db"
        shutil.copy2(DB_PATH, backup)

        for old_id, new_id, old_links, new_links, old_path, new_path in merges:
            # Repoint links. In the current conflict model, this is safe because the existing row has zero links.
            if new_links != 0:
                raise SystemExit(f"STOP: conflict heeft al nieuwe links: old={old_id} new={new_id}")
            c.execute("UPDATE track_mp3 SET mp3_id = ? WHERE mp3_id = ?", (new_id, old_id))
            c.execute("DELETE FROM mp3_files WHERE id = ?", (old_id,))

        for mp3_id, new_path in normal:
            c.execute("UPDATE mp3_files SET path = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?", (new_path, mp3_id))

        c.commit()
        remaining = c.execute("SELECT COUNT(*) FROM mp3_files WHERE path LIKE ?", (f"%{OLD}%",)).fetchone()[0]
        print()
        print(f"Aangepast        : {len(normal)}")
        print(f"Gemerged         : {len(merges)}")
        print(f"Oude paden over  : {remaining}")
        print(f"Backup            : {backup}")
        print(f"track_mp3 scores gewijzigd : NEE")
        print(f"preferred gewijzigd          : NEE")
        print(f"Database gewijzigd            : JA")
        print("=" * 80)
    except Exception:
        c.rollback()
        raise
    finally:
        c.close()


if __name__ == "__main__":
    main()

from pathlib import Path
import sqlite3

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "vinylvault.db"
OLD = "23. Discogs Database"
NEW = "21. Discogs Database"

c = sqlite3.connect(DB_PATH)
c.row_factory = sqlite3.Row
try:
    rows = c.execute("SELECT id, path FROM mp3_files WHERE path LIKE ? ORDER BY id", (f"%{OLD}%",)).fetchall()
    conflicts = []
    for row in rows:
        new_path = str(row["path"]).replace(OLD, NEW)
        hit = c.execute("SELECT id, path, filename FROM mp3_files WHERE path = ? AND id <> ?", (new_path, row["id"])).fetchone()
        if hit:
            links_old = c.execute("SELECT COUNT(*) FROM track_mp3 WHERE mp3_id = ?", (row["id"],)).fetchone()[0]
            links_new = c.execute("SELECT COUNT(*) FROM track_mp3 WHERE mp3_id = ?", (hit["id"],)).fetchone()[0]
            conflicts.append((row["id"], hit["id"], row["path"], new_path, links_old, links_new))

    print("=" * 100)
    print("VINYLVAULT - MP3 23 -> 21 CONFLICTEN")
    print("=" * 100)
    print(f"23-paden             : {len(rows)}")
    print(f"Conflicten           : {len(conflicts)}")
    print("Database gewijzigd   : NEE")
    print("=" * 100)
    for a, b, old_path, new_path, old_links, new_links in conflicts:
        print(f"OLD MP3 {a} | links={old_links}")
        print(f"  {old_path}")
        print(f"NEW MP3 {b} | links={new_links}")
        print(f"  {new_path}")
        print("-" * 100)
finally:
    c.close()

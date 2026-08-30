import sqlite3
import os

DB = r".\data\vinylvault.db"

conn = sqlite3.connect(DB)

rows = conn.execute("""
    SELECT id, artist, title, cover
    FROM releases
    WHERE cover IS NOT NULL AND TRIM(cover) != ''
""").fetchall()

total = len(rows)
existing = 0
missing = 0

print("DATABASE COVERS:", total)
print()

for release_id, artist, title, cover in rows:
    if os.path.isfile(cover):
        existing += 1
    else:
        missing += 1

print("BESTAANDE BESTANDEN:", existing)
print("ONTBREKENDE BESTANDEN:", missing)

print()
print("EERSTE 20 ONTBREKENDE PADEN:")
print("-" * 80)

shown = 0

for release_id, artist, title, cover in rows:
    if not os.path.isfile(cover):
        print(f"ID: {release_id} | {artist} - {title}")
        print(f"DB: {cover}")
        shown += 1

        if shown >= 20:
            break

conn.close()
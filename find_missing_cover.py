import sqlite3
import os

DB = r".\data\vinylvault.db"

conn = sqlite3.connect(DB)

rows = conn.execute("""
    SELECT id, artist, title, cover
    FROM releases
    WHERE cover IS NOT NULL
      AND TRIM(cover) != ''
""").fetchall()

print("COVERS DIE NOG NIET GEVONDEN WORDEN:")
print("=" * 80)

found = 0

for release_id, artist, title, cover in rows:
    if not os.path.isfile(cover):
        print(f"ID     : {release_id}")
        print(f"Artist : {artist}")
        print(f"Title  : {title}")
        print(f"Cover  : {cover}")
        print()
        found += 1

print("=" * 80)
print(f"TOTAAL ONTBREKEND: {found}")

conn.close()
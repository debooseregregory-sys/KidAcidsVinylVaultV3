import sqlite3
import os

DB = r".\data\vinylvault.db"

print("=" * 80)
print("CONTROLE RELEASE 4497")
print("=" * 80)

print()
print("DATABASE:")
print(os.path.abspath(DB))

conn = sqlite3.connect(DB)

print()
print("RELEASES:")
print("-" * 80)

rows = conn.execute("""
    SELECT
        id,
        artist,
        title,
        discogs,
        storage_code
    FROM releases
    WHERE discogs = '4497'
""").fetchall()

for row in rows:
    print(row)

print()
print("TRACKS:")
print("-" * 80)

rows = conn.execute("""
    SELECT
        id,
        release_id,
        position,
        artist,
        title
    FROM tracks
    WHERE release_id IN (
        SELECT id
        FROM releases
        WHERE discogs = '4497'
    )
    ORDER BY id
""").fetchall()

for row in rows:
    print(row)

print()
print("TOTAAL TRACKS:", len(rows))

conn.close()

print()
print("=" * 80)
print("CONTROLE KLAAR")
print("=" * 80)

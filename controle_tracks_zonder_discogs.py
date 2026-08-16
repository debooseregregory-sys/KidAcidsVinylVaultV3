import sqlite3

db = r".\data\vinylvault.db"

c = sqlite3.connect(db)
c.row_factory = sqlite3.Row

rows = c.execute("""
SELECT
    t.id,
    t.artist,
    t.title,
    r.id AS release_id,
    r.title AS release_title,
    r.discogs,
    r.storage_code
FROM tracks t
JOIN releases r
    ON r.id = t.release_id
WHERE r.discogs IS NULL
   OR r.discogs = ''
ORDER BY t.id
LIMIT 20
""").fetchall()

print()
print("=" * 100)
print("TRACKS ZONDER DISCOGS RELEASE")
print("=" * 100)
print()

if not rows:
    print("GEEN TRACKS GEVONDEN.")
else:
    for r in rows:
        print(
            f"{r['id']} | "
            f"{r['artist']} | "
            f"{r['title']} | "
            f"Release ID: {r['release_id']} | "
            f"Release: {r['release_title']} | "
            f"Discogs: {r['discogs']} | "
            f"Kastcode: {r['storage_code']}"
        )

print()
print("TOTAAL:", len(rows))

c.close()

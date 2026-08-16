import sqlite3

c = sqlite3.connect(r".\data\vinylvault.db")

rows = c.execute("""
SELECT
    r.id,
    r.artist,
    r.title,
    r.discogs,
    r.storage_code,
    COUNT(t.id)
FROM releases r
LEFT JOIN tracks t ON t.release_id = r.id
WHERE r.title IS NULL OR TRIM(r.title) = ''
GROUP BY r.id
ORDER BY r.id
LIMIT 30
""").fetchall()

print("ID | ARTIST | TITLE | DISCOGS | KASTCODE | TRACKS")
print("-" * 100)

for r in rows:
    print(r)

print()
print("GETOOND:", len(rows))

c.close()

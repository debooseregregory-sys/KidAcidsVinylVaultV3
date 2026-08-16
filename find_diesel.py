from database.database import get_connection

c = get_connection()

print("=== ZOEK DIESEL DRUDGE IN ALLE MP3S ===")

rows = c.execute("""
SELECT
    id,
    artist,
    title,
    filename,
    path
FROM mp3_files
WHERE lower(title) LIKE '%diesel%'
   OR lower(title) LIKE '%drudge%'
ORDER BY artist, title
""").fetchall()

print("Aantal:", len(rows))

for row in rows:
    print(dict(row))

print()
print("=== ZOEK BOOSTER IN ALLE MP3S ===")

rows = c.execute("""
SELECT
    id,
    artist,
    title,
    filename,
    path
FROM mp3_files
WHERE lower(title) LIKE '%booster%'
ORDER BY artist, title
""").fetchall()

print("Aantal:", len(rows))

for row in rows:
    print(dict(row))

c.close()
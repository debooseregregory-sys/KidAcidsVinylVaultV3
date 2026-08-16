from database.database import get_connection

c = get_connection()

print("=== TRACKS PLANETARY ASSAULT SYSTEMS ===")

rows = c.execute("""
SELECT
    t.id,
    t.release_id,
    t.position,
    t.artist,
    t.title,
    t.duration,
    t.bpm,
    t.genre
FROM tracks t
JOIN releases r
    ON r.id = t.release_id
WHERE lower(r.artist) LIKE '%planetary assault systems%'
ORDER BY r.title, t.id
""").fetchall()

for row in rows:
    print(dict(row))

print()
print("=== MP3 FILES ===")

rows = c.execute("""
SELECT
    id,
    artist,
    title,
    filename,
    path
FROM mp3_files
WHERE lower(artist) LIKE '%planetary assault systems%'
ORDER BY title, filename
""").fetchall()

print("Aantal:", len(rows))

for row in rows:
    print(dict(row))

print()
print("=== BESTAANDE TRACK-MP3 LINKS ===")

rows = c.execute("""
SELECT
    tm.track_id,
    tm.mp3_id,
    t.position,
    t.title AS track_title,
    m.artist AS mp3_artist,
    m.title AS mp3_title,
    m.filename,
    m.path
FROM track_mp3 tm
JOIN tracks t
    ON t.id = tm.track_id
JOIN mp3_files m
    ON m.id = tm.mp3_id
JOIN releases r
    ON r.id = t.release_id
WHERE lower(r.artist) LIKE '%planetary assault systems%'
ORDER BY t.id, m.id
""").fetchall()

print("Links:", len(rows))

for row in rows:
    print(dict(row))

c.close()

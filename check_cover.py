import sqlite3

conn = sqlite3.connect(r"data\vinylvault.db")

row = conn.execute("""
SELECT id, artist, title, discogs, cover
FROM releases
WHERE discogs = '5942009'
""").fetchone()

print(row)

conn.close()

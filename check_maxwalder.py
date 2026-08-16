import sqlite3

c = sqlite3.connect("data/vinylvault.db")

rows = c.execute(
    """
    SELECT id, artist, title, discogs, catalog
    FROM releases
    WHERE artist LIKE ?
       OR title LIKE ?
    """,
    ("%Max Walder%", "%I Can Be Hard%")
).fetchall()

for row in rows:
    print(row)

c.close()
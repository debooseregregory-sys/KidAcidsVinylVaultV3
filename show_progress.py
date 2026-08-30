import sqlite3

db = r".\data\vinylvault.db"

c = sqlite3.connect(db)
c.row_factory = sqlite3.Row

rows = c.execute("""
SELECT id, artist, title, storage_code, checked, media_type
FROM releases
WHERE storage_code != ''
ORDER BY id
LIMIT 20
""").fetchall()

for r in rows:
    print(dict(r))

c.close()

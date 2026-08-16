import sqlite3
import re

DB = "data/vinylvault.db"

def norm(x):
    x = str(x or "").lower()
    x = x.replace("&", " and ").replace("'", "").replace("’", "")
    return " ".join(re.sub(r"[^a-z0-9]+", " ", x).split())

db = sqlite3.connect(DB)
db.row_factory = sqlite3.Row

mp3s = db.execute("""
SELECT id,artist,title FROM mp3_files
WHERE artist!='' AND title!=''
""").fetchall()

idx = {}

for m in mp3s:
    idx.setdefault(
        (norm(m["artist"]),norm(m["title"])), []
    ).append(m)

tracks = db.execute("""
SELECT id,artist,title FROM tracks
""").fetchall()

new = 0

for t in tracks:

    matches = idx.get(
        (norm(t["artist"]),norm(t["title"])), []
    )

    if len(matches) != 1:
        continue

    m = matches[0]

    db.execute("""
    INSERT OR IGNORE INTO track_mp3
    (track_id,mp3_id)
    VALUES (?,?)
    """,(t["id"],m["id"]))

    new += 1

db.commit()

print()
print("=" * 60)
print("MP3 KOPPELING KLAAR")
print("=" * 60)
print("Nieuwe koppelingen:",new)
print("Totaal track_mp3 :",db.execute(
    "SELECT COUNT(*) FROM track_mp3"
).fetchone()[0])

db.close()
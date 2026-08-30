import sqlite3
import json
from pathlib import Path

db = r".\data\vinylvault.db"
js = r".\data\discogs_public_collection.json"

conn = sqlite3.connect(db)

rows = conn.execute("""
    SELECT artist, title
    FROM releases
    WHERE media_type = 'VINYL'
""").fetchall()

existing = {
    ((a or "").strip().lower(), (t or "").strip().lower())
    for a, t in rows
}

conn.close()

with open(js, "r", encoding="utf-8") as f:
    data = json.load(f)

missing = []

for item in data:
    b = item.get("basic_information", {})
    artist = ", ".join(
        x.get("name", "")
        for x in b.get("artists", [])
    ).strip()

    title = (b.get("title") or "").strip()

    key = (artist.lower(), title.lower())

    if key not in existing:
        missing.append((item.get("id"), item.get("instance_id"), artist, title))

print("HUIDIGE VINYL:", len(existing))
print("DISCOGS:", len(data))
print("ONTBREKEND:", len(missing))
print()
print("EERSTE 100 ONTBREKENDE:")
for x in missing[:100]:
    print(x)

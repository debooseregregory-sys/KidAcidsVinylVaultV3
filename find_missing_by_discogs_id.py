import sqlite3
import json

db = r".\data\vinylvault.db"
js = r".\data\discogs_public_collection.json"

c = sqlite3.connect(db)

db_ids = set()

for row in c.execute("SELECT discogs, review_discogs_id FROM releases"):
    for x in row:
        if x:
            s = str(x).strip()
            if s.isdigit():
                db_ids.add(int(s))

c.close()

with open(js, "r", encoding="utf-8") as f:
    data = json.load(f)

missing = []

for item in data:
    b = item.get("basic_information", {})
    fmt = b.get("formats", [])

    is_vinyl = any(
        "Vinyl" in str(f.get("name", ""))
        for f in fmt
    )

    if not is_vinyl:
        continue

    did = item.get("id")

    if did not in db_ids:
        artists = ", ".join(
            a.get("name", "")
            for a in b.get("artists", [])
        )

        missing.append((
            did,
            item.get("instance_id"),
            artists,
            b.get("title", ""),
        ))

print("VINYL IN DISCOGS:", sum(
    1 for item in data
    if any("Vinyl" in str(f.get("name",""))
           for f in item.get("basic_information", {}).get("formats", []))
))

print("DISCOGS-ID'S IN HUIDIGE DB:", len(db_ids))
print("VINYL ONTBREKEND OP DISCOGS-ID:", len(missing))
print()

for x in missing[:100]:
    print(x)

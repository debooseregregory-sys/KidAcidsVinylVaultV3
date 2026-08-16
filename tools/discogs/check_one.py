import sqlite3
import json

DB = r".\data\vinylvault.db"
JSON_FILE = r".\data\discogs_public_collection.json"

db = sqlite3.connect(DB)

row = db.execute("""
    SELECT id, artist, title, label, catalog, year, genre,
           discogs, discogs_link, cover, storage_code
    FROM releases
    WHERE discogs IS NOT NULL
      AND TRIM(discogs) <> ''
    LIMIT 1
""").fetchone()

print()
print("=" * 80)
print("DATABASE")
print("=" * 80)

print("id           :", row[0])
print("artist       :", row[1])
print("title        :", row[2])
print("label        :", row[3])
print("catalog      :", row[4])
print("year         :", row[5])
print("genre        :", row[6])
print("discogs      :", row[7])
print("discogs_link :", row[8])
print("cover        :", row[9])
print("storage_code :", row[10])

print()
print("=" * 80)
print("JSON")
print("=" * 80)

with open(JSON_FILE, "r", encoding="utf-8") as f:
    data = json.load(f)

discogs_id = int(row[7])

match = None

for item in data:
    if int(item.get("id", 0)) == discogs_id:
        match = item
        break

if match is None:
    print("GEEN JSON MATCH VOOR:", discogs_id)
else:
    print(json.dumps(match, indent=2, ensure_ascii=False))

print()
print("=" * 80)

db.close()

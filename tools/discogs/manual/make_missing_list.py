import sqlite3
import csv
import os

BASE = r"C:\Users\andyb\Desktop\KidAcidsVinylVaultV3"
DB = os.path.join(BASE, "data", "vinylvault.db")
OUT = os.path.join(BASE, "tools", "discogs", "manual", "missing_discogs_174.csv")

db = sqlite3.connect(DB)
db.row_factory = sqlite3.Row

# Alle Discogs IDs uit de lokale database
rows = db.execute("""
    SELECT
        id,
        artist,
        title,
        label,
        catalog,
        year,
        genre,
        discogs,
        discogs_link,
        cover,
        storage_code
    FROM releases
    WHERE discogs IS NOT NULL
      AND TRIM(discogs) <> ''
    ORDER BY id
""").fetchall()

# JSON IDs laden
JSON_FILE = os.path.join(
    BASE,
    "data",
    "discogs",
    "kid_acid_collection.json"
)

import json

with open(JSON_FILE, "r", encoding="utf-8") as f:
    data = json.load(f)

json_ids = set()

for item in data:
    try:
        json_ids.add(int(item.get("id", 0)))
    except:
        pass

missing = []

for row in rows:

    try:
        discogs_id = int(str(row["discogs"]).strip())
    except:
        continue

    if discogs_id not in json_ids:

        missing.append({
            "database_id": row["id"],
            "artist": row["artist"] or "",
            "title": row["title"] or "",
            "label": row["label"] or "",
            "catalog": row["catalog"] or "",
            "year": row["year"] or "",
            "genre": row["genre"] or "",
            "discogs_id": discogs_id,
            "discogs_url": f"https://www.discogs.com/release/{discogs_id}",
            "storage_code": row["storage_code"] or ""
        })

db.close()

with open(
    OUT,
    "w",
    newline="",
    encoding="utf-8-sig"
) as f:

    writer = csv.DictWriter(
        f,
        fieldnames=[
            "database_id",
            "artist",
            "title",
            "label",
            "catalog",
            "year",
            "genre",
            "discogs_id",
            "discogs_url",
            "storage_code"
        ]
    )

    writer.writeheader()
    writer.writerows(missing)

print("=" * 78)
print("KID ACID'S VINYL VAULT V3")
print("ONTBREKENDE DISCOGS RELEASES")
print("=" * 78)
print()
print("Ontbrekende releases :", len(missing))
print()
print("CSV BESTAND:")
print(OUT)
print()
print("=" * 78)

for i, item in enumerate(missing, 1):

    print(
        f"{i:3} | "
        f"DB {item['database_id']:4} | "
        f"Discogs {item['discogs_id']:8} | "
        f"{item['artist']} - {item['title']}"
    )

print()
print("=" * 78)
print("DATABASE IS NIET GEWIJZIGD")
print("=" * 78)

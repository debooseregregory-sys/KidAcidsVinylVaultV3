import sqlite3
import json
import os

BASE = r"C:\Users\andyb\Desktop\KidAcidsVinylVaultV3"
DB = os.path.join(BASE, "data", "vinylvault.db")
JSON_FILE = os.path.join(BASE, "data", "discogs", "kid_acid_collection.json")

print("=" * 78)
print("KID ACID'S VINYL VAULT V3")
print("DISCOGS CONTROLE ID 11375")
print("=" * 78)

print()
print("DATABASE :", DB)
print("JSON     :", JSON_FILE)

if not os.path.isfile(DB):
    print()
    print("FOUT: DATABASE BESTAAT NIET")
    raise SystemExit(1)

if not os.path.isfile(JSON_FILE):
    print()
    print("FOUT: JSON BESTAAT NIET")
    raise SystemExit(1)

db = sqlite3.connect(DB)
db.row_factory = sqlite3.Row

row = db.execute("""
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
WHERE discogs = '11375'
LIMIT 1
""").fetchone()

if row is None:
    print()
    print("FOUT: Discogs ID 11375 staat niet in releases.")
    db.close()
    raise SystemExit(1)

print()
print("-" * 78)
print("DATABASE")
print("-" * 78)

for key in row.keys():
    print(f"{key:15}: {row[key]}")

with open(JSON_FILE, "r", encoding="utf-8") as f:
    data = json.load(f)

item = None

for record in data:
    try:
        if int(record.get("id", 0)) == 11375:
            item = record
            break
    except (TypeError, ValueError):
        pass

if item is None:
    print()
    print("FOUT: Discogs ID 11375 staat niet in JSON.")
    db.close()
    raise SystemExit(1)

basic = item.get("basic_information", {})

artists = basic.get("artists") or []
labels = basic.get("labels") or []
genres = basic.get("genres") or []

json_artist = artists[0].get("name", "") if artists else ""
json_title = basic.get("title", "")
json_label = labels[0].get("name", "") if labels else ""
json_catalog = labels[0].get("catno", "") if labels else ""
json_year = basic.get("year", "")
json_genre = genres[0] if genres else ""

json_link = f"https://www.discogs.com/release/11375"
json_cover = basic.get("cover_image", "")

print()
print("-" * 78)
print("JSON")
print("-" * 78)

print(f"{'artist':15}: {json_artist}")
print(f"{'title':15}: {json_title}")
print(f"{'label':15}: {json_label}")
print(f"{'catalog':15}: {json_catalog}")
print(f"{'year':15}: {json_year}")
print(f"{'genre':15}: {json_genre}")
print(f"{'discogs_link':15}: {json_link}")
print(f"{'cover':15}: {json_cover}")

print()
print("-" * 78)
print("VERSCHILLEN")
print("-" * 78)

checks = [
    ("artist", row["artist"], json_artist),
    ("title", row["title"], json_title),
    ("label", row["label"], json_label),
    ("catalog", row["catalog"], json_catalog),
    ("year", row["year"], json_year),
    ("genre", row["genre"], json_genre),
    ("discogs_link", row["discogs_link"], json_link),
    ("cover", row["cover"], json_cover),
]

different = 0

for field, db_value, json_value in checks:

    db_text = "" if db_value is None else str(db_value).strip()
    json_text = "" if json_value is None else str(json_value).strip()

    if db_text != json_text:
        different += 1

        print()
        print("VELD:", field)
        print("DATABASE:")
        print(repr(db_value))
        print("JSON:")
        print(repr(json_value))

if different == 0:
    print()
    print("GEEN VERSCHILLEN GEVONDEN.")

print()
print("-" * 78)
print("RESULTAAT")
print("-" * 78)
print("Verschillende velden:", different)
print()
print("DATABASE IS NIET GEWIJZIGD.")

db.close()

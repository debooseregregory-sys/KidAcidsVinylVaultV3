import json
import sqlite3
from pathlib import Path

BASE = Path.cwd()
DB = BASE / "data" / "vinylvault.db"

json_files = [
    p for p in (BASE / "data").rglob("*.json")
    if p.stat().st_size == 9916192
]

if not json_files:
    raise RuntimeError("Discogs JSON niet gevonden.")

JSON_FILE = json_files[0]

with open(JSON_FILE, "r", encoding="utf-8") as f:
    data = json.load(f)

index = {}

for item in data:
    if not isinstance(item, dict):
        continue

    basic = item.get("basic_information", {})

    if not isinstance(basic, dict):
        continue

    rid = basic.get("id")

    try:
        rid = int(rid)
    except (TypeError, ValueError):
        continue

    index[rid] = item

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
    WHERE id = 2
""").fetchone()

if row is None:
    raise RuntimeError("Release ID 2 niet gevonden.")

discogs_id = int(row["discogs"])

item = index.get(discogs_id)

if item is None:
    raise RuntimeError(
        f"Discogs ID {discogs_id} staat niet in JSON."
    )

basic = item.get("basic_information", {})

artists = basic.get("artists", [])
labels = basic.get("labels", [])
genres = basic.get("genres", [])

artist = ""

if artists:
    names = []

    for a in artists:
        if isinstance(a, dict):
            name = a.get("name")
            if name:
                names.append(str(name))

    artist = ", ".join(names)

title = basic.get("title") or ""

label = ""

if labels:
    names = []

    for x in labels:
        if isinstance(x, dict):
            name = x.get("name")
            if name:
                names.append(str(name))

    label = ", ".join(names)

catalog = ""

if labels:
    cats = []

    for x in labels:
        if isinstance(x, dict):
            cat = x.get("catno")
            if cat:
                cats.append(str(cat))

    catalog = ", ".join(cats)

year = basic.get("year") or ""

genre = ""

if genres:
    genre = ", ".join(str(x) for x in genres if x)

link = f"https://www.discogs.com/release/{discogs_id}"

cover = basic.get("cover_image") or ""

print()
print("=" * 75)
print("PROEFVERRIJKING — GEEN DATABASE UPDATE")
print("=" * 75)

print()
print("DATABASE")
print("ID          :", row["id"])
print("Artist      :", row["artist"])
print("Title       :", row["title"])
print("Label       :", row["label"])
print("Catalog     :", row["catalog"])
print("Year        :", row["year"])
print("Genre       :", row["genre"])
print("Discogs ID  :", row["discogs"])
print("Storage     :", row["storage_code"])

print()
print("JSON → NIEUWE WAARDEN")
print("Artist      :", artist)
print("Title       :", title)
print("Label       :", label)
print("Catalog     :", catalog)
print("Year        :", year)
print("Genre       :", genre)
print("Discogs link:", link)
print("Cover       :", cover)

print()
print("=" * 75)
print("DATABASE IS NIET GEWIJZIGD.")
print("=" * 75)

db.close()

import sqlite3
import json
import os

BASE = r"C:\Users\andyb\Desktop\KidAcidsVinylVaultV3"
DB = os.path.join(BASE, "data", "vinylvault.db")
JSON_FILE = os.path.join(BASE, "data", "discogs", "kid_acid_collection.json")

db = sqlite3.connect(DB)
db.row_factory = sqlite3.Row

with open(JSON_FILE, "r", encoding="utf-8") as f:
    data = json.load(f)

discogs = {}

for item in data:
    try:
        rid = int(item.get("id", 0))
        if rid:
            discogs[rid] = item
    except:
        pass

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

print("=" * 80)
print("KID ACID'S VINYL VAULT V3")
print("DISCOGS ENRICHMENT - DEFINITIEVE CONTROLE")
print("=" * 80)

print()
print("JSON records :", len(data))
print("JSON IDs     :", len(discogs))
print("DB releases  :", db.execute("SELECT COUNT(*) FROM releases").fetchone()[0])
print("DB Discogs ID:", len(rows))

matched = []
missing = []

for row in rows:
    try:
        rid = int(str(row["discogs"]).strip())
    except:
        missing.append(row)
        continue

    if rid in discogs:
        matched.append((row, discogs[rid]))
    else:
        missing.append(row)

print("JSON matches :", len(matched))
print("Geen match   :", len(missing))

# ------------------------------------------------------------
# MOGELIJKE WIJZIGINGEN
# ------------------------------------------------------------

fields = {
    "artist": 0,
    "title": 0,
    "label": 0,
    "catalog": 0,
    "year": 0,
    "genre": 0,
    "discogs_link": 0,
    "cover": 0,
}

examples = []

for row, item in matched:

    basic = item.get("basic_information", {})

    artists = basic.get("artists") or []
    labels = basic.get("labels") or []
    genres = basic.get("genres") or []

    artist = artists[0].get("name", "") if artists else ""
    title = basic.get("title", "")
    label = labels[0].get("name", "") if labels else ""
    catalog = labels[0].get("catno", "") if labels else ""
    year = basic.get("year", "")
    genre = genres[0] if genres else ""

    link = f"https://www.discogs.com/release/{item.get('id')}"

    cover = basic.get("cover_image", "")

    values = {
        "artist": artist,
        "title": title,
        "label": label,
        "catalog": catalog,
        "year": year,
        "genre": genre,
        "discogs_link": link,
        "cover": cover,
    }

    differences = []

    for field, json_value in values.items():

        db_value = row[field]

        db_text = "" if db_value is None else str(db_value).strip()
        json_text = "" if json_value is None else str(json_value).strip()

        if not db_text and json_text:
            fields[field] += 1
            differences.append(field)

    if differences and len(examples) < 30:
        examples.append(
            (
                row["id"],
                row["artist"],
                row["title"],
                row["discogs"],
                differences
            )
        )

print()
print("=" * 80)
print("VELDEN DIE NOG LEEG ZIJN")
print("=" * 80)

for field, count in fields.items():
    print(f"{field:15}: {count}")

total = sum(fields.values())

print()
print("TOTAAL MOGELIJKE VELDAANVULLINGEN:", total)

# ------------------------------------------------------------
# VOORBEELDEN
# ------------------------------------------------------------

print()
print("=" * 80)
print("VOORBEELDEN VAN RELEASES DIE NOG IETS MISSEN")
print("=" * 80)

if not examples:
    print("GEEN RELEASES GEVONDEN DIE NOG VELDEN MISSEN.")

else:
    for n, artist, title, rid, differences in examples:
        print()
        print(f"DB ID    : {n}")
        print(f"Artist   : {artist}")
        print(f"Title    : {title}")
        print(f"Discogs  : {rid}")
        print(f"Ontbreekt: {', '.join(differences)}")

# ------------------------------------------------------------
# 174 NIET GEVONDEN
# ------------------------------------------------------------

print()
print("=" * 80)
print("DISCOGS-ID'S DIE NIET IN JSON STAAN")
print("=" * 80)

for row in missing[:50]:
    print(
        f"{row['id']} | "
        f"{row['artist']} | "
        f"{row['title']} | "
        f"Discogs={row['discogs']}"
    )

if len(missing) > 50:
    print()
    print(f"... en nog {len(missing) - 50}")

print()
print("=" * 80)
print("DATABASE IS NIET GEWIJZIGD")
print("=" * 80)

db.close()

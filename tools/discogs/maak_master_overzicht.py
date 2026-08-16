import json
import sqlite3
from pathlib import Path
from collections import Counter

BASE = Path(r"C:\Users\andyb\Desktop\KidAcidsVinylVaultV3")
DB = BASE / "data" / "vinylvault.db"
JSON_FILE = BASE / "data" / "discogs_public_collection.json"
OUT = BASE / "data" / "discogs_master_overzicht.txt"

print("=" * 90)
print("KID ACID'S VINYL VAULT V3")
print("OPENBARE DISCOGS COLLECTIE ALS MASTERBRON")
print("=" * 90)
print()

# ============================================================
# JSON
# ============================================================

print("OPENBARE DISCOGS COLLECTIE LADEN...")

with open(
    JSON_FILE,
    "r",
    encoding="utf-8"
) as f:
    collection = json.load(f)

print(
    f"JSON records: {len(collection)}"
)

# ============================================================
# DISCogs DATA UITLEZEN
# ============================================================

records = []

formats = Counter()
years = Counter()
artists = Counter()
catalogs = Counter()

for item in collection:

    basic = item.get(
        "basic_information",
        {}
    )

    discogs_id = basic.get(
        "id"
    )

    instance_id = item.get(
        "instance_id"
    )

    title = basic.get(
        "title"
    ) or ""

    artist_names = []

    for a in basic.get(
        "artists",
        []
    ):

        if isinstance(
            a,
            dict
        ):

            name = a.get(
                "name"
            ) or ""

            if name:
                artist_names.append(
                    name
                )

    artist = ", ".join(
        artist_names
    )

    label_names = []
    catalog_numbers = []

    for label in basic.get(
        "labels",
        []
    ):

        if not isinstance(
            label,
            dict
        ):
            continue

        label_name = label.get(
            "name"
        ) or ""

        catno = label.get(
            "catno"
        ) or ""

        if label_name:
            label_names.append(
                str(label_name)
            )

        if catno:
            catalog_numbers.append(
                str(catno)
            )

    format_names = []

    for fmt in basic.get(
        "formats",
        []
    ):

        if not isinstance(
            fmt,
            dict
        ):
            continue

        name = fmt.get(
            "name"
        ) or ""

        if name:
            format_names.append(
                str(name)
                )

    fmt = " / ".join(
        format_names
    )

    record = {
        "discogs_id": discogs_id,
        "instance_id": instance_id,
        "artist": artist,
        "title": str(title),
        "label": " / ".join(label_names),
        "catalog": " / ".join(catalog_numbers),
        "format": fmt,
        "year": basic.get("year"),
        "genre": ", ".join(
            str(x)
            for x in basic.get(
                "genres",
                []
            )
        ),
        "style": ", ".join(
            str(x)
            for x in basic.get(
                "styles",
                []
            )
        )
    }

    records.append(
        record
    )

    # Statistieken
    if fmt:
        formats[fmt] += 1

    if record["year"]:
        years[record["year"]] += 1

    if artist:
        artists[artist] += 1

    if record["catalog"]:
        catalogs[record["catalog"]] += 1

# ============================================================
# DATABASE
# ============================================================

print()
print("LOKALE DATABASE LADEN...")

conn = sqlite3.connect(
    DB
)

cur = conn.cursor()

cur.execute("""
SELECT
    id,
    artist,
    title,
    label,
    catalog,
    discogs,
    discogs_link,
    storage_code
FROM releases
ORDER BY id
""")

local = cur.fetchall()

print(
    f"Lokale releases: {len(local)}"
)

# ============================================================
# FORMATEN
# ============================================================

vinyl = 0
cd = 0
other = 0

for r in records:

    f = r["format"].lower()

    if "vinyl" in f:
        vinyl += 1

    elif "cd" in f:
        cd += 1

    else:
        other += 1

# ============================================================
# OVERZICHT
# ============================================================

print()
print("=" * 90)
print("OPENBARE COLLECTIE")
print("=" * 90)

print(
    f"Totaal : {len(records)}"
)

print(
    f"Vinyl  : {vinyl}"
)

print(
    f"CD     : {cd}"
)

print(
    f"Andere : {other}"
)

print()
print("=" * 90)
print("LOKALE DATABASE")
print("=" * 90)

print(
    f"Releases: {len(local)}"
)

# ============================================================
# BESTAND
# ============================================================

with open(
    OUT,
    "w",
    encoding="utf-8"
) as f:

    f.write(
        "=" * 100 + "\n"
    )

    f.write(
        "KID ACID'S VINYL VAULT V3\n"
    )

    f.write(
        "OPENBARE DISCOGS COLLECTIE - MASTER OVERZICHT\n"
    )

    f.write(
        "=" * 100 + "\n\n"
    )

    f.write(
        f"TOTAAL JSON RECORDS : {len(records)}\n"
    )

    f.write(
        f"VINYL                : {vinyl}\n"
    )

    f.write(
        f"CD                   : {cd}\n"
    )

    f.write(
        f"ANDERE               : {other}\n"
    )

    f.write(
        f"LOKALE RELEASES      : {len(local)}\n"
    )

    f.write("\n")

    f.write(
        "=" * 100 + "\n"
    )

    f.write(
        "ALLE OPENBARE DISCOGS RECORDS\n"
    )

    f.write(
        "=" * 100 + "\n\n"
    )

    for n, r in enumerate(
        records,
        1
    ):

        f.write(
            f"[{n}/{len(records)}]\n"
        )

        f.write(
            f"DISCOGS ID : {r['discogs_id']}\n"
        )

        f.write(
            f"INSTANCE   : {r['instance_id']}\n"
        )

        f.write(
            f"ARTIST     : {r['artist']}\n"
        )

        f.write(
            f"TITLE      : {r['title']}\n"
        )

        f.write(
            f"LABEL      : {r['label']}\n"
        )

        f.write(
            f"CATALOG    : {r['catalog']}\n"
        )

        f.write(
            f"FORMAT     : {r['format']}\n"
        )

        f.write(
            f"YEAR       : {r['year'] or ''}\n"
        )

        f.write(
            f"GENRE      : {r['genre']}\n"
        )

        f.write(
            f"STYLE      : {r['style']}\n"
        )

        f.write(
            "\n"
        )

# ============================================================
# VOORBEELDEN
# ============================================================

print()
print("=" * 90)
print("EERSTE 10 OPENBARE RECORDS")
print("=" * 90)

for r in records[:10]:

    print()
    print(
        f"Discogs ID : {r['discogs_id']}"
    )

    print(
        f"{r['artist']} - {r['title']}"
    )

    print(
        f"Catalog    : {r['catalog']}"
    )

    print(
        f"Format     : {r['format']}"
    )

# ============================================================
# EINDE
# ============================================================

conn.close()

print()
print("=" * 90)
print("KLAAR")
print("=" * 90)
print()
print(
    "Master overzicht:"
)

print(
    OUT
)

print()
print(
    "DATABASE IS NIET GEWIJZIGD."
)

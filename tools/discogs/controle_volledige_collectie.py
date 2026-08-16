import json
import sqlite3
from pathlib import Path

BASE = Path(r"C:\Users\andyb\Desktop\KidAcidsVinylVaultV3")
DB = BASE / "data" / "vinylvault.db"
JSON_FILE = BASE / "data" / "discogs_public_collection.json"
OUT = BASE / "data" / "discogs_match_results.txt"

print("=" * 80)
print("VINYLVAULT V3 - OPENBARE COLLECTIE CONTROLE")
print("=" * 80)

print(f"Database : {DB}")
print(f"JSON     : {JSON_FILE}")
print()

print("JSON laden...")

with open(JSON_FILE, "r", encoding="utf-8") as f:
    public = json.load(f)

print(f"JSON records: {len(public)}")

print()
print("Database laden...")

conn = sqlite3.connect(DB)
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

print(f"Lokale releases: {len(local)}")
print()

# ------------------------------------------------------------
# INDEX JSON
# ------------------------------------------------------------

print("JSON-index bouwen...")

by_id = {}
by_catalog = {}
by_title = {}

for record in public:

    basic = record.get("basic_information", {})

    rid = basic.get("id")

    if rid:
        by_id[str(rid)] = record

    title = str(
        basic.get("title", "")
    ).strip().lower()

    if title:
        by_title.setdefault(
            title,
            []
        ).append(record)

    for label in basic.get("labels", []):

        if not isinstance(label, dict):
            continue

        catno = str(
            label.get("catno", "")
        ).strip().lower()

        if catno:
            by_catalog.setdefault(
                catno,
                []
            ).append(record)

print(f"Unieke Discogs IDs : {len(by_id)}")
print(f"Unieke titels      : {len(by_title)}")
print(f"Unieke catalogi    : {len(by_catalog)}")

print()
print("Lokale collectie controleren...")
print()

results = []

exact_id = 0
catalog_matches = 0
title_matches = 0
missing = 0

for number, row in enumerate(local, 1):

    (
        local_id,
        artist,
        title,
        label,
        catalog,
        discogs,
        discogs_link,
        storage_code
    ) = row

    match = None
    method = ""

    # --------------------------------------------------------
    # 1. BESTAANDE DISCOGS ID
    # --------------------------------------------------------

    if discogs:

        key = str(discogs).strip()

        if key in by_id:
            match = by_id[key]
            method = "BESTAANDE DISCOGS ID"
            exact_id += 1

    # --------------------------------------------------------
    # 2. CATALOGUS
    # --------------------------------------------------------

    if match is None and catalog:

        key = str(catalog).strip().lower()

        candidates = by_catalog.get(
            key,
            []
        )

        if len(candidates) == 1:

            match = candidates[0]
            method = "EXACT CATALOG"
            catalog_matches += 1

    # --------------------------------------------------------
    # 3. TITEL
    # --------------------------------------------------------

    if match is None and title:

        key = str(title).strip().lower()

        candidates = by_title.get(
            key,
            []
        )

        if len(candidates) == 1:

            match = candidates[0]
            method = "EXACT TITEL"
            title_matches += 1

    # --------------------------------------------------------
    # RESULTAAT
    # --------------------------------------------------------

    if match:

        basic = match.get(
            "basic_information",
            {}
        )

        remote_id = basic.get(
            "id",
            ""
        )

        remote_title = basic.get(
            "title",
            ""
        )

        remote_artists = ", ".join(
            a.get("name", "")
            for a in basic.get(
                "artists",
                []
            )
            if isinstance(a, dict)
        )

        remote_catalogs = ", ".join(
            str(x.get("catno", ""))
            for x in basic.get(
                "labels",
                []
            )
            if isinstance(x, dict)
            and x.get("catno")
        )

        formats = ", ".join(
            str(x.get("name", ""))
            for x in basic.get(
                "formats",
                []
            )
            if isinstance(x, dict)
            and x.get("name")
        )

        results.append(
            (
                local_id,
                artist,
                title,
                catalog,
                storage_code,
                remote_id,
                remote_artists,
                remote_title,
                remote_catalogs,
                formats,
                method
            )
        )

    else:

        missing += 1

    # --------------------------------------------------------
    # VOORTGANG
    # --------------------------------------------------------

    if number % 100 == 0:

        print(
            f"{number}/{len(local)} "
            f"| matches={len(results)} "
            f"| catalog={catalog_matches} "
            f"| geen={missing}"
        )

# ------------------------------------------------------------
# BESTAND SCHRIJVEN
# ------------------------------------------------------------

with open(
    OUT,
    "w",
    encoding="utf-8"
) as f:

    f.write(
        "=" * 100 + "\n"
    )

    f.write(
        "VINYLVAULT V3 - MATCH RESULTATEN\n"
    )

    f.write(
        "=" * 100 + "\n\n"
    )

    f.write(
        f"JSON records: {len(public)}\n"
    )

    f.write(
        f"Lokale releases: {len(local)}\n"
    )

    f.write(
        f"Bestaande Discogs IDs: {exact_id}\n"
    )

    f.write(
        f"Exact catalog: {catalog_matches}\n"
    )

    f.write(
        f"Exact titel: {title_matches}\n"
    )

    f.write(
        f"Geen directe match: {missing}\n\n"
    )

    for item in results:

        (
            local_id,
            artist,
            title,
            catalog,
            storage_code,
            remote_id,
            remote_artists,
            remote_title,
            remote_catalogs,
            formats,
            method
        ) = item

        f.write(
            "-" * 100 + "\n"
        )

        f.write(
            f"LOCAL ID    : {local_id}\n"
        )

        f.write(
            f"LOCAL       : {artist} - {title}\n"
        )

        f.write(
            f"LOCAL CATALOG: {catalog or ''}\n"
        )

        f.write(
            f"KASTCODE    : {storage_code or ''}\n"
        )

        f.write(
            f"DISCOGS ID  : {remote_id}\n"
        )

        f.write(
            f"DISCOGS     : {remote_artists} - {remote_title}\n"
        )

        f.write(
            f"CATALOG     : {remote_catalogs}\n"
        )

        f.write(
            f"FORMAT      : {formats}\n"
        )

        f.write(
            f"MATCH METHODE: {method}\n"
        )

conn.close()

print()
print("=" * 80)
print("KLAAR")
print("=" * 80)
print()
print(f"Matches       : {len(results)}")
print(f"Catalogmatches: {catalog_matches}")
print(f"Titels        : {title_matches}")
print(f"Geen directe  : {missing}")
print()
print(f"Resultaat:")
print(OUT)
print()
print("DATABASE IS NIET GEWIJZIGD.")

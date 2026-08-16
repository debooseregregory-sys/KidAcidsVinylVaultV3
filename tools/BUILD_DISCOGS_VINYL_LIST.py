import csv
import json
import re
import sqlite3
from collections import defaultdict

ROOT = r"C:\Users\andyb\Desktop\KidAcidsVinylVaultV3"

CSV_FILE = r"C:\Users\andyb\Desktop\vinyl_collectie.csv"
JSON_FILE = ROOT + r"\discogs\public_data\collection.json"
DB_FILE = ROOT + r"\data\vinylvault.db"

OUTPUT_CSV = ROOT + r"\data\discogs_vinyl_definitive.csv"


# ============================================================
# HELPERS
# ============================================================

def clean(value):
    if value is None:
        return ""
    return str(value).strip()


def norm(value):
    return re.sub(r"[^a-z0-9]", "", clean(value).lower())


# ============================================================
# CSV INLEZEN
# ============================================================

print()
print("=" * 70)
print("BUILD DEFINITIEVE DISCOGS VINYL LIJST")
print("=" * 70)

with open(CSV_FILE, "r", encoding="cp1252", newline="") as f:
    rows = list(csv.DictReader(f))

print()
print("CSV rijen:", len(rows))


# ============================================================
# CATALOGUS -> KASTCODES
# ============================================================

catalog_index = defaultdict(set)

for row in rows:

    label_catalog = clean(row.get("Label / Catalog"))
    kast = clean(row.get("ID - CODE"))

    if not label_catalog or not kast:
        continue

    catalog_index[norm(label_catalog)].add(kast)


print("CSV catalogusgroepen:", len(catalog_index))


# ============================================================
# DISCOGS JSON
# ============================================================

with open(JSON_FILE, "r", encoding="utf-8") as f:
    data = json.load(f)

releases = data.get("releases", [])

print("Discogs releases:", len(releases))


# ============================================================
# ALLEEN VINYL
# ============================================================

vinyl = []

for release in releases:

    bi = release.get("basic_information") or {}

    formats = bi.get("formats") or []

    is_vinyl = False

    for fmt in formats:

        if not isinstance(fmt, dict):
            continue

        if clean(fmt.get("name")).lower() == "vinyl":
            is_vinyl = True
            break

    if is_vinyl:
        vinyl.append(release)


print("Discogs vinyl:", len(vinyl))


# ============================================================
# MATCH EXACTE CATALOGUS
# ============================================================

matches = []

for release in vinyl:

    bi = release.get("basic_information") or {}

    discogs_id = release.get("id")

    title = clean(bi.get("title"))

    artists = bi.get("artists") or []

    artist_parts = []

    for a in artists:

        if not isinstance(a, dict):
            continue

        name = clean(a.get("name"))

        if name:
            artist_parts.append(name)

    artist = ", ".join(artist_parts)

    labels = bi.get("labels") or []

    if not labels:
        continue

    found_codes = set()
    matched_catalogs = set()

    for label in labels:

        if not isinstance(label, dict):
            continue

        label_name = clean(label.get("name"))
        catno = clean(label.get("catno"))

        if not catno:
            continue

        # Alleen de echte cataloguscode is leidend.
        key = norm(catno)

        if not key:
            continue

        # Exacte match.
        if key in catalog_index:

            found_codes.update(catalog_index[key])
            matched_catalogs.add(catno)

        # Sommige CSV-codes bevatten label + catalogus.
        # Daarom tweede controle met labelnaam + catalogus.
        combined_key = norm(label_name + catno)

        if combined_key in catalog_index:

            found_codes.update(catalog_index[combined_key])
            matched_catalogs.add(catno)

    if not found_codes:
        continue

    matches.append({
        "discogs_id": discogs_id,
        "instance_id": release.get("instance_id"),
        "artist": artist,
        "title": title,
        "year": clean(bi.get("year")),
        "labels": " / ".join(
            clean(x.get("name"))
            for x in labels
            if isinstance(x, dict)
        ),
        "catalogs": " / ".join(
            clean(x.get("catno"))
            for x in labels
            if isinstance(x, dict)
        ),
        "matched_catalogs": " / ".join(sorted(matched_catalogs)),
        "kastcodes": " / ".join(sorted(found_codes)),
    })


# ============================================================
# DUBBELE DISCOGS ID'S SAMENVOEGEN
# ============================================================

unique = {}

for item in matches:

    discogs_id = item["discogs_id"]

    if discogs_id not in unique:

        unique[discogs_id] = item

    else:

        old = unique[discogs_id]

        old_codes = set(
            x.strip()
            for x in old["kastcodes"].split("/")
            if x.strip()
        )

        new_codes = set(
            x.strip()
            for x in item["kastcodes"].split("/")
            if x.strip()
        )

        old["kastcodes"] = " / ".join(
            sorted(old_codes | new_codes)
        )


matches = list(unique.values())


# ============================================================
# SORTEREN
# ============================================================

matches.sort(
    key=lambda x: (
        clean(x["artist"]).lower(),
        clean(x["title"]).lower()
    )
)


# ============================================================
# CSV OPSLAAN
# ============================================================

with open(
    OUTPUT_CSV,
    "w",
    encoding="utf-8-sig",
    newline=""
) as f:

    writer = csv.DictWriter(
        f,
        fieldnames=[
            "discogs_id",
            "instance_id",
            "artist",
            "title",
            "year",
            "labels",
            "catalogs",
            "matched_catalogs",
            "kastcodes",
        ]
    )

    writer.writeheader()

    writer.writerows(matches)


# ============================================================
# RESULTAAT
# ============================================================

all_codes = set()

for item in matches:

    for code in item["kastcodes"].split("/"):

        code = code.strip()

        if code:
            all_codes.add(code)


print()
print("=" * 70)
print("RESULTAAT")
print("=" * 70)

print("Definitieve Discogs matches :", len(matches))
print("Unieke kastcodes            :", len(all_codes))

print()
print("CSV aangemaakt:")
print(OUTPUT_CSV)

print()
print("EERSTE 20:")
print("-" * 70)

for i, item in enumerate(matches[:20], 1):

    print()
    print(f"{i}. {item['artist']} - {item['title']}")
    print("   Discogs ID :", item["discogs_id"])
    print("   Catalog    :", item["catalogs"])
    print("   Match      :", item["matched_catalogs"])
    print("   Kast       :", item["kastcodes"])
    print("   Jaar       :", item["year"])


print()
print("=" * 70)
print("KLAAR")
print("=" * 70)

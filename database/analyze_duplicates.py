import sqlite3
from pathlib import Path
from collections import defaultdict

BASE_DIR = Path(__file__).resolve().parent.parent
DB = BASE_DIR / "data" / "vinylvault.db"

print("=" * 70)
print("VINYLVAULT V3 - DUPLICATE RELEASE ANALYSE")
print("=" * 70)
print()
print("Database:")
print(DB)
print()

if not DB.exists():
    print("FOUT: database bestaat niet:")
    print(DB)
    raise SystemExit(1)

conn = sqlite3.connect(DB)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

cur.execute("""
    SELECT
        id,
        artist,
        title,
        label,
        catalog,
        year,
        discogs,
        storage_code
    FROM releases
    ORDER BY id
""")

releases = cur.fetchall()

print(f"TOTAAL RELEASES: {len(releases)}")
print()

# ------------------------------------------------------------
# 1. DUBBELE DISCOGS IDS
# ------------------------------------------------------------

groups = defaultdict(list)

for r in releases:
    discogs = str(r["discogs"] or "").strip()

    if discogs:
        groups[discogs].append(r)

duplicates_discogs = {
    k: v for k, v in groups.items()
    if len(v) > 1
}

print("=" * 70)
print("1. DUBBELE DISCOGS-ID'S")
print("=" * 70)
print()

print(f"Gevonden groepen: {len(duplicates_discogs)}")
print()

for discogs, rows in duplicates_discogs.items():
    print(f"DISCOGS {discogs} - {len(rows)} records")

    for r in rows:
        print(
            f"  ID={r['id']} | "
            f"{r['artist']} | "
            f"{r['title']} | "
            f"{r['label']} | "
            f"{r['catalog']} | "
            f"Storage={r['storage_code']}"
        )

    print()

# ------------------------------------------------------------
# 2. DUBBELE LABEL + CATALOGUS
# ------------------------------------------------------------

groups = defaultdict(list)

for r in releases:
    label = str(r["label"] or "").strip().lower()
    catalog = str(r["catalog"] or "").strip().lower()

    if label and catalog:
        key = (label, catalog)
        groups[key].append(r)

duplicates_catalog = {
    k: v for k, v in groups.items()
    if len(v) > 1
}

print("=" * 70)
print("2. DUBBELE LABEL + CATALOGUS")
print("=" * 70)
print()

print(f"Gevonden groepen: {len(duplicates_catalog)}")
print()

for (label, catalog), rows in duplicates_catalog.items():
    print(f"LABEL={label} | CATALOG={catalog} - {len(rows)} records")

    for r in rows:
        print(
            f"  ID={r['id']} | "
            f"{r['artist']} | "
            f"{r['title']} | "
            f"Discogs={r['discogs']} | "
            f"Storage={r['storage_code']}"
        )

    print()

# ------------------------------------------------------------
# 3. ARTIST + LABEL + CATALOGUS
# ------------------------------------------------------------

groups = defaultdict(list)

for r in releases:
    artist = str(r["artist"] or "").strip().lower()
    label = str(r["label"] or "").strip().lower()
    catalog = str(r["catalog"] or "").strip().lower()

    if artist and label and catalog:
        key = (artist, label, catalog)
        groups[key].append(r)

duplicates_full = {
    k: v for k, v in groups.items()
    if len(v) > 1
}

print("=" * 70)
print("3. ARTIST + LABEL + CATALOGUS DUBBELS")
print("=" * 70)
print()

print(f"Gevonden groepen: {len(duplicates_full)}")
print()

for (artist, label, catalog), rows in duplicates_full.items():
    print(
        f"ARTIST={artist} | LABEL={label} | "
        f"CATALOG={catalog} - {len(rows)} records"
    )

    for r in rows:
        print(
            f"  ID={r['id']} | "
            f"{r['artist']} | "
            f"{r['title']} | "
            f"Discogs={r['discogs']} | "
            f"Storage={r['storage_code']}"
        )

    print()

# ------------------------------------------------------------
# 4. ARTIST NORMALISATIE
# ------------------------------------------------------------

groups = defaultdict(list)

for r in releases:
    artist = str(r["artist"] or "").strip().lower()

    if artist:
        groups[artist].append(r)

print("=" * 70)
print("4. ARTIESTEN MET VERSCHILLENDE SCHRIJFWIJZEN")
print("=" * 70)
print()

# bekende voorbeelden zoals:
# Adam Beyer / Adam beyer
# A Paul / A. Paul

artist_variants = defaultdict(set)

for r in releases:
    original = str(r["artist"] or "").strip()

    if original:
        normalized = (
            original
            .lower()
            .replace(".", "")
            .replace("  ", " ")
        )

        artist_variants[normalized].add(original)

variants = {
    k: sorted(v)
    for k, v in artist_variants.items()
    if len(v) > 1
}

print(f"Gevonden groepen: {len(variants)}")
print()

for normalized, names in sorted(variants.items()):
    print(" / ".join(names))

print()

# ------------------------------------------------------------
# 5. SAMENVATTING
# ------------------------------------------------------------

print("=" * 70)
print("SAMENVATTING")
print("=" * 70)
print()
print(f"Totaal releases              : {len(releases)}")
print(f"Dubbele Discogs-ID groepen   : {len(duplicates_discogs)}")
print(f"Dubbele label/catalog groepen: {len(duplicates_catalog)}")
print(f"Dubbele artist/label/catalog : {len(duplicates_full)}")
print(f"Artist schrijfvarianten      : {len(variants)}")
print()
print("=" * 70)
print("ANALYSE KLAAR - ER IS NIETS GEWIJZIGD")
print("=" * 70)

conn.close()

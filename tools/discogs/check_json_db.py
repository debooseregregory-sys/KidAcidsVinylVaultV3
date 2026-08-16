from pathlib import Path
import json
import sqlite3
import shutil
from datetime import datetime

ROOT = Path(__file__).resolve().parents[3]
DB = ROOT / "data" / "vinylvault.db"

print("=" * 79)
print("KID ACID'S VINYL VAULT V3")
print("DISCOGS JSON CONTROLE")
print("=" * 79)

# ---------------------------------------------------------
# JUISTE JSON AUTOMATISCH VINDEN
# ---------------------------------------------------------

possible = [
    ROOT / "data" / "discogs_public_collection.json",
    ROOT / "data" / "discogs" / "public_collection.json",
    ROOT / "data" / "discogs_public_collection.json",
    Path.home() / "Desktop" / "data" / "discogs_public_collection.json",
]

json_file = next((p for p in possible if p.exists()), None)

if json_file is None:
    print()
    print("FOUT: JSON-BESTAND NIET GEVONDEN")
    print()
    print("Gezocht naar:")
    for p in possible:
        print(" ", p)
    raise SystemExit(1)

print()
print("JSON gevonden:")
print(json_file)

# ---------------------------------------------------------
# JSON CONTROLEREN
# ---------------------------------------------------------

with json_file.open("r", encoding="utf-8") as f:
    data = json.load(f)

print()
print("JSON records:", len(data))
print("JSON type:", type(data).__name__)

# ---------------------------------------------------------
# DATABASE CONTROLEREN
# ---------------------------------------------------------

if not DB.exists():
    raise SystemExit(f"Database niet gevonden: {DB}")

print()
print("Database:")
print(DB)

db = sqlite3.connect(DB)
cur = db.cursor()

tables = [
    r[0]
    for r in cur.execute(
        "SELECT name FROM sqlite_master "
        "WHERE type='table' ORDER BY name"
    )
]

print()
print("Tabellen:")
for table in tables:
    print(" ", table)

if "releases" not in tables:
    db.close()
    raise SystemExit("FOUT: tabel releases ontbreekt.")

columns = [
    r[1]
    for r in cur.execute("PRAGMA table_info(releases)")
]

print()
print("Kolommen releases:")
for column in columns:
    print(" ", column)

required = [
    "id",
    "artist",
    "title",
    "label",
    "catalog",
    "year",
    "genre",
    "discogs",
    "discogs_link",
    "cover",
    "storage_code",
]

missing = [c for c in required if c not in columns]

if missing:
    db.close()
    raise SystemExit(
        "FOUT: ontbrekende kolommen: " + ", ".join(missing)
    )

count = cur.execute(
    "SELECT COUNT(*) FROM releases"
).fetchone()[0]

with_id = cur.execute(
    "SELECT COUNT(*) FROM releases "
    "WHERE discogs IS NOT NULL AND TRIM(discogs) <> ''"
).fetchone()[0]

with_link = cur.execute(
    "SELECT COUNT(*) FROM releases "
    "WHERE discogs_link IS NOT NULL AND TRIM(discogs_link) <> ''"
).fetchone()[0]

with_cover = cur.execute(
    "SELECT COUNT(*) FROM releases "
    "WHERE cover IS NOT NULL AND TRIM(cover) <> ''"
).fetchone()[0]

with_storage = cur.execute(
    "SELECT COUNT(*) FROM releases "
    "WHERE storage_code IS NOT NULL AND TRIM(storage_code) <> ''"
).fetchone()[0]

print()
print("=" * 79)
print("DATABASE STATUS")
print("=" * 79)
print("Releases        :", count)
print("Met Discogs ID  :", with_id)
print("Met Discogs link:", with_link)
print("Met cover       :", with_cover)
print("Met kastcode    :", with_storage)

# ---------------------------------------------------------
# ECHTE MATCHCONTROLE
# ---------------------------------------------------------

json_ids = set()

for item in data:
    if not isinstance(item, dict):
        continue

    rid = item.get("id")

    if rid is None:
        basic = item.get("basic_information", {})
        if isinstance(basic, dict):
            rid = basic.get("id")

    try:
        if rid is not None:
            json_ids.add(int(rid))
    except (ValueError, TypeError):
        pass

db_ids = {
    int(r[0])
    for r in cur.execute(
        "SELECT discogs FROM releases "
        "WHERE discogs IS NOT NULL AND TRIM(discogs) <> ''"
    )
    if str(r[0]).strip().isdigit()
}

matches = db_ids & json_ids
missing_json = db_ids - json_ids

print()
print("=" * 79)
print("MATCH CONTROLE")
print("=" * 79)
print("Unieke JSON Discogs IDs :", len(json_ids))
print("Database Discogs IDs    :", len(db_ids))
print("IDs gevonden in JSON    :", len(matches))
print("IDs niet in JSON        :", len(missing_json))

print()
print("=" * 79)
print("VEILIGHEIDSCONTROLE")
print("=" * 79)
print("DATABASE GEWIJZIGD : NEE")
print("KASTCODES GEWIJZIGD: NEE")
print("TRACKS GEWIJZIGD    : NEE")
print("MP3 GEWIJZIGD       : NEE")
print()

db.close()

print("=" * 79)
print("CONTROLE KLAAR")
print("=" * 79)

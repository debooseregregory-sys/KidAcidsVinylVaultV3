import json
import sqlite3
from pathlib import Path

BASE = Path.cwd()
DB_FILE = BASE / "data" / "vinylvault.db"

print("=" * 75)
print("KID ACID'S VINYL VAULT V3")
print("DISCOGS KOPPELING CONTROLE")
print("=" * 75)

# ============================================================
# DATABASE
# ============================================================

if not DB_FILE.exists():
    raise RuntimeError(f"Database bestaat niet: {DB_FILE}")

# ============================================================
# JUISTE JSON AUTOMATISCH VINDEN
# ============================================================

candidates = []

for p in (BASE / "data").rglob("*.json"):
    try:
        size = p.stat().st_size
    except OSError:
        continue

    if size >= 9_000_000:
        candidates.append(p)

if not candidates:
    raise RuntimeError(
        "Geen groot Discogs JSON-bestand gevonden onder data."
    )

print()
print("MOGELIJKE DISCOGS JSON-BESTANDEN:")

for p in candidates:
    print(f"  {p}")
    print(f"  grootte: {p.stat().st_size}")

# ============================================================
# JSON INHOUD CONTROLEREN
# ============================================================

JSON_FILE = None
data = None

for p in candidates:
    try:
        with open(p, "r", encoding="utf-8") as f:
            test = json.load(f)
    except Exception:
        continue

    if isinstance(test, list) and len(test) >= 5000:
        JSON_FILE = p
        data = test
        break

if JSON_FILE is None:
    raise RuntimeError(
        "Geen JSON gevonden met minimaal 5000 records."
    )

print()
print("=" * 75)
print("JSON GEVONDEN")
print("=" * 75)

print("Bestand :", JSON_FILE)
print("Records :", len(data))
print("Type    :", type(data).__name__)

# ============================================================
# DISCOGS INDEX
# ============================================================

discogs_index = {}

for item in data:

    if not isinstance(item, dict):
        continue

    rid = item.get("id")

    if rid is None:
        basic = item.get("basic_information")

        if isinstance(basic, dict):
            rid = basic.get("id")

    try:
        rid = int(rid)
    except (TypeError, ValueError):
        continue

    discogs_index[rid] = item

print("Unieke IDs:", len(discogs_index))

# ============================================================
# DATABASE OPENEN
# ============================================================

db = sqlite3.connect(DB_FILE)
db.row_factory = sqlite3.Row

tables = {
    r[0]
    for r in db.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
    )
}

if "releases" not in tables:
    db.close()
    raise RuntimeError("Tabel 'releases' ontbreekt.")

columns = {
    r[1]
    for r in db.execute("PRAGMA table_info(releases)")
}

if "discogs" not in columns:
    db.close()
    raise RuntimeError("Kolom 'discogs' ontbreekt in releases.")

# ============================================================
# DATABASE STATISTIEKEN
# ============================================================

total = db.execute(
    "SELECT COUNT(*) FROM releases"
).fetchone()[0]

with_id = db.execute("""
    SELECT COUNT(*)
    FROM releases
    WHERE discogs IS NOT NULL
      AND TRIM(discogs) <> ''
""").fetchone()[0]

with_link = db.execute("""
    SELECT COUNT(*)
    FROM releases
    WHERE discogs_link IS NOT NULL
      AND TRIM(discogs_link) <> ''
""").fetchone()[0]

print()
print("=" * 75)
print("DATABASE")
print("=" * 75)

print("Releases        :", total)
print("Met Discogs ID  :", with_id)
print("Met Discogs link:", with_link)

# ============================================================
# MATCH CONTROL
# ============================================================

rows = db.execute("""
    SELECT id, artist, title, discogs
    FROM releases
    WHERE discogs IS NOT NULL
      AND TRIM(discogs) <> ''
    ORDER BY id
""").fetchall()

matched = []
missing = []

for row in rows:

    try:
        rid = int(str(row["discogs"]).strip())
    except (TypeError, ValueError):
        missing.append(row)
        continue

    if rid in discogs_index:
        matched.append(row)
    else:
        missing.append(row)

print()
print("=" * 75)
print("MATCH RESULTAAT")
print("=" * 75)

print("Database IDs :", len(rows))
print("Match JSON   :", len(matched))
print("Geen match  :", len(missing))

# ============================================================
# EERSTE MATCH TONEN
# ============================================================

if matched:

    row = matched[0]

    rid = int(str(row["discogs"]).strip())
    item = discogs_index[rid]

    basic = item.get("basic_information", {})

    print()
    print("=" * 75)
    print("EERSTE MATCH")
    print("=" * 75)

    print("Database ID :", row["id"])
    print("Artist      :", row["artist"])
    print("Title       :", row["title"])
    print("Discogs ID  :", rid)

    if isinstance(basic, dict):
        print()
        print("JSON artist :", basic.get("title"))
        print("JSON title  :", basic.get("title"))
        print("JSON year   :", basic.get("year"))

# ============================================================
# NIET GEVONDEN
# ============================================================

if missing:

    print()
    print("=" * 75)
    print("EERSTE 20 NIET GEVONDEN")
    print("=" * 75)

    for row in missing[:20]:
        print(
            f"{row['id']} | "
            f"{row['artist']} | "
            f"{row['title']} | "
            f"Discogs={row['discogs']}"
        )

# ============================================================
# EINDE
# ============================================================

db.close()

print()
print("=" * 75)
print("CONTROLE KLAAR")
print("=" * 75)
print("DATABASE IS NIET GEWIJZIGD.")
print("=" * 75)

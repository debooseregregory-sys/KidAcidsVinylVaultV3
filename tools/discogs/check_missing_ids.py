import json
import sqlite3
from pathlib import Path

BASE = Path(r"C:\Users\andyb\Desktop\KidAcidsVinylVaultV3")

JSON_FILE = BASE / "data" / "discogs" / "kid_acid_collection.json"
DB_FILE = BASE / "data" / "vinylvault.db"

print("=" * 90)
print("KID ACID'S VINYL VAULT V3")
print("DISCOGS - CONTROLE ONTBREKENDE IDS")
print("=" * 90)
print()

# ------------------------------------------------------------
# BESTANDEN CONTROLEREN
# ------------------------------------------------------------

print("JSON:")
print(JSON_FILE)

if not JSON_FILE.is_file():
    raise RuntimeError(
        "JSON-bestand bestaat niet:\n" + str(JSON_FILE)
    )

print()
print("DATABASE:")
print(DB_FILE)

if not DB_FILE.is_file():
    raise RuntimeError(
        "Database bestaat niet:\n" + str(DB_FILE)
    )

# ------------------------------------------------------------
# JSON LADEN
# ------------------------------------------------------------

print()
print("=" * 90)
print("JSON LADEN")
print("=" * 90)

with JSON_FILE.open("r", encoding="utf-8") as f:
    data = json.load(f)

if not isinstance(data, list):
    raise RuntimeError(
        "JSON heeft niet het verwachte formaat: lijst."
    )

json_ids = set()

for item in data:
    if not isinstance(item, dict):
        continue

    value = item.get("id")

    try:
        if value is not None:
            json_ids.add(int(value))
    except (TypeError, ValueError):
        pass

print("JSON records :", len(data))
print("Unieke IDs   :", len(json_ids))

# ------------------------------------------------------------
# DATABASE OPENEN
# ------------------------------------------------------------

db = sqlite3.connect(str(DB_FILE))
db.row_factory = sqlite3.Row

try:

    # --------------------------------------------------------
    # TABEL CONTROLEREN
    # --------------------------------------------------------

    tables = {
        row["name"]
        for row in db.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        )
    }

    if "releases" not in tables:
        raise RuntimeError(
            "Tabel 'releases' ontbreekt in de database."
        )

    columns = {
        row["name"]
        for row in db.execute(
            "PRAGMA table_info(releases)"
        )
    }

    required = {
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
    }

    missing = required - columns

    if missing:
        raise RuntimeError(
            "Ontbrekende kolommen in releases: "
            + ", ".join(sorted(missing))
        )

    # --------------------------------------------------------
    # RELEASES MET DISCOGS ID
    # --------------------------------------------------------

    rows = db.execute(
        """
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
          AND TRIM(CAST(discogs AS TEXT)) <> ''
        ORDER BY id
        """
    ).fetchall()

    print()
    print("=" * 90)
    print("DATABASE")
    print("=" * 90)

    print("Lokale releases :", db.execute(
        "SELECT COUNT(*) FROM releases"
    ).fetchone()[0])

    print("Met Discogs ID  :", len(rows))

    # --------------------------------------------------------
    # ONTBREKENDE IDS
    # --------------------------------------------------------

    missing_rows = []

    for row in rows:
        try:
            discogs_id = int(str(row["discogs"]).strip())
        except (TypeError, ValueError):
            continue

        if discogs_id not in json_ids:
            missing_rows.append(row)

    print("JSON matches    :", len(rows) - len(missing_rows))
    print("Geen JSON match :", len(missing_rows))

    # --------------------------------------------------------
    # RESULTAAT
    # --------------------------------------------------------

    print()
    print("=" * 90)
    print("ONTBREKENDE DISCOGS IDS")
    print("=" * 90)

    if not missing_rows:
        print()
        print("GEEN ONTBREKENDE IDS.")
        print()
    else:

        for number, row in enumerate(missing_rows, 1):

            print(
                f"{number:03d} | "
                f"DB ID={row['id']} | "
                f"Discogs={row['discogs']} | "
                f"{row['artist']} | "
                f"{row['title']}"
            )

    # --------------------------------------------------------
    # BELANGRIJKE VEILIGHEIDSCONTROLE
    # --------------------------------------------------------

    print()
    print("=" * 90)
    print("DATABASE-CONTROLE")
    print("=" * 90)

    print()
    print("DIT SCRIPT HEEFT GEEN DATABASE-WIJZIGINGEN UITGEVOERD.")
    print("Geen UPDATE.")
    print("Geen INSERT.")
    print("Geen DELETE.")
    print("Geen COMMIT.")

finally:
    db.close()

print()
print("=" * 90)
print("CONTROLE KLAAR")
print("=" * 90)

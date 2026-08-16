from pathlib import Path
import sqlite3
import json
import shutil
from datetime import datetime
import re
import unicodedata

BASE = Path(r"C:\Users\andyb\Desktop\KidAcidsVinylVaultV3")
DB = BASE / "data" / "vinylvault.db"
JSON_FILE = BASE / "data" / "discogs_public_collection.json"
BACKUP_DIR = BASE / "data" / "backup"

print("=" * 90)
print("KID ACID'S VINYL VAULT V3")
print("DEFINITIEVE DISCOGS MASTER MERGE")
print("=" * 90)
print()

# ============================================================
# BACKUP
# ============================================================

BACKUP_DIR.mkdir(
    parents=True,
    exist_ok=True
)

stamp = datetime.now().strftime(
    "%Y%m%d_%H%M%S"
)

backup = BACKUP_DIR / f"vinylvault_before_discogs_merge_{stamp}.db"

shutil.copy2(
    DB,
    backup
)

print("BACKUP GEMAAKT:")
print(backup)
print()

# ============================================================
# JSON
# ============================================================

print("Discogs JSON laden...")

with open(
    JSON_FILE,
    "r",
    encoding="utf-8"
) as f:
    collection = json.load(f)

print(
    f"Openbare records: {len(collection)}"
)

# ============================================================
# DATABASE
# ============================================================

conn = sqlite3.connect(DB)
cur = conn.cursor()

cur.execute(
    "SELECT name FROM sqlite_master "
    "WHERE type='table' AND name='releases'"
)

if not cur.fetchone():
    raise RuntimeError(
        "Tabel 'releases' bestaat niet."
    )

# ============================================================
# JSON RECORD OMZETTEN
# ============================================================

def get_remote(item):

    basic = item.get(
        "basic_information",
        {}
    )

    discogs_id = basic.get("id")

    title = (
        basic.get("title")
        or ""
    )

    artists = []

    for a in basic.get(
        "artists",
        []
    ):

        if not isinstance(a, dict):
            continue

        name = a.get("name")

        if name:
            artists.append(
                str(name)
            )

    artist = ", ".join(artists)

    labels = []
    catalogs = []

    for l in basic.get(
        "labels",
        []
    ):

        if not isinstance(l, dict):
            continue

        name = l.get("name")
        catno = l.get("catno")

        if name:
            labels.append(
                str(name)
            )

        if catno:
            catalogs.append(
                str(catno)
            )

    label = " / ".join(labels)

    catalog = " / ".join(
        catalogs
    )

    formats = []

    for fmt in basic.get(
        "formats",
        []
    ):

        if not isinstance(
            fmt,
            dict
        ):
            continue

        name = fmt.get("name")

        if name:
            formats.append(
                str(name)
            )

    fmt = " / ".join(formats)

    cover = (
        basic.get("cover_image")
        or basic.get("thumb")
        or ""
    )

    year = basic.get("year")

    resource_url = (
        basic.get("resource_url")
        or ""
    )

    if discogs_id:
        discogs_link = (
            f"https://www.discogs.com/release/"
            f"{discogs_id}"
        )
    else:
        discogs_link = ""

    return {
        "id": discogs_id,
        "artist": artist,
        "title": str(title),
        "label": label,
        "catalog": catalog,
        "year": year,
        "genre": ", ".join(
            str(x)
            for x in basic.get(
                "genres",
                []
            )
            if x
        ),
        "discogs": str(
            discogs_id
        ) if discogs_id else "",
        "discogs_link": discogs_link,
        "cover": cover,
        "format": fmt,
        "resource_url": resource_url,
    }


# ============================================================
# MASTER INDEX
# ============================================================

print()
print("Discogs master-index bouwen...")

remote_by_id = {}

for item in collection:

    data = get_remote(item)

    rid = data["id"]

    if rid:
        remote_by_id[
            str(rid)
        ] = data

print(
    f"Unieke Discogs IDs: "
    f"{len(remote_by_id)}"
)

# ============================================================
# LOKALE RECORDS
# ============================================================

cur.execute(
    """
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
    """
)

local_rows = cur.fetchall()

print(
    f"Lokale releases: "
    f"{len(local_rows)}"
)

# ============================================================
# MATCH OP BESTAANDE DISCOGS ID
# ============================================================

matched_id = 0
updated = 0
skipped = 0

for row in local_rows:

    (
        local_id,
        old_artist,
        old_title,
        old_label,
        old_catalog,
        old_discogs,
        old_link,
        storage_code
    ) = row

    if not old_discogs:
        continue

    rid = str(
        old_discogs
    ).strip()

    remote = remote_by_id.get(
        rid
    )

    if not remote:
        continue

    # --------------------------------------------------------
    # ALLEEN MASTER DATA UIT DISCOGS
    # KASTCODE BLIJFT 100% ONAANGETAST
    # --------------------------------------------------------

    cur.execute(
        """
        UPDATE releases

        SET
            artist = ?,
            title = ?,
            label = ?,
            catalog = ?,
            year = ?,
            genre = ?,
            discogs = ?,
            discogs_link = ?,
            cover = ?,
            updated_at = datetime('now')

        WHERE id = ?
        """,
        (
            remote["artist"],
            remote["title"],
            remote["label"],
            remote["catalog"],
            remote["year"],
            remote["genre"],
            remote["discogs"],
            remote["discogs_link"],
            remote["cover"],
            local_id,
        )
    )

    matched_id += 1
    updated += 1


# ============================================================
# TWEEDE STAP:
# MATCH OP EXACTE TITEL + ARTIEST
# ALLEEN ALS ER NOG GEEN DISCOGS ID IS
# ============================================================

def normalize(value):

    if not value:
        return ""

    value = unicodedata.normalize(
        "NFKD",
        str(value)
    )

    value = value.encode(
        "ascii",
        "ignore"
    ).decode(
        "ascii"
    ).lower()

    value = value.replace(
        "&",
        "and"
    )

    value = re.sub(
        r"[^a-z0-9]+",
        " ",
        value
    )

    return " ".join(
        value.split()
    )


exact_index = {}

for remote in remote_by_id.values():

    key = (
        normalize(
            remote["artist"]
        ),
        normalize(
            remote["title"]
        )
    )

    if not key[0] or not key[1]:
        continue

    exact_index.setdefault(
        key,
        []
    ).append(remote)


for row in local_rows:

    (
        local_id,
        old_artist,
        old_title,
        old_label,
        old_catalog,
        old_discogs,
        old_link,
        storage_code
    ) = row

    # Alleen records zonder ID
    if old_discogs:
        continue

    key = (
        normalize(old_artist),
        normalize(old_title)
    )

    if not key[0] or not key[1]:
        continue

    candidates = exact_index.get(
        key,
        []
    )

    # Alleen volledig unieke match
    if len(candidates) != 1:
        continue

    remote = candidates[0]

    cur.execute(
        """
        UPDATE releases

        SET
            artist = ?,
            title = ?,
            label = ?,
            catalog = ?,
            year = ?,
            genre = ?,
            discogs = ?,
            discogs_link = ?,
            cover = ?,
            updated_at = datetime('now')

        WHERE id = ?
        """,
        (
            remote["artist"],
            remote["title"],
            remote["label"],
            remote["catalog"],
            remote["year"],
            remote["genre"],
            remote["discogs"],
            remote["discogs_link"],
            remote["cover"],
            local_id,
        )
    )

    matched_id += 1
    updated += 1


# ============================================================
# COMMIT
# ============================================================

conn.commit()

# ============================================================
# RESULTAAT
# ============================================================

cur.execute(
    """
    SELECT COUNT(*)
    FROM releases
    WHERE discogs IS NOT NULL
      AND TRIM(discogs) <> ''
    """
)

discogs_count = cur.fetchone()[0]

cur.execute(
    """
    SELECT COUNT(*)
    FROM releases
    WHERE catalog IS NOT NULL
      AND TRIM(catalog) <> ''
    """
)

catalog_count = cur.fetchone()[0]

cur.execute(
    """
    SELECT COUNT(*)
    FROM releases
    WHERE storage_code IS NOT NULL
      AND TRIM(storage_code) <> ''
    """
)

storage_count = cur.fetchone()[0]

print()
print("=" * 90)
print("KLAAR")
print("=" * 90)
print()

print(
    f"Openbare records       : {len(remote_by_id)}"
)

print(
    f"Lokale releases        : {len(local_rows)}"
)

print(
    f"Gematcht via Discogs ID: {matched_id}"
)

print(
    f"Database updates       : {updated}"
)

print(
    f"Met Discogs ID         : {discogs_count}"
)

print(
    f"Met catalogus          : {catalog_count}"
)

print(
    f"Met kastcode           : {storage_count}"
)

print()
print(
    "KASTCODES ZIJN NIET GEWIJZIGD."
)

print()
print(
    "BACKUP:"
)

print(
    backup
)

conn.close()

print()
print(
    "DATABASE IS BIJGEWERKT."
)

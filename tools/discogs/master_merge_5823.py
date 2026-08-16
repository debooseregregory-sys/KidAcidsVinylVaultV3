from pathlib import Path
import sqlite3
import json
import shutil
import re
import unicodedata
from datetime import datetime

BASE = Path(r"C:\Users\andyb\Desktop\KidAcidsVinylVaultV3")
DB = BASE / "data" / "vinylvault.db"
JSON_FILE = BASE / "data" / "discogs_public_collection.json"
BACKUP_DIR = BASE / "data" / "backup"

# ============================================================
# NORMALISATIE
# ============================================================

def norm(value):
    if value is None:
        return ""

    s = str(value)

    s = unicodedata.normalize(
        "NFKD",
        s
    ).encode(
        "ascii",
        "ignore"
    ).decode(
        "ascii"
    ).lower()

    s = s.replace("&", " and ")
    s = s.replace("+", " and ")

    s = re.sub(
        r"[^a-z0-9]+",
        " ",
        s
    )

    return " ".join(
        s.split()
    )


def catnorm(value):
    return re.sub(
        r"[^a-z0-9]",
        "",
        norm(value)
    )


def discogs_id_from_link(value):

    if not value:
        return ""

    m = re.search(
        r"/release/(\d+)",
        str(value)
    )

    return m.group(1) if m else ""


# ============================================================
# DISCOGS RECORD
# ============================================================

def parse_discogs(item):

    basic = item.get(
        "basic_information",
        {}
    )

    if not isinstance(
        basic,
        dict
    ):
        return None

    rid = basic.get("id")

    if not rid:
        return None

    artists = []

    for a in basic.get(
        "artists",
        []
    ):

        if isinstance(a, dict):

            name = a.get("name")

            if name:
                artists.append(
                    str(name)
                )

    labels = []
    catalogs = []

    for label in basic.get(
        "labels",
        []
    ):

        if not isinstance(
            label,
            dict
        ):
            continue

        name = label.get("name")
        catno = label.get("catno")

        if name:
            labels.append(
                str(name)
            )

        if catno:
            catalogs.append(
                str(catno)
            )

    genres = []

    for g in basic.get(
        "genres",
        []
    ):

        if g:
            genres.append(
                str(g)
            )

    formats = []

    for fmt in basic.get(
        "formats",
        []
    ):

        if isinstance(
            fmt,
            dict
        ):

            name = fmt.get("name")

            if name:
                formats.append(
                    str(name)
                )

    return {
        "id": str(rid),

        "artist": ", ".join(
            artists
        ),

        "title": str(
            basic.get("title") or ""
        ),

        "label": " / ".join(
            labels
        ),

        "catalog": " / ".join(
            catalogs
        ),

        "year": basic.get(
            "year"
        ),

        "genre": ", ".join(
            genres
        ),

        "format": " / ".join(
            formats
        ),

        "cover": str(
            basic.get("cover_image")
            or basic.get("thumb")
            or ""
        ),

        "link":
            f"https://www.discogs.com/release/{rid}"
    }


# ============================================================
# START
# ============================================================

print()
print("=" * 90)
print("KID ACID'S VINYL VAULT V3")
print("DISCOGS 5823 MASTER MERGE")
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

backup = (
    BACKUP_DIR
    / f"vinylvault_before_master_merge_{stamp}.db"
)

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

    raw = json.load(f)

if not isinstance(
    raw,
    list
):

    raise RuntimeError(
        "Discogs JSON is geen lijst."
    )

print(
    f"JSON records: {len(raw)}"
)

# ============================================================
# ALLE 5823 RECORDS
# ============================================================

remote = []

for item in raw:

    if not isinstance(
        item,
        dict
    ):
        continue

    r = parse_discogs(
        item
    )

    if r:
        remote.append(r)

print(
    f"Bruikbaar: {len(remote)}"
)

if len(remote) < 5000:

    raise RuntimeError(
        "TE WEINIG DISCOGS RECORDS "
        f"GELEZEN: {len(remote)}"
    )

# ============================================================
# DATABASE
# ============================================================

print()
print("Database laden...")

conn = sqlite3.connect(
    DB
)

cur = conn.cursor()

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
    ORDER BY id
    """
)

local = cur.fetchall()

print(
    f"Lokale releases: {len(local)}"
)

# ============================================================
# INDEXEN
# ============================================================

print()
print("Indexen bouwen...")

by_id = {}
by_catalog = {}
by_artist_title = {}

for r in remote:

    by_id[
        r["id"]
    ] = r

    c = catnorm(
        r["catalog"]
    )

    if c:

        by_catalog.setdefault(
            c,
            []
        ).append(r)

    a = norm(
        r["artist"]
    )

    t = norm(
        r["title"]
    )

    if a and t:

        key = (
            a,
            t
        )

        by_artist_title.setdefault(
            key,
            []
        ).append(r)

print(
    f"Discogs IDs        : {len(by_id)}"
)

print(
    f"Catalogi           : {len(by_catalog)}"
)

print(
    f"Artiest + titel    : {len(by_artist_title)}"
)

# ============================================================
# MATCHING
# ============================================================

existing_id = 0
existing_link = 0
catalog_match = 0
artist_title_match = 0
ambiguous = 0
no_match = 0

updates = []

for n, row in enumerate(
    local,
    1
):

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

    remote = None
    method = ""

    # --------------------------------------------------------
    # 1. BESTAANDE ID
    # --------------------------------------------------------

    if discogs:

        rid = str(
            discogs
        ).strip()

        if rid in by_id:

            remote = by_id[
                rid
            ]

            method = (
                "BESTAANDE DISCOGS ID"
            )

            existing_id += 1

    # --------------------------------------------------------
    # 2. LINK
    # --------------------------------------------------------

    if remote is None and discogs_link:

        rid = discogs_id_from_link(
            discogs_link
        )

        if rid in by_id:

            remote = by_id[
                rid
            ]

            method = (
                "BESTAANDE LINK"
            )

            existing_link += 1

    # --------------------------------------------------------
    # 3. CATALOGUS
    # --------------------------------------------------------

    if remote is None and catalog:

        c = catnorm(
            catalog
        )

        candidates = by_catalog.get(
            c,
            []
        )

        if len(candidates) == 1:

            remote = candidates[0]

            method = (
                "UNIEKE CATALOGUS"
            )

            catalog_match += 1

        elif len(candidates) > 1:

            # Probeer label te gebruiken
            nl = norm(
                label
            )

            label_candidates = [
                x
                for x in candidates
                if nl
                and norm(x["label"]) == nl
            ]

            if len(
                label_candidates
            ) == 1:

                remote = (
                    label_candidates[0]
                )

                method = (
                    "CATALOGUS + LABEL"
                )

                catalog_match += 1

            else:

                ambiguous += 1

    # --------------------------------------------------------
    # 4. UNIEKE ARTIEST + TITEL
    # --------------------------------------------------------

    if remote is None:

        key = (
            norm(artist),
            norm(title)
        )

        if key[0] and key[1]:

            candidates = (
                by_artist_title.get(
                    key,
                    []
                )
            )

            if len(candidates) == 1:

                remote = candidates[0]

                method = (
                    "UNIEKE ARTIEST + TITEL"
                )

                artist_title_match += 1

            elif len(candidates) > 1:

                nl = norm(
                    label
                )

                label_candidates = [
                    x
                    for x in candidates
                    if nl
                    and norm(x["label"]) == nl
                ]

                if len(
                    label_candidates
                ) == 1:

                    remote = (
                        label_candidates[0]
                    )

                    method = (
                        "ARTIEST + TITEL + LABEL"
                    )

                    artist_title_match += 1

                else:

                    ambiguous += 1

    # --------------------------------------------------------
    # OPSLAAN
    # --------------------------------------------------------

    if remote is None:

        no_match += 1

    else:

        updates.append(
            (
                local_id,
                remote,
                method
            )
        )

    if n % 500 == 0:

        print(
            f"{n}/{len(local)} "
            f"| matches={len(updates)} "
            f"| geen={no_match} "
            f"| twijfel={ambiguous}"
        )

# ============================================================
# DATABASE UPDATE
# ============================================================

print()
print("=" * 90)
print("DATABASE BIJWERKEN")
print("=" * 90)
print()

for (
    local_id,
    remote,
    method
) in updates:

    # storage_code STAAT HIER EXPRES NIET IN.
    # Daardoor kan deze UPDATE de kastcode niet wijzigen.

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
            remote["discogs"]
            if "discogs" in remote
            else remote["id"],
            remote["link"],
            remote["cover"],
            local_id
        )
    )

conn.commit()

# ============================================================
# CONTROLEREN
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
    WHERE discogs_link IS NOT NULL
    AND TRIM(discogs_link) <> ''
    """
)

link_count = cur.fetchone()[0]

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

conn.close()

# ============================================================
# RESULTAAT
# ============================================================

print()
print("=" * 90)
print("KLAAR")
print("=" * 90)
print()

print(
    f"Openbare records       : {len(remote)}"
)

print(
    f"Lokale releases        : {len(local)}"
)

print()
print(
    f"Bestaande Discogs ID   : {existing_id}"
)

print(
    f"Bestaande links        : {existing_link}"
)

print(
    f"Catalogusmatches       : {catalog_match}"
)

print(
    f"Artiest+titelmatches   : {artist_title_match}"
)

print(
    f"Totaal gekoppeld       : {len(updates)}"
)

print(
    f"Geen match             : {no_match}"
)

print(
    f"Twijfel/ambigu         : {ambiguous}"
)

print()
print(
    f"MET DISCOGS ID         : {discogs_count}"
)

print(
    f"MET DISCOGS LINK       : {link_count}"
)

print(
    f"MET CATALOGUS          : {catalog_count}"
)

print(
    f"MET KASTCODE           : {storage_count}"
)

print()
print(
    "KASTCODES NIET GEWIJZIGD."
)

print(
    "TRACKS NIET GEWIJZIGD."
)

print(
    "MP3-KOPPELINGEN NIET GEWIJZIGD."
)

print()
print(
    "BACKUP:"
)

print(
    backup
)

print()
print(
    "DATABASE IS BIJGEWERKT."
)

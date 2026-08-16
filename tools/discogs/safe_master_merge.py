from pathlib import Path
import sqlite3
import json
import re
import shutil
import unicodedata
from datetime import datetime

BASE = Path(r"C:\Users\andyb\Desktop\KidAcidsVinylVaultV3")
DB = BASE / "data" / "vinylvault.db"
JSON_FILE = BASE / "data" / "discogs_public_collection.json"
BACKUP_DIR = BASE / "data" / "backup"

# ============================================================
# NORMALISEREN
# ============================================================

def norm(value):
    if value is None:
        return ""

    value = str(value)

    value = unicodedata.normalize(
        "NFKD",
        value
    ).encode(
        "ascii",
        "ignore"
    ).decode(
        "ascii"
    ).lower()

    value = value.replace("&", " and ")
    value = value.replace("+", " and ")

    value = re.sub(
        r"[^a-z0-9]+",
        " ",
        value
    )

    return " ".join(value.split())


def catnorm(value):
    if value is None:
        return ""

    return re.sub(
        r"[^a-z0-9]",
        "",
        norm(value)
    )


def extract_discogs_id(link):
    if not link:
        return ""

    m = re.search(
        r"/release/(\d+)",
        str(link)
    )

    if m:
        return m.group(1)

    return ""


# ============================================================
# DISCOGS RECORD
# ============================================================

def parse_remote(item):

    basic = item.get(
        "basic_information",
        {}
    )

    rid = basic.get("id")

    if not rid:
        return None

    artists = []

    for a in basic.get("artists", []):
        if isinstance(a, dict):
            name = a.get("name")
            if name:
                artists.append(str(name))

    labels = []
    catalogs = []

    for l in basic.get("labels", []):
        if not isinstance(l, dict):
            continue

        name = l.get("name")
        cat = l.get("catno")

        if name:
            labels.append(str(name))

        if cat:
            catalogs.append(str(cat))

    formats = []

    for fmt in basic.get("formats", []):
        if isinstance(fmt, dict):
            name = fmt.get("name")
            if name:
                formats.append(str(name))

    genres = []

    for g in basic.get("genres", []):
        if g:
            genres.append(str(g))

    return {
        "id": str(rid),
        "artist": ", ".join(artists),
        "title": str(basic.get("title") or ""),
        "label": " / ".join(labels),
        "catalog": " / ".join(catalogs),
        "year": basic.get("year"),
        "genre": ", ".join(genres),
        "format": " / ".join(formats),
        "cover": str(
            basic.get("cover_image")
            or basic.get("thumb")
            or ""
        ),
        "link": f"https://www.discogs.com/release/{rid}",
    }


# ============================================================
# START
# ============================================================

print()
print("=" * 90)
print("KID ACID'S VINYL VAULT V3")
print("DEFINITIEVE VEILIGE DISCOGS KOPPELING")
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
    / f"vinylvault_before_safe_match_{stamp}.db"
)

shutil.copy2(
    DB,
    backup
)

print("BACKUP:")
print(backup)
print()

# ============================================================
# JSON LADEN
# ============================================================

print("Openbare Discogs collectie laden...")

with open(
    JSON_FILE,
    "r",
    encoding="utf-8"
) as f:
    raw = json.load(f)

remote = []

for item in raw:

    r = parse_remote(item)

    if r:
        remote.append(r)

print(
    f"Discogs records: {len(remote)}"
)

# ============================================================
# DATABASE
# ============================================================

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

print(
    f"Lokale releases: {len(local)}"
)

# ============================================================
# INDEXEN
# ============================================================

print()
print("Indexen bouwen...")

remote_by_id = {}

catalog_index = {}

artist_title_index = {}

for r in remote:

    remote_by_id[r["id"]] = r

    # Catalogus
    c = catnorm(
        r["catalog"]
    )

    if c:
        catalog_index.setdefault(
            c,
            []
        ).append(r)

    # Artist + title
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

        artist_title_index.setdefault(
            key,
            []
        ).append(r)

print(
    f"Discogs IDs        : {len(remote_by_id)}"
)

print(
    f"Catalogus-index     : {len(catalog_index)}"
)

print(
    f"Artiest+titel-index : {len(artist_title_index)}"
)

# ============================================================
# MATCHING
# ============================================================

matched_existing_id = 0
matched_link = 0
matched_catalog = 0
matched_artist_title = 0
already_correct = 0
ambiguous = 0
no_match = 0

updates = []

used_remote_ids = set()

for n, row in enumerate(local, 1):

    (
        local_id,
        local_artist,
        local_title,
        local_label,
        local_catalog,
        local_discogs,
        local_link,
        storage_code
    ) = row

    remote = None
    match_type = ""

    # --------------------------------------------------------
    # 1. BESTAANDE DISCOGS ID
    # --------------------------------------------------------

    if local_discogs:

        rid = str(
            local_discogs
        ).strip()

        remote = remote_by_id.get(
            rid
        )

        if remote:
            match_type = "BESTAANDE ID"
            matched_existing_id += 1

    # --------------------------------------------------------
    # 2. BESTAANDE LINK
    # --------------------------------------------------------

    if remote is None and local_link:

        rid = extract_discogs_id(
            local_link
        )

        if rid:

            remote = remote_by_id.get(
                rid
            )

            if remote:

                match_type = "BESTAANDE LINK"
                matched_link += 1

    # --------------------------------------------------------
    # 3. UNIEKE CATALOGUSMATCH
    # --------------------------------------------------------

    if remote is None and local_catalog:

        lc = catnorm(
            local_catalog
        )

        candidates = catalog_index.get(
            lc,
            []
        )

        if len(candidates) == 1:

            remote = candidates[0]
            match_type = "UNIEKE CATALOGUS"
            matched_catalog += 1

        elif len(candidates) > 1:

            # Probeer label mee te nemen
            label_norm = norm(
                local_label
            )

            label_candidates = []

            for candidate in candidates:

                if (
                    label_norm
                    and
                    norm(candidate["label"])
                    == label_norm
                ):

                    label_candidates.append(
                        candidate
                    )

            if len(label_candidates) == 1:

                remote = label_candidates[0]
                match_type = (
                    "CATALOGUS + LABEL"
                )
                matched_catalog += 1

            else:

                ambiguous += 1

    # --------------------------------------------------------
    # 4. UNIEKE ARTIEST + TITEL
    # --------------------------------------------------------

    if remote is None:

        a = norm(
            local_artist
        )

        t = norm(
            local_title
        )

        if a and t:

            candidates = artist_title_index.get(
                (a, t),
                []
            )

            if len(candidates) == 1:

                remote = candidates[0]

                match_type = (
                    "UNIEKE ARTIEST + TITEL"
                )

                matched_artist_title += 1

            elif len(candidates) > 1:

                # Label kan ambiguiteit oplossen
                label_norm = norm(
                    local_label
                )

                label_candidates = [
                    x
                    for x in candidates
                    if label_norm
                    and norm(x["label"])
                    == label_norm
                ]

                if len(label_candidates) == 1:

                    remote = label_candidates[0]

                    match_type = (
                        "ARTIEST + TITEL + LABEL"
                    )

                    matched_artist_title += 1

                else:

                    ambiguous += 1

    # --------------------------------------------------------
    # GEEN MATCH
    # --------------------------------------------------------

    if remote is None:

        no_match += 1

    else:

        rid = remote["id"]

        # Een remote release mag maar aan één lokale
        # release gekoppeld worden via deze veilige ronde.
        if rid in used_remote_ids:

            # Bestaande ID's mogen wel meerdere lokale
            # exemplaren hebben. Alleen nieuwe matches
            # beschermen we tegen dubbel toewijzen.
            if match_type not in (
                "BESTAANDE ID",
                "BESTAANDE LINK"
            ):

                remote = None
                ambiguous += 1

        if remote:

            used_remote_ids.add(
                rid
            )

            updates.append(
                (
                    local_id,
                    remote,
                    match_type,
                    storage_code
                )
            )

    if n % 500 == 0:

        print(
            f"{n}/{len(local)} "
            f"| veilige matches={len(updates)} "
            f"| geen={no_match} "
            f"| twijfel={ambiguous}"
        )

# ============================================================
# DATABASE BIJWERKEN
# ============================================================

print()
print("=" * 90)
print("VEILIGE MATCHES SCHRIJVEN")
print("=" * 90)
print()

for (
    local_id,
    remote,
    match_type,
    storage_code
) in updates:

    # BELANGRIJK:
    # storage_code wordt NIET gewijzigd.
    # Tracks worden NIET gewijzigd.
    # MP3 wordt NIET gewijzigd.

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
            remote["id"],
            remote["link"],
            remote["cover"],
            local_id
        )
    )

conn.commit()

# ============================================================
# RESULTAAT CONTROLEREN
# ============================================================

cur.execute("""
    SELECT COUNT(*)
    FROM releases
    WHERE discogs IS NOT NULL
      AND TRIM(discogs) <> ''
""")

discogs_count = cur.fetchone()[0]

cur.execute("""
    SELECT COUNT(*)
    FROM releases
    WHERE discogs_link IS NOT NULL
      AND TRIM(discogs_link) <> ''
""")

link_count = cur.fetchone()[0]

cur.execute("""
    SELECT COUNT(*)
    FROM releases
    WHERE catalog IS NOT NULL
      AND TRIM(catalog) <> ''
""")

catalog_count = cur.fetchone()[0]

cur.execute("""
    SELECT COUNT(*)
    FROM releases
    WHERE storage_code IS NOT NULL
      AND TRIM(storage_code) <> ''
""")

storage_count = cur.fetchone()[0]

# ============================================================
# SLUIT
# ============================================================

conn.close()

# ============================================================
# EINDRESULTAAT
# ============================================================

print()
print("=" * 90)
print("KLAAR")
print("=" * 90)
print()

print(
    f"Openbare Discogs records : {len(remote)}"
)

print(
    f"Lokale releases          : {len(local)}"
)

print()
print(
    f"Bestaande Discogs ID     : "
    f"{matched_existing_id}"
)

print(
    f"Bestaande links          : "
    f"{matched_link}"
)

print(
    f"Unieke catalogusmatches  : "
    f"{matched_catalog}"
)

print(
    f"Unieke artiest+titel     : "
    f"{matched_artist_title}"
)

print()
print(
    f"TOTAAL VEILIG GEKOPPELD  : "
    f"{len(updates)}"
)

print(
    f"Niet automatisch gekoppeld: "
    f"{no_match}"
)

print(
    f"Ambigu / overgeslagen    : "
    f"{ambiguous}"
)

print()
print(
    f"Nu met Discogs ID        : "
    f"{discogs_count}"
)

print(
    f"Nu met Discogs link      : "
    f"{link_count}"
)

print(
    f"Nu met catalogus         : "
    f"{catalog_count}"
)

print(
    f"Kastcodes                : "
    f"{storage_count}"
)

print()
print(
    "KASTCODES ZIJN NIET GEWIJZIGD."
)

print(
    "TRACKS ZIJN NIET GEWIJZIGD."
)

print(
    "MP3-KOPPELINGEN ZIJN NIET GEWIJZIGD."
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
    "DATABASE IS BIJGEWERKT MET ALLEEN VEILIGE MATCHES."
)

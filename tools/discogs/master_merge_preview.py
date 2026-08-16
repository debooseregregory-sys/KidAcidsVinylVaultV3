import json
import sqlite3
import re
import unicodedata
from pathlib import Path
from difflib import SequenceMatcher

BASE = Path(r"C:\Users\andyb\Desktop\KidAcidsVinylVaultV3")
DB = BASE / "data" / "vinylvault.db"
JSON_FILE = BASE / "data" / "discogs_public_collection.json"
OUT = BASE / "data" / "discogs_merge_preview.txt"

print("=" * 90)
print("KID ACID'S VINYL VAULT V3")
print("VEILIGE MASTER-COLLECTIE MERGE PREVIEW")
print("=" * 90)
print()

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

    replacements = {
        "&": " and ",
        "+": " and ",
        "feat.": " featuring ",
        "feat": " featuring ",
        "ft.": " featuring ",
        "ft": " featuring ",
        "pres.": " presents ",
        "pres": " presents ",
        "e.p.": " ep ",
        "e.p": " ep ",
        "dj ": " dj ",
    }

    for a, b in replacements.items():
        value = value.replace(a, b)

    value = re.sub(
        r"[^a-z0-9]+",
        " ",
        value
    )

    return re.sub(
        r"\s+",
        " ",
        value
    ).strip()


def similarity(a, b):
    a = norm(a)
    b = norm(b)

    if not a or not b:
        return 0

    if a == b:
        return 100

    return SequenceMatcher(
        None,
        a,
        b
    ).ratio() * 100


def catalog_norm(value):
    value = norm(value)
    return re.sub(
        r"[^a-z0-9]",
        "",
        value
    )


# ============================================================
# JSON
# ============================================================

print("JSON laden...")

with open(
    JSON_FILE,
    "r",
    encoding="utf-8"
) as f:
    collection = json.load(f)

print(
    f"Openbare collectie: {len(collection)}"
)

remote = []

for item in collection:

    basic = item.get(
        "basic_information",
        {}
    )

    artists = []

    for a in basic.get(
        "artists",
        []
    ):

        if isinstance(a, dict):
            name = a.get("name") or ""

            if name:
                artists.append(
                    str(name)
                )

    labels = []
    catalogs = []

    for l in basic.get(
        "labels",
        []
    ):

        if not isinstance(l, dict):
            continue

        name = l.get("name") or ""
        cat = l.get("catno") or ""

        if name:
            labels.append(
                str(name)
            )

        if cat:
            catalogs.append(
                str(cat)
            )

    formats = []

    for fmt in basic.get(
        "formats",
        []
    ):

        if isinstance(fmt, dict):

            name = fmt.get("name") or ""

            if name:
                formats.append(
                    str(name)
                )

    remote.append({
        "id": basic.get("id"),
        "instance_id": item.get("instance_id"),
        "artist": ", ".join(artists),
        "title": str(
            basic.get("title") or ""
        ),
        "label": " / ".join(labels),
        "catalog": " / ".join(catalogs),
        "format": " / ".join(formats),
        "year": basic.get("year"),
    })

# ============================================================
# DATABASE
# ============================================================

print()
print("Lokale database laden...")

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
# INDEX REMOTE
# ============================================================

print()
print("Index openbare collectie bouwen...")

by_id = {
    str(r["id"]): r
    for r in remote
    if r["id"] is not None
}

by_catalog = {}

for r in remote:

    cat = catalog_norm(
        r["catalog"]
    )

    if cat:

        by_catalog.setdefault(
            cat,
            []
        ).append(r)

by_title = {}

for r in remote:

    title = norm(
        r["title"]
    )

    if title:

        by_title.setdefault(
            title,
            []
        ).append(r)

print(
    f"Discogs IDs : {len(by_id)}"
)

print(
    f"Catalogi    : {len(by_catalog)}"
)

print(
    f"Titels      : {len(by_title)}"
)

# ============================================================
# MATCH
# ============================================================

print()
print("LOKALE RELEASES CONTROLEREN...")
print()

matched = []
new_remote = []
review = []

matched_remote_ids = set()

for number, row in enumerate(
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

    best = None

    # --------------------------------------------------------
    # 1. BESTAANDE DISCOGS ID
    # --------------------------------------------------------

    if discogs:

        r = by_id.get(
            str(discogs).strip()
        )

        if r:

            best = (
                100,
                "BESTAANDE DISCOGS ID",
                r
            )

    # --------------------------------------------------------
    # 2. EXACT CATALOG
    # --------------------------------------------------------

    if best is None and catalog:

        candidates = by_catalog.get(
            catalog_norm(catalog),
            []
        )

        if len(candidates) == 1:

            best = (
                99,
                "EXACT CATALOG",
                candidates[0]
            )

        elif len(candidates) > 1:

            scored = []

            for r in candidates:

                ts = similarity(
                    title,
                    r["title"]
                )

                ass = similarity(
                    artist,
                    r["artist"]
                )

                scored.append(
                    (
                        ts + ass,
                        r
                    )
                )

            scored.sort(
                reverse=True,
                key=lambda x: x[0]
            )

            if scored:

                best = (
                    min(
                        98,
                        scored[0][0] / 2
                    ),
                    "CATALOG + TITEL/ARTIST",
                    scored[0][1]
                )

    # --------------------------------------------------------
    # 3. EXACT TITEL
    # --------------------------------------------------------

    if best is None:

        candidates = by_title.get(
            norm(title),
            []
        )

        if len(candidates) == 1:

            r = candidates[0]

            ass = similarity(
                artist,
                r["artist"]
            )

            if ass >= 60:

                best = (
                    ass,
                    "EXACT TITEL",
                    r
                )

    # --------------------------------------------------------
    # RESULT
    # --------------------------------------------------------

    if best:

        score, method, r = best

        matched_remote_ids.add(
            r["id"]
        )

        matched.append(
            (
                score,
                method,
                row,
                r
            )
        )

    else:

        review.append(
            row
        )

    if number % 100 == 0:

        print(
            f"{number}/{len(local)} "
            f"| gekoppeld={len(matched)} "
            f"| controleren={len(review)}"
        )

# ============================================================
# REMOTE RECORDS DIE NIET LOKAAL ZIJN
# ============================================================

for r in remote:

    if r["id"] not in matched_remote_ids:

        new_remote.append(
            r
        )

# ============================================================
# PREVIEW
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
        "VEILIGE DISCOGS MASTER MERGE PREVIEW\n"
    )

    f.write(
        "=" * 100 + "\n\n"
    )

    f.write(
        f"OPENBARE RECORDS : {len(remote)}\n"
    )

    f.write(
        f"LOKALE RELEASES  : {len(local)}\n"
    )

    f.write(
        f"GEKOPPELD        : {len(matched)}\n"
    )

    f.write(
        f"CONTROLEREN      : {len(review)}\n"
    )

    f.write(
        f"NIET LOKAAL      : {len(new_remote)}\n"
    )

    f.write("\n\n")

    # --------------------------------------------------------
    # GEKOPPELD
    # --------------------------------------------------------

    f.write(
        "=" * 100 + "\n"
    )

    f.write(
        "GEKOPPELDE LOKALE RELEASES\n"
    )

    f.write(
        "=" * 100 + "\n\n"
    )

    for score, method, local_row, r in matched:

        (
            local_id,
            artist,
            title,
            label,
            catalog,
            discogs,
            link,
            storage
        ) = local_row

        f.write(
            f"LOCAL {local_id} | "
            f"{artist} - {title}\n"
        )

        f.write(
            f"   KASTCODE : {storage or ''}\n"
        )

        f.write(
            f"   DISCogs  : {r['id']}\n"
        )

        f.write(
            f"   REMOTE   : "
            f"{r['artist']} - {r['title']}\n"
        )

        f.write(
            f"   CATALOG  : {r['catalog']}\n"
        )

        f.write(
            f"   FORMAT   : {r['format']}\n"
        )

        f.write(
            f"   SCORE    : {score:.1f}\n"
        )

        f.write(
            f"   METHODE  : {method}\n\n"
        )

    # --------------------------------------------------------
    # CONTROLEREN
    # --------------------------------------------------------

    f.write(
        "=" * 100 + "\n"
    )

    f.write(
        "LOKALE RELEASES ZONDER VEILIGE KOPPELING\n"
    )

    f.write(
        "=" * 100 + "\n\n"
    )

    for row in review:

        (
            local_id,
            artist,
            title,
            label,
            catalog,
            discogs,
            link,
            storage
        ) = row

        f.write(
            f"LOCAL {local_id}\n"
        )

        f.write(
            f"ARTIST  : {artist}\n"
        )

        f.write(
            f"TITLE   : {title}\n"
        )

        f.write(
            f"CATALOG : {catalog or ''}\n"
        )

        f.write(
            f"KASTCODE: {storage or ''}\n\n"
        )

    # --------------------------------------------------------
    # NIEUW
    # --------------------------------------------------------

    f.write(
        "=" * 100 + "\n"
    )

    f.write(
        "OPENBARE RECORDS DIE NIET AAN EEN LOKALE RELEASE ZIJN GEKOPPELD\n"
    )

    f.write(
        "=" * 100 + "\n\n"
    )

    for r in new_remote:

        f.write(
            f"DISCogs ID : {r['id']}\n"
        )

        f.write(
            f"ARTIST     : {r['artist']}\n"
        )

        f.write(
            f"TITLE      : {r['title']}\n"
        )

        f.write(
            f"CATALOG    : {r['catalog']}\n"
        )

        f.write(
            f"FORMAT     : {r['format']}\n"
        )

        f.write(
            f"YEAR       : {r['year'] or ''}\n\n"
        )

conn.close()

# ============================================================
# EINDE
# ============================================================

print()
print("=" * 90)
print("KLAAR")
print("=" * 90)
print()

print(
    f"Openbare records : {len(remote)}"
)

print(
    f"Lokale releases  : {len(local)}"
)

print(
    f"Gekoppeld        : {len(matched)}"
)

print(
    f"Controleren      : {len(review)}"
)

print(
    f"Niet lokaal      : {len(new_remote)}"
)

print()
print(
    "Preview:"
)

print(
    OUT
)

print()
print(
    "DATABASE IS NIET GEWIJZIGD."
)

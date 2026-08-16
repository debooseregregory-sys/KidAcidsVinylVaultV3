from pathlib import Path
import sqlite3
import json
import re
import unicodedata
from difflib import SequenceMatcher

BASE = Path(r"C:\Users\andyb\Desktop\KidAcidsVinylVaultV3")
DB = BASE / "data" / "vinylvault.db"
JSON_FILE = BASE / "data" / "discogs_public_collection.json"
OUT = BASE / "data" / "discogs_final_preview.txt"


# ============================================================
# HELPERS
# ============================================================

def clean(value):
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

    replacements = [
        ("&", " and "),
        ("+", " and "),
        ("feat.", " feat "),
        ("featuring", " feat "),
        ("ft.", " feat "),
        ("vs.", " vs "),
        ("e.p.", " ep "),
        ("e.p", " ep "),
    ]

    for old, new in replacements:
        value = value.replace(old, new)

    value = re.sub(
        r"[^a-z0-9]+",
        " ",
        value
    )

    return " ".join(value.split())


def compact(value):
    return re.sub(
        r"[^a-z0-9]",
        "",
        clean(value)
    )


def similarity(a, b):
    a = clean(a)
    b = clean(b)

    if not a or not b:
        return 0.0

    if a == b:
        return 100.0

    return SequenceMatcher(
        None,
        a,
        b
    ).ratio() * 100.0


def catalog_similarity(a, b):
    a = compact(a)
    b = compact(b)

    if not a or not b:
        return 0.0

    if a == b:
        return 100.0

    if a in b or b in a:
        return 95.0

    return SequenceMatcher(
        None,
        a,
        b
    ).ratio() * 100.0


def artist_similarity(a, b):
    a = clean(a)
    b = clean(b)

    if not a or not b:
        return 0.0

    if a == b:
        return 100.0

    # Extra tolerant voor "A & B" / "A and B"
    sa = set(a.split())
    sb = set(b.split())

    if sa and sb:
        overlap = len(sa & sb) / max(len(sa), len(sb))
        token_score = overlap * 100.0
    else:
        token_score = 0.0

    return max(
        similarity(a, b),
        token_score
    )


# ============================================================
# DISCOGS JSON
# ============================================================

def make_remote(item):

    basic = item.get(
        "basic_information",
        {}
    )

    artists = []

    for artist in basic.get(
        "artists",
        []
    ):
        if isinstance(
            artist,
            dict
        ):
            name = artist.get("name")

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
        "id": basic.get("id"),
        "artist": ", ".join(artists),
        "title": str(
            basic.get("title") or ""
        ),
        "label": " / ".join(labels),
        "catalog": " / ".join(catalogs),
        "format": " / ".join(formats),
        "year": basic.get("year"),
    }


# ============================================================
# LOAD JSON
# ============================================================

print()
print("=" * 90)
print("KID ACID'S VINYL VAULT V3")
print("VEILIGE DISCOGS MASTER MATCH PREVIEW")
print("=" * 90)
print()

print("Discogs JSON laden...")

with open(
    JSON_FILE,
    "r",
    encoding="utf-8"
) as f:
    raw = json.load(f)

remote = []

for item in raw:

    r = make_remote(item)

    if r["id"] is not None:
        remote.append(r)

print(
    f"Openbare records : {len(remote)}"
)


# ============================================================
# LOAD DATABASE
# ============================================================

print()
print("Database laden...")

conn = sqlite3.connect(DB)
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
    f"Lokale releases  : {len(local)}"
)


# ============================================================
# INDEX
# ============================================================

print()
print("Discogs indexen bouwen...")

by_id = {}

by_catalog = {}

by_title = {}

by_artist = {}

for r in remote:

    rid = str(r["id"])

    by_id[rid] = r

    cat = compact(
        r["catalog"]
    )

    if cat:
        by_catalog.setdefault(
            cat,
            []
        ).append(r)

    title = clean(
        r["title"]
    )

    if title:
        by_title.setdefault(
            title,
            []
        ).append(r)

    artist = clean(
        r["artist"]
    )

    if artist:
        by_artist.setdefault(
            artist,
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

print(
    f"Artiesten   : {len(by_artist)}"
)


# ============================================================
# RESULTAATSTRUCTUUR
#
# ELKE RESULTAAT IS ALTIJD:
#
# {
#   "local": tuple,
#   "remote": dict of None,
#   "score": float,
#   "gap": float,
#   "type": str,
#   "title": float,
#   "artist": float,
#   "label": float,
#   "catalog": float
# }
# ============================================================

results = []


# ============================================================
# MATCHING
# ============================================================

print()
print("=" * 90)
print("VOLLEDIGE LOKALE COLLECTIE CONTROLEREN...")
print("=" * 90)
print()

for number, row in enumerate(
    local,
    1
):

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


    # --------------------------------------------------------
    # BESTAANDE DISCOGS ID
    # --------------------------------------------------------

    if local_discogs:

        key = str(
            local_discogs
        ).strip()

        remote_record = by_id.get(
            key
        )

        if remote_record:

            results.append(
                {
                    "local": row,
                    "remote": remote_record,
                    "score": 100.0,
                    "gap": 100.0,
                    "type": "BESTAANDE DISCOGS ID",
                    "title": 100.0,
                    "artist": 100.0,
                    "label": 100.0,
                    "catalog": 100.0,
                }
            )

            if number % 100 == 0:
                print(
                    f"{number}/{len(local)}"
                )

            continue


    # --------------------------------------------------------
    # KANDIDATEN
    # --------------------------------------------------------

    candidates = {}

    local_cat = compact(
        local_catalog
    )

    local_title = clean(
        local_title
    )

    local_artist = clean(
        local_artist
    )

    local_label = clean(
        local_label
    )


    # --------------------------------------------------------
    # CATALOGUS
    # --------------------------------------------------------

    if local_cat:

        for cat, records in by_catalog.items():

            if (
                local_cat == cat
                or local_cat in cat
                or cat in local_cat
            ):

                for r in records:
                    candidates[
                        str(r["id"])
                    ] = r


    # --------------------------------------------------------
    # EXACTE TITEL
    # --------------------------------------------------------

    if local_title:

        for r in by_title.get(
            local_title,
            []
        ):

            candidates[
                str(r["id"])
            ] = r


    # --------------------------------------------------------
    # EXACTE ARTIEST
    # --------------------------------------------------------

    if local_artist:

        for r in by_artist.get(
            local_artist,
            []
        ):

            candidates[
                str(r["id"])
            ] = r


    # --------------------------------------------------------
    # BREDE ZOEK
    #
    # Alleen kandidaten die redelijk overeenkomen.
    # --------------------------------------------------------

    if len(candidates) < 5:

        for r in remote:

            ts = similarity(
                local_title,
                r["title"]
            )

            if ts < 50:
                continue

            ass = artist_similarity(
                local_artist,
                r["artist"]
            )

            if ass < 30:
                continue

            candidates[
                str(r["id"])
            ] = r


    # --------------------------------------------------------
    # SCORE KANDIDATEN
    # --------------------------------------------------------

    scored = []

    for r in candidates.values():

        ts = similarity(
            local_title,
            r["title"]
        )

        ass = artist_similarity(
            local_artist,
            r["artist"]
        )

        ls = similarity(
            local_label,
            r["label"]
        )

        cs = catalog_similarity(
            local_catalog,
            r["catalog"]
        )

        score = (
            ts * 0.45
            +
            ass * 0.30
            +
            cs * 0.20
            +
            ls * 0.05
        )

        # Catalogus bijna gelijk
        if cs >= 99:
            score += 15

        elif cs >= 92:
            score += 8

        # Titel + artiest zeer sterk
        if (
            ts >= 95
            and ass >= 90
        ):
            score += 10

        score = min(
            score,
            100.0
        )

        scored.append(
            {
                "remote": r,
                "score": score,
                "title": ts,
                "artist": ass,
                "label": ls,
                "catalog": cs,
            }
        )


    scored.sort(
        key=lambda x: x["score"],
        reverse=True
    )


    # --------------------------------------------------------
    # GEEN KANDIDAAT
    # --------------------------------------------------------

    if not scored:

        results.append(
            {
                "local": row,
                "remote": None,
                "score": 0.0,
                "gap": 0.0,
                "type": "GEEN KANDIDAAT",
                "title": 0.0,
                "artist": 0.0,
                "label": 0.0,
                "catalog": 0.0,
            }
        )

    else:

        best = scored[0]

        best_score = best["score"]

        second_score = (
            scored[1]["score"]
            if len(scored) > 1
            else 0.0
        )

        gap = (
            best_score
            -
            second_score
        )

        cs = best["catalog"]

        if cs >= 99:

            match_type = "CATALOGUS MATCH"

        elif (
            best_score >= 90
            and gap >= 5
        ):

            match_type = "STERKE MATCH"

        elif (
            best_score >= 78
            and gap >= 4
        ):

            match_type = "WAARSCHIJNLIJKE MATCH"

        elif best_score >= 60:

            match_type = "CONTROLEREN"

        else:

            match_type = "GEEN BETROUWBARE MATCH"

        results.append(
            {
                "local": row,
                "remote": best["remote"],
                "score": best_score,
                "gap": gap,
                "type": match_type,
                "title": best["title"],
                "artist": best["artist"],
                "label": best["label"],
                "catalog": best["catalog"],
            }
        )


    if number % 100 == 0:

        print(
            f"{number}/{len(local)}"
        )


# ============================================================
# GROEPEN
# ============================================================

groups = {
    "BESTAANDE DISCOGS IDS": [],
    "CATALOGUS MATCHES": [],
    "STERKE MATCHES": [],
    "WAARSCHIJNLIJKE MATCHES": [],
    "CONTROLEREN": [],
    "GEEN MATCH": [],
}

for result in results:

    t = result["type"]

    if t == "BESTAANDE DISCOGS ID":

        groups[
            "BESTAANDE DISCOGS IDS"
        ].append(result)

    elif t == "CATALOGUS MATCH":

        groups[
            "CATALOGUS MATCHES"
        ].append(result)

    elif t == "STERKE MATCH":

        groups[
            "STERKE MATCHES"
        ].append(result)

    elif t == "WAARSCHIJNLIJKE MATCH":

        groups[
            "WAARSCHIJNLIJKE MATCHES"
        ].append(result)

    elif t == "CONTROLEREN":

        groups[
            "CONTROLEREN"
        ].append(result)

    else:

        groups[
            "GEEN MATCH"
        ].append(result)


# ============================================================
# PREVIEW SCHRIJVEN
# ============================================================

print()
print("Preview schrijven...")

with open(
    OUT,
    "w",
    encoding="utf-8"
) as f:

    f.write(
        "=" * 100
        + "\n"
    )

    f.write(
        "KID ACID'S VINYL VAULT V3\n"
    )

    f.write(
        "DISCOGS MASTER MERGE PREVIEW\n"
    )

    f.write(
        "=" * 100
        + "\n\n"
    )

    f.write(
        f"OPENBARE RECORDS : {len(remote)}\n"
    )

    f.write(
        f"LOKALE RELEASES  : {len(local)}\n\n"
    )

    for name, items in groups.items():

        f.write(
            f"{name:<28}: "
            f"{len(items)}\n"
        )

    f.write(
        "\n"
    )


    # --------------------------------------------------------
    # DETAIL
    # --------------------------------------------------------

    for name, items in groups.items():

        f.write(
            "\n"
            + "=" * 100
            + "\n"
        )

        f.write(
            name
            + "\n"
        )

        f.write(
            "=" * 100
            + "\n\n"
        )

        for result in items:

            row = result["local"]

            remote_record = result["remote"]

            (
                local_id,
                artist,
                title,
                label,
                catalog,
                discogs_id,
                discogs_link,
                storage_code
            ) = row

            f.write(
                f"LOCAL ID   : {local_id}\n"
            )

            f.write(
                f"LOCAL      : "
                f"{artist or ''} - "
                f"{title or ''}\n"
            )

            f.write(
                f"LOCAL CAT  : "
                f"{catalog or ''}\n"
            )

            f.write(
                f"KASTCODE   : "
                f"{storage_code or ''}\n"
            )

            if remote_record:

                f.write(
                    f"DISCOGS ID : "
                    f"{remote_record['id']}\n"
                )

                f.write(
                    f"DISCogs    : "
                    f"{remote_record['artist']} - "
                    f"{remote_record['title']}\n"
                )

                f.write(
                    f"DISC CAT   : "
                    f"{remote_record['catalog'] or ''}\n"
                )

                f.write(
                    f"LABEL      : "
                    f"{remote_record['label'] or ''}\n"
                )

                f.write(
                    f"FORMAT     : "
                    f"{remote_record['format'] or ''}\n"
                )

                f.write(
                    f"YEAR       : "
                    f"{remote_record['year'] or ''}\n"
                )

                f.write(
                    f"SCORE      : "
                    f"{result['score']:.1f}\n"
                )

                f.write(
                    f"GAP        : "
                    f"{result['gap']:.1f}\n"
                )

                f.write(
                    f"TITLE      : "
                    f"{result['title']:.1f}\n"
                )

                f.write(
                    f"ARTIST     : "
                    f"{result['artist']:.1f}\n"
                )

                f.write(
                    f"LABEL      : "
                    f"{result['label']:.1f}\n"
                )

                f.write(
                    f"CATALOG    : "
                    f"{result['catalog']:.1f}\n"
                )

            f.write(
                "\n"
                + "-" * 100
                + "\n\n"
            )


conn.close()


# ============================================================
# SAMENVATTING
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
    f"Bestaande ID     : "
    f"{len(groups['BESTAANDE DISCOGS IDS'])}"
)

print(
    f"Catalog matches  : "
    f"{len(groups['CATALOGUS MATCHES'])}"
)

print(
    f"Sterke matches   : "
    f"{len(groups['STERKE MATCHES'])}"
)

print(
    f"Waarschijnlijke  : "
    f"{len(groups['WAARSCHIJNLIJKE MATCHES'])}"
)

print(
    f"Controleren      : "
    f"{len(groups['CONTROLEREN'])}"
)

print(
    f"Geen match       : "
    f"{len(groups['GEEN MATCH'])}"
)

print()
print(
    "RESULTAAT:"
)

print(
    OUT
)

print()
print(
    "DATABASE IS NIET GEWIJZIGD."
)

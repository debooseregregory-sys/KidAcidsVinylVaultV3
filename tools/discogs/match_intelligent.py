import json
import sqlite3
import re
import unicodedata
from pathlib import Path
from difflib import SequenceMatcher

BASE = Path(r"C:\Users\andyb\Desktop\KidAcidsVinylVaultV3")
DB = BASE / "data" / "vinylvault.db"
JSON_FILE = BASE / "data" / "discogs_public_collection.json"
OUT_DIR = BASE / "data"

STRONG = OUT_DIR / "discogs_strong_matches.txt"
REVIEW = OUT_DIR / "discogs_review_matches.txt"
NONE = OUT_DIR / "discogs_no_matches.txt"

print("=" * 90)
print("KID ACID'S VINYL VAULT V3")
print("INTELLIGENTE DISCOGS MATCHER")
print("=" * 90)
print()

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
    )

    value = value.lower()

    replacements = {
        "&": " and ",
        "+": " and ",
        "feat.": " featuring ",
        "feat": " featuring ",
        "ft.": " featuring ",
        "ft": " featuring ",
        "pres.": " presents ",
        "pres": " presents ",
        "vs.": " vs ",
        "v.": " vs ",
        "e.p.": " ep ",
        "e.p": " ep ",
        "12\"": " ",
        "7\"": " ",
        "lp": " ",
        "maxi": " ",
    }

    for a, b in replacements.items():
        value = value.replace(a, b)

    value = re.sub(
        r"[\(\)\[\]\{\},;:_/\\\-]+",
        " ",
        value
    )

    value = re.sub(
        r"\s+",
        " ",
        value
    ).strip()

    return value


def words(value):

    return set(
        x for x in norm(value).split()
        if len(x) > 1
    )


def similarity(a, b):

    a = norm(a)
    b = norm(b)

    if not a or not b:
        return 0.0

    if a == b:
        return 100.0

    return SequenceMatcher(
        None,
        a,
        b
    ).ratio() * 100


def word_similarity(a, b):

    wa = words(a)
    wb = words(b)

    if not wa or not wb:
        return 0.0

    intersection = len(
        wa & wb
    )

    union = len(
        wa | wb
    )

    return (
        intersection / union
    ) * 100


def artist_similarity(a, b):

    a = norm(a)
    b = norm(b)

    if not a or not b:
        return 0.0

    if a == b:
        return 100.0

    return max(
        similarity(a, b),
        word_similarity(a, b)
    )


def title_similarity(a, b):

    return max(
        similarity(a, b),
        word_similarity(a, b)
    )


# ============================================================
# DISCogs DATA
# ============================================================

def remote_data(record):

    basic = record.get(
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

            name = artist.get(
                "name",
                ""
            )

            if name:
                artists.append(name)

    artist = ", ".join(
        artists
    )

    title = basic.get(
        "title",
        ""
    )

    labels = []

    for label in basic.get(
        "labels",
        []
    ):

        if not isinstance(
            label,
            dict
        ):
            continue

        catno = label.get(
            "catno",
            ""
        )

        if catno:
            labels.append(
                str(catno)
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

        name = fmt.get(
            "name",
            ""
        )

        if name:
            formats.append(
                name
            )

    return {
        "id": basic.get(
            "id"
        ),
        "artist": artist,
        "title": title,
        "catalog": " / ".join(labels),
        "formats": " / ".join(formats),
        "year": basic.get(
            "year"
        ),
        "label": ", ".join(
            str(x.get("name") or "") for x in basic.get("labels", []) if isinstance(x, dict)
        )
    }


# ============================================================
# FORMAT
# ============================================================

def format_score(local_format, remote_format):

    local = norm(
        local_format
    )

    remote = norm(
        remote_format
    )

    if not local or not remote:
        return 0

    if local in remote:
        return 100

    if "vinyl" in remote and "vinyl" in local:
        return 100

    if "cd" in remote and "cd" in local:
        return 100

    return 0


# ============================================================
# CATALOGUS
# ============================================================

def catalog_score(local_catalog, remote_catalog):

    a = norm(
        local_catalog
    )

    b = norm(
        remote_catalog
    )

    if not a or not b:
        return 0

    if a == b:
        return 100

    compact_a = re.sub(
        r"[^a-z0-9]",
        "",
        a
    )

    compact_b = re.sub(
        r"[^a-z0-9]",
        "",
        b
    )

    if compact_a and compact_a == compact_b:
        return 100

    if (
        compact_a
        and compact_b
        and (
            compact_a in compact_b
            or compact_b in compact_a
        )
    ):
        return 90

    return similarity(
        compact_a,
        compact_b
    )


# ============================================================
# DATABASE
# ============================================================

print("Database laden...")
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

local_rows = cur.fetchall()

print(
    f"Lokale releases: {len(local_rows)}"
)

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

    public = json.load(f)

print(
    f"Openbare records: {len(public)}"
)

print()

# ============================================================
# REMOTE PREP
# ============================================================

print("Discogs records voorbereiden...")

remote = []

for record in public:

    data = remote_data(
        record
    )

    if data["id"]:

        remote.append(
            data
        )

print(
    f"bruikbare records: {len(remote)}"
)

print()

# ============================================================
# INDEXEN
# ============================================================

print("Indexen bouwen...")

title_index = {}
artist_index = {}
catalog_index = {}

for r in remote:

    nt = norm(
        r["title"]
    )

    na = norm(
        r["artist"]
    )

    nc = norm(
        r["catalog"]
    )

    if nt:
        title_index.setdefault(
            nt,
            []
        ).append(r)

    if na:
        artist_index.setdefault(
            na,
            []
        ).append(r)

    if nc:
        catalog_index.setdefault(
            nc,
            []
        ).append(r)

print(
    f"Titels   : {len(title_index)}"
)

print(
    f"Artiesten: {len(artist_index)}"
)

print(
    f"Catalogi : {len(catalog_index)}"
)

print()

# ============================================================
# MATCHEN
# ============================================================

strong_matches = []
review_matches = []
no_matches = []

print(
    "VOLLEDIGE LOKALE COLLECTIE CONTROLEREN..."
)

print()

total = len(
    local_rows
)

for number, local in enumerate(
    local_rows,
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
    ) = local

    candidates = {}

    # --------------------------------------------------------
    # BESTAANDE ID
    # --------------------------------------------------------

    if local_discogs:

        try:
            wanted = int(
                str(
                    local_discogs
                ).strip()
            )

        except:
            wanted = None

        if wanted:

            for r in remote:

                if r["id"] == wanted:

                    candidates[
                        r["id"]
                    ] = r

                    break

    # --------------------------------------------------------
    # TITEL INDEX
    # --------------------------------------------------------

    nt = norm(
        local_title
    )

    if nt:

        for r in title_index.get(
            nt,
            []
        ):

            candidates[
                r["id"]
            ] = r

    # --------------------------------------------------------
    # ARTIST INDEX
    # --------------------------------------------------------

    na = norm(
        local_artist
    )

    if na:

        for r in artist_index.get(
            na,
            []
        ):

            candidates[
                r["id"]
            ] = r

    # --------------------------------------------------------
    # ALS ER WEINIG KANDIDATEN ZIJN:
    # ALLEEN DAN FUZZY SEARCH
    # --------------------------------------------------------

    if len(candidates) < 5:

        for r in remote:

            ts = title_similarity(
                local_title,
                r["title"]
            )

            if ts < 45:
                continue

            ass = artist_similarity(
                local_artist,
                r["artist"]
            )

            if ass < 30:
                continue

            candidates[
                r["id"]
            ] = r

    scored = []

    for r in candidates.values():

        ts = title_similarity(
            local_title,
            r["title"]
        )

        ass = artist_similarity(
            local_artist,
            r["artist"]
        )

        cs = catalog_score(
            local_catalog,
            r["catalog"]
        )

        # Titel zwaar
        score = (
            ts * 0.50
            + ass * 0.35
            + cs * 0.15
        )

        # Exact catalogus is zeer sterk
        if cs >= 99:

            score += 20

        # Exact titel + artiest
        if ts >= 99 and ass >= 99:

            score += 15

        score = min(
            score,
            100
        )

        scored.append(
            (
                score,
                ts,
                ass,
                cs,
                r
            )
        )

    scored.sort(
        key=lambda x: x[0],
        reverse=True
    )

    if not scored:

        no_matches.append(
            local
        )

    else:

        best = scored[0]

        score, ts, ass, cs, r = best

        if len(scored) > 1:

            second_score = scored[1][0]

        else:

            second_score = 0

        gap = (
            score
            - second_score
        )

        item = (
            local,
            r,
            score,
            gap,
            ts,
            ass,
            cs
        )

        # ----------------------------------------------------
        # STERKE MATCH
        # ----------------------------------------------------

        if (
            score >= 82
            and gap >= 8
        ):

            strong_matches.append(
                item
            )

        # ----------------------------------------------------
        # TWIJFEL
        # ----------------------------------------------------

        elif score >= 60:

            review_matches.append(
                item
            )

        # ----------------------------------------------------
        # GEEN MATCH
        # ----------------------------------------------------

        else:

            no_matches.append(
                local
            )

    # --------------------------------------------------------
    # VOORTGANG
    # --------------------------------------------------------

    if number % 100 == 0:

        print(
            f"{number:4}/{total} "
            f"| sterk={len(strong_matches):4} "
            f"| twijfel={len(review_matches):4} "
            f"| geen={len(no_matches):4}"
        )

# ============================================================
# BESTANDEN
# ============================================================

def write_match(
    f,
    item
):

    local, remote, score, gap, ts, ass, cs = item

    (
        local_id,
        local_artist,
        local_title,
        local_label,
        local_catalog,
        local_discogs,
        local_link,
        storage_code
    ) = local

    f.write(
        "=" * 100
        + "\n"
    )

    f.write(
        f"LOCAL ID     : {local_id}\n"
    )

    f.write(
        f"LOCAL        : {local_artist} - {local_title}\n"
    )

    f.write(
        f"LOCAL CATALOG: {local_catalog or ''}\n"
    )

    f.write(
        f"KASTCODE     : {storage_code or ''}\n"
    )

    f.write(
        f"DISCogs ID   : {remote['id']}\n"
    )

    f.write(
        f"DISCogs      : {remote['artist']} - {remote['title']}\n"
    )

    f.write(
        f"DISC CATALOG : {remote['catalog'] or 'none'}\n"
    )

    f.write(
        f"FORMAT       : {remote['formats'] or 'none'}\n"
    )

    f.write(
        f"LABEL        : {remote['label'] or 'none'}\n"
    )

    f.write(
        f"YEAR         : {remote['year'] or ''}\n"
    )

    f.write(
        f"SCORE        : {score:.1f}\n"
    )

    f.write(
        f"GAP          : {gap:.1f}\n"
    )

    f.write(
        f"TITLE SCORE  : {ts:.1f}\n"
    )

    f.write(
        f"ARTIST SCORE : {ass:.1f}\n"
    )

    f.write(
        f"CAT SCORE    : {cs:.1f}\n"
    )

    f.write("\n")


with open(
    STRONG,
    "w",
    encoding="utf-8"
) as f:

    f.write(
        "STERKE MATCHES\n\n"
    )

    for item in strong_matches:

        write_match(
            f,
            item
        )


with open(
    REVIEW,
    "w",
    encoding="utf-8"
) as f:

    f.write(
        "TWIJFELMATCHES\n\n"
    )

    for item in review_matches:

        write_match(
            f,
            item
        )


with open(
    NONE,
    "w",
    encoding="utf-8"
) as f:

    f.write(
        "GEEN BETROUWBARE MATCH\n\n"
    )

    for local in no_matches:

        (
            local_id,
            artist,
            title,
            label,
            catalog,
            discogs,
            link,
            storage_code
        ) = local

        f.write(
            "=" * 100
            + "\n"
        )

        f.write(
            f"LOCAL ID     : {local_id}\n"
        )

        f.write(
            f"ARTIST       : {artist}\n"
        )

        f.write(
            f"TITLE        : {title}\n"
        )

        f.write(
            f"CATALOG      : {catalog or ''}\n"
        )

        f.write(
            f"KASTCODE     : {storage_code or ''}\n"
        )

        f.write("\n")

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
    f"Lokale releases : {total}"
)

print(
    f"Sterke matches  : {len(strong_matches)}"
)

print(
    f"Twijfelgevallen : {len(review_matches)}"
)

print(
    f"Geen match      : {len(no_matches)}"
)

print()
print(
    "RESULTATEN:"
)

print(
    STRONG
)

print(
    REVIEW
)

print(
    NONE
)

print()
print(
    "DRY RUN — DATABASE IS NIET GEWIJZIGD."
)

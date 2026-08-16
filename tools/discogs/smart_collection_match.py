import json
import sqlite3
import re
import unicodedata
from pathlib import Path
from difflib import SequenceMatcher

BASE = Path(r"C:\Users\andyb\Desktop\KidAcidsVinylVaultV3")
DB = BASE / "data" / "vinylvault.db"
JSON_FILE = BASE / "data" / "discogs_public_collection.json"
OUT = BASE / "data" / "discogs_smart_match.txt"

def norm(s):
    if s is None:
        return ""
    s = str(s)
    s = unicodedata.normalize("NFKD", s)
    s = s.encode("ascii", "ignore").decode("ascii")
    s = s.lower()

    replacements = [
        ("featuring", "feat"),
        ("feat.", "feat"),
        ("feat", "feat"),
        ("ft.", "feat"),
        ("ft", "feat"),
        ("presents", "pres"),
        ("present", "pres"),
        ("pres.", "pres"),
        ("vs.", "vs"),
        ("e.p.", "ep"),
        ("e.p", "ep"),
        ("12 inch", ""),
        ("12\"", ""),
        ("7\"", ""),
        ("&", " and "),
        ("+", " and "),
    ]

    for a, b in replacements:
        s = s.replace(a, b)

    s = re.sub(r"[^a-z0-9]+", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def compact(s):
    return re.sub(r"[^a-z0-9]", "", norm(s))


def ratio(a, b):
    a = norm(a)
    b = norm(b)

    if not a or not b:
        return 0.0

    if a == b:
        return 100.0

    return SequenceMatcher(None, a, b).ratio() * 100


def token_score(a, b):
    a = set(norm(a).split())
    b = set(norm(b).split())

    if not a or not b:
        return 0.0

    return (
        len(a & b) /
        max(len(a), len(b))
    ) * 100


def field_score(a, b):
    return max(
        ratio(a, b),
        token_score(a, b)
    )


def catalog_score(a, b):
    a = compact(a)
    b = compact(b)

    if not a or not b:
        return 0.0

    if a == b:
        return 100.0

    if a in b or b in a:
        return 92.0

    return SequenceMatcher(
        None,
        a,
        b
    ).ratio() * 100


def remote_record(item):
    b = item.get("basic_information", {})

    artists = []
    labels = []
    catalogs = []
    formats = []

    for a in b.get("artists", []):
        if isinstance(a, dict):
            name = a.get("name") or ""
            if name:
                artists.append(str(name))

    for l in b.get("labels", []):
        if isinstance(l, dict):
            name = l.get("name") or ""
            cat = l.get("catno") or ""

            if name:
                labels.append(str(name))

            if cat:
                catalogs.append(str(cat))

    for f in b.get("formats", []):
        if isinstance(f, dict):
            name = f.get("name") or ""
            if name:
                formats.append(str(name))

    return {
        "id": b.get("id"),
        "instance_id": item.get("instance_id"),
        "artist": ", ".join(artists),
        "title": str(b.get("title") or ""),
        "label": " / ".join(labels),
        "catalog": " / ".join(catalogs),
        "format": " / ".join(formats),
        "year": b.get("year"),
    }


print("=" * 90)
print("KID ACID'S VINYL VAULT V3")
print("SMART DISCogs COLLECTION MATCH")
print("=" * 90)
print()

print("JSON laden...")

with open(
    JSON_FILE,
    "r",
    encoding="utf-8"
) as f:
    raw = json.load(f)

remote = [
    remote_record(x)
    for x in raw
]

print(
    f"Openbare collectie-items : {len(remote)}"
)

print(
    f"Unieke Discogs releases  : "
    f"{len(set(str(x['id']) for x in remote if x['id']))}"
)

print()
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

local = cur.fetchall()

print(
    f"Lokale releases : {len(local)}"
)

print()
print("Indexen bouwen...")

catalog_index = {}
title_index = {}
artist_index = {}
label_index = {}

for r in remote:

    if r["id"] is None:
        continue

    rid = r["id"]

    c = compact(r["catalog"])
    t = norm(r["title"])
    a = norm(r["artist"])
    l = norm(r["label"])

    if c:
        catalog_index.setdefault(c, []).append(r)

    if t:
        title_index.setdefault(t, []).append(r)

    if a:
        artist_index.setdefault(a, []).append(r)

    if l:
        label_index.setdefault(l, []).append(r)

print(
    f"Catalog-index : {len(catalog_index)}"
)

print(
    f"Titel-index   : {len(title_index)}"
)

print(
    f"Artiest-index : {len(artist_index)}"
)

print()

# ------------------------------------------------------------
# MATCH
# ------------------------------------------------------------

results = []
used_remote = {}

print("SMART MATCHING START...")
print()

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

    candidates = {}

    # --------------------------------------------------------
    # bestaande Discogs ID
    # --------------------------------------------------------

    if local_discogs:

        try:
            did = int(str(local_discogs).strip())
        except:
            did = None

        if did:

            for r in remote:
                if r["id"] == did:
                    candidates[did] = r
                    break

    # --------------------------------------------------------
    # catalogus kandidaat
    # --------------------------------------------------------

    lc = compact(local_catalog)

    if lc:

        for key, rows in catalog_index.items():

            if (
                lc == key
                or lc in key
                or key in lc
            ):

                for r in rows:
                    candidates[r["id"]] = r

    # --------------------------------------------------------
    # titel kandidaat
    # --------------------------------------------------------

    lt = norm(local_title)

    if lt:

        exact = title_index.get(
            lt,
            []
        )

        for r in exact:
            candidates[r["id"]] = r

    # --------------------------------------------------------
    # artiest kandidaat
    # --------------------------------------------------------

    la = norm(local_artist)

    if la:

        exact = artist_index.get(
            la,
            []
        )

        for r in exact:
            candidates[r["id"]] = r

    # --------------------------------------------------------
    # ALS TE WEINIG KANDIDATEN:
    # alle records scannen
    # --------------------------------------------------------

    if len(candidates) < 3:

        for r in remote:

            ts = field_score(
                local_title,
                r["title"]
            )

            if ts < 45:
                continue

            ass = field_score(
                local_artist,
                r["artist"]
            )

            if ass < 25:
                continue

            candidates[r["id"]] = r

    # --------------------------------------------------------
    # SCORE
    # --------------------------------------------------------

    scored = []

    for r in candidates.values():

        ts = field_score(
            local_title,
            r["title"]
        )

        ass = field_score(
            local_artist,
            r["artist"]
        )

        ls = field_score(
            local_label,
            r["label"]
        )

        cs = catalog_score(
            local_catalog,
            r["catalog"]
        )

        year_score = 0

        if (
            local_catalog
            and r["catalog"]
        ):
            pass

        # hoofdscore
        score = (
            ts * 0.40
            + ass * 0.30
            + cs * 0.20
            + ls * 0.10
        )

        # sterke bonus voor catalogus
        if cs >= 99:
            score += 15

        elif cs >= 92:
            score += 8

        # sterke bonus titel + artiest
        if (
            ts >= 95
            and ass >= 90
        ):
            score += 10

        score = min(
            score,
            100
        )

        scored.append(
            (
                score,
                ts,
                ass,
                ls,
                cs,
                r
            )
        )

    scored.sort(
        key=lambda x: x[0],
        reverse=True
    )

    if scored:

        best = scored[0]

        if len(scored) > 1:
            second = scored[1][0]
        else:
            second = 0

        gap = best[0] - second

        results.append(
            (
                row,
                best,
                gap
            )
        )

    else:

        results.append(
            (
                row,
                None,
                0
            )
        )

    if n % 100 == 0:

        print(
            f"{n}/{len(local)}"
        )

# ------------------------------------------------------------
# CLASSIFICEREN
# ------------------------------------------------------------

strong = []
probable = []
review = []
none = []

for row, best, gap in results:

    if best is None:

        none.append(
            (row, None, gap)
        )

        continue

    score, ts, ass, ls, cs, r = best

    # Zeer sterk
    if (
        score >= 90
        and gap >= 5
    ):

        strong.append(
            (row, best, gap)
        )

    # Waarschijnlijk
    elif (
        score >= 78
        and gap >= 4
    ):

        probable.append(
            (row, best, gap)
        )

    # Handmatige controle
    elif score >= 60:

        review.append(
            (row, best, gap)
        )

    else:

        none.append(
            (row, best, gap)
        )

# ------------------------------------------------------------
# OUTPUT
# ------------------------------------------------------------

with open(
    OUT,
    "w",
    encoding="utf-8"
) as f:

    f.write(
        "=" * 100 + "\n"
    )

    f.write(
        "SMART DISCogs MATCH RESULTAAT\n"
    )

    f.write(
        "=" * 100 + "\n\n"
    )

    f.write(
        f"Openbare records : {len(remote)}\n"
    )

    f.write(
        f"Lokale releases  : {len(local)}\n"
    )

    f.write(
        f"STERK            : {len(strong)}\n"
    )

    f.write(
        f"WAARSCHIJNLIJK   : {len(probable)}\n"
    )

    f.write(
        f"CONTROLEREN      : {len(review)}\n"
    )

    f.write(
        f"GEEN MATCH       : {len(none)}\n\n"
    )

    def write_item(
        row,
        best,
        gap
    ):

        (
            local_id,
            la,
            lt,
            ll,
            lc,
            ld,
            link,
            storage
        ) = row

        if best:

            score, ts, ass, ls, cs, r = best

            f.write(
                f"LOCAL ID : {local_id}\n"
            )

            f.write(
                f"LOCAL    : {la} - {lt}\n"
            )

            f.write(
                f"LOCAL CAT: {lc or ''}\n"
            )

            f.write(
                f"KASTCODE : {storage or ''}\n"
            )

            f.write(
                f"DISCogs  : {r['id']}\n"
            )

            f.write(
                f"REMOTE   : {r['artist']} - {r['title']}\n"
            )

            f.write(
                f"REMOTE CAT: {r['catalog'] or ''}\n"
            )

            f.write(
                f"FORMAT   : {r['format'] or ''}\n"
            )

            f.write(
                f"SCORE    : {score:.1f}\n"
            )

            f.write(
                f"GAP      : {gap:.1f}\n"
            )

            f.write(
                f"TITLE    : {ts:.1f}\n"
            )

            f.write(
                f"ARTIST   : {ass:.1f}\n"
            )

            f.write(
                f"LABEL    : {ls:.1f}\n"
            )

            f.write(
                f"CATALOG  : {cs:.1f}\n"
            )

        else:

            f.write(
                f"LOCAL ID : {local_id}\n"
            )

            f.write(
                f"LOCAL    : {la} - {lt}\n"
            )

            f.write(
                f"LOCAL CAT: {lc or ''}\n"
            )

            f.write(
                f"KASTCODE : {storage or ''}\n"
            )

        f.write(
            "\n" + "-" * 100 + "\n\n"
        )

    sections = [
        ("STERKE MATCHES", strong),
        ("WAARSCHIJNLIJKE MATCHES", probable),
        ("HANDMATIG CONTROLEREN", review),
        ("GEEN MATCH", none),
    ]

    for name, items in sections:

        f.write(
            "\n" + "=" * 100 + "\n"
        )

        f.write(
            name + "\n"
        )

        f.write(
            "=" * 100 + "\n\n"
        )

        for row, best, gap in items:

            write_item(
                row,
                best,
                gap
            )

conn.close()

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
    f"Sterke matches   : {len(strong)}"
)

print(
    f"Waarschijnlijk    : {len(probable)}"
)

print(
    f"Controleren      : {len(review)}"
)

print(
    f"Geen match       : {len(none)}"
)

print()
print(
    "Resultaat:"
)

print(
    OUT
)

print()
print(
    "DATABASE IS NIET GEWIJZIGD."
)

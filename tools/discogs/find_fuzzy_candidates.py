import sqlite3
import json
import re
import difflib
from collections import defaultdict

DB = "data/vinylvault.db"
JSON_FILE = "data/discogs/kid_acid_collection.json"
OUTPUT = "data/discogs/fuzzy_candidates.txt"


def norm(value):
    value = str(value or "").lower()

    replacements = {
        "&": "and",
        "feat.": "feat",
        "featuring": "feat",
        "vs.": "vs",
        "versus": "vs",
        "e.p.": "ep",
        "e.p": "ep",
    }

    for old, new in replacements.items():
        value = value.replace(old, new)

    return re.sub(r"[^a-z0-9]", "", value)


def similarity(a, b):
    if not a or not b:
        return 0.0

    return difflib.SequenceMatcher(
        None,
        a,
        b
    ).ratio()


print("=" * 100)
print("SNELLE DISCOGS CONTROLE")
print("=" * 100)

# --------------------------------------------------
# DATABASE
# --------------------------------------------------

conn = sqlite3.connect(DB)

rows = conn.execute(
    """
    SELECT
        id,
        artist,
        title,
        label,
        catalog,
        storage_code
    FROM releases
    WHERE
        (discogs IS NULL OR TRIM(discogs) = '')
        AND
        (catalog IS NULL OR TRIM(catalog) = '')
        AND
        TRIM(title) <> ''
    ORDER BY id
    """
).fetchall()

conn.close()

print()
print("RESTERENDE RECORDS:", len(rows))

# --------------------------------------------------
# DISCOGS JSON
# --------------------------------------------------

with open(JSON_FILE, "r", encoding="utf-8") as f:
    collection = json.load(f)

print("DISCOGS RECORDS:", len(collection))

discogs = []

for item in collection:

    basic = item.get("basic_information") or {}

    artists = basic.get("artists") or []
    labels = basic.get("labels") or []

    artist = ""

    if artists:
        artist = artists[0].get("name", "")

    label = ""

    if labels:
        label = labels[0].get("name", "")

    catalog = ""

    if labels:
        catalog = labels[0].get("catno", "")

    title = basic.get("title", "")

    record = {
        "id": item.get("id"),
        "artist": artist,
        "title": title,
        "label": label,
        "catalog": catalog,
        "artist_n": norm(artist),
        "title_n": norm(title),
        "label_n": norm(label),
        "catalog_n": norm(catalog),
    }

    discogs.append(record)

# --------------------------------------------------
# SNELLE INDEXEN
# --------------------------------------------------

by_title = defaultdict(list)
by_artist = defaultdict(list)
by_label = defaultdict(list)
by_catalog = defaultdict(list)

for item in discogs:

    if item["title_n"]:
        by_title[item["title_n"]].append(item)

    if item["artist_n"]:
        by_artist[item["artist_n"]].append(item)

    if item["label_n"]:
        by_label[item["label_n"]].append(item)

    if item["catalog_n"]:
        by_catalog[item["catalog_n"]].append(item)

# --------------------------------------------------
# RESULTATEN
# --------------------------------------------------

results = []

for number, row in enumerate(rows, 1):

    release_id = row[0]
    artist = row[1]
    title = row[2]
    label = row[3]
    catalog = row[4]
    storage = row[5]

    artist_n = norm(artist)
    title_n = norm(title)
    label_n = norm(label)
    catalog_n = norm(catalog)

    candidates = {}

    # ----------------------------------------------
    # 1. EXACTE TITEL
    # ----------------------------------------------

    for item in by_title.get(title_n, []):
        candidates[item["id"]] = item

    # ----------------------------------------------
    # 2. EXACTE CATALOGUS
    # ----------------------------------------------

    if catalog_n:

        for item in by_catalog.get(catalog_n, []):
            candidates[item["id"]] = item

    # ----------------------------------------------
    # 3. EXACTE ARTIEST
    # ----------------------------------------------

    if artist_n:

        for item in by_artist.get(artist_n, []):
            candidates[item["id"]] = item

    # ----------------------------------------------
    # 4. LABEL
    # ----------------------------------------------

    if label_n:

        for item in by_label.get(label_n, []):
            candidates[item["id"]] = item

    # ----------------------------------------------
    # ALS WE NOG GEEN KANDIDATEN HEBBEN:
    # beperkte fuzzy zoekactie
    # ----------------------------------------------

    if not candidates:

        title_start = title_n[:5]

        if title_start:

            for item in discogs:

                candidate_title = item["title_n"]

                if not candidate_title:
                    continue

                if (
                    title_start in candidate_title
                    or candidate_title[:5] == title_start
                ):
                    candidates[item["id"]] = item

                if len(candidates) >= 40:
                    break

    # ----------------------------------------------
    # SCORE
    # ----------------------------------------------

    scored = []

    for item in candidates.values():

        title_score = similarity(
            title_n,
            item["title_n"]
        )

        artist_score = similarity(
            artist_n,
            item["artist_n"]
        )

        label_score = similarity(
            label_n,
            item["label_n"]
        )

        catalog_score = 0.0

        if catalog_n and item["catalog_n"]:
            catalog_score = similarity(
                catalog_n,
                item["catalog_n"]
            )

        score = (
            title_score * 0.55
            + artist_score * 0.25
            + label_score * 0.10
            + catalog_score * 0.10
        )

        if catalog_n and catalog_n == item["catalog_n"]:
            score += 0.50

        if title_n and title_n == item["title_n"]:
            score += 0.40

        scored.append(
            (
                score,
                title_score,
                artist_score,
                label_score,
                catalog_score,
                item,
            )
        )

    scored.sort(
        key=lambda x: x[0],
        reverse=True
    )

    top = scored[:5]

    results.append(
        (
            release_id,
            artist,
            title,
            label,
            catalog,
            storage,
            top,
        )
    )

    if number % 100 == 0:
        print(
            f"Verwerkt: {number}/{len(rows)}"
        )

# --------------------------------------------------
# RAPPORT
# --------------------------------------------------

with open(
    OUTPUT,
    "w",
    encoding="utf-8"
) as f:

    f.write(
        "=" * 120 + "\n"
    )

    f.write(
        "DISCOGS HANDMATIGE CONTROLE\n"
    )

    f.write(
        "=" * 120 + "\n\n"
    )

    f.write(
        f"RESTERENDE RECORDS: {len(rows)}\n"
    )

    f.write(
        f"DISCOGS RECORDS: {len(discogs)}\n\n"
    )

    for (
        release_id,
        artist,
        title,
        label,
        catalog,
        storage,
        top,
    ) in results:

        f.write(
            "\n" + "-" * 120 + "\n"
        )

        f.write(
            f"LOCAL ID  : {release_id}\n"
        )

        f.write(
            f"ARTIST    : {artist}\n"
        )

        f.write(
            f"TITLE     : {title}\n"
        )

        f.write(
            f"LABEL     : {label}\n"
        )

        f.write(
            f"CATALOG   : {catalog}\n"
        )

        f.write(
            f"STORAGE   : {storage}\n\n"
        )

        if not top:

            f.write(
                "GEEN KANDIDATEN GEVONDEN\n"
            )

            continue

        for n, candidate in enumerate(top, 1):

            (
                score,
                title_score,
                artist_score,
                label_score,
                catalog_score,
                item,
            ) = candidate

            basic_url = (
                f"https://www.discogs.com/release/{item['id']}"
            )

            f.write(
                f"KANDIDAAT {n}\n"
            )

            f.write(
                f"  SCORE        : {score:.3f}\n"
            )

            f.write(
                f"  TITLE SCORE  : {title_score:.3f}\n"
            )

            f.write(
                f"  ARTIST SCORE : {artist_score:.3f}\n"
            )

            f.write(
                f"  LABEL SCORE  : {label_score:.3f}\n"
            )

            f.write(
                f"  CATALOG SCORE: {catalog_score:.3f}\n"
            )

            f.write(
                f"  DISCOGS ID   : {item['id']}\n"
            )

            f.write(
                f"  ARTIST       : {item['artist']}\n"
            )

            f.write(
                f"  TITLE        : {item['title']}\n"
            )

            f.write(
                f"  LABEL        : {item['label']}\n"
            )

            f.write(
                f"  CATALOG      : {item['catalog']}\n"
            )

            f.write(
                f"  LINK         : {basic_url}\n\n"
            )

print()
print("=" * 100)
print("KLAAR")
print("=" * 100)
print()
print("RAPPORT:")
print(OUTPUT)
print()
print("DATABASE NIET GEWIJZIGD.")
print("=" * 100)
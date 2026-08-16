import sys
import time
import re
import sqlite3
from difflib import SequenceMatcher
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[2]

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import config


DB_PATH = ROOT / config.DB_PATH

USERNAME = "kid_acid"

COLLECTION_URL = (
    f"https://api.discogs.com/users/{USERNAME}/collection/folders/0/releases"
)

REQUEST_DELAY = 1.05

MIN_SCORE = 86.0
GOOD_SCORE = 94.0

WRITE_MODE = "--write" in sys.argv


session = requests.Session()

session.headers.update(
    {
        "User-Agent": config.DISCOGS_USER_AGENT,
        "Accept": "application/json",
    }
)


def normalize(value):
    if value is None:
        return ""

    value = str(value).lower().strip()

    value = value.replace("&", " and ")
    value = value.replace("'", "")
    value = value.replace("’", "")

    value = re.sub(r"[^a-z0-9]+", " ", value)
    value = re.sub(r"\s+", " ", value).strip()

    return value


def similarity(a, b):
    a = normalize(a)
    b = normalize(b)

    if not a or not b:
        return 0.0

    if a == b:
        return 100.0

    return SequenceMatcher(None, a, b).ratio() * 100.0


def catalog_variants(value):
    if not value:
        return set()

    raw = str(value).lower().strip()

    variants = {raw}

    compact = re.sub(r"[^a-z0-9]", "", raw)

    if compact:
        variants.add(compact)

    spaced = re.sub(r"[^a-z0-9]+", " ", raw)
    spaced = re.sub(r"\s+", " ", spaced).strip()

    if spaced:
        variants.add(spaced)

    parts = re.findall(r"[a-z]+|\d+", compact)

    if parts:
        variants.add(" ".join(parts))

        clean_parts = []

        for part in parts:
            if part.isdigit():
                part = part.lstrip("0") or "0"

            clean_parts.append(part)

        variants.add(" ".join(clean_parts))
        variants.add("".join(clean_parts))

    return variants


def catalog_match(a, b):
    if not a or not b:
        return False

    if catalog_variants(a).intersection(
        catalog_variants(b)
    ):
        return True

    ca = re.sub(
        r"[^a-z0-9]",
        "",
        str(a).lower()
    )

    cb = re.sub(
        r"[^a-z0-9]",
        "",
        str(b).lower()
    )

    return ca == cb


def open_db():
    if not DB_PATH.exists():
        print()
        print("FOUT: database niet gevonden:")
        print(DB_PATH)
        sys.exit(1)

    return sqlite3.connect(str(DB_PATH))


def get_missing_releases(conn):

    rows = conn.execute(
        """
        SELECT
            id,
            artist,
            title,
            catalog,
            discogs
        FROM releases
        WHERE
            (discogs IS NULL OR TRIM(discogs) = '')
            AND TRIM(COALESCE(artist, '')) <> ''
            AND TRIM(COALESCE(title, '')) <> ''
        ORDER BY id
        """
    ).fetchall()

    result = []

    for row in rows:

        release_id, artist, title, catalog, discogs = row

        artist_n = normalize(artist)

        if artist_n in {
            "various artists",
            "various",
            "va",
        }:
            continue

        result.append(
            {
                "id": release_id,
                "artist": artist or "",
                "title": title or "",
                "catalog": catalog or "",
                "discogs": discogs or "",
            }
        )

    return result


def get_collection():

    print()
    print("=" * 80)
    print("DISCOGS OPENBARE COLLECTIE INLEZEN")
    print("=" * 80)
    print("Gebruiker:", USERNAME)
    print()

    all_items = []

    page = 1
    per_page = 100

    while True:

        params = {
            "page": page,
            "per_page": per_page,
        }

        try:

            response = session.get(
                COLLECTION_URL,
                params=params,
                timeout=30,
            )

        except requests.RequestException as exc:

            print(
                "Discogs netwerkfout:",
                exc
            )

            break

        if response.status_code != 200:

            print(
                "Discogs HTTP-fout:",
                response.status_code
            )

            print(response.text[:500])

            break

        try:

            data = response.json()

        except ValueError:

            print(
                "Discogs gaf geen geldige JSON terug."
            )

            break

        releases = data.get(
            "releases",
            []
        )

        if not releases:
            break

        all_items.extend(releases)

        pagination = data.get(
            "pagination",
            {}
        )

        pages = pagination.get(
            "pages",
            page
        )

        print(
            f"Pagina {page}/{pages} "
            f"- {len(releases)} releases "
            f"- totaal {len(all_items)}"
        )

        if page >= pages:
            break

        page += 1

        time.sleep(
            REQUEST_DELAY
        )

    print()
    print(
        "Discogs collectie:",
        len(all_items)
    )

    return all_items


def collection_release_data(item):

    basic = item.get(
        "basic_information",
        {}
    ) or {}

    artists = basic.get(
        "artists",
        []
    ) or []

    artist_names = []

    for artist in artists:

        name = artist.get(
            "name",
            ""
        )

        if name:
            artist_names.append(name)

    artist = ", ".join(
        artist_names
    )

    title = basic.get(
        "title",
        ""
    ) or ""

    year = basic.get(
        "year",
        ""
    ) or ""

    labels = basic.get(
        "labels",
        []
    ) or []

    catnos = []

    for label in labels:

        catno = label.get(
            "catno",
            ""
        )

        if catno:
            catnos.append(catno)

    catno = (
        catnos[0]
        if catnos
        else ""
    )

    return {
        "discogs_id": item.get("id"),
        "artist": artist,
        "title": title,
        "year": year,
        "catalog": catno,
    }


def build_collection_indexes(items):

    by_artist = {}
    by_catalog = {}

    for item in items:

        data = collection_release_data(
            item
        )

        if not data["discogs_id"]:
            continue

        artist_key = normalize(
            data["artist"]
        )

        if artist_key:

            by_artist.setdefault(
                artist_key,
                []
            ).append(data)

        for cat in catalog_variants(
            data["catalog"]
        ):

            if cat:

                by_catalog.setdefault(
                    cat,
                    []
                ).append(data)

    return by_artist, by_catalog


def score_candidate(
    local_release,
    candidate
):

    artist_score = similarity(
        local_release["artist"],
        candidate["artist"]
    )

    title_score = similarity(
        local_release["title"],
        candidate["title"]
    )

    cat_match = catalog_match(
        local_release["catalog"],
        candidate["catalog"]
    )

    score = (
        artist_score * 0.45
        + title_score * 0.55
    )

    if cat_match:
        score += 18.0

    return min(
        score,
        100.0
    ), cat_match


def find_best_match(
    local_release,
    by_artist,
    by_catalog
):

    candidates = []

    for cat in catalog_variants(
        local_release["catalog"]
    ):

        for candidate in by_catalog.get(
            cat,
            []
        ):

            if candidate not in candidates:
                candidates.append(candidate)

    artist_key = normalize(
        local_release["artist"]
    )

    for candidate in by_artist.get(
        artist_key,
        []
    ):

        if candidate not in candidates:
            candidates.append(candidate)

    if not candidates and artist_key:

        for key, values in by_artist.items():

            if similarity(
                artist_key,
                key
            ) >= 88:

                for candidate in values:

                    if candidate not in candidates:
                        candidates.append(candidate)

    if not candidates:
        return None, 0.0, False

    best = None
    best_score = 0.0
    best_cat_match = False

    for candidate in candidates:

        score, cat_match = score_candidate(
            local_release,
            candidate
        )

        if score > best_score:

            best = candidate
            best_score = score
            best_cat_match = cat_match

    if best_score < MIN_SCORE:

        return (
            None,
            best_score,
            best_cat_match
        )

    return (
        best,
        best_score,
        best_cat_match
    )


def write_match(
    conn,
    local_release_id,
    discogs_id
):

    conn.execute(
        """
        UPDATE releases
        SET discogs = ?
        WHERE id = ?
        """,
        (
            str(discogs_id),
            local_release_id,
        )
    )


def main():

    print()
    print("=" * 80)
    print("KID ACID'S VINYLVAULT V3")
    print("DISCOGS AUTO MATCH COLLECTION")
    print("=" * 80)

    if WRITE_MODE:

        print(
            "MODUS: DATABASE WORDT GEWIJZIGD"
        )

    else:

        print(
            "MODUS: DRY RUN - DATABASE BLIJFT ONGEWIJZIGD"
        )

    conn = open_db()

    missing = get_missing_releases(
        conn
    )

    print()
    print(
        "Te controleren releases:",
        len(missing)
    )

    collection = get_collection()

    if not collection:

        print()
        print(
            "GEEN COLLECTIEGEGEVENS GEVONDEN."
        )

        print(
            "Er wordt niets gewijzigd."
        )

        conn.close()

        return

    by_artist, by_catalog = (
        build_collection_indexes(
            collection
        )
    )

    print()
    print(
        "Collectie-index:",
        len(collection),
        "items"
    )

    print(
        "Artiesten:",
        len(by_artist)
    )

    print(
        "Catalogusvarianten:",
        len(by_catalog)
    )

    matched = 0
    unmatched = 0
    weak = 0
    catalog_matches = 0

    for number, local_release in enumerate(
        missing,
        start=1
    ):

        candidate, score, cat_match = (
            find_best_match(
                local_release,
                by_artist,
                by_catalog
            )
        )

        print()
        print(
            f"[{number}/{len(missing)}] "
            f"V3 #{local_release['id']}"
        )

        print(
            "  Lokaal:",
            local_release["artist"],
            "-",
            local_release["title"]
        )

        if local_release["catalog"]:

            print(
                "  Cat:",
                local_release["catalog"]
            )

        if candidate:

            print(
                "  Discogs:",
                candidate["discogs_id"],
                "|",
                candidate["artist"],
                "-",
                candidate["title"]
            )

            print(
                "  Cat:",
                candidate["catalog"],
                "| Score:",
                f"{score:.1f}"
            )

            if cat_match:

                print(
                    "  >>> CATALOGUS MATCH <<<"
                )

                catalog_matches += 1

            if score >= GOOD_SCORE:

                matched += 1

                if WRITE_MODE:

                    write_match(
                        conn,
                        local_release["id"],
                        candidate["discogs_id"]
                    )

                    conn.commit()

                    print(
                        "  >>> OPGESLAGEN <<<"
                    )

                else:

                    print(
                        "  >>> MATCH - DRY RUN <<<"
                    )

            else:

                weak += 1

                print(
                    "  >>> ZWAKKE MATCH - NIET OPGESLAGEN <<<"
                )

        else:

            unmatched += 1

            print(
                "  >>> GEEN MATCH IN COLLECTIE <<<"
            )

        time.sleep(
            REQUEST_DELAY
        )

    print()
    print("=" * 80)
    print("KLAAR")
    print("=" * 80)

    print(
        "Te controleren:",
        len(missing)
    )

    print(
        "Sterke matches:",
        matched
    )

    print(
        "Zwakke matches:",
        weak
    )

    print(
        "Geen match:",
        unmatched
    )

    print(
        "Catalogusmatches:",
        catalog_matches
    )

    if WRITE_MODE:

        print()
        print(
            "DATABASE IS BIJGEWERKT."
        )

    else:

        print()
        print(
            "DRY RUN: DATABASE IS NIET GEWIJZIGD."
        )

        print()
        print(
            "Voor echt opslaan:"
        )

        print(
            r"python tools\discogs\auto_match_collection.py --write"
        )

    conn.close()


if __name__ == "__main__":
    main()
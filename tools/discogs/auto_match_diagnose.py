import sys
import sqlite3
import re
import time
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
TEST_LIMIT = 20


def normalize(value):
    if value is None:
        return ""

    value = str(value).lower().strip()

    value = value.replace("&", " and ")
    value = value.replace("'", "")
    value = value.replace("’", "")

    value = re.sub(r"[^a-z0-9]+", " ", value)
    value = re.sub(r"\s+", " ", value)

    return value.strip()


def similarity(a, b):
    a = normalize(a)
    b = normalize(b)

    if not a or not b:
        return 0.0

    if a == b:
        return 100.0

    return SequenceMatcher(None, a, b).ratio() * 100.0


def catalog_normalize(value):
    if not value:
        return ""

    value = str(value).lower().strip()

    value = value.replace(" ", "")
    value = value.replace("-", "")
    value = value.replace("_", "")
    value = value.replace(".", "")

    return re.sub(r"[^a-z0-9]", "", value)


def catalog_match(a, b):
    a = catalog_normalize(a)
    b = catalog_normalize(b)

    if not a or not b:
        return False

    return a == b


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
    print("OPENBARE DISCOGS-COLLECTIE INLEZEN")
    print("=" * 80)
    print("Gebruiker:", USERNAME)
    print()

    all_items = []

    page = 1
    per_page = 100

    while True:

        print(
            f"Collectie ophalen: pagina {page}...",
            flush=True
        )

        params = {
            "page": page,
            "per_page": per_page,
        }

        try:

            response = requests.get(
                COLLECTION_URL,
                params=params,
                headers={
                    "User-Agent": config.DISCOGS_USER_AGENT,
                    "Accept": "application/json",
                },
                timeout=30,
            )

        except requests.RequestException as exc:

            print()
            print("Discogs netwerkfout:")
            print(exc)
            break

        print(
            "HTTP:",
            response.status_code
        )

        if response.status_code != 200:

            print()
            print("Discogs fout:")
            print(response.text[:1000])
            break

        try:

            data = response.json()

        except ValueError:

            print()
            print("Discogs gaf geen geldige JSON terug.")
            break

        releases = data.get("releases", [])

        if not releases:
            break

        all_items.extend(releases)

        pagination = data.get("pagination", {})

        pages = pagination.get("pages", page)

        print(
            f"  {len(releases)} releases "
            f"| totaal {len(all_items)} "
            f"| {page}/{pages}"
        )

        if page >= pages:
            break

        page += 1

        time.sleep(REQUEST_DELAY)

    print()
    print("TOTAAL OPENBARE COLLECTIE:", len(all_items))

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

    artist = ", ".join(artist_names)

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

    catalog = catnos[0] if catnos else ""

    return {
        "discogs_id": item.get("id"),
        "artist": artist,
        "title": title,
        "year": year,
        "catalog": catalog,
    }


def score_candidate(local, remote):

    artist_score = similarity(
        local["artist"],
        remote["artist"]
    )

    title_score = similarity(
        local["title"],
        remote["title"]
    )

    cat_match = catalog_match(
        local["catalog"],
        remote["catalog"]
    )

    score = (
        artist_score * 0.45
        + title_score * 0.55
    )

    if cat_match:
        score += 20

    score = min(score, 100)

    return score, artist_score, title_score, cat_match


def find_candidates(local, collection):

    candidates = []

    local_artist = normalize(local["artist"])
    local_title = normalize(local["title"])
    local_catalog = catalog_normalize(local["catalog"])

    for remote in collection:

        remote_artist = normalize(remote.get("artist", ""))
        remote_title = normalize(remote.get("title", ""))
        remote_catalog = catalog_normalize(remote.get("catalog", ""))

        artist_score = similarity(
            local_artist,
            remote_artist
        )

        title_score = similarity(
            local_title,
            remote_title
        )

        cat_match = (
            bool(local_catalog)
            and bool(remote_catalog)
            and local_catalog == remote_catalog
        )

        # Snelle selectie:
        # artiest redelijk gelijk
        # OF titel redelijk gelijk
        # OF catalogus exact gelijk

        if (
            artist_score >= 55
            or title_score >= 70
            or cat_match
        ):

            score, a_score, t_score, c_match = score_candidate(
                local,
                remote
            )

            candidates.append(
                (
                    score,
                    a_score,
                    t_score,
                    c_match,
                    remote,
                )
            )

    candidates.sort(
        key=lambda x: x[0],
        reverse=True
    )

    return candidates[:5]


def main():

    print()
    print("=" * 80)
    print("KID ACID'S VINYLVAULT V3")
    print("DISCOGS MATCH DIAGNOSE")
    print("=" * 80)
    print()
    print("DATABASE:", DB_PATH)
    print("DATABASE WORDT NIET GEWIJZIGD")
    print()
    print("Aantal testmatches:", TEST_LIMIT)

    conn = open_db()

    missing = get_missing_releases(conn)

    print()
    print(
        "Releases zonder Discogs:",
        len(missing)
    )

    collection = get_collection()

    if not collection:
        print()
        print("GEEN COLLECTIE GEVONDEN.")
        conn.close()
        return

    print()
    print("=" * 80)
    print("MATCH-DIAGNOSE")
    print("=" * 80)

    test_items = missing[:TEST_LIMIT]

    for number, local in enumerate(
        test_items,
        start=1
    ):

        print()
        print("-" * 80)
        print(
            f"[{number}/{len(test_items)}] "
            f"V3 RELEASE #{local['id']}"
        )
        print("-" * 80)

        print(
            "LOKAAL ARTIEST :",
            local["artist"]
        )

        print(
            "LOKAAL TITEL   :",
            local["title"]
        )

        print(
            "LOKAAL CATALOG :",
            local["catalog"]
        )

        candidates = find_candidates(
            local,
            collection
        )

        if not candidates:

            print()
            print("GEEN KANDIDATEN GEVONDEN")
            continue

        print()
        print("BESTE KANDIDATEN:")

        for rank, candidate in enumerate(
            candidates,
            start=1
        ):

            score = candidate[0]
            artist_score = candidate[1]
            title_score = candidate[2]
            cat_match = candidate[3]
            remote = candidate[4]

            print()
            print(
                f"  #{rank}"
            )

            print(
                "  Discogs ID :",
                remote["discogs_id"]
            )

            print(
                "  Artiest    :",
                remote["artist"]
            )

            print(
                "  Titel      :",
                remote["title"]
            )

            print(
                "  Catalogus  :",
                remote["catalog"]
            )

            print(
                "  Artist     :",
                f"{artist_score:.1f}%"
            )

            print(
                "  Titel      :",
                f"{title_score:.1f}%"
            )

            print(
                "  Catalogus  :",
                "JA" if cat_match else "NEE"
            )

            print(
                "  TOTAAL     :",
                f"{score:.1f}%"
            )

    print()
    print("=" * 80)
    print("DIAGNOSE KLAAR")
    print("=" * 80)
    print()
    print("DATABASE IS NIET GEWIJZIGD.")

    conn.close()


if __name__ == "__main__":
    main()

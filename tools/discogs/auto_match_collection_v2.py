import sys
import time
import re
import json
import sqlite3
import requests
from difflib import SequenceMatcher
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import config


DB_PATH = ROOT / config.DB_PATH

USERNAME = "kid_acid"

COLLECTION_URL = (
    f"https://api.discogs.com/users/{USERNAME}/collection/folders/0/releases"
)

CACHE_DIR = ROOT / "data" / "discogs"
CACHE_FILE = CACHE_DIR / "kid_acid_collection.json"

REQUEST_DELAY = 1.10
MAX_RETRIES = 8

MIN_SCORE = 88.0
STRONG_SCORE = 93.0

WRITE_MODE = "--write" in sys.argv
REFRESH_MODE = "--refresh" in sys.argv


session = requests.Session()

session.headers.update(
    {
        "User-Agent": config.DISCOGS_USER_AGENT,
        "Accept": "application/json",
    }
)


# ============================================================
# NORMALISEREN
# ============================================================

def normalize(value):
    if value is None:
        return ""

    value = str(value).lower().strip()

    replacements = {
        "&": " and ",
        "â€™": "",
        "'": "",
        "’": "",
        "´": "",
        "`": "",
    }

    for old, new in replacements.items():
        value = value.replace(old, new)

    value = value.replace("feat.", " feat ")
    value = value.replace("featuring", " feat ")
    value = value.replace("pres.", " pres ")
    value = value.replace("vs.", " vs ")
    value = value.replace("v.", " vs ")

    value = re.sub(r"[^a-z0-9]+", " ", value)
    value = re.sub(r"\s+", " ", value).strip()

    return value


def normalize_catalog(value):
    if value is None:
        return ""

    value = str(value).lower().strip()

    value = value.replace("â€™", "")
    value = value.replace("’", "")
    value = value.replace("'", "")

    return re.sub(r"[^a-z0-9]", "", value)


def similarity(a, b):
    a = normalize(a)
    b = normalize(b)

    if not a or not b:
        return 0.0

    if a == b:
        return 100.0

    return SequenceMatcher(None, a, b).ratio() * 100.0


def catalog_match(a, b):
    a = normalize_catalog(a)
    b = normalize_catalog(b)

    if not a or not b:
        return False

    return a == b


def is_various(artist):
    value = normalize(artist)

    return value in {
        "various",
        "various artists",
        "va",
    }


# ============================================================
# DATABASE
# ============================================================

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

    for release_id, artist, title, catalog, discogs in rows:
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


# ============================================================
# DISCOGS API
# ============================================================

def request_page(page):
    params = {
        "page": page,
        "per_page": 100,
    }

    for attempt in range(1, MAX_RETRIES + 1):

        try:
            response = session.get(
                COLLECTION_URL,
                params=params,
                timeout=45,
            )

        except requests.RequestException as exc:
            print()
            print("Netwerkfout:", exc)
            print(
                f"Opnieuw proberen "
                f"({attempt}/{MAX_RETRIES})..."
            )
            time.sleep(min(attempt * 3, 20))
            continue

        if response.status_code == 200:
            try:
                return response.json()

            except ValueError:
                print("Ongeldige JSON ontvangen.")
                time.sleep(3)
                continue

        if response.status_code == 429:

            retry_after = response.headers.get(
                "Retry-After"
            )

            try:
                wait = int(retry_after)
            except (TypeError, ValueError):
                wait = min(
                    20 * attempt,
                    120
                )

            print()
            print(
                f"HTTP 429 - Discogs rate limit."
            )
            print(
                f"Wachten: {wait} seconden..."
            )

            time.sleep(wait)
            continue

        if response.status_code in {
            500,
            502,
            503,
            504,
        }:

            wait = min(
                10 * attempt,
                60
            )

            print()
            print(
                f"Discogs HTTP {response.status_code}."
            )
            print(
                f"Opnieuw proberen over {wait}s..."
            )

            time.sleep(wait)
            continue

        print()
        print(
            "Discogs HTTP-fout:",
            response.status_code
        )

        print(
            response.text[:500]
        )

        return None

    print()
    print(
        f"Pagina {page} kon niet worden opgehaald."
    )

    return None


def download_collection():
    print()
    print("=" * 80)
    print("DISCOGS OPENBARE COLLECTIE DOWNLOADEN")
    print("=" * 80)
    print()
    print("Gebruiker:", USERNAME)
    print()

    all_items = []

    page = 1

    while True:

        data = request_page(page)

        if data is None:
            print()
            print(
                "DOWNLOAD GESTOPT."
            )

            return all_items

        releases = data.get(
            "releases",
            []
        )

        if not releases:
            break

        all_items.extend(
            releases
        )

        pagination = data.get(
            "pagination",
            {}
        )

        pages = pagination.get(
            "pages",
            page
        )

        print(
            f"Pagina {page}/{pages} | "
            f"{len(releases)} releases | "
            f"totaal {len(all_items)}"
        )

        if page >= pages:
            break

        page += 1

        time.sleep(
            REQUEST_DELAY
        )

    print()
    print(
        "TOTAAL OPENBARE COLLECTIE:",
        len(all_items)
    )

    return all_items


def save_cache(items):
    CACHE_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    with open(
        CACHE_FILE,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            items,
            f,
            ensure_ascii=False,
            indent=2
        )

    print()
    print(
        "Collectie opgeslagen:"
    )

    print(
        CACHE_FILE
    )


def load_cache():
    if not CACHE_FILE.exists():
        return None

    try:
        with open(
            CACHE_FILE,
            "r",
            encoding="utf-8"
        ) as f:

            return json.load(f)

    except Exception as exc:

        print()
        print(
            "Cache kon niet worden gelezen:",
            exc
        )

        return None


def get_collection():
    if not REFRESH_MODE:

        cached = load_cache()

        if cached:

            print()
            print(
                "=" * 80
            )

            print(
                "LOKALE DISCOGS-COLLECTIE GEBRUIKEN"
            )

            print(
                "=" * 80
            )

            print()
            print(
                "Cache:",
                CACHE_FILE
            )

            print(
                "Collectie:",
                len(cached)
            )

            return cached

    items = download_collection()

    if items:
        save_cache(items)

    return items


# ============================================================
# DISCOGS DATA
# ============================================================

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
            artist_names.append(
                name
            )

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
            catnos.append(
                catno
            )

    catalog = (
        catnos[0]
        if catnos
        else ""
    )

    formats = basic.get(
        "formats",
        []
    ) or []

    format_names = []

    for fmt in formats:

        name = fmt.get(
            "name",
            ""
        )

        if name:
            format_names.append(
                name
            )

    return {
        "discogs_id": item.get("id"),
        "artist": artist,
        "title": title,
        "year": year,
        "catalog": catalog,
        "formats": format_names,
    }


# ============================================================
# INDEX
# ============================================================

def build_indexes(items):

    records = []

    by_catalog = {}
    by_title = {}
    by_artist = {}

    for item in items:

        data = collection_release_data(
            item
        )

        if not data["discogs_id"]:
            continue

        records.append(
            data
        )

        cat = normalize_catalog(
            data["catalog"]
        )

        if cat:

            by_catalog.setdefault(
                cat,
                []
            ).append(data)

        title = normalize(
            data["title"]
        )

        if title:

            by_title.setdefault(
                title,
                []
            ).append(data)

        artist = normalize(
            data["artist"]
        )

        if artist:

            by_artist.setdefault(
                artist,
                []
            ).append(data)

    return (
        records,
        by_catalog,
        by_title,
        by_artist,
    )


# ============================================================
# TITLE MATCHING
# ============================================================

def title_similarity(local_title, remote_title):

    a = normalize(local_title)
    b = normalize(remote_title)

    if not a or not b:
        return 0.0

    score = SequenceMatcher(
        None,
        a,
        b
    ).ratio() * 100.0

    # EP / E.P. / album / volume woorden
    # mogen het resultaat niet kapotmaken.

    remove_words = {
        "ep",
        "e",
        "p",
        "album",
        "release",
        "vinyl",
        "record",
    }

    aa = [
        x for x in a.split()
        if x not in remove_words
    ]

    bb = [
        x for x in b.split()
        if x not in remove_words
    ]

    if aa and bb:

        cleaned_score = SequenceMatcher(
            None,
            " ".join(aa),
            " ".join(bb)
        ).ratio() * 100.0

        score = max(
            score,
            cleaned_score
        )

    return score


# ============================================================
# ARTIST MATCHING
# ============================================================

def artist_similarity(local_artist, remote_artist):

    if is_various(local_artist):

        if is_various(remote_artist):
            return 100.0

        return 0.0

    a = normalize(local_artist)
    b = normalize(remote_artist)

    if not a or not b:
        return 0.0

    if a == b:
        return 100.0

    direct = SequenceMatcher(
        None,
        a,
        b
    ).ratio() * 100.0

    # Volgorde van artiesten kan verschillen.
    a_parts = set(
        x for x in a.split()
        if x not in {
            "dj",
            "feat",
            "and",
            "vs",
            "pres",
        }
    )

    b_parts = set(
        x for x in b.split()
        if x not in {
            "dj",
            "feat",
            "and",
            "vs",
            "pres",
        }
    )

    if a_parts and b_parts:

        common = len(
            a_parts.intersection(
                b_parts
            )
        )

        if common:

            coverage_a = (
                common /
                len(a_parts)
            ) * 100

            coverage_b = (
                common /
                len(b_parts)
            ) * 100

            set_score = (
                coverage_a +
                coverage_b
            ) / 2

            direct = max(
                direct,
                set_score
            )

    return direct


# ============================================================
# CANDIDATEN
# ============================================================

def candidate_score(
    local,
    remote
):

    local_artist = local["artist"]
    local_title = local["title"]
    local_catalog = local["catalog"]

    remote_artist = remote["artist"]
    remote_title = remote["title"]
    remote_catalog = remote["catalog"]

    cat_match = catalog_match(
        local_catalog,
        remote_catalog
    )

    title_score = title_similarity(
        local_title,
        remote_title
    )

    artist_score = artist_similarity(
        local_artist,
        remote_artist
    )

    # --------------------------------------------------------
    # VARIOUS ARTISTS
    # --------------------------------------------------------

    if is_various(local_artist):

        if not is_various(remote_artist):
            return 0.0, title_score, artist_score, cat_match

        score = (
            title_score * 0.85
            + artist_score * 0.15
        )

        if cat_match:
            score += 30

        return (
            min(score, 100),
            title_score,
            artist_score,
            cat_match
        )

    # --------------------------------------------------------
    # NORMALE RELEASE
    # --------------------------------------------------------

    score = (
        artist_score * 0.45
        + title_score * 0.55
    )

    if cat_match:
        score += 25

    return (
        min(score, 100),
        title_score,
        artist_score,
        cat_match
    )


def find_candidates(
    local,
    records,
    by_catalog,
    by_title,
    by_artist
):

    candidates = []

    # --------------------------------------------------------
    # 1. EXACT CATALOGUS
    # --------------------------------------------------------

    cat = normalize_catalog(
        local["catalog"]
    )

    if cat:

        for candidate in by_catalog.get(
            cat,
            []
        ):

            if candidate not in candidates:
                candidates.append(
                    candidate
                )

    # --------------------------------------------------------
    # 2. EXACTE TITEL
    # --------------------------------------------------------

    title = normalize(
        local["title"]
    )

    if title:

        for candidate in by_title.get(
            title,
            []
        ):

            if candidate not in candidates:
                candidates.append(
                    candidate
                )

    # --------------------------------------------------------
    # 3. ARTIEST
    # --------------------------------------------------------

    if not is_various(
        local["artist"]
    ):

        artist = normalize(
            local["artist"]
        )

        if artist:

            for candidate in by_artist.get(
                artist,
                []
            ):

                if candidate not in candidates:
                    candidates.append(
                        candidate
                    )

    # --------------------------------------------------------
    # 4. TITEL FUZZY
    # --------------------------------------------------------

    if len(candidates) < 10:

        for candidate in records:

            remote_title = candidate[
                "title"
            ]

            if (
                title_similarity(
                    local["title"],
                    remote_title
                ) >= 70
            ):

                if candidate not in candidates:
                    candidates.append(
                        candidate
                    )

    scored = []

    for candidate in candidates:

        score, title_score, artist_score, cat_match = (
            candidate_score(
                local,
                candidate
            )
        )

        if score >= 40:

            scored.append(
                (
                    score,
                    title_score,
                    artist_score,
                    cat_match,
                    candidate,
                )
            )

    scored.sort(
        key=lambda x: x[0],
        reverse=True
    )

    return scored[:5]


# ============================================================
# SCHRIJVEN
# ============================================================

def write_match(
    conn,
    release_id,
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
            release_id,
        )
    )


# ============================================================
# MAIN
# ============================================================

def main():

    print()
    print("=" * 80)
    print("KID ACID'S VINYLVAULT V3")
    print("SLIMME DISCOGS COLLECTION MATCHER")
    print("=" * 80)

    print()
    print(
        "DATABASE:",
        DB_PATH
    )

    print()

    if WRITE_MODE:

        print(
            "DATABASE WORDT GEWIJZIGD"
        )

    else:

        print(
            "DATABASE WORDT NIET GEWIJZIGD"
        )

    conn = open_db()

    missing = get_missing_releases(
        conn
    )

    print()
    print(
        "Releases zonder Discogs:",
        len(missing)
    )

    collection = get_collection()

    if not collection:

        print()
        print(
            "GEEN COLLECTIE GEVONDEN."
        )

        conn.close()
        return

    (
        records,
        by_catalog,
        by_title,
        by_artist,
    ) = build_indexes(
        collection
    )

    print()
    print(
        "Bruikbare Discogs releases:",
        len(records)
    )

    print(
        "Catalogusindex:",
        len(by_catalog)
    )

    print(
        "Titelindex:",
        len(by_title)
    )

    print(
        "Artiestenindex:",
        len(by_artist)
    )

    strong = 0
    weak = 0
    none = 0
    catalog_matches = 0

    for number, local in enumerate(
        missing,
        start=1
    ):

        print()
        print(
            "-" * 80
        )

        print(
            f"[{number}/{len(missing)}] "
            f"V3 RELEASE #{local['id']}"
        )

        print(
            "LOKAAL:",
            local["artist"],
            "-",
            local["title"]
        )

        if local["catalog"]:

            print(
                "CATALOG:",
                local["catalog"]
            )

        candidates = find_candidates(
            local,
            records,
            by_catalog,
            by_title,
            by_artist,
        )

        if not candidates:

            print()
            print(
                "GEEN KANDIDATEN GEVONDEN"
            )

            none += 1
            continue

        print()
        print(
            "BESTE KANDIDATEN:"
        )

        best = candidates[0]

        for index, (
            score,
            title_score,
            artist_score,
            cat_match,
            candidate,
        ) in enumerate(
            candidates,
            start=1
        ):

            print()
            print(
                f"#{index} "
                f"Score: {score:.1f}"
            )

            print(
                "Discogs ID:",
                candidate["discogs_id"]
            )

            print(
                "Artiest:",
                candidate["artist"]
            )

            print(
                "Titel:",
                candidate["title"]
            )

            print(
                "Catalog:",
                candidate["catalog"]
            )

            print(
                f"Titel-score: "
                f"{title_score:.1f}%"
            )

            print(
                f"Artiest-score: "
                f"{artist_score:.1f}%"
            )

            print(
                "Catalog-match:",
                "JA" if cat_match else "NEE"
            )

            if cat_match:
                print(
                    "FORMAT:",
                    ", ".join(
                        candidate["formats"]
                    )
                )

        (
            best_score,
            best_title,
            best_artist,
            best_cat,
            best_candidate,
        ) = best

        if best_cat:
            catalog_matches += 1

        # ----------------------------------------------------
        # STERKE MATCH
        # ----------------------------------------------------

        if best_score >= STRONG_SCORE:

            strong += 1

            print()
            print(
                ">>> STERKE MATCH <<<"
            )

            if WRITE_MODE:

                write_match(
                    conn,
                    local["id"],
                    best_candidate[
                        "discogs_id"
                    ]
                )

                conn.commit()

                print(
                    ">>> OPGESLAGEN <<<"
                )

            else:

                print(
                    ">>> DRY RUN - NIET OPGESLAGEN <<<"
                )

        elif best_score >= MIN_SCORE:

            weak += 1

            print()
            print(
                ">>> ZWAKKE MATCH - NIET OPGESLAGEN <<<"
            )

        else:

            none += 1

            print()
            print(
                ">>> GEEN BETROUWBARE MATCH <<<"
            )

    print()
    print("=" * 80)
    print("KLAAR")
    print("=" * 80)

    print()
    print(
        "Te controleren:",
        len(missing)
    )

    print(
        "Sterke matches:",
        strong
    )

    print(
        "Zwakke matches:",
        weak
    )

    print(
        "Geen betrouwbare match:",
        none
    )

    print(
        "Catalogusmatches:",
        catalog_matches
    )

    print()

    if WRITE_MODE:

        print(
            "DATABASE IS BIJGEWERKT."
        )

    else:

        print(
            "DRY RUN: DATABASE IS NIET GEWIJZIGD."
        )

        print()
        print(
            "Als de resultaten goed zijn:"
        )

        print(
            "python tools\\discogs\\auto_match_collection_v2.py --write"
        )

        print()
        print(
            "Volledige collectie opnieuw downloaden:"
        )

        print(
            "python tools\\discogs\\auto_match_collection_v2.py --refresh"
        )

    conn.close()


if __name__ == "__main__":
    main()

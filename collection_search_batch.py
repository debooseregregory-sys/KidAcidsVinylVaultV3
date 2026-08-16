# ============================================================
# KID ACID'S VINYLVAULT V3
# COLLECTION SEARCH BATCH ENGINE
# ============================================================
#
# CSV -> unieke releases -> Discogs zoeken -> kandidaten
# -> volledige controle van beste kandidaten
#
# GEEN handmatige Discogs Release ID nodig.
#
# Bron:
# C:\Users\andyb\Desktop\vinyl_collectie.csv
#
# CSV:
# cp1252
#
# ============================================================

import csv
import os
import sys
import time
import requests
import config


# ============================================================
# PROJECT
# ============================================================

ROOT = os.path.dirname(
    os.path.abspath(__file__)
)

if ROOT not in sys.path:
    sys.path.insert(0, ROOT)


# ============================================================
# CONFIG
# ============================================================

API_URL = "https://api.discogs.com"

HEADERS = {
    "User-Agent": config.DISCOGS_USER_AGENT,
    "Accept": "application/json",
}

COLLECTION_FILE = r"C:\Users\andyb\Desktop\vinyl_collectie.csv"

SEARCH_DELAY = 1.2
RELEASE_DELAY = 2.0

MIN_SCORE_TO_IMPORT = 80.0


# ============================================================
# NORMALIZE
# ============================================================

def normalize(text):

    if text is None:
        return ""

    text = str(text)

    text = (
        text
        .replace("\ufeff", "")
        .replace("\xa0", " ")
    )

    return " ".join(
        text.strip().split()
    )


def normalize_compare(text):

    return (
        normalize(text)
        .lower()
        .replace("–", "-")
        .replace("—", "-")
    )


# ============================================================
# READ CSV
# ============================================================

def read_collection(
    filename=COLLECTION_FILE
):

    if not os.path.exists(filename):

        raise FileNotFoundError(
            f"Collectiebestand niet gevonden:\n{filename}"
        )

    rows = []

    with open(
        filename,
        "r",
        encoding="cp1252",
        newline=""
    ) as handle:

        reader = csv.DictReader(handle)

        for row in reader:

            artist = normalize(
                row.get("Artist", "")
            )

            track = normalize(
                row.get("Tracks", "")
            )

            label_catalog = normalize(
                row.get("Label / Catalog", "")
            )

            code = normalize(
                row.get("ID - CODE", "")
            )

            if not any(
                (
                    artist,
                    track,
                    label_catalog,
                    code
                )
            ):
                continue

            rows.append(
                {
                    "artist": artist,
                    "track": track,
                    "label_catalog":
                        label_catalog,
                    "code": code,
                }
            )

    return rows


# ============================================================
# GROUP RELEASES
# ============================================================

def release_key(row):

    return (
        normalize_compare(
            row["label_catalog"]
        ),
        normalize_compare(
            row["code"]
        ),
    )


def group_collection(rows):

    groups = {}

    for row in rows:

        key = release_key(row)

        if key not in groups:

            groups[key] = {
                "artist":
                    row["artist"],

                "label_catalog":
                    row["label_catalog"],

                "code":
                    row["code"],

                "tracks": [],
            }

        if row["track"]:

            groups[key]["tracks"].append(
                {
                    "artist":
                        row["artist"],

                    "title":
                        row["track"],
                }
            )

    return list(
        groups.values()
    )


# ============================================================
# RELEASE TITLE FILTER
# ============================================================

def is_release_header(
    group,
    track
):

    artist = normalize_compare(
        track.get("artist", "")
    )

    title = normalize_compare(
        track.get("title", "")
    )

    collection_artist = normalize_compare(
        group.get("artist", "")
    )

    if (
        artist == "various artists"
        and
        collection_artist == "various artists"
        and
        (
            title.startswith(
                "i love techno classics"
            )
            or
            title.endswith(
                "ep"
            )
        )
    ):

        return True

    return False


# ============================================================
# REAL TRACKS
# ============================================================

def get_real_tracks(group):

    tracks = []

    for track in group["tracks"]:

        if is_release_header(
            group,
            track
        ):
            continue

        artist = normalize(
            track.get("artist", "")
        )

        title = normalize(
            track.get("title", "")
        )

        if not title:
            continue

        tracks.append(
            {
                "artist": artist,
                "title": title,
            }
        )

    return tracks


# ============================================================
# DISCOGS REQUEST
# ============================================================

def discogs_search(
    artist="",
    title="",
    catalog=""
):

    params = {
        "type": "release",
        "per_page": 10,
        "page": 1,
    }

    if artist:
        params["artist"] = artist

    if title:
        params["track"] = title

    if catalog:
        params["catno"] = catalog

    response = requests.get(
        f"{API_URL}/database/search",
        headers=HEADERS,
        params=params,
        timeout=30,
    )

    if response.status_code == 429:

        raise RuntimeError(
            "DISCOGS_RATE_LIMIT"
        )

    response.raise_for_status()

    return response.json().get(
        "results",
        []
    )


# ============================================================
# SEARCH CANDIDATES
# ============================================================

def find_candidates(group):

    tracks = get_real_tracks(
        group
    )

    candidates = {}

    # maximaal 5 echte tracks
    # gebruiken om zoekvolume te beperken

    for track in tracks[:5]:

        artist = track["artist"]
        title = track["title"]

        queries = [
            {
                "artist": artist,
                "title": title,
                "catalog":
                    group["code"],
            },
            {
                "artist": artist,
                "title": title,
            },
        ]

        for query in queries:

            try:

                results = discogs_search(
                    artist=query.get(
                        "artist",
                        ""
                    ),
                    title=query.get(
                        "title",
                        ""
                    ),
                    catalog=query.get(
                        "catalog",
                        ""
                    ),
                )

            except RuntimeError as exc:

                if str(exc) == "DISCOGS_RATE_LIMIT":

                    print()
                    print(
                        "DISCogs rate limit."
                    )

                    print(
                        "Wachten 10 seconden..."
                    )

                    time.sleep(
                        10
                    )

                    continue

                raise

            except Exception as exc:

                print(
                    "Zoekfout:",
                    exc
                )

                continue

            for result in results:

                result_id = result.get(
                    "id"
                )

                if not result_id:
                    continue

                if result_id not in candidates:

                    candidates[result_id] = {
                        "result":
                            result,

                        "search_hits":
                            0,

                        "matched_search_tracks":
                            [],
                    }

                candidates[result_id][
                    "search_hits"
                ] += 1

                candidates[result_id][
                    "matched_search_tracks"
                ].append(
                    {
                        "artist":
                            artist,

                        "title":
                            title,
                    }
                )

            time.sleep(
                SEARCH_DELAY
            )

    return list(
        candidates.values()
    )


# ============================================================
# COMPLETE RELEASE
# ============================================================

def get_release(
    release_id,
    retries=5
):

    url = (
        f"{API_URL}/releases/"
        f"{release_id}"
    )

    for attempt in range(
        retries
    ):

        response = requests.get(
            url,
            headers=HEADERS,
            timeout=30,
        )

        if response.status_code == 200:

            time.sleep(
                RELEASE_DELAY
            )

            return response.json()

        if response.status_code == 429:

            wait = 15 * (
                attempt + 1
            )

            print(
                f"429 voor {release_id}."
            )

            print(
                f"Wachten {wait} seconden..."
            )

            time.sleep(
                wait
            )

            continue

        response.raise_for_status()

    return None


# ============================================================
# TRACK NORMALIZE
# ============================================================

def track_key(
    artist,
    title
):

    return (
        normalize_compare(
            artist
        ),
        normalize_compare(
            title
        ),
    )


# ============================================================
# TRACK MATCH
# ============================================================

def tracks_match(
    collection_track,
    discogs_track
):

    collection_artist = (
        normalize_compare(
            collection_track["artist"]
        )
    )

    collection_title = (
        normalize_compare(
            collection_track["title"]
        )
    )

    discogs_artist = (
        normalize_compare(
            discogs_track["artist"]
        )
    )

    discogs_title = (
        normalize_compare(
            discogs_track["title"]
        )
    )

    if not collection_title:
        return False

    # Titel moet exact overeenkomen
    if collection_title != discogs_title:
        return False

    # Artist exact
    if collection_artist == discogs_artist:
        return True

    # Various Artists kan op Discogs
    # anders weergegeven worden
    if collection_artist == "various artists":
        return True

    return False


# ============================================================
# RELEASE TRACKS
# ============================================================

def get_discogs_tracks(
    release
):

    tracks = []

    for item in release.get(
        "tracklist",
        []
    ):

        title = normalize(
            item.get(
                "title",
                ""
            )
        )

        if not title:
            continue

        artists = item.get(
            "artists",
            []
        )

        artist = ""

        if artists:

            artist = normalize(
                artists[0].get(
                    "name",
                    ""
                )
            )

        if not artist:

            release_artists = release.get(
                "artists",
                []
            )

            if release_artists:

                artist = normalize(
                    release_artists[0].get(
                        "name",
                        ""
                    )
                )

        tracks.append(
            {
                "artist":
                    artist,

                "title":
                    title,
            }
        )

    return tracks


# ============================================================
# SCORE RELEASE
# ============================================================

def score_release(
    group,
    release
):

    collection_tracks = (
        get_real_tracks(
            group
        )
    )

    discogs_tracks = (
        get_discogs_tracks(
            release
        )
    )

    matched = []
    unmatched = []

    used = set()

    for collection_track in collection_tracks:

        found = False

        for index, discogs_track in enumerate(
            discogs_tracks
        ):

            if index in used:
                continue

            if tracks_match(
                collection_track,
                discogs_track
            ):

                matched.append(
                    collection_track
                )

                used.add(
                    index
                )

                found = True

                break

        if not found:

            unmatched.append(
                collection_track
            )

    total = len(
        collection_tracks
    )

    matched_count = len(
        matched
    )

    # ========================================================
    # TRACK SCORE
    # ========================================================

    track_score = 0

    if total:

        track_score = (
            matched_count
            /
            total
        ) * 70

    # ========================================================
    # CATALOG SCORE
    # ========================================================

    wanted_code = normalize_compare(
        group["code"]
    )

    catalog_match = False

    release_catalogs = []

    for label in release.get(
        "labels",
        []
    ):

        catno = normalize_compare(
            label.get(
                "catno",
                ""
            )
        )

        if catno:

            release_catalogs.append(
                catno
            )

    for catno in release_catalogs:

        if (
            wanted_code
            and
            (
                wanted_code == catno
                or
                wanted_code in catno
                or
                catno in wanted_code
            )
        ):

            catalog_match = True

            break

    catalog_score = (
        20
        if catalog_match
        else 0
    )

    # ========================================================
    # LABEL SCORE
    # ========================================================

    wanted_label = normalize_compare(
        group["label_catalog"]
    )

    label_match = False

    for label in release.get(
        "labels",
        []
    ):

        label_name = normalize_compare(
            label.get(
                "name",
                ""
            )
        )

        if not label_name:
            continue

        if (
            label_name in wanted_label
            or
            wanted_label in label_name
        ):

            label_match = True

            break

    label_score = (
        10
        if label_match
        else 0
    )

    total_score = (
        track_score
        +
        catalog_score
        +
        label_score
    )

    return {
        "score":
            round(
                total_score,
                1
            ),

        "matched":
            matched,

        "unmatched":
            unmatched,

        "total_tracks":
            total,

        "matched_tracks":
            matched_count,

        "catalog_match":
            catalog_match,

        "label_match":
            label_match,
    }


# ============================================================
# FIND BEST RELEASE
# ============================================================

def find_best_release(
    group,
    candidates,
    max_verify=5
):

    # Eerst de zoekhits gebruiken om de beste
    # kandidaten te kiezen.
    #
    # Daarna pas volledige releases ophalen.

    candidates.sort(
        key=lambda item:
        item["search_hits"],
        reverse=True
    )

    verified = []

    for candidate in candidates[
        :max_verify
    ]:

        result = candidate[
            "result"
        ]

        release_id = result.get(
            "id"
        )

        print()
        print(
            "Controleer Discogs ID:",
            release_id
        )

        release = get_release(
            release_id
        )

        if not release:

            continue

        match = score_release(
            group,
            release
        )

        verified.append(
            {
                "id":
                    release_id,

                "release":
                    release,

                "match":
                    match,

                "search_hits":
                    candidate[
                        "search_hits"
                    ],
            }
        )

    verified.sort(
        key=lambda item:
        item["match"]["score"],
        reverse=True
    )

    if not verified:

        return None

    return verified[0]


# ============================================================
# PRINT RESULT
# ============================================================

def print_result(
    group,
    best
):

    print()
    print("=" * 80)
    print("BESTE MATCH")
    print("=" * 80)

    print(
        "Collectie:",
        group["artist"]
    )

    print(
        "Catalog:",
        group["label_catalog"]
    )

    print(
        "Code:",
        group["code"]
    )

    if not best:

        print(
            "GEEN MATCH GEVONDEN"
        )

        return

    release = best[
        "release"
    ]

    match = best[
        "match"
    ]

    print()
    print(
        "Discogs:",
        release.get(
            "title",
            ""
        )
    )

    print(
        "Discogs ID:",
        release.get(
            "id"
        )
    )

    print(
        "Jaar:",
        release.get(
            "year"
        )
    )

    print(
        "SCORE:",
        f"{match['score']}%"
    )

    print(
        "Tracks:",
        f"{match['matched_tracks']}/"
        f"{match['total_tracks']}"
    )

    print(
        "Catalog:",
        "JA"
        if match["catalog_match"]
        else "NEE"
    )

    print(
        "Label:",
        "JA"
        if match["label_match"]
        else "NEE"
    )

    if match["unmatched"]:

        print()
        print(
            "NIET GEVONDEN:"
        )

        for track in match[
            "unmatched"
        ]:

            print(
                " -",
                track["artist"],
                "|",
                track["title"]
            )


# ============================================================
# TEST BATCH
# ============================================================

def test_batch(
    limit=10
):

    rows = read_collection()

    groups = group_collection(
        rows
    )

    print()
    print("=" * 80)
    print("VINYLVAULT V3 BATCH TEST")
    print("=" * 80)

    print(
        "CSV rijen:",
        len(rows)
    )

    print(
        "Unieke releases:",
        len(groups)
    )

    print(
        "Test aantal:",
        limit
    )

    print()

    for number, group in enumerate(
        groups[:limit],
        start=1
    ):

        print()
        print("#" * 80)

        print(
            f"RELEASE {number}/{limit}"
        )

        print(
            "Artist:",
            group["artist"]
        )

        print(
            "Label:",
            group["label_catalog"]
        )

        print(
            "Code:",
            group["code"]
        )

        tracks = get_real_tracks(
            group
        )

        print(
            "Tracks:",
            len(tracks)
        )

        candidates = find_candidates(
            group
        )

        print(
            "Kandidaten:",
            len(candidates)
        )

        best = find_best_release(
            group,
            candidates,
            max_verify=5
        )

        print_result(
            group,
            best
        )

    print()
    print("=" * 80)
    print("BATCH TEST KLAAR")
    print("=" * 80)


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    test_batch(
        limit=10
    )

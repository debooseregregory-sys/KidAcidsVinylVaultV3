# ============================================================
# KID ACID'S VINYLVAULT V3
# COLLECTION SEARCH IMPORT
# ============================================================

import csv
import os
import time
import requests
import config


API_URL = "https://api.discogs.com"

HEADERS = {
    "User-Agent": config.DISCOGS_USER_AGENT,
    "Accept": "application/json",
}

DEFAULT_FILE = r"C:\Users\andyb\Desktop\vinyl_collectie.csv"


# ============================================================
# NORMALIZE
# ============================================================

def normalize(text):

    if text is None:
        return ""

    return " ".join(
        str(text)
        .replace("\ufeff", "")
        .strip()
        .split()
    )


def normalize_compare(text):

    text = normalize(text).lower()

    replacements = {
        "á": "a",
        "à": "a",
        "ä": "a",
        "â": "a",
        "ã": "a",
        "å": "a",
        "é": "e",
        "è": "e",
        "ë": "e",
        "ê": "e",
        "í": "i",
        "ì": "i",
        "ï": "i",
        "î": "i",
        "ó": "o",
        "ò": "o",
        "ö": "o",
        "ô": "o",
        "õ": "o",
        "ú": "u",
        "ù": "u",
        "ü": "u",
        "û": "u",
        "ñ": "n",
    }

    for old, new in replacements.items():
        text = text.replace(old, new)

    return text


# ============================================================
# READ COLLECTION
# ============================================================

def read_collection(filename=DEFAULT_FILE):

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
                    "label_catalog": label_catalog,
                    "code": code,
                }
            )

    return rows


# ============================================================
# RELEASE KEY
# ============================================================

def release_key(row):

    return (
        normalize(
            row["label_catalog"]
        ).lower(),

        normalize(
            row["code"]
        ).lower()
    )


# ============================================================
# GROUP RELEASES
# ============================================================

def group_collection(rows):

    groups = {}

    for row in rows:

        key = release_key(row)

        if key not in groups:

            groups[key] = {
                "artist": row["artist"],
                "label_catalog": row["label_catalog"],
                "code": row["code"],
                "tracks": [],
            }

        if row["track"]:

            groups[key]["tracks"].append(
                {
                    "artist": row["artist"],
                    "title": row["track"],
                }
            )

    return list(
        groups.values()
    )


# ============================================================
# RELEASE HEADER DETECTION
# ============================================================

def is_release_header(group, track):

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
        collection_artist == "various artists"
        and
        artist == "various artists"
    ):
        return True

    if (
        collection_artist == "untitled"
        and
        artist == "untitled"
        and
        title.lower()
        in {
            "i love techno classics 4 / 5",
            "i love techno classics 4/5",
        }
    ):
        return True

    return False


# ============================================================
# REAL TRACKS
# ============================================================

def get_real_tracks(group):

    real_tracks = []

    for track in group["tracks"]:

        artist = normalize(
            track.get("artist", "")
        )

        title = normalize(
            track.get("title", "")
        )

        if not title:
            continue

        if is_release_header(
            group,
            track
        ):
            continue

        real_tracks.append(
            {
                "artist": artist,
                "title": title,
            }
        )

    return real_tracks


# ============================================================
# HTTP SESSION
# ============================================================

SESSION = requests.Session()

SESSION.headers.update(
    HEADERS
)


# ============================================================
# RATE LIMIT
# ============================================================

_LAST_REQUEST = 0.0

REQUEST_DELAY = 2.0


def wait_before_request():

    global _LAST_REQUEST

    now = time.time()

    elapsed = now - _LAST_REQUEST

    if elapsed < REQUEST_DELAY:

        time.sleep(
            REQUEST_DELAY - elapsed
        )

    _LAST_REQUEST = time.time()


# ============================================================
# DISCOGS REQUEST
# ============================================================

def discogs_get(
    url,
    params=None,
    retries=5
):

    for attempt in range(retries):

        wait_before_request()

        try:

            response = SESSION.get(
                url,
                params=params,
                timeout=30,
            )

        except requests.RequestException as exc:

            print(
                "Discogs netwerkfout:",
                exc
            )

            time.sleep(
                5 * (attempt + 1)
            )

            continue

        if response.status_code == 200:

            return response.json()

        if response.status_code == 429:

            retry_after = response.headers.get(
                "Retry-After"
            )

            if retry_after:

                try:
                    wait_time = float(
                        retry_after
                    )
                except ValueError:
                    wait_time = 10
            else:

                wait_time = (
                    10 * (attempt + 1)
                )

            print(
                "Discogs rate limit.",
                f"Wachten {wait_time:.0f} seconden..."
            )

            time.sleep(
                wait_time
            )

            continue

        if response.status_code in (
            500,
            502,
            503,
            504,
        ):

            wait_time = (
                5 * (attempt + 1)
            )

            print(
                "Discogs serverfout:",
                response.status_code,
                f"- wachten {wait_time} seconden..."
            )

            time.sleep(
                wait_time
            )

            continue

        response.raise_for_status()

    raise RuntimeError(
        "Discogs API blijft tijdelijk "
        "onbeschikbaar."
    )


# ============================================================
# DISCOGS SEARCH
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

    data = discogs_get(
        f"{API_URL}/database/search",
        params=params,
    )

    return data.get(
        "results",
        []
    )


# ============================================================
# SEARCH COLLECTION RELEASE
# ============================================================

def search_collection_release(group):

    collection_artist = group["artist"]

    tracks = get_real_tracks(
        group
    )

    print()
    print("=" * 80)
    print("DISCOGS ZOEKOPDRACHT")
    print("=" * 80)

    print(
        "Artist :",
        collection_artist
    )

    print(
        "Label  :",
        group["label_catalog"]
    )

    print(
        "Code   :",
        group["code"]
    )

    print(
        "Tracks :",
        len(group["tracks"])
    )

    print()
    print("ECHTE TRACKS:")

    for track in tracks:

        print(
            "-",
            track["artist"],
            "|",
            track["title"]
        )

    candidates = {}

    # ========================================================
    # MAXIMAAL 3 TRACKS VOOR SEARCH
    # ========================================================

    for track in tracks[:3]:

        artist = track["artist"]
        title = track["title"]

        print()
        print(
            "Zoeken:",
            artist,
            "-",
            title
        )

        queries = [
            {
                "artist": artist,
                "title": title,
                "catalog": group["code"],
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

            except Exception as exc:

                print(
                    "Discogs zoekfout:",
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
                        "result": result,
                        "search_hits": set(),
                    }

                candidates[result_id][
                    "search_hits"
                ].add(
                    normalize_compare(title)
                )

    ordered = []

    for item in candidates.values():

        result = item["result"]

        ordered.append(
            {
                "result": result,
                "search_hits": len(
                    item["search_hits"]
                ),
            }
        )

    ordered.sort(
        key=lambda item:
        item["search_hits"],
        reverse=True
    )

    print()
    print("=" * 80)
    print("DISCOGS KANDIDATEN")
    print("=" * 80)

    print(
        "Kandidaten:",
        len(ordered)
    )

    final_results = []

    for item in ordered[:20]:

        result = item["result"]

        print()
        print(
            "Search hits:",
            item["search_hits"]
        )

        print(
            "ID:",
            result.get("id")
        )

        print(
            "Titel:",
            result.get("title")
        )

        print(
            "Jaar:",
            result.get("year")
        )

        print(
            "Label:",
            result.get("label")
        )

        result["_vv_search_hits"] = (
            item["search_hits"]
        )

        final_results.append(
            result
        )

    return final_results


# ============================================================
# GET COMPLETE DISCOGS RELEASE
# ============================================================

def get_discogs_release(
    release_id
):

    url = (
        f"{API_URL}/releases/"
        f"{release_id}"
    )

    return discogs_get(
        url
    )


# ============================================================
# NORMALIZE TRACK
# ============================================================

def normalize_track(
    artist,
    title
):

    return (
        normalize_compare(artist),
        normalize_compare(title)
    )


# ============================================================
# TRACK TITLE MATCH
# ============================================================

def track_title_match(
    wanted,
    actual
):

    wanted = normalize_compare(
        wanted
    )

    actual = normalize_compare(
        actual
    )

    if not wanted or not actual:
        return False

    if wanted == actual:
        return True

    # Haakjes en remix-info niet altijd
    # identiek in CSV / Discogs.

    wanted_base = wanted.split("(")[0].strip()
    actual_base = actual.split("(")[0].strip()

    if (
        wanted_base
        and
        wanted_base == actual_base
    ):
        return True

    return False


# ============================================================
# ARTIST MATCH
# ============================================================

def artist_match(
    wanted,
    actual
):

    wanted = normalize_compare(
        wanted
    )

    actual = normalize_compare(
        actual
    )

    if (
        not wanted
        or
        not actual
    ):
        return True

    if wanted == actual:
        return True

    if wanted == "various artists":
        return True

    if (
        wanted in actual
        or
        actual in wanted
    ):
        return True

    return False


# ============================================================
# RELEASE TRACK MATCHING
# ============================================================

def calculate_release_match(
    group,
    release
):

    collection_tracks = []

    for track in get_real_tracks(
        group
    ):

        collection_tracks.append(
            {
                "artist":
                    normalize(
                        track["artist"]
                    ),
                "title":
                    normalize(
                        track["title"]
                    ),
            }
        )

    discogs_tracks = []

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

        if artists:

            artist_parts = []

            for artist in artists:

                name = normalize(
                    artist.get(
                        "name",
                        ""
                    )
                )

                if name:
                    artist_parts.append(
                        name
                    )

            artist = " & ".join(
                artist_parts
            )

        else:

            release_artists = (
                release.get(
                    "artists",
                    []
                )
            )

            if release_artists:

                artist = normalize(
                    release_artists[0].get(
                        "name",
                        ""
                    )
                )

            else:

                artist = ""

        discogs_tracks.append(
            {
                "artist": artist,
                "title": title,
            }
        )

    matched = []
    unmatched = []

    used_discogs_indexes = set()

    for collection_track in collection_tracks:

        found_index = None

        for index, discogs_track in enumerate(
            discogs_tracks
        ):

            if index in used_discogs_indexes:
                continue

            if not track_title_match(
                collection_track["title"],
                discogs_track["title"]
            ):
                continue

            if not artist_match(
                collection_track["artist"],
                discogs_track["artist"]
            ):
                continue

            found_index = index
            break

        if found_index is not None:

            used_discogs_indexes.add(
                found_index
            )

            matched.append(
                collection_track
            )

        else:

            unmatched.append(
                collection_track
            )

    total = len(
        collection_tracks
    )

    matches = len(
        matched
    )

    # ========================================================
    # TRACK SCORE
    # ========================================================

    track_score = 0

    if total:

        track_score = (
            matches / total
        ) * 70

    # ========================================================
    # CATALOG SCORE
    # ========================================================

    catalog_score = 0

    wanted_catalog = normalize_compare(
        group["code"]
    )

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
            wanted_catalog
            and
            (
                wanted_catalog == catno
                or
                wanted_catalog in catno
                or
                catno in wanted_catalog
            )
        ):

            catalog_score = 20
            break

    # ========================================================
    # LABEL SCORE
    # ========================================================

    label_score = 0

    wanted_label = normalize_compare(
        group["label_catalog"]
    )

    # De CSV kan het veld bevatten:
    #
    # 541 (NEWS) 541416 501474
    #
    # Discogs heeft meestal alleen:
    #
    # 541
    #
    # Daarom zoeken we losse betekenisvolle
    # delen.

    wanted_label_parts = [
        part
        for part in wanted_label.replace(
            "(",
            " "
        ).replace(
            ")",
            " "
        ).split()
        if len(part) >= 3
    ]

    release_labels = []

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

        if label_name:
            release_labels.append(
                label_name
            )

    for release_label in release_labels:

        for wanted_part in wanted_label_parts:

            if wanted_part in release_label:

                label_score = 10
                break

        if label_score:
            break

    # ========================================================
    # EXTRA RELEASE TITLE / ARTIST CHECK
    # ========================================================

    artist_score = 0

    wanted_artist = normalize_compare(
        group.get(
            "artist",
            ""
        )
    )

    release_artist_names = []

    for artist in release.get(
        "artists",
        []
    ):

        name = normalize_compare(
            artist.get(
                "name",
                ""
            )
        )

        if name:
            release_artist_names.append(
                name
            )

    if (
        wanted_artist == "various artists"
        and release_artist_names
    ):

        artist_score = 5

    elif wanted_artist:

        for release_artist in release_artist_names:

            if artist_match(
                wanted_artist,
                release_artist
            ):

                artist_score = 5
                break

    # ========================================================
    # FINAL SCORE
    # ========================================================

    score = (
        track_score
        +
        catalog_score
        +
        label_score
        +
        artist_score
    )

    return {
        "score": round(
            score,
            1
        ),
        "matched": matched,
        "unmatched": unmatched,
        "total_tracks": total,
        "matched_tracks": matches,
        "catalog_match":
            catalog_score > 0,
        "label_match":
            label_score > 0,
        "artist_match":
            artist_score > 0,
    }


# ============================================================
# VERIFY DISCOGS CANDIDATES
# ============================================================

def verify_discogs_candidates(
    group,
    candidates,
    minimum_score=60
):

    verified = []

    print()
    print("=" * 80)
    print("DISCOGS RELEASE CONTROLE")
    print("=" * 80)

    for candidate in candidates:

        release_id = candidate.get(
            "id"
        )

        if not release_id:
            continue

        try:

            release = get_discogs_release(
                release_id
            )

        except Exception as exc:

            print(
                "Release",
                release_id,
                "kon niet worden opgehaald:",
                exc
            )

            continue

        match = calculate_release_match(
            group,
            release
        )

        candidate["_vv_match"] = match
        candidate["_vv_release"] = release

        verified.append(
            candidate
        )

    verified.sort(
        key=lambda item:
        item["_vv_match"]["score"],
        reverse=True
    )

    print()

    for number, candidate in enumerate(
        verified[:10],
        start=1
    ):

        release = candidate[
            "_vv_release"
        ]

        match = candidate[
            "_vv_match"
        ]

        print(
            f"{number}. "
            f"{release.get('title', '')}"
        )

        print(
            "   Discogs ID:",
            release.get("id")
        )

        print(
            "   Jaar:",
            release.get("year")
        )

        print(
            "   Score:",
            match["score"],
            "%"
        )

        print(
            "   Tracks:",
            f"{match['matched_tracks']}/"
            f"{match['total_tracks']}"
        )

        print(
            "   Catalog:",
            "JA"
            if match["catalog_match"]
            else "NEE"
        )

        print(
            "   Label:",
            "JA"
            if match["label_match"]
            else "NEE"
        )

        print(
            "   Artist:",
            "JA"
            if match["artist_match"]
            else "NEE"
        )

        print()

    # ========================================================
    # BEST RESULT
    # ========================================================

    if not verified:

        return None

    best = verified[0]

    best_match = best[
        "_vv_match"
    ]

    print(
        "BESTE KANDIDAAT:"
    )

    print(
        "Discogs ID:",
        best.get("id")
    )

    print(
        "Titel:",
        best[
            "_vv_release"
        ].get(
            "title"
        )
    )

    print(
        "Score:",
        best_match["score"],
        "%"
    )

    print(
        "Tracks:",
        f"{best_match['matched_tracks']}/"
        f"{best_match['total_tracks']}"
    )

    if (
        best_match["score"]
        >= minimum_score
    ):

        print()
        print(
            ">>> GOEDE MATCH"
        )

        return best

    print()
    print(
        ">>> SCORE TE LAAG"
    )

    print(
        ">>> Release wordt overgeslagen."
    )

    return None


# ============================================================
# SUMMARY
# ============================================================

def collection_summary(
    filename=DEFAULT_FILE
):

    rows = read_collection(
        filename
    )

    groups = group_collection(
        rows
    )

    print()
    print("=" * 80)
    print("VINYLVAULT V3 COLLECTIE")
    print("=" * 80)

    print(
        "CSV rijen       :",
        len(rows)
    )

    print(
        "Unieke releases :",
        len(groups)
    )

    print()

    return groups


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    groups = collection_summary()

    for number, group in enumerate(
        groups[:10],
        start=1
    ):

        print(
            f"{number}. "
            f"{group['artist']} | "
            f"{group['label_catalog']} | "
            f"{group['code']} | "
            f"{len(group['tracks'])} tracks"
        )

import sqlite3
import requests
import time
import re
import os

DB = os.path.abspath(r".\data\vinylvault.db")

HEADERS = {
    "User-Agent": "KidAcidVinylVaultV3/1.0",
    "Accept": "application/json"
}

API = "https://api.discogs.com"


def normalize(text):
    if not text:
        return ""

    text = str(text).lower()

    text = re.sub(r"[\(\)\[\]\{\},.!?:;\"'/\\_-]", " ", text)

    text = re.sub(r"\s+", " ", text)

    return text.strip()


def search_discogs(artist, track):

    try:
        r = requests.get(
            f"{API}/database/search",
            headers=HEADERS,
            params={
                "artist": artist,
                "track": track,
                "type": "release",
                "format": "Vinyl"
            },
            timeout=30
        )

        if r.status_code == 429:

            wait = int(
                r.headers.get(
                    "Retry-After",
                    "10"
                )
            )

            print(
                f"RATE LIMIT - wachten {wait}s"
            )

            time.sleep(wait)

            return search_discogs(
                artist,
                track
            )

        if r.status_code != 200:
            return []

        return r.json().get(
            "results",
            []
        )

    except Exception as exc:

        print(
            "NETWERKFOUT:",
            exc
        )

        return []


def get_release(release_id):

    try:

        r = requests.get(
            f"{API}/releases/{release_id}",
            headers=HEADERS,
            timeout=30
        )

        if r.status_code == 429:

            wait = int(
                r.headers.get(
                    "Retry-After",
                    "10"
                )
            )

            print(
                f"RATE LIMIT - wachten {wait}s"
            )

            time.sleep(wait)

            return get_release(
                release_id
            )

        if r.status_code != 200:
            return None

        return r.json()

    except Exception as exc:

        print(
            "NETWERKFOUT:",
            exc
        )

        return None


def is_vinyl(release):

    for fmt in release.get(
        "formats",
        []
    ):

        name = normalize(
            fmt.get(
                "name",
                ""
            )
        )

        if name == "vinyl":
            return True

    return False


def release_tracks(release):

    result = []

    for track in release.get(
        "tracklist",
        []
    ):

        title = track.get(
            "title",
            ""
        ).strip()

        position = track.get(
            "position",
            ""
        ).strip()

        if not title:
            continue

        result.append(
            (
                position,
                normalize(title),
                title
            )
        )

    return result


def compare_tracks(local_tracks, discogs_tracks):

    local = [
        normalize(t)
        for t in local_tracks
        if normalize(t)
    ]

    discogs = [
        x[1]
        for x in discogs_tracks
    ]

    if not local:
        return 0, 0

    matched = 0

    for title in local:

        if title in discogs:
            matched += 1

    return matched, len(local)


def get_incomplete_releases(conn):

    return conn.execute("""
        SELECT
            id,
            artist,
            title,
            discogs,
            storage_code
        FROM releases
        WHERE
            discogs IS NULL
            OR TRIM(discogs) = ''
            OR title IS NULL
            OR TRIM(title) = ''
        ORDER BY id
    """).fetchall()


def main():

    print("=" * 80)
    print("KID ACID'S VINYLVAULT V3")
    print("AUTOMATISCHE DISCOGS MATCHER")
    print("DRY-RUN - DATABASE WORDT NIET GEWIJZIGD")
    print("=" * 80)

    print()
    print("Database:")
    print(DB)

    conn = sqlite3.connect(
        DB
    )

    releases = get_incomplete_releases(
        conn
    )

    print()
    print(
        "Incomplete releases:",
        len(releases)
    )

    print()
    print("=" * 80)
    print("START")
    print("=" * 80)

    counters = {
        "strong": 0,
        "possible": 0,
        "skip": 0
    }

    # --------------------------------------------------------
    # MAXIMAAL 20 PER TEST
    # --------------------------------------------------------

    for number, release in enumerate(
        releases[:20],
        1
    ):

        release_id = release[0]
        artist = release[1] or ""
        title = release[2] or ""
        discogs = release[3] or ""
        storage = release[4] or ""

        print()
        print(
            f"[{number}/20] RELEASE {release_id}"
        )

        print(
            "Artist   :",
            artist
        )

        print(
            "Titel    :",
            title
        )

        print(
            "Kastcode :",
            storage
        )

        local_tracks = conn.execute("""
            SELECT title
            FROM tracks
            WHERE release_id = ?
            ORDER BY id
        """, (
            release_id,
        )).fetchall()

        local_titles = [
            x[0]
            for x in local_tracks
        ]

        print(
            "Tracks   :",
            len(local_titles)
        )

        if not artist or artist.lower() == "untitled":

            print(
                "STATUS   : OVERSLAAN - GEEN BETROUWBARE ARTIST"
            )

            counters["skip"] += 1

            continue

        if not local_titles:

            print(
                "STATUS   : OVERSLAAN - GEEN TRACKS"
            )

            counters["skip"] += 1

            continue

        # ----------------------------------------------------
        # EERSTE TRACK ALS ZOEKANKER
        # ----------------------------------------------------

        anchor = local_titles[0]

        print(
            "Zoekanker:",
            anchor
        )

        results = search_discogs(
            artist,
            anchor
        )

        print(
            "Kandidaten:",
            len(results)
        )

        candidate_ids = []

        for item in results:

            rid = item.get(
                "id"
            )

            if rid and rid not in candidate_ids:

                candidate_ids.append(
                    rid
                )

        best = None

        # ----------------------------------------------------
        # KANDIDATEN CONTROLEREN
        # ----------------------------------------------------

        for rid in candidate_ids[:20]:

            data = get_release(
                rid
            )

            if not data:
                continue

            if not is_vinyl(
                data
            ):
                continue

            dtracks = release_tracks(
                data
            )

            matched, total = compare_tracks(
                local_titles,
                dtracks
            )

            if total == 0:
                continue

            score = matched / len(
                local_titles
            )

            if best is None or score > best[0]:

                best = (
                    score,
                    matched,
                    total,
                    rid,
                    data,
                    dtracks
                )

            time.sleep(
                0.25
            )

        # ----------------------------------------------------
        # RESULTAAT
        # ----------------------------------------------------

        if best is None:

            print(
                "STATUS   : GEEN KANDIDAAT"
            )

            counters["skip"] += 1

            continue

        score, matched, total, rid, data, dtracks = best

        print()
        print(
            "BESTE KANDIDAAT"
        )

        print(
            "Discogs  :",
            rid
        )

        print(
            "Release  :",
            data.get("title")
        )

        print(
            "Year     :",
            data.get("year")
        )

        print(
            "Match    :",
            f"{matched}/{len(local_titles)}"
        )

        print(
            "Score    :",
            f"{score * 100:.1f}%"
        )

        # ----------------------------------------------------
        # CLASSIFICATIE
        # ----------------------------------------------------

        if score >= 0.90 and matched >= 2:

            print(
                "STATUS   : STERKE MATCH"
            )

            counters["strong"] += 1

        elif score >= 0.60:

            print(
                "STATUS   : MOGELIJKE MATCH"
            )

            counters["possible"] += 1

        else:

            print(
                "STATUS   : OVERSLAAN"
            )

            counters["skip"] += 1

        print()
        print(
            "LOKALE TRACKS:"
        )

        for x in local_titles:
            print(
                " ",
                x
            )

        print()
        print(
            "DISCOGS TRACKS:"
        )

        for position, normalized, original in dtracks:
            print(
                " ",
                position,
                "|",
                original
            )

    # --------------------------------------------------------
    # EINDE
    # --------------------------------------------------------

    print()
    print("=" * 80)
    print("DRY-RUN RESULTAAT")
    print("=" * 80)

    print()
    print(
        "Sterke matches   :",
        counters["strong"]
    )

    print(
        "Mogelijke matches:",
        counters["possible"]
    )

    print(
        "Overgeslagen     :",
        counters["skip"]
    )

    print()
    print(
        "DATABASE GEWIJZIGD: NEE"
    )

    print("=" * 80)

    conn.close()


if __name__ == "__main__":
    main()

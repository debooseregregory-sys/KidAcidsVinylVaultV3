# ============================================================
# KID ACID'S VINYLVAULT V3
# COLLECTION MATCH ENGINE V3 - TEST
# ============================================================

import os
import sys
import json
import sqlite3
import time
import requests

# ============================================================
# PROJECT ROOT
# ============================================================

ROOT = os.path.dirname(
    os.path.dirname(
        os.path.dirname(
            os.path.abspath(__file__)
        )
    )
)

if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import config

# ============================================================
# DATABASE
# ============================================================

DB = os.path.join(
    ROOT,
    "data",
    "vinylvault.db"
)

# ============================================================
# COLLECTION
# ============================================================

COLLECTION_FILE = os.path.join(
    ROOT,
    "discogs",
    "public_data",
    "collection.json"
)

# ============================================================
# DISCOGS
# ============================================================

API_URL = "https://api.discogs.com"

HEADERS = {
    "User-Agent": getattr(
        config,
        "DISCOGS_USER_AGENT",
        "KidAcidVinylVaultV3/1.0"
    ),
    "Accept": "application/json",
}

# ============================================================
# TEST
# ============================================================

ARTIST = "Planetary Assault Systems"
TITLE = "In From The Night"
KASTCODE = "XCV 11"

# ============================================================
# NORMALIZE
# ============================================================

def normalize(value):

    if value is None:
        return ""

    text = str(value).lower()

    replacements = (
        ("(", " "),
        (")", " "),
        ("[", " "),
        ("]", " "),
        ("{", " "),
        ("}", " "),
        ("-", " "),
        ("_", " "),
        ("/", " "),
        ("\\", " "),
        (".", " "),
        (",", " "),
        ("'", " "),
        ('"', " "),
        (":", " "),
        (";", " "),
    )

    for old, new in replacements:
        text = text.replace(old, new)

    return " ".join(text.split())

# ============================================================
# DATABASE
# ============================================================

def db_connect():

    conn = sqlite3.connect(DB)

    conn.row_factory = sqlite3.Row

    return conn

# ============================================================
# COLLECTION
# ============================================================

def load_collection():

    print()
    print("=" * 80)
    print("DISCOGS COLLECTIE LADEN")
    print("=" * 80)

    print()
    print("Bestand:")
    print(COLLECTION_FILE)

    if not os.path.exists(COLLECTION_FILE):

        print()
        print("FOUT: collection.json bestaat niet.")

        return []

    with open(
        COLLECTION_FILE,
        "r",
        encoding="utf-8"
    ) as f:

        data = json.load(f)

    releases = data.get(
        "releases",
        []
    )

    print()
    print(
        "Collectie releases:",
        len(releases)
    )

    return releases

# ============================================================
# COLLECTION ARTIST
# ============================================================

def collection_artist(item):

    basic = item.get(
        "basic_information",
        {}
    )

    artists = basic.get(
        "artists",
        []
    )

    names = []

    for artist in artists:

        name = artist.get(
            "name",
            ""
        )

        if name:
            names.append(name)

    return ", ".join(names)

# ============================================================
# COLLECTION VINYL
# ============================================================

def collection_is_vinyl(item):

    basic = item.get(
        "basic_information",
        {}
    )

    formats = basic.get(
        "formats",
        []
    )

    for fmt in formats:

        name = normalize(
            fmt.get(
                "name",
                ""
            )
        )

        descriptions = normalize(
            " ".join(
                fmt.get(
                    "descriptions",
                    []
                )
            )
        )

        if name == "vinyl":
            return True

        if "12 inch" in descriptions:
            return True

        if "10 inch" in descriptions:
            return True

        if "7 inch" in descriptions:
            return True

    return False

# ============================================================
# DISCOGS RELEASE
# ============================================================

def get_release(release_id):

    url = (
        f"{API_URL}/releases/"
        f"{release_id}"
    )

    while True:

        response = requests.get(
            url,
            headers=HEADERS,
            timeout=30
        )

        if response.status_code == 429:

            retry_after = response.headers.get(
                "Retry-After"
            )

            try:
                wait = int(retry_after)
            except:
                wait = 10

            print(
                f"Rate limit - wachten {wait} sec..."
            )

            time.sleep(wait)

            continue

        if response.status_code != 200:

            print(
                "Discogs HTTP:",
                response.status_code
            )

            return None

        return response.json()

# ============================================================
# RELEASE ARTIST
# ============================================================

def release_artist(release):

    names = []

    for artist in release.get(
        "artists",
        []
    ):

        name = artist.get(
            "name",
            ""
        )

        if name:
            names.append(name)

    return ", ".join(names)

# ============================================================
# VINYL RELEASE
# ============================================================

def is_vinyl_release(release):

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

        descriptions = normalize(
            " ".join(
                fmt.get(
                    "descriptions",
                    []
                )
            )
        )

        if name == "vinyl":
            return True

        if "12 inch" in descriptions:
            return True

        if "10 inch" in descriptions:
            return True

        if "7 inch" in descriptions:
            return True

    return False

# ============================================================
# TRACK ZOEKEN
# ============================================================

def find_track(
    release,
    wanted_title
):

    wanted = normalize(
        wanted_title
    )

    for track in release.get(
        "tracklist",
        []
    ):

        title = normalize(
            track.get(
                "title",
                ""
            )
        )

        if title == wanted:
            return track

    return None

# ============================================================
# ARTIST MATCH
# ============================================================

def artist_matches(
    release,
    wanted_artist
):

    actual = normalize(
        release_artist(release)
    )

    wanted = normalize(
        wanted_artist
    )

    return (
        actual == wanted
        or wanted in actual
        or actual in wanted
    )

# ============================================================
# EXACT MATCH
# ============================================================

def exact_match(
    release
):

    if not artist_matches(
        release,
        ARTIST
    ):
        return None

    if not is_vinyl_release(
        release
    ):
        return None

    return find_track(
        release,
        TITLE
    )

# ============================================================
# LOKALE RELEASE
# ============================================================

def find_local_release(
    discogs_id
):

    conn = db_connect()

    row = conn.execute(
        """
        SELECT *
        FROM releases
        WHERE discogs = ?
        LIMIT 1
        """,
        (
            str(discogs_id),
        )
    ).fetchone()

    conn.close()

    return row

# ============================================================
# LOKALE TRACK
# ============================================================

def find_local_track(
    release_id,
    position,
    title
):

    conn = db_connect()

    row = conn.execute(
        """
        SELECT *
        FROM tracks
        WHERE release_id = ?
        AND position = ?
        LIMIT 1
        """,
        (
            release_id,
            position
        )
    ).fetchone()

    if not row:

        row = conn.execute(
            """
            SELECT *
            FROM tracks
            WHERE release_id = ?
            AND lower(title) = lower(?)
            LIMIT 1
            """,
            (
                release_id,
                title
            )
        ).fetchone()

    conn.close()

    return row

# ============================================================
# KOPPELING OPSLAAN
# ============================================================

def save_storage_code(
    release_id,
    kastcode
):

    conn = db_connect()

    conn.execute(
        """
        UPDATE releases
        SET storage_code = ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """,
        (
            kastcode,
            release_id
        )
    )

    conn.commit()

    conn.close()

# ============================================================
# MAIN
# ============================================================

def main():

    print()
    print("=" * 80)
    print("KID ACID'S VINYLVAULT V3")
    print("COLLECTION MATCH ENGINE V3")
    print("=" * 80)

    print()
    print("Artist   :", ARTIST)
    print("Track    :", TITLE)
    print("Kastcode :", KASTCODE)

    print()
    print(
        "DATABASE WORDT ALLEEN GEWIJZIGD BIJ EEN EXACTE MATCH."
    )

    print(
        "KASTCODE WORDT NIET NAAR DISCOGS GESTUURD."
    )

    # ========================================================
    # COLLECTION
    # ========================================================

    releases = load_collection()

    if not releases:
        return

    # ========================================================
    # VINYL ARTIST RELEASES
    # ========================================================

    wanted_artist = normalize(
        ARTIST
    )

    candidates = []

    for item in releases:

        if not collection_is_vinyl(
            item
        ):
            continue

        artist = normalize(
            collection_artist(item)
        )

        if (
            artist == wanted_artist
            or wanted_artist in artist
            or artist in wanted_artist
        ):

            candidates.append(item)

    print()
    print("=" * 80)
    print("LOKALE COLLECTIE ZOEKEN")
    print("=" * 80)

    print()
    print(
        "Vinyl releases van artist:",
        len(candidates)
    )

    # ========================================================
    # RELEASES CONTROLEREN
    # ========================================================

    print()
    print("=" * 80)
    print("DISCOGS RELEASES CONTROLEREN")
    print("=" * 80)

    matches = []

    for number, item in enumerate(
        candidates,
        start=1
    ):

        basic = item.get(
            "basic_information",
            {}
        )

        release_id = basic.get(
            "id"
        )

        title = basic.get(
            "title",
            ""
        )

        print()
        print(
            f"[{number}/{len(candidates)}]"
        )

        print(
            "Discogs ID:",
            release_id
        )

        print(
            "Collectie:",
            collection_artist(item),
            "|",
            title
        )

        release = get_release(
            release_id
        )

        if not release:

            print(
                "STATUS: RELEASE FOUT"
            )

            continue

        track = exact_match(
            release
        )

        if track:

            print(
                "STATUS: EXACTE MATCH"
            )

            print(
                "Trackpositie:",
                track.get("position")
            )

            print(
                "Track:",
                track.get("title")
            )

            matches.append(
                (
                    release,
                    track
                )
            )

        else:

            print(
                "STATUS: GEEN EXACTE TRACK"
            )

    # ========================================================
    # RESULTAAT
    # ========================================================

    print()
    print("=" * 80)
    print("RESULTAAT")
    print("=" * 80)

    print()
    print(
        "Exacte vinyl matches:",
        len(matches)
    )

    if len(matches) == 0:

        print()
        print(
            "GEEN BETROUWBARE MATCH GEVONDEN."
        )

        print()
        print(
            "DATABASE GEWIJZIGD: NEE"
        )

        return

    if len(matches) > 1:

        print()
        print(
            "MEERDERE EXACTE MATCHES."
        )

        print(
            "DATABASE WORDT NIET GEWIJZIGD."
        )

        return

    # ========================================================
    # EXACTE MATCH
    # ========================================================

    release, track = matches[0]

    discogs_id = release.get(
        "id"
    )

    position = track.get(
        "position",
        ""
    )

    track_title = track.get(
        "title",
        ""
    )

    print()
    print("=" * 80)
    print("EXACTE MATCH")
    print("=" * 80)

    print()
    print(
        "Discogs ID :",
        discogs_id
    )

    print(
        "Release    :",
        release.get("title")
    )

    print(
        "Artist     :",
        release_artist(release)
    )

    print(
        "Track      :",
        position,
        "|",
        track_title
    )

    # ========================================================
    # LOKALE RELEASE
    # ========================================================

    local_release = find_local_release(
        discogs_id
    )

    if not local_release:

        print()
        print(
            "FOUT: RELEASE NIET IN VINYLVAULT DATABASE."
        )

        print()
        print(
            "DATABASE GEWIJZIGD: NEE"
        )

        return

    print()
    print("=" * 80)
    print("LOKALE RELEASE")
    print("=" * 80)

    print()
    print(
        "Lokale release ID:",
        local_release["id"]
    )

    print(
        "Release:",
        local_release["title"]
    )

    print(
        "Artist:",
        local_release["artist"]
    )

    # ========================================================
    # LOKALE TRACK
    # ========================================================

    local_track = find_local_track(
        local_release["id"],
        position,
        track_title
    )

    if not local_track:

        print()
        print(
            "WAARSCHUWING: lokale track niet gevonden."
        )

        print(
            "Release wordt NIET gewijzigd."
        )

        print()
        print(
            "DATABASE GEWIJZIGD: NEE"
        )

        return

    print()
    print(
        "Lokale track:"
    )

    print(
        "Track ID:",
        local_track["id"]
    )

    print(
        "Positie:",
        local_track["position"]
    )

    print(
        "Titel:",
        local_track["title"]
    )

    # ========================================================
    # OPSLAAN
    # ========================================================

    print()
    print("=" * 80)
    print("AUTOMATISCHE KOPPELING")
    print("=" * 80)

    print()
    print(
        "Release ID :",
        local_release["id"]
    )

    print(
        "Track ID   :",
        local_track["id"]
    )

    print(
        "Discogs ID :",
        discogs_id
    )

    print(
        "Trackpositie:",
        position
    )

    print(
        "Kastcode   :",
        KASTCODE
    )

    save_storage_code(
        local_release["id"],
        KASTCODE
    )

    # ========================================================
    # CONTROLE
    # ========================================================

    check = find_local_release(
        discogs_id
    )

    print()
    print("=" * 80)
    print("KOPPELING OPGESLAGEN")
    print("=" * 80)

    print()
    print(
        "Release ID :",
        check["id"]
    )

    print(
        "Discogs ID :",
        check["discogs"]
    )

    print(
        "Release    :",
        check["title"]
    )

    print(
        "Artist     :",
        check["artist"]
    )

    print(
        "Track ID   :",
        local_track["id"]
    )

    print(
        "Positie    :",
        local_track["position"]
    )

    print(
        "Track      :",
        local_track["title"]
    )

    print(
        "Kastcode   :",
        check["storage_code"]
    )

    print()
    print(
        "DATABASE GEWIJZIGD: JA"
    )

    print(
        "DISCOGS GEWIJZIGD: NEE"
    )

    print()
    print("=" * 80)
    print("KOPPELING GESLAAGD")
    print("=" * 80)


# ============================================================
# START
# ============================================================

if __name__ == "__main__":
    main()


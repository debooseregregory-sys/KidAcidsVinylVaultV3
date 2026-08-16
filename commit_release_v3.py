# ============================================================
# KID ACID'S VINYLVAULT V3
# ALGEMENE RELEASE COMMIT ENGINE
#
# REGELS:
# - Alleen exacte ARTIEST + TITEL
# - Geen fuzzy matching
# - Geen gokken
# - Bestaande koppelingen niet dubbel toevoegen
# - Dubbele MP3-bestanden blijven behouden
# - Alleen geldige koppelingen worden toegevoegd
# ============================================================

import os
import sys
import sqlite3
import requests

# ============================================================
# PROJECT ROOT
# ============================================================

ROOT = os.path.dirname(
    os.path.abspath(__file__)
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
# DISCOGS
# ============================================================

API_URL = "https://api.discogs.com"

HEADERS = {
    "User-Agent": config.DISCOGS_USER_AGENT,
    "Accept": "application/json",
}

# ============================================================
# DATABASE
# ============================================================

def db_connect():
    return sqlite3.connect(DB)


# ============================================================
# NORMALIZE
# ============================================================

def normalize(value):

    if value is None:
        return ""

    return " ".join(
        str(value)
        .strip()
        .lower()
        .split()
    )


# ============================================================
# DISCOGS RELEASE
# ============================================================

def get_release(release_id):

    print()
    print("=" * 80)
    print("DISCOGS RELEASE OPHALEN")
    print("=" * 80)

    print(
        "Release ID:",
        release_id
    )

    response = requests.get(
        f"{API_URL}/releases/{release_id}",
        headers=HEADERS,
        timeout=30,
    )

    if response.status_code != 200:

        print()
        print(
            "DISCOGS FOUT:",
            response.status_code
        )

        print(
            response.text[:500]
        )

        return None

    return response.json()


# ============================================================
# V3 RELEASE
# ============================================================

def get_v3_release(release_id):

    conn = db_connect()

    row = conn.execute(
        """
        SELECT
            id,
            artist,
            title,
            label,
            catalog,
            year,
            discogs
        FROM releases
        WHERE discogs = ?
        """,
        (
            str(release_id),
        )
    ).fetchone()

    conn.close()

    return row


# ============================================================
# V3 TRACKS
# ============================================================

def get_tracks(release_id):

    conn = db_connect()

    rows = conn.execute(
        """
        SELECT
            id,
            position,
            artist,
            title,
            duration
        FROM tracks
        WHERE release_id = ?
        ORDER BY id
        """,
        (
            release_id,
        )
    ).fetchall()

    conn.close()

    return rows


# ============================================================
# MP3 DATABASE
# ============================================================

def load_mp3_database():

    conn = db_connect()

    rows = conn.execute(
        """
        SELECT
            id,
            artist,
            title,
            path
        FROM mp3_files
        """
    ).fetchall()

    conn.close()

    exact = {}

    for row in rows:

        mp3_id = row[0]
        artist = row[1] or ""
        title = row[2] or ""
        path = row[3] or ""

        key = (
            normalize(artist),
            normalize(title)
        )

        if key not in exact:
            exact[key] = []

        exact[key].append(
            {
                "id": mp3_id,
                "artist": artist,
                "title": title,
                "path": path,
            }
        )

    return exact, len(rows)


# ============================================================
# BESTAANDE KOPPELING
# ============================================================

def link_exists(track_id, mp3_id):

    conn = db_connect()

    row = conn.execute(
        """
        SELECT id
        FROM track_mp3
        WHERE track_id = ?
        AND mp3_id = ?
        """,
        (
            track_id,
            mp3_id,
        )
    ).fetchone()

    conn.close()

    return row is not None


# ============================================================
# NIEUWE KOPPELING
# ============================================================

def create_link(track_id, mp3_id):

    conn = db_connect()

    try:

        conn.execute(
            """
            INSERT INTO track_mp3 (
                track_id,
                mp3_id,
                score,
                is_preferred,
                manually_added
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                track_id,
                mp3_id,
                100.0,
                1,
                0,
            )
        )

        conn.commit()

        return True

    except sqlite3.IntegrityError:

        conn.rollback()

        return False

    finally:

        conn.close()


# ============================================================
# EXACTE MATCH
# ============================================================

def find_exact_match(
    artist,
    title,
    mp3_index
):

    key = (
        normalize(artist),
        normalize(title)
    )

    matches = mp3_index.get(
        key,
        []
    )

    if not matches:
        return None

    # --------------------------------------------------------
    # Eén exacte MP3
    # --------------------------------------------------------

    if len(matches) == 1:

        return matches[0]

    # --------------------------------------------------------
    # Meerdere identieke MP3's
    #
    # NIET gokken.
    # --------------------------------------------------------

    print()
    print(
        "MEERDERE EXACTE MP3'S:"
    )

    for number, match in enumerate(
        matches,
        start=1
    ):

        print(
            f"  [{number}] "
            f"{match['path']}"
        )

    print(
        "ACTIE: NIET AUTOMATISCH KOPPELEN"
    )

    return None


# ============================================================
# RELEASE CONTROLEREN
# ============================================================

def check_release(
    release,
    v3_release
):

    discogs_artist = normalize(
        ", ".join(
            a.get("name", "")
            for a in release.get(
                "artists",
                []
            )
        )
    )

    v3_artist = normalize(
        v3_release[1]
    )

    discogs_title = normalize(
        release.get(
            "title",
            ""
        )
    )

    v3_title = normalize(
        v3_release[2]
    )

    if discogs_artist != v3_artist:

        print()
        print(
            "WAARSCHUWING:"
        )

        print(
            "Discogs artist:",
            discogs_artist
        )

        print(
            "V3 artist:",
            v3_artist
        )

        return False

    if discogs_title != v3_title:

        print()
        print(
            "WAARSCHUWING:"
        )

        print(
            "Discogs release:",
            discogs_title
        )

        print(
            "V3 release:",
            v3_title
        )

        return False

    return True


# ============================================================
# MAIN
# ============================================================

def main():

    print()
    print("=" * 80)
    print("KID ACID'S VINYLVAULT V3")
    print("ALGEMENE RELEASE COMMIT ENGINE")
    print("=" * 80)

    print()
    print(
        "Database:"
    )

    print(
        DB
    )

    # --------------------------------------------------------
    # DATABASE CONTROLE
    # --------------------------------------------------------

    if not os.path.isfile(DB):

        print()
        print(
            "FOUT: DATABASE NIET GEVONDEN"
        )

        return

    # --------------------------------------------------------
    # RELEASE ID
    # --------------------------------------------------------

    print()
    print(
        "Voer een Discogs Release ID in."
    )

    print(
        "Voorbeeld: 5942009"
    )

    print()

    release_input = input(
        "Discogs Release ID: "
    ).strip()

    if not release_input.isdigit():

        print()
        print(
            "FOUT: ONGELDIG RELEASE ID"
        )

        return

    release_id = int(
        release_input
    )

    # --------------------------------------------------------
    # DISCOGS
    # --------------------------------------------------------

    release = get_release(
        release_id
    )

    if not release:

        return

    print()
    print("=" * 80)
    print("DISCOGS")
    print("=" * 80)

    artist = ", ".join(
        a.get("name", "")
        for a in release.get(
            "artists",
            []
        )
    )

    title = release.get(
        "title",
        ""
    )

    year = release.get(
        "year"
    )

    tracklist = release.get(
        "tracklist",
        []
    )

    print(
        "Artist:",
        artist
    )

    print(
        "Release:",
        title
    )

    print(
        "Year:",
        year
    )

    print(
        "Tracks:",
        len(tracklist)
    )

    # --------------------------------------------------------
    # V3 RELEASE
    # --------------------------------------------------------

    v3_release = get_v3_release(
        release_id
    )

    if not v3_release:

        print()
        print(
            "RELEASE BESTAAT NOG NIET IN V3."
        )

        print()
        print(
            "Deze commit-tool koppelt alleen"
        )

        print(
            "releases die al in VinylVault V3 staan."
        )

        print()
        print(
            "DATABASE GEWIJZIGD: NEE"
        )

        return

    # --------------------------------------------------------
    # RELEASE CONTROLEREN
    # --------------------------------------------------------

    if not check_release(
        release,
        v3_release
    ):

        print()
        print(
            "RELEASE CONTROLE MISLUKT."
        )

        print(
            "DATABASE GEWIJZIGD: NEE"
        )

        return

    v3_release_id = v3_release[0]

    print()
    print(
        "V3 Release ID:",
        v3_release_id
    )

    print(
        "Release:",
        v3_release[2]
    )

    print(
        "Artist:",
        v3_release[1]
    )

    print(
        "Catalog:",
        v3_release[4]
    )

    print(
        "Discogs:",
        v3_release[6]
    )

    # --------------------------------------------------------
    # TRACKS
    # --------------------------------------------------------

    tracks = get_tracks(
        v3_release_id
    )

    print()
    print("=" * 80)
    print("TRACKS")
    print("=" * 80)

    for track in tracks:

        print(
            f"{track[1]:4} | "
            f"{track[2]} | "
            f"{track[3]}"
        )

    # --------------------------------------------------------
    # MP3 DATABASE
    # --------------------------------------------------------

    print()
    print("=" * 80)
    print("MP3 DATABASE INLEZEN")
    print("=" * 80)

    mp3_index, total_mp3 = (
        load_mp3_database()
    )

    print(
        "MP3's beschikbaar:",
        total_mp3
    )

    print(
        "Exacte combinaties:",
        len(mp3_index)
    )

    # --------------------------------------------------------
    # COMMIT
    # --------------------------------------------------------

    print()
    print("=" * 80)
    print("START COMMIT")
    print("=" * 80)

    exact_count = 0
    no_match_count = 0
    existing_count = 0
    new_count = 0
    multiple_count = 0

    for number, track in enumerate(
        tracks,
        start=1
    ):

        track_id = track[0]
        position = track[1]
        track_artist = track[2]
        track_title = track[3]

        print()
        print(
            f"[{number}/{len(tracks)}] "
            f"{position} | "
            f"{track_artist} - "
            f"{track_title}"
        )

        print(
            "Track ID:",
            track_id
        )

        key = (
            normalize(track_artist),
            normalize(track_title)
        )

        candidates = mp3_index.get(
            key,
            []
        )

        if len(candidates) == 0:

            print(
                "MP3: GEEN EXACTE MATCH"
            )

            print(
                "STATUS: GEEN MATCH"
            )

            print(
                "ACTIE: NIET KOPPELEN"
            )

            no_match_count += 1

            continue

        if len(candidates) > 1:

            print()
            print(
                "MP3: MEERDERE EXACTE MATCHES"
            )

            for candidate in candidates:

                print(
                    " -",
                    candidate["path"]
                )

            print(
                "STATUS: DUBBEL EXACT"
            )

            print(
                "ACTIE: NIET AUTOMATISCH KOPPELEN"
            )

            multiple_count += 1

            continue

        match = candidates[0]

        exact_count += 1

        print()
        print(
            "MP3:",
            f"{match['artist']} - "
            f"{match['title']}"
        )

        print(
            "Bestand:",
            match["path"]
        )

        print(
            "Artiest: 100"
        )

        print(
            "Titel: 100"
        )

        print(
            "Score: 100.0"
        )

        print(
            "STATUS: EXACT"
        )

        # ----------------------------------------------------
        # BESTAANDE KOPPELING
        # ----------------------------------------------------

        if link_exists(
            track_id,
            match["id"]
        ):

            print(
                "KOPPELING BESTAAT AL"
            )

            existing_count += 1

            continue

        # ----------------------------------------------------
        # NIEUWE KOPPELING
        # ----------------------------------------------------

        success = create_link(
            track_id,
            match["id"]
        )

        if success:

            print(
                "ACTIE: NIEUWE KOPPELING"
            )

            new_count += 1

        else:

            print(
                "ACTIE: KOPPELING NIET TOEGEVOEGD"
            )

    # --------------------------------------------------------
    # RESULTAAT
    # --------------------------------------------------------

    print()
    print("=" * 80)
    print("COMMIT RESULTAAT")
    print("=" * 80)

    print()
    print(
        "Release:",
        v3_release[2]
    )

    print(
        "Artist :",
        v3_release[1]
    )

    print(
        "Discogs:",
        v3_release[6]
    )

    print()

    print(
        f"EXACT                 : {exact_count}"
    )

    print(
        f"GEEN MATCH            : {no_match_count}"
    )

    print(
        f"MEERDERE EXACTE MATCH : {multiple_count}"
    )

    print(
        f"BESTAAND              : {existing_count}"
    )

    print(
        f"NIEUWE KOPPELINGEN    : {new_count}"
    )

    print()
    print(
        "DATABASE COMMIT: OK"
    )

    print()
    print("=" * 80)
    print("COMMIT KLAAR")
    print("=" * 80)


# ============================================================
# START
# ============================================================

if __name__ == "__main__":
    main()
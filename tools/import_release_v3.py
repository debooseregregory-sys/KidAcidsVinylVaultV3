# ============================================================
# KID ACID'S VINYLVAULT V3
#
# PRODUCTION RELEASE IMPORTER + MP3 MATCHER
#
# Discogs Release
#       ↓
# Release import
#       ↓
# Tracks import
#       ↓
# Bestaande tracks bijwerken
#       ↓
# MP3 artiest-index
#       ↓
# Exacte artiest + exacte titel
#       ↓
# Alleen betrouwbare koppeling
#       ↓
# Geen dubbele koppelingen
#
# ============================================================

import os
import sys
import sqlite3
import time
import re
import requests

# ============================================================
# V3 ROOT
# ============================================================

ROOT = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
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
# INSTELLINGEN
# ============================================================

# Gebruik:
#
# python tools\import_release_v3.py 4690
#
# Als er geen ID wordt opgegeven gebruiken we deze testrelease.

DEFAULT_RELEASE_ID = 5942009


# ============================================================
# DATABASE
# ============================================================

def db_connect():

    connection = sqlite3.connect(DB)

    connection.row_factory = sqlite3.Row

    connection.execute(
        "PRAGMA foreign_keys = ON"
    )

    return connection


# ============================================================
# STRING NORMALIZER
# ============================================================

def normalize(text):

    if text is None:
        return ""

    text = str(text).strip().lower()

    # --------------------------------------------------------
    # Ampersand
    # --------------------------------------------------------

    text = text.replace(
        "&",
        " and "
    )

    # --------------------------------------------------------
    # Speciale tekens
    # --------------------------------------------------------

    text = re.sub(
        r"[\(\)\[\]\{\}\.,;:'\"!?\-_\/\\]+",
        " ",
        text
    )

    # --------------------------------------------------------
    # Meerdere spaties
    # --------------------------------------------------------

    text = " ".join(
        text.split()
    )

    return text


# ============================================================
# ARTIST NORMALIZER
# ============================================================

def normalize_artist(text):

    return normalize(text)


# ============================================================
# TITLE NORMALIZER
# ============================================================

def normalize_title(text):

    return normalize(text)


# ============================================================
# DISCOGS REQUEST
# ============================================================

def discogs_get(url):

    while True:

        try:

            response = requests.get(
                url,
                headers=HEADERS,
                timeout=30
            )

        except Exception as exc:

            print()
            print("NETWERKFOUT:")
            print(exc)

            return None

        # ----------------------------------------------------
        # RATE LIMIT
        # ----------------------------------------------------

        if response.status_code == 429:

            retry_after = response.headers.get(
                "Retry-After"
            )

            try:
                wait = int(
                    retry_after
                )
            except (
                TypeError,
                ValueError
            ):
                wait = 5

            print()
            print(
                f"Discogs rate limit. "
                f"Wachten: {wait} seconden..."
            )

            time.sleep(wait)

            continue

        # ----------------------------------------------------
        # ERROR
        # ----------------------------------------------------

        if response.status_code != 200:

            print()
            print(
                "DISCOGS FOUT:"
            )

            print(
                "HTTP:",
                response.status_code
            )

            print(
                response.text[:500]
            )

            return None

        return response


# ============================================================
# RELEASE OPHALEN
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

    response = discogs_get(
        f"{API_URL}/releases/{release_id}"
    )

    if not response:
        return None

    return response.json()


# ============================================================
# RELEASE ARTIST
# ============================================================

def get_release_artist(release):

    artists = (
        release.get("artists")
        or []
    )

    names = []

    for artist in artists:

        name = (
            artist.get("name")
            or ""
        ).strip()

        if name:
            names.append(name)

    return ", ".join(names)


# ============================================================
# TRACK ARTIST
# ============================================================

def get_track_artist(
    track,
    release
):

    artists = (
        track.get("artists")
        or []
    )

    names = []

    for artist in artists:

        name = (
            artist.get("name")
            or ""
        ).strip()

        if name:
            names.append(name)

    if names:

        return ", ".join(names)

    return get_release_artist(
        release
    )


# ============================================================
# POSITION NORMALIZER
# ============================================================

def normalize_position(
    position,
    side_counts
):

    position = (
        position
        or ""
    ).strip().upper()

    if not position:
        return ""

    # --------------------------------------------------------
    # Discogs A
    # --------------------------------------------------------

    if position == "A":

        side_counts["A"] += 1

        return (
            f"A{side_counts['A']}"
        )

    # --------------------------------------------------------
    # Discogs B
    # --------------------------------------------------------

    if position == "B":

        side_counts["B"] += 1

        return (
            f"B{side_counts['B']}"
        )

    # --------------------------------------------------------
    # A1 / A2 / B1 / B2
    # --------------------------------------------------------

    return position


# ============================================================
# DURATION
# ============================================================

def duration_to_seconds(duration):

    if not duration:
        return 0

    try:

        parts = str(
            duration
        ).strip().split(":")

        if len(parts) == 2:

            minutes = int(
                parts[0]
            )

            seconds = int(
                parts[1]
            )

            return (
                minutes * 60
                + seconds
            )

        if len(parts) == 3:

            hours = int(
                parts[0]
            )

            minutes = int(
                parts[1]
            )

            seconds = int(
                parts[2]
            )

            return (
                hours * 3600
                + minutes * 60
                + seconds
            )

    except (
        ValueError,
        TypeError
    ):

        pass

    return 0


# ============================================================
# RELEASE IN DATABASE
# ============================================================

def get_or_create_release(
    release
):

    conn = db_connect()

    discogs_id = str(
        release.get("id")
    )

    existing = conn.execute(
        """
        SELECT *
        FROM releases
        WHERE discogs = ?
        """,
        (
            discogs_id,
        )
    ).fetchone()

    if existing:

        print()
        print(
            "RELEASE BESTAAT AL"
        )

        print(
            "V3 Release ID:",
            existing["id"]
        )

        conn.close()

        return existing["id"], False

    # --------------------------------------------------------
    # Artist
    # --------------------------------------------------------

    artist = get_release_artist(
        release
    )

    # --------------------------------------------------------
    # Title
    # --------------------------------------------------------

    title = (
        release.get("title")
        or ""
    ).strip()

    # --------------------------------------------------------
    # Label
    # --------------------------------------------------------

    labels = (
        release.get("labels")
        or []
    )

    label_names = []
    catalog = ""

    for label in labels:

        name = (
            label.get("name")
            or ""
        ).strip()

        if name:
            label_names.append(name)

        if not catalog:

            catalog = (
                label.get("catno")
                or ""
            ).strip()

    label_name = ", ".join(
        label_names
    )

    # --------------------------------------------------------
    # Year
    # --------------------------------------------------------

    year = release.get(
        "year"
    )

    # --------------------------------------------------------
    # Discogs URL
    # --------------------------------------------------------

    discogs_link = (
        f"https://www.discogs.com/release/"
        f"{discogs_id}"
    )

    # --------------------------------------------------------
    # IMPORT
    # --------------------------------------------------------

    cursor = conn.execute(
        """
        INSERT INTO releases (
            artist,
            title,
            label,
            catalog,
            year,
            discogs,
            discogs_link,
            notes
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            artist,
            title,
            label_name,
            catalog,
            year,
            discogs_id,
            discogs_link,
            ""
        )
    )

    release_db_id = cursor.lastrowid

    conn.commit()

    conn.close()

    print()
    print(
        "NIEUWE RELEASE AANGEMAAKT"
    )

    print(
        "V3 Release ID:",
        release_db_id
    )

    return release_db_id, True


# ============================================================
# TRACKS IMPORTEREN
# ============================================================

def import_tracks(
    release_db_id,
    release
):

    conn = db_connect()

    tracklist = (
        release.get("tracklist")
        or []
    )

    side_counts = {
        "A": 0,
        "B": 0
    }

    imported = 0
    updated = 0

    print()
    print("=" * 80)
    print("TRACKS IMPORTEREN")
    print("=" * 80)

    for track in tracklist:

        # ----------------------------------------------------
        # Positie
        # ----------------------------------------------------

        position = normalize_position(
            track.get("position"),
            side_counts
        )

        # ----------------------------------------------------
        # Discogs gebruikt soms headings zoals:
        #
        # Black Side
        # Silver Side
        #
        # Die hebben geen positie.
        # ----------------------------------------------------

        if not position:
            continue

        # ----------------------------------------------------
        # Titel
        # ----------------------------------------------------

        title = (
            track.get("title")
            or ""
        ).strip()

        if not title:
            continue

        # ----------------------------------------------------
        # Artiest
        # ----------------------------------------------------

        artist = get_track_artist(
            track,
            release
        )

        # ----------------------------------------------------
        # SPEELDUUR
        # ----------------------------------------------------

        duration = duration_to_seconds(
            track.get("duration")
        )

        # ----------------------------------------------------
        # Bestaat deze track al?
        # ----------------------------------------------------

        existing = conn.execute(
            """
            SELECT
                id,
                duration
            FROM tracks
            WHERE release_id = ?
            AND position = ?
            """,
            (
                release_db_id,
                position
            )
        ).fetchone()

        # ====================================================
        # BESTAANDE TRACK
        # ====================================================

        if existing:

            track_id = existing["id"]
            old_duration = existing["duration"] or 0

            # ------------------------------------------------
            # Discogs heeft een geldige speelduur
            #
            # Update altijd de duur.
            #
            # Ook als er al een andere duur stond, gebruiken
            # we Discogs als bron.
            # ------------------------------------------------

            if duration > 0:

                conn.execute(
                    """
                    UPDATE tracks
                    SET
                        artist = ?,
                        title = ?,
                        duration = ?
                    WHERE id = ?
                    """,
                    (
                        artist,
                        title,
                        duration,
                        track_id
                    )
                )

                updated += 1

                print(
                    f"{position:4} | "
                    f"{artist} | "
                    f"{title} | "
                    f"{duration // 60}:"
                    f"{duration % 60:02d} "
                    f"[DUUR BIJGEWERKT]"
                )

            else:

                print(
                    f"{position:4} | "
                    f"{artist} | "
                    f"{title} "
                    f"[BESTAAT - GEEN DUUR]"
                )

            continue

        # ====================================================
        # NIEUWE TRACK
        # ====================================================

        conn.execute(
            """
            INSERT INTO tracks (
                release_id,
                position,
                artist,
                title,
                duration
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                release_db_id,
                position,
                artist,
                title,
                duration
            )
        )

        imported += 1

        if duration > 0:

            duration_display = (
                f"{duration // 60}:"
                f"{duration % 60:02d}"
            )

        else:

            duration_display = "geen duur"

        print(
            f"{position:4} | "
            f"{artist} | "
            f"{title} | "
            f"{duration_display} "
            f"[NIEUW]"
        )

    # --------------------------------------------------------
    # COMMIT
    # --------------------------------------------------------

    conn.commit()

    conn.close()

    print()
    print(
        "Nieuwe tracks:",
        imported
    )

    print(
        "Tracks bijgewerkt:",
        updated
    )

    return imported


# ============================================================
# MP3 INDEX
# ============================================================

def build_mp3_index():

    conn = db_connect()

    rows = conn.execute(
        """
        SELECT
            id,
            path,
            filename,
            artist,
            title
        FROM mp3_files
        WHERE artist != ''
        AND title != ''
        """
    ).fetchall()

    conn.close()

    # --------------------------------------------------------
    # Index:
    #
    # normalized artist
    #       ↓
    # lijst MP3's
    # --------------------------------------------------------

    index = {}

    for row in rows:

        artist_key = normalize_artist(
            row["artist"]
        )

        if not artist_key:
            continue

        index.setdefault(
            artist_key,
            []
        ).append(row)

    print()
    print("=" * 80)
    print("MP3 DATABASE INLEZEN")
    print("=" * 80)

    print(
        "MP3's beschikbaar:",
        len(rows)
    )

    print(
        "Artiesten met MP3's:",
        len(index)
    )

    return index


# ============================================================
# EXACTE MP3 MATCH
# ============================================================

def find_exact_match(
    track,
    mp3_index
):

    artist_key = normalize_artist(
        track["artist"]
    )

    title_key = normalize_title(
        track["title"]
    )

    candidates = mp3_index.get(
        artist_key,
        []
    )

    # --------------------------------------------------------
    # Geen MP3 artiest
    # --------------------------------------------------------

    if not candidates:

        return None, 0, 0, 0

    # --------------------------------------------------------
    # Exacte titel
    # --------------------------------------------------------

    for mp3 in candidates:

        mp3_title_key = normalize_title(
            mp3["title"]
        )

        if mp3_title_key == title_key:

            return (
                mp3,
                100.0,
                100,
                100
            )

    # --------------------------------------------------------
    # Geen exacte match
    #
    # We geven GEEN kandidaat terug.
    #
    # Dit voorkomt dat bijvoorbeeld:
    #
    # Diesel Drudge
    #
    # automatisch:
    #
    # Mod
    #
    # wordt.
    # --------------------------------------------------------

    return (
        None,
        0,
        100,
        0
    )


# ============================================================
# KOPPELING BESTAAT?
# ============================================================

def link_exists(
    conn,
    track_id,
    mp3_id
):

    row = conn.execute(
        """
        SELECT id
        FROM track_mp3
        WHERE track_id = ?
        AND mp3_id = ?
        """,
        (
            track_id,
            mp3_id
        )
    ).fetchone()

    return row is not None


# ============================================================
# TRACK MATCHING + COMMIT
# ============================================================

def match_and_commit(
    release_db_id,
    mp3_index
):

    conn = db_connect()

    tracks = conn.execute(
        """
        SELECT *
        FROM tracks
        WHERE release_id = ?
        ORDER BY id
        """,
        (
            release_db_id,
        )
    ).fetchall()

    exact = 0
    no_match = 0
    no_artist = 0
    existing = 0
    new_links = 0

    print()
    print("=" * 80)
    print("START MATCHING + COMMIT")
    print("=" * 80)

    for number, track in enumerate(
        tracks,
        start=1
    ):

        print()
        print(
            f"[{number}/{len(tracks)}] "
            f"{track['position']} | "
            f"{track['artist']} - "
            f"{track['title']}"
        )

        mp3, score, artist_score, title_score = (
            find_exact_match(
                track,
                mp3_index
            )
        )

        # ----------------------------------------------------
        # Geen artiest in MP3 database
        # ----------------------------------------------------

        if (
            not mp3
            and artist_score == 0
        ):

            no_artist += 1

            print(
                "MP3: GEEN ARTIEST"
            )

            print(
                "STATUS: GEEN ARTIEST"
            )

            print(
                "ACTIE: NIET KOPPELEN"
            )

            continue

        # ----------------------------------------------------
        # Geen exacte titel
        # ----------------------------------------------------

        if not mp3:

            no_match += 1

            print(
                "MP3: GEEN EXACTE MATCH"
            )

            print(
                "STATUS: NIET GEKOPPELD"
            )

            print(
                "ACTIE: NIET KOPPELEN"
            )

            continue

        # ----------------------------------------------------
        # Exacte match gevonden
        # ----------------------------------------------------

        exact += 1

        mp3_id = mp3["id"]
        track_id = track["id"]

        print(
            "MP3:",
            mp3["filename"]
        )

        print(
            "ARTIST SCORE:",
            artist_score
        )

        print(
            "TITLE SCORE:",
            title_score
        )

        print(
            "TOTAL SCORE:",
            score
        )

        # ----------------------------------------------------
        # Bestaat koppeling al?
        # ----------------------------------------------------

        if link_exists(
            conn,
            track_id,
            mp3_id
        ):

            existing += 1

            print(
                "STATUS: KOPPELING BESTAAT AL"
            )

            continue

        # ----------------------------------------------------
        # Nieuwe koppeling
        # ----------------------------------------------------

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
                score,
                0,
                0
            )
        )

        new_links += 1

        print(
            "STATUS: NIEUW GEKOPPELD"
        )

    # --------------------------------------------------------
    # COMMIT
    # --------------------------------------------------------

    conn.commit()

    conn.close()

    # --------------------------------------------------------
    # RESULTAAT
    # --------------------------------------------------------

    print()
    print("=" * 80)
    print("MATCHING KLAAR")
    print("=" * 80)

    print(
        "Exacte matches:",
        exact
    )

    print(
        "Geen exacte match:",
        no_match
    )

    print(
        "Geen artiest:",
        no_artist
    )

    print(
        "Bestaande koppelingen:",
        existing
    )

    print(
        "Nieuwe koppelingen:",
        new_links
    )

    return {
        "exact": exact,
        "no_match": no_match,
        "no_artist": no_artist,
        "existing": existing,
        "new_links": new_links
    }


# ============================================================
# MAIN
# ============================================================

def main():

    # --------------------------------------------------------
    # Release ID
    # --------------------------------------------------------

    if len(sys.argv) > 1:

        try:

            release_id = int(
                sys.argv[1]
            )

        except ValueError:

            print(
                "Ongeldig Discogs Release ID."
            )

            return

    else:

        release_id = DEFAULT_RELEASE_ID

    # --------------------------------------------------------
    # Discogs release
    # --------------------------------------------------------

    release = get_release(
        release_id
    )

    if not release:

        print()
        print(
            "Release kon niet worden opgehaald."
        )

        return

    # --------------------------------------------------------
    # Release database
    # --------------------------------------------------------

    release_db_id, is_new = (
        get_or_create_release(
            release
        )
    )

    # --------------------------------------------------------
    # Tracks importeren / bijwerken
    # --------------------------------------------------------

    import_tracks(
        release_db_id,
        release
    )

    # --------------------------------------------------------
    # MP3 index
    # --------------------------------------------------------

    mp3_index = build_mp3_index()

    # --------------------------------------------------------
    # MP3 matching
    # --------------------------------------------------------

    match_and_commit(
        release_db_id,
        mp3_index
    )

    # --------------------------------------------------------
    # Klaar
    # --------------------------------------------------------

    print()
    print("=" * 80)
    print("RELEASE IMPORT VOLLEDIG KLAAR")
    print("=" * 80)

    print(
        "Discogs Release:",
        release_id
    )

    print(
        "V3 Release ID:",
        release_db_id
    )


# ============================================================
# START
# ============================================================

if __name__ == "__main__":
    main()
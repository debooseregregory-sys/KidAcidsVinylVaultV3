# ============================================================
# KID ACID'S VINYLVAULT V3
# DISCOGS RELEASE IMPORTER
#
# V3 STRUCTUUR:
#
# releases
#     ↓
# tracks
#     ↓
# track_mp3
#     ↓
# mp3_files
#
# KASTCODE = LOKAAL
# Discogs wordt NOOIT met de kastcode aangeroepen.
# ============================================================

import os
import sys
import sqlite3
import time
import requests


# ============================================================
# PROJECT ROOT
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
# TEST VINYL
# ============================================================

ARTIST = "Planetary Assault Systems"

TRACK_TITLE = "Booster"

KASTCODE = "XCV 11"


# Discogs match die we eerder betrouwbaar gevonden hebben.

DISCOGS_RELEASE_ID = 5942009


# ============================================================
# DATABASE CONNECTIE
# ============================================================

def db_connect():

    conn = sqlite3.connect(DB)

    conn.row_factory = sqlite3.Row

    return conn


# ============================================================
# STRING HELPERS
# ============================================================

def clean(value):

    if value is None:
        return ""

    return str(value).strip()


# ============================================================
# POSITION NORMALIZER
# ============================================================

def normalize_position(
    position,
    side_counts
):

    position = clean(
        position
    ).upper()

    if not position:
        return ""


    # --------------------------------------------------------
    # Discogs:
    #
    # A
    # B
    #
    # wordt:
    #
    # A1
    # B1
    # --------------------------------------------------------

    if position == "A":

        side_counts["A"] += 1

        return (
            f"A{side_counts['A']}"
        )


    if position == "B":

        side_counts["B"] += 1

        return (
            f"B{side_counts['B']}"
        )


    # --------------------------------------------------------
    # Als Discogs al A1/A2/B1/B2 gebruikt
    # --------------------------------------------------------

    if position.startswith("A"):

        return position


    if position.startswith("B"):

        return position


    # --------------------------------------------------------
    # Andere posities:
    #
    # C1
    # D1
    # AA
    # etc.
    #
    # behouden.
    # --------------------------------------------------------

    return position


# ============================================================
# DISCOGS RELEASE OPHALEN
# ============================================================

def get_release(
    release_id
):

    print()
    print(
        "=" * 80
    )

    print(
        "DISCOGS RELEASE OPHALEN"
    )

    print(
        "Release ID:",
        release_id
    )

    print(
        "=" * 80
    )


    url = (
        f"{API_URL}/releases/"
        f"{release_id}"
    )


    while True:

        try:

            response = requests.get(
                url,
                headers=HEADERS,
                timeout=30
            )

        except Exception as exc:

            print()
            print(
                "NETWERKFOUT:"
            )

            print(
                exc
            )

            return None


        # ----------------------------------------------------
        # Rate limit
        # ----------------------------------------------------

        if response.status_code == 429:

            print()
            print(
                "Discogs rate limit."
            )

            print(
                "10 seconden wachten..."
            )

            time.sleep(10)

            continue


        # ----------------------------------------------------
        # Authenticatie
        # ----------------------------------------------------

        if response.status_code == 401:

            print()
            print(
                "DISCOGS AUTHENTICATIE MISLUKT"
            )

            print(
                response.text
            )

            return None


        # ----------------------------------------------------
        # Andere fouten
        # ----------------------------------------------------

        if response.status_code != 200:

            print()
            print(
                "HTTP STATUS:",
                response.status_code
            )

            print(
                response.text
            )

            return None


        print()
        print(
            "HTTP STATUS: 200"
        )

        return response.json()


# ============================================================
# RELEASE IN DATABASE
# ============================================================

def create_release(
    release
):

    conn = db_connect()

    # --------------------------------------------------------
    # Discogs gegevens
    # --------------------------------------------------------

    release_id = release.get(
        "id"
    )

    title = clean(
        release.get(
            "title"
        )
    )

    year = release.get(
        "year"
    )

    labels = (
        release.get(
            "labels"
        )
        or []
    )

    artists = (
        release.get(
            "artists"
        )
        or []
    )


    # --------------------------------------------------------
    # Artist
    # --------------------------------------------------------

    artist_names = []

    for artist in artists:

        name = clean(
            artist.get(
                "name"
            )
        )

        if name:

            artist_names.append(
                name
            )


    artist_name = ", ".join(
        artist_names
    )


    # --------------------------------------------------------
    # Label
    # --------------------------------------------------------

    label_names = []

    catalog = ""


    for label in labels:

        name = clean(
            label.get(
                "name"
            )
        )

        if name:

            label_names.append(
                name
            )


        if not catalog:

            catalog = clean(
                label.get(
                    "catno"
                )
            )


    label_name = ", ".join(
        label_names
    )


    # --------------------------------------------------------
    # Discogs URL
    # --------------------------------------------------------

    discogs_url = (
        f"https://www.discogs.com/release/"
        f"{release_id}"
    )


    # --------------------------------------------------------
    # BELANGRIJK:
    #
    # catalog = Discogs catalogusnummer
    #
    # KASTCODE wordt hier NIET opgeslagen.
    #
    # De kastcode blijft lokaal:
    #
    # XCV 11
    #
    # --------------------------------------------------------

    existing = conn.execute(
        """
        SELECT id
        FROM releases
        WHERE discogs = ?
        """,
        (
            str(release_id),
        )
    ).fetchone()


    if existing:

        db_release_id = existing["id"]

        print()
        print(
            "Release bestaat al."
        )

        print(
            "V3 Release ID:",
            db_release_id
        )

    else:

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
                artist_name,
                title,
                label_name,
                catalog,
                year,
                str(release_id),
                discogs_url,
                f"Kastcode: {KASTCODE}"
            )
        )


        db_release_id = (
            cursor.lastrowid
        )


        print()
        print(
            "Nieuwe release aangemaakt."
        )

        print(
            "V3 Release ID:",
            db_release_id
        )


    conn.commit()

    conn.close()

    return db_release_id


# ============================================================
# TRACK ARTIST
# ============================================================

def get_track_artist(
    track,
    release
):

    artists = (
        track.get(
            "artists"
        )
        or []
    )


    names = []


    for artist in artists:

        name = clean(
            artist.get(
                "name"
            )
        )

        if name:

            names.append(
                name
            )


    if names:

        return ", ".join(
            names
        )


    # --------------------------------------------------------
    # Geen trackartist:
    # release artist gebruiken.
    # --------------------------------------------------------

    artists = (
        release.get(
            "artists"
        )
        or []
    )


    names = []


    for artist in artists:

        name = clean(
            artist.get(
                "name"
            )
        )

        if name:

            names.append(
                name
            )


    return ", ".join(
        names
    )


# ============================================================
# DURATION
# ============================================================

def duration_to_seconds(
    duration
):

    duration = clean(
        duration
    )

    if not duration:

        return 0


    try:

        parts = duration.split(
            ":"
        )


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

    except ValueError:

        pass


    return 0


# ============================================================
# TRACKS IMPORTEREN
# ============================================================

def import_tracks(
    release_db_id,
    release
):

    conn = db_connect()


    tracklist = (
        release.get(
            "tracklist"
        )
        or []
    )


    side_counts = {
        "A": 0,
        "B": 0
    }


    imported = 0


    print()
    print(
        "=" * 80
    )

    print(
        "TRACKLIST"
    )

    print(
        "=" * 80
    )


    for track in tracklist:

        # ----------------------------------------------------
        # Discogs position
        # ----------------------------------------------------

        original_position = clean(
            track.get(
                "position"
            )
        )


        position = normalize_position(
            original_position,
            side_counts
        )


        # ----------------------------------------------------
        # Titel
        # ----------------------------------------------------

        title = clean(
            track.get(
                "title"
            )
        )


        if not title:

            continue


        # ----------------------------------------------------
        # Artist
        # ----------------------------------------------------

        artist = get_track_artist(
            track,
            release
        )


        # ----------------------------------------------------
        # Duration
        # ----------------------------------------------------

        duration_text = clean(
            track.get(
                "duration"
            )
        )


        duration = duration_to_seconds(
            duration_text
        )


        # ----------------------------------------------------
        # Controleer bestaande track
        # ----------------------------------------------------

        existing = conn.execute(
            """
            SELECT id
            FROM tracks
            WHERE release_id = ?
            AND position = ?
            """,
            (
                release_db_id,
                position
            )
        ).fetchone()


        if existing:

            track_id = existing["id"]

            print(
                f"{position:4} | "
                f"{artist:35} | "
                f"{title:45} "
                f"[BESTAAT]"
            )

            continue


        # ----------------------------------------------------
        # Nieuwe track
        # ----------------------------------------------------

        cursor = conn.execute(
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


        track_id = cursor.lastrowid


        imported += 1


        print(
            f"{position:4} | "
            f"{artist:35} | "
            f"{title:45} "
            f"{duration_text}"
        )


    conn.commit()

    conn.close()


    print()
    print(
        "Nieuwe tracks:",
        imported
    )


# ============================================================
# RESULTAAT
# ============================================================

def show_release(
    release_db_id
):

    conn = db_connect()


    release = conn.execute(
        """
        SELECT *
        FROM releases
        WHERE id = ?
        """,
        (
            release_db_id,
        )
    ).fetchone()


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


    conn.close()


    print()
    print()
    print(
        "=" * 80
    )

    print(
        "VINYLVAULT V3 RELEASE"
    )

    print(
        "=" * 80
    )


    print()
    print(
        "Artist   :",
        release["artist"]
    )

    print(
        "Release  :",
        release["title"]
    )

    print(
        "Label    :",
        release["label"]
    )

    print(
        "Discogs  :",
        release["discogs"]
    )

    print(
        "Kastcode :",
        KASTCODE
    )


    print()
    print(
        "-" * 80
    )


    for track in tracks:

        seconds = track["duration"]


        if seconds:

            minutes = seconds // 60

            secs = seconds % 60

            duration = (
                f"{minutes}:"
                f"{secs:02d}"
            )

        else:

            duration = ""


        print(
            f"{track['position']:4} | "
            f"{track['artist']:35} | "
            f"{track['title']:45} "
            f"{duration}"
        )


    print()
    print(
        "=" * 80
    )


# ============================================================
# MAIN
# ============================================================

def main():

    print()
    print(
        "=" * 80
    )

    print(
        "KID ACID'S VINYLVAULT V3"
    )

    print(
        "DISCOGS RELEASE IMPORT"
    )

    print(
        "=" * 80
    )


    print()
    print(
        "VinylVault:"
    )

    print(
        "Artist  :",
        ARTIST
    )

    print(
        "Track   :",
        TRACK_TITLE
    )

    print(
        "Kastcode:",
        KASTCODE
    )


    print()
    print(
        "Discogs:"
    )

    print(
        "Release ID:",
        DISCOGS_RELEASE_ID
    )


    # --------------------------------------------------------
    # Release ophalen
    # --------------------------------------------------------

    release = get_release(
        DISCOGS_RELEASE_ID
    )


    if not release:

        print()
        print(
            "Release kon niet worden opgehaald."
        )

        return


    # --------------------------------------------------------
    # Release tonen
    # --------------------------------------------------------

    print()
    print(
        "Discogs release:"
    )

    print(
        release.get(
            "title"
        )
    )


    # --------------------------------------------------------
    # Release toevoegen
    # --------------------------------------------------------

    release_db_id = create_release(
        release
    )


    # --------------------------------------------------------
    # Tracks toevoegen
    # --------------------------------------------------------

    import_tracks(
        release_db_id,
        release
    )


    # --------------------------------------------------------
    # Resultaat
    # --------------------------------------------------------

    show_release(
        release_db_id
    )


    print()
    print(
        "IMPORT KLAAR."
    )


# ============================================================
# START
# ============================================================

if __name__ == "__main__":

    main()
# ============================================================
# KID ACID'S VINYLVAULT V3
# DISCOGS -> V3 RELEASE IMPORTER
#
# VEILIGE TESTVERSIE
#
# TEST RELEASE:
# 5942009 - Planetary Funk Vol. 4
#
# Deze versie:
# - gebruikt de V3 tabellen
# - importeert releases
# - importeert tracks
# - normaliseert A -> A1 en B -> B1
# - voorkomt dubbele releases
# - voorkomt dubbele tracks
# - zoekt MP3's
# - koppelt alleen voldoende zekere matches
#
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
# VEILIGE TEST
# ============================================================

TEST_RELEASE_ID = 5942009


# ============================================================
# MATCHING
# ============================================================

EXACT_SCORE = 100

MIN_MATCH_SCORE = 80


# ============================================================
# DATABASE CONNECTIE
# ============================================================

def db_connect():

    conn = sqlite3.connect(DB)

    conn.row_factory = sqlite3.Row

    conn.execute(
        "PRAGMA foreign_keys = ON"
    )

    return conn


# ============================================================
# CLEAN
# ============================================================

def clean(value):

    if value is None:
        return ""

    return str(value).strip()


# ============================================================
# NORMALIZE TEKST
# ============================================================

def normalize(text):

    text = clean(text).lower()

    replacements = (
        "(", ")",
        "[", "]",
        "{", "}",
        "-", "_",
        "/", "\\",
        ".", ",",
        "'", '"',
    )

    for char in replacements:

        text = text.replace(
            char,
            " "
        )

    return " ".join(
        text.split()
    )


# ============================================================
# DISCOGS API
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
            print(
                "NETWERKFOUT:"
            )

            print(
                exc
            )

            return None


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
                "Discogs rate limit."
            )

            print(
                f"Wachten: {wait} seconden..."
            )

            time.sleep(
                wait
            )

            continue


        if response.status_code != 200:

            print()
            print(
                "Discogs HTTP:",
                response.status_code
            )

            print(
                response.text[:500]
            )

            return None


        return response.json()


# ============================================================
# DISCOGS RELEASE
# ============================================================

def get_discogs_release(
    release_id
):

    print()
    print(
        "DISCOGS RELEASE OPHALEN"
    )

    print(
        "Release ID:",
        release_id
    )

    return discogs_get(
        f"{API_URL}/releases/{release_id}"
    )


# ============================================================
# RELEASE ARTIST
# ============================================================

def get_release_artist(
    release
):

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

    position = clean(
        position
    ).upper()


    if not position:

        return ""


    # --------------------------------------------------------
    # A -> A1
    # --------------------------------------------------------

    if position == "A":

        side_counts["A"] += 1

        return (
            f"A{side_counts['A']}"
        )


    # --------------------------------------------------------
    # B -> B1
    # --------------------------------------------------------

    if position == "B":

        side_counts["B"] += 1

        return (
            f"B{side_counts['B']}"
        )


    # --------------------------------------------------------
    # Reeds bestaande posities behouden
    # --------------------------------------------------------

    return position


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
# RELEASE BESTAAT?
# ============================================================

def find_existing_release(
    conn,
    discogs_id
):

    return conn.execute(
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


# ============================================================
# RELEASE IMPORTEREN
# ============================================================

def import_release(
    conn,
    release
):

    discogs_id = clean(
        release.get(
            "id"
        )
    )

    existing = find_existing_release(
        conn,
        discogs_id
    )


    if existing:

        print()
        print(
            "RELEASE BESTAAT AL"
        )

        print(
            "V3 Release ID:",
            existing["id"]
        )

        return existing["id"]


    artist = get_release_artist(
        release
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


    label = ", ".join(
        label_names
    )


    discogs_link = (
        f"https://www.discogs.com/release/"
        f"{discogs_id}"
    )


    notes = (
        "TEST IMPORT - "
        "Kastcode blijft lokaal"
    )


    cursor = conn.execute(
        """
        INSERT INTO releases (
            artist,
            title,
            label,
            catalog,
            year,
            genre,
            discogs,
            discogs_link,
            cover,
            notes
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            artist,
            title,
            label,
            catalog,
            year,
            "",
            str(discogs_id),
            discogs_link,
            "",
            notes
        )
    )


    release_id = cursor.lastrowid


    print()
    print(
        "NIEUWE RELEASE"
    )

    print(
        "V3 Release ID:",
        release_id
    )

    return release_id


# ============================================================
# TRACK BESTAAT?
# ============================================================

def find_existing_track(
    conn,
    release_id,
    position
):

    return conn.execute(
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


# ============================================================
# TRACKS IMPORTEREN
# ============================================================

def import_tracks(
    conn,
    release_id,
    release
):

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
        "TRACKS"
    )

    print(
        "=" * 80
    )


    for discogs_track in tracklist:

        original_position = clean(
            discogs_track.get(
                "position"
            )
        )


        position = normalize_position(
            original_position,
            side_counts
        )


        title = clean(
            discogs_track.get(
                "title"
            )
        )


        if not title:

            continue


        artist = get_track_artist(
            discogs_track,
            release
        )


        duration = duration_to_seconds(
            discogs_track.get(
                "duration"
            )
        )


        existing = find_existing_track(
            conn,
            release_id,
            position
        )


        if existing:

            print(
                f"{position:4} | "
                f"{artist} | "
                f"{title} "
                f"[BESTAAT]"
            )

            continue


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
                release_id,
                position,
                artist,
                title,
                duration
            )
        )


        imported += 1


        print(
            f"{position:4} | "
            f"{artist} | "
            f"{title} "
            f"[NIEUW]"
        )


    print()
    print(
        "Nieuwe tracks:",
        imported
    )


# ============================================================
# MP3 ARTIST MATCH
# ============================================================

def get_mp3_candidates(
    conn,
    artist
):

    rows = conn.execute(
        """
        SELECT *
        FROM mp3_files
        WHERE lower(trim(artist))
            = lower(trim(?))
        ORDER BY title
        """,
        (
            artist,
        )
    ).fetchall()


    return rows


# ============================================================
# SCORE
# ============================================================

def calculate_score(
    vinyl_artist,
    vinyl_title,
    mp3_artist,
    mp3_title
):

    artist_score = 100 if (
        normalize(vinyl_artist)
        ==
        normalize(mp3_artist)
    ) else 0


    title_score = 100 if (
        normalize(vinyl_title)
        ==
        normalize(mp3_title)
    ) else 0


    if (
        artist_score == 100
        and title_score == 100
    ):

        total = 100

    elif artist_score == 100:

        total = 20

    else:

        total = 0


    return (
        total,
        artist_score,
        title_score
    )


# ============================================================
# TRACK MATCHEN
# ============================================================

def match_track(
    conn,
    track
):

    artist = clean(
        track["artist"]
    )

    title = clean(
        track["title"]
    )


    candidates = get_mp3_candidates(
        conn,
        artist
    )


    if not candidates:

        print()
        print(
            f"{track['position']} | "
            f"{artist} - {title}"
        )

        print(
            "STATUS: GEEN MP3 ARTIEST"
        )

        return None


    best = None


    for mp3 in candidates:

        score, artist_score, title_score = (
            calculate_score(
                artist,
                title,
                mp3["artist"],
                mp3["title"]
            )
        )


        candidate = (
            score,
            artist_score,
            title_score,
            mp3
        )


        if best is None:

            best = candidate

        elif score > best[0]:

            best = candidate


    score = best[0]
    artist_score = best[1]
    title_score = best[2]
    mp3 = best[3]


    if score == EXACT_SCORE:

        status = "EXACT"

    elif score >= MIN_MATCH_SCORE:

        status = "VARIANT"

    else:

        status = "GEEN MATCH"


    print()
    print(
        f"{track['position']} | "
        f"{artist} - {title}"
    )

    print(
        "MP3:",
        mp3["artist"],
        "-",
        mp3["title"]
    )

    print(
        "Score:",
        score
    )

    print(
        "Artiest:",
        artist_score
    )

    print(
        "Titel:",
        title_score
    )

    print(
        "STATUS:",
        status
    )


    if score < MIN_MATCH_SCORE:

        return None


    return {
        "track_id": track["id"],
        "mp3_id": mp3["id"],
        "score": score
    }


# ============================================================
# MP3 MATCHING
# ============================================================

def match_release_tracks(
    conn,
    release_id
):

    tracks = conn.execute(
        """
        SELECT *
        FROM tracks
        WHERE release_id = ?
        ORDER BY id
        """,
        (
            release_id,
        )
    ).fetchall()


    exact = 0
    variant = 0
    no_match = 0
    no_artist = 0
    linked = 0


    print()
    print(
        "=" * 80
    )

    print(
        "MP3 MATCHING"
    )

    print(
        "=" * 80
    )


    for track in tracks:

        result = match_track(
            conn,
            track
        )


        if result is None:

            candidates = get_mp3_candidates(
                conn,
                track["artist"]
            )


            if not candidates:

                no_artist += 1

            else:

                no_match += 1

            continue


        score = result["score"]


        if score == 100:

            exact += 1

        else:

            variant += 1


        # ----------------------------------------------------
        # Controleer dubbele koppeling
        # ----------------------------------------------------

        existing = conn.execute(
            """
            SELECT id
            FROM track_mp3
            WHERE track_id = ?
            AND mp3_id = ?
            """,
            (
                result["track_id"],
                result["mp3_id"]
            )
        ).fetchone()


        if existing:

            print(
                "KOPPELING BESTAAT AL"
            )

            continue


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
                result["track_id"],
                result["mp3_id"],
                result["score"],
                1,
                0
            )
        )


        linked += 1


    return (
        exact,
        variant,
        no_match,
        no_artist,
        linked
    )


# ============================================================
# RESULTAAT
# ============================================================

def show_result(
    conn,
    release_id
):

    release = conn.execute(
        """
        SELECT *
        FROM releases
        WHERE id = ?
        """,
        (
            release_id,
        )
    ).fetchone()


    tracks = conn.execute(
        """
        SELECT
            t.id,
            t.position,
            t.artist,
            t.title,
            m.artist AS mp3_artist,
            m.title AS mp3_title,
            m.path AS mp3_path,
            tm.score
        FROM tracks t

        LEFT JOIN track_mp3 tm
            ON tm.track_id = t.id

        LEFT JOIN mp3_files m
            ON m.id = tm.mp3_id

        WHERE t.release_id = ?

        ORDER BY t.id
        """,
        (
            release_id,
        )
    ).fetchall()


    print()
    print()
    print(
        "=" * 80
    )

    print(
        "VINYLVAULT V3 RESULTAAT"
    )

    print(
        "=" * 80
    )


    print()
    print(
        "Release:",
        release["title"]
    )

    print(
        "Artist :",
        release["artist"]
    )

    print(
        "Discogs:",
        release["discogs"]
    )


    print()
    print(
        "-" * 80
    )


    for track in tracks:

        print()

        print(
            f"{track['position']} | "
            f"{track['artist']} - "
            f"{track['title']}"
        )


        if track["mp3_path"]:

            print(
                "MP3:",
                track["mp3_artist"],
                "-",
                track["mp3_title"]
            )

            print(
                "Score:",
                track["score"]
            )

            print(
                "Actie: KOPPELEN"
            )

        else:

            print(
                "MP3: GEEN MATCH"
            )

            print(
                "Actie: NIET KOPPELEN"
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
        "DEFINITIEVE RELEASE IMPORT TEST"
    )

    print(
        "=" * 80
    )


    print()
    print(
        "DATABASE:"
    )

    print(
        DB
    )


    print()
    print(
        "TEST RELEASE:",
        TEST_RELEASE_ID
    )


    # --------------------------------------------------------
    # Database
    # --------------------------------------------------------

    conn = db_connect()


    try:

        # ----------------------------------------------------
        # Discogs
        # ----------------------------------------------------

        release = get_discogs_release(
            TEST_RELEASE_ID
        )


        if not release:

            print()
            print(
                "Release kon niet worden opgehaald."
            )

            return


        print()
        print(
            "DISCOGS:"
        )

        print(
            "Artist:",
            get_release_artist(
                release
            )
        )

        print(
            "Release:",
            release.get(
                "title"
            )
        )

        print(
            "Year:",
            release.get(
                "year"
            )
        )

        print(
            "Tracks:",
            len(
                release.get(
                    "tracklist",
                    []
                )
            )
        )


        # ----------------------------------------------------
        # TRANSACTION
        # ----------------------------------------------------

        conn.execute(
            "BEGIN"
        )


        # ----------------------------------------------------
        # Release
        # ----------------------------------------------------

        release_id = import_release(
            conn,
            release
        )


        # ----------------------------------------------------
        # Tracks
        # ----------------------------------------------------

        import_tracks(
            conn,
            release_id,
            release
        )


        # ----------------------------------------------------
        # MP3 matching
        # ----------------------------------------------------

        stats = match_release_tracks(
            conn,
            release_id
        )


        # ----------------------------------------------------
        # Commit
        # ----------------------------------------------------

        conn.commit()


        print()
        print(
            "DATABASE COMMIT: OK"
        )


        # ----------------------------------------------------
        # Result
        # ----------------------------------------------------

        show_result(
            conn,
            release_id
        )


        exact = stats[0]
        variant = stats[1]
        no_match = stats[2]
        no_artist = stats[3]
        linked = stats[4]


        print()
        print(
            "=" * 80
        )

        print(
            "STATISTIEKEN"
        )

        print(
            "=" * 80
        )

        print(
            "EXACT       :",
            exact
        )

        print(
            "VARIANT     :",
            variant
        )

        print(
            "GEEN MATCH  :",
            no_match
        )

        print(
            "GEEN ARTIEST:",
            no_artist
        )

        print(
            "KOPPELINGEN :",
            linked
        )


        print()
        print(
            "IMPORT TEST KLAAR"
        )


    except Exception as exc:

        print()
        print(
            "=" * 80
        )

        print(
            "FOUT"
        )

        print(
            "=" * 80
        )

        print(
            type(exc).__name__,
            ":",
            exc
        )


        print()
        print(
            "ROLLBACK..."
        )


        try:

            conn.rollback()

        except Exception:

            pass


        print(
            "DATABASE NIET GEWIJZIGD."
        )


    finally:

        conn.close()


# ============================================================
# START
# ============================================================

if __name__ == "__main__":

    main()
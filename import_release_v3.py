# ============================================================
# KID ACID'S VINYLVAULT V3
# GENERAL DISCOGS RELEASE IMPORTER
#
# BELANGRIJK:
# - Exacte ARTIST + TITLE matching voor MP3's
# - Geen fuzzy matching
# - Geen gokwerk
# - Bestaande tracks worden herkend
# - Discogs A / A1 / AA / AA1 worden correct behandeld
# - Bestaande MP3-koppelingen worden niet dubbel toegevoegd
# - Bestaande dubbele MP3-bestanden blijven behouden
# ============================================================

import os
import sys
import sqlite3
import requests
import config


# ============================================================
# PROJECT ROOT
# ============================================================

ROOT = os.path.dirname(
    os.path.abspath(__file__)
)

if ROOT not in sys.path:
    sys.path.insert(0, ROOT)


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
# TEXT NORMALIZATION
# ============================================================

def normalize(text):

    if not text:
        return ""

    text = str(text).lower()

    for char in (
        "(", ")",
        "[", "]",
        "{", "}",
        "-", "_",
        "/", "\\",
        ".", ",",
        "'", '"',
    ):
        text = text.replace(char, " ")

    return " ".join(text.split())


# ============================================================
# POSITION NORMALIZATION
# ============================================================

def normalize_position(position):

    if not position:
        return ""

    position = str(position).strip().upper()

    # A1 -> A
    # B1 -> B
    # AA1 -> AA
    # BB1 -> BB
    #
    # We only remove a trailing numeric suffix.
    #
    # Examples:
    # A1  -> A
    # A2  -> A
    # AA1 -> AA
    # B1  -> B

    while position and position[-1].isdigit():
        position = position[:-1]

    return position


# ============================================================
# DATABASE CONNECTION
# ============================================================

def db_connect():

    os.makedirs(
        os.path.dirname(DB),
        exist_ok=True
    )

    conn = sqlite3.connect(DB)

    conn.row_factory = sqlite3.Row

    conn.execute(
        "PRAGMA foreign_keys = ON"
    )

    return conn


# ============================================================
# DISCOGS GET
# ============================================================

def discogs_get(url):

    response = requests.get(
        url,
        headers=HEADERS,
        timeout=30
    )

    response.raise_for_status()

    return response.json()


# ============================================================
# GET RELEASE
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

    return discogs_get(
        f"{API_URL}/releases/{release_id}"
    )


# ============================================================
# FIND EXISTING RELEASE
# ============================================================

def find_release(
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
        (str(discogs_id),)
    ).fetchone()


# ============================================================
# INSERT RELEASE
# ============================================================

def insert_release(
    conn,
    release
):

    artists = release.get(
        "artists",
        []
    )

    artist = ""

    if artists:
        artist = artists[0].get(
            "name",
            ""
        )

    title = release.get(
        "title",
        ""
    )

    label = ""

    labels = release.get(
        "labels",
        []
    )

    if labels:
        label = labels[0].get(
            "name",
            ""
        )

    catalog_number = ""

    if labels:
        catalog_number = labels[0].get(
            "catno",
            ""
        )

    year = release.get(
        "year"
    )

    discogs_id = release.get(
        "id"
    )

    conn.execute(
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
            catalog_number,
            year,
            "",
            str(discogs_id),
            f"https://www.discogs.com/release/{discogs_id}",
            "",
            ""
        )
    )

    conn.commit()

    return find_release(
        conn,
        discogs_id
    )


# ============================================================
# FIND EXISTING TRACK
#
# BELANGRIJKE WIJZIGING:
#
# We zoeken NIET meer op position.
#
# Daardoor:
#
# bestaande:
# A1 | Booster
#
# Discogs:
# A | Booster
#
# = ZELFDE TRACK
# ============================================================

def find_existing_track(
    conn,
    release_id,
    artist,
    title
):

    normalized_artist = normalize(
        artist
    )

    normalized_title = normalize(
        title
    )

    rows = conn.execute(
        """
        SELECT *
        FROM tracks
        WHERE release_id = ?
        ORDER BY id
        """,
        (release_id,)
    ).fetchall()

    for row in rows:

        row_artist = normalize(
            row["artist"]
        )

        row_title = normalize(
            row["title"]
        )

        if (
            row_artist == normalized_artist
            and
            row_title == normalized_title
        ):
            return row

    return None


# ============================================================
# INSERT TRACK
# ============================================================

def insert_track(
    conn,
    release_id,
    position,
    artist,
    title,
    duration
):

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

    conn.commit()

    return cursor.lastrowid


# ============================================================
# LOAD MP3 DATABASE
# ============================================================

def load_mp3s(conn):

    print()
    print("=" * 80)
    print("MP3 DATABASE INLEZEN")
    print("=" * 80)

    rows = conn.execute(
        """
        SELECT *
        FROM mp3_files
        """
    ).fetchall()

    print(
        "MP3's beschikbaar:",
        len(rows)
    )

    exact = {}

    for row in rows:

        artist = normalize(
            row["artist"]
        )

        title = normalize(
            row["title"]
        )

        if not artist or not title:
            continue

        key = (
            artist,
            title
        )

        exact.setdefault(
            key,
            []
        ).append(row)

    print(
        "Exacte combinaties:",
        len(exact)
    )

    return exact


# ============================================================
# FIND EXACT MP3
# ============================================================

def find_exact_mp3(
    mp3_index,
    artist,
    title
):

    key = (
        normalize(artist),
        normalize(title)
    )

    return mp3_index.get(
        key,
        []
    )


# ============================================================
# CHECK LINK
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
        LIMIT 1
        """,
        (
            track_id,
            mp3_id
        )
    ).fetchone()

    return row is not None


# ============================================================
# CREATE LINK
# ============================================================

def create_link(
    conn,
    track_id,
    mp3_id
):

    if link_exists(
        conn,
        track_id,
        mp3_id
    ):
        return False

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
            100,
            0,
            0
        )
    )

    return True


# ============================================================
# IMPORT RELEASE
# ============================================================

def import_release(
    release,
    conn
):

    discogs_id = release.get(
        "id"
    )

    artists = release.get(
        "artists",
        []
    )

    artist = ""

    if artists:
        artist = artists[0].get(
            "name",
            ""
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

    print()
    print("=" * 80)
    print("DISCOGS")
    print("=" * 80)

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

    # ========================================================
    # RELEASE
    # ========================================================

    release_row = find_release(
        conn,
        discogs_id
    )

    if release_row:

        print()
        print(
            "V3 RELEASE BESTAAT AL"
        )

    else:

        release_row = insert_release(
            conn,
            release
        )

        print()
        print(
            "NIEUWE V3 RELEASE AANGEMAAKT"
        )

    release_id = release_row["id"]

    print(
        "V3 Release ID:",
        release_id
    )

    print(
        "Release:",
        release_row["title"]
    )

    print(
        "Artist:",
        release_row["artist"]
    )

    print(
        "Catalog:",
        release_row["catalog"]
    )

    print(
        "Discogs:",
        release_row["discogs"]
    )

    # ========================================================
    # TRACKS
    # ========================================================

    print()
    print("=" * 80)
    print("TRACKS")
    print("=" * 80)

    new_tracks = 0

    for item in tracklist:

        position = (
            item.get("position")
            or ""
        )

        track_title = (
            item.get("title")
            or ""
        )

        if not track_title:
            continue

        track_artists = item.get(
            "artists"
        )

        track_artist = artist

        if track_artists:

            first_artist = track_artists[0].get(
                "name",
                ""
            )

            if first_artist:
                track_artist = first_artist

        duration_text = (
            item.get("duration")
            or ""
        )

        duration = 0

        if duration_text:

            try:

                parts = duration_text.split(":")

                if len(parts) == 2:

                    duration = (
                        int(parts[0]) * 60
                        + int(parts[1])
                    )

            except Exception:

                duration = 0

        # ----------------------------------------------------
        # NIEUWE BELANGRIJKE MATCH
        # ----------------------------------------------------

        existing_track = find_existing_track(
            conn,
            release_id,
            track_artist,
            track_title
        )

        if existing_track:

            track_id = existing_track["id"]

            existing_position = (
                existing_track["position"]
                or ""
            )

            print(
                f"{existing_position:4} | "
                f"{track_artist} | "
                f"{track_title} [BESTAAT]"
            )

        else:

            track_id = insert_track(
                conn,
                release_id,
                position,
                track_artist,
                track_title,
                duration
            )

            new_tracks += 1

            print(
                f"{position:4} | "
                f"{track_artist} | "
                f"{track_title} [NIEUW]"
            )

    print()
    print(
        "Nieuwe tracks:",
        new_tracks
    )

    # ========================================================
    # MP3 DATABASE
    # ========================================================

    mp3_index = load_mp3s(
        conn
    )

    # ========================================================
    # MATCHING
    # ========================================================

    print()
    print("=" * 80)
    print("START EXACTE MP3 MATCHING")
    print("=" * 80)

    exact_count = 0
    multiple_count = 0
    no_match_count = 0
    existing_link_count = 0
    new_link_count = 0

    tracks = conn.execute(
        """
        SELECT *
        FROM tracks
        WHERE release_id = ?
        ORDER BY id
        """,
        (release_id,)
    ).fetchall()

    for number, track in enumerate(
        tracks,
        start=1
    ):

        track_artist = track["artist"]

        track_title = track["title"]

        print()
        print(
            f"[{number}/{len(tracks)}] "
            f"{track['position']} | "
            f"{track_artist} - "
            f"{track_title}"
        )

        matches = find_exact_mp3(
            mp3_index,
            track_artist,
            track_title
        )

        if not matches:

            print(
                "MP3: GEEN EXACTE MATCH"
            )

            print(
                "STATUS: GEEN MATCH"
            )

            no_match_count += 1

            continue

        exact_count += 1

        if len(matches) > 1:

            print(
                "MP3: MEERDERE EXACTE MATCHES"
            )

            multiple_count += 1

        else:

            print(
                "MP3: EXACTE MATCH"
            )

        for mp3 in matches:

            print(
                "Bestand:",
                mp3["path"]
            )

            if link_exists(
                conn,
                track["id"],
                mp3["id"]
            ):

                print(
                    "ACTIE: KOPPELING BESTAAT AL"
                )

                existing_link_count += 1

            else:

                create_link(
                    conn,
                    track["id"],
                    mp3["id"]
                )

                print(
                    "ACTIE: NIEUWE KOPPELING"
                )

                new_link_count += 1

    # ========================================================
    # COMMIT
    # ========================================================

    conn.commit()

    # ========================================================
    # RESULT
    # ========================================================

    print()
    print("=" * 80)
    print("IMPORT RESULTAAT")
    print("=" * 80)

    print()
    print(
        "Release:",
        title
    )

    print(
        "Artist :",
        artist
    )

    print(
        "Discogs:",
        discogs_id
    )

    print()
    print(
        "EXACTE MATCHES         :",
        exact_count
    )

    print(
        "MEERDERE EXACTE        :",
        multiple_count
    )

    print(
        "GEEN MATCH              :",
        no_match_count
    )

    print(
        "BESTAANDE KOPPELINGEN  :",
        existing_link_count
    )

    print(
        "NIEUWE KOPPELINGEN     :",
        new_link_count
    )

    print()
    print(
        "DATABASE COMMIT: OK"
    )


# ============================================================
# MAIN
# ============================================================

def main():

    print()
    print("=" * 80)
    print("KID ACID'S VINYLVAULT V3")
    print("GENERAL DISCOGS RELEASE IMPORTER")
    print("=" * 80)

    print()
    print(
        "Database:"
    )

    print(
        DB
    )

    print()
    print(
        "Voer een Discogs Release ID in."
    )

    print(
        "Voorbeeld: 5942009"
    )

    release_id = input(
        "\nDiscogs Release ID: "
    ).strip()

    if not release_id:

        print(
            "Geen Release ID ingevoerd."
        )

        return

    try:

        release_id = int(
            release_id
        )

    except ValueError:

        print(
            "Release ID moet een nummer zijn."
        )

        return

    try:

        release = get_release(
            release_id
        )

    except Exception as e:

        print()
        print(
            "FOUT BIJ DISCOGS:"
        )

        print(
            e
        )

        return

    conn = db_connect()

    try:

        import_release(
            release,
            conn
        )

    except Exception:

        conn.rollback()

        print()
        print("=" * 80)
        print("IMPORT MISLUKT")
        print("=" * 80)

        raise

    finally:

        conn.close()

    print()
    print("=" * 80)
    print("IMPORT KLAAR")
    print("=" * 80)


# ============================================================
# START
# ============================================================

if __name__ == "__main__":
    main()
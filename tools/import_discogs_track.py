import os
import sys
import sqlite3
import requests
import time


# ============================================================
# KID ACID'S VINYLVAULT V3
# DISCOGS -> RELEASE TRACK IMPORT
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
    "User-Agent": config.DISCOGS_USER_AGENT,
    "Accept": "application/json",
}


# ============================================================
# TEST RELEASE
# ============================================================

DISCOGS_RELEASE_ID = 5942009

STORAGE_CODE = "XCV 11"


# ============================================================
# DATABASE HELPERS
# ============================================================

def connect():
    return sqlite3.connect(DB)


def ensure_storage_code():
    conn = connect()

    columns = [
        row[1]
        for row in conn.execute(
            "PRAGMA table_info(releases)"
        ).fetchall()
    ]

    if "storage_code" not in columns:
        conn.execute(
            "ALTER TABLE releases "
            "ADD COLUMN storage_code TEXT DEFAULT ''"
        )
        conn.commit()

        print("storage_code toegevoegd.")

    conn.close()


# ============================================================
# DISCOGS REQUEST
# ============================================================

def discogs_get(url):

    while True:

        response = requests.get(
            url,
            headers=HEADERS,
            timeout=30,
        )

        if response.status_code == 429:

            print()
            print("Discogs rate limit bereikt.")
            print("10 seconden wachten...")

            time.sleep(10)

            continue

        response.raise_for_status()

        return response.json()


# ============================================================
# POSITION NORMALIZER
# ============================================================

def normalize_position(position, previous_side=None, counters=None):

    if counters is None:
        counters = {
            "A": 0,
            "B": 0,
            "C": 0,
            "D": 0,
        }

    if not position:
        side = previous_side or "A"
        counters[side] += 1
        return f"{side}{counters[side]}"

    position = str(position).strip().upper()

    # Already correct: A1, A2, B1, etc.
    if len(position) >= 2:
        first = position[0]

        if first in "ABCD" and position[1:].isdigit():
            counters[first] = max(
                counters[first],
                int(position[1:])
            )
            return position

    # Discogs sometimes returns:
    # A, B, C, D
    if position in "ABCD":
        counters[position] += 1
        return f"{position}{counters[position]}"

    # Discogs sometimes returns:
    # 1, 2, 3, 4
    if position.isdigit():

        number = int(position)

        if number <= 1:
            side = "A"

        elif number <= 2:
            side = "B"

        elif number <= 3:
            side = "C"

        else:
            side = "D"

        counters[side] += 1

        return f"{side}{counters[side]}"

    return position


# ============================================================
# RELEASE OPHALEN
# ============================================================

def get_discogs_release():

    print()
    print("=" * 80)
    print("DISCOGS RELEASE OPHALEN")
    print("=" * 80)
    print()
    print("Release ID:", DISCOGS_RELEASE_ID)

    data = discogs_get(
        f"{API_URL}/releases/{DISCOGS_RELEASE_ID}"
    )

    print()
    print("HTTP STATUS: 200")
    print()
    print("Release :", data.get("title"))
    print("Year    :", data.get("year"))
    print("Country :", data.get("country"))
    print("Catalog :", data.get("catno"))
    print("Labels  :", data.get("labels"))

    return data


# ============================================================
# ARTIST HELPER
# ============================================================

def get_track_artist(track, release_artist):

    artists = track.get("artists")

    if artists:

        names = []

        for artist in artists:

            name = artist.get("name", "").strip()

            if name:
                names.append(name)

        if names:
            return ", ".join(names)

    return release_artist


# ============================================================
# RELEASE ARTIST
# ============================================================

def get_release_artist(data):

    artists = data.get("artists")

    if artists:

        names = []

        for artist in artists:

            name = artist.get("name", "").strip()

            if name:
                names.append(name)

        if names:
            return ", ".join(names)

    return ""


# ============================================================
# EXISTING RELEASE
# ============================================================

def find_existing_release(conn, discogs_id):

    row = conn.execute(
        """
        SELECT id
        FROM releases
        WHERE discogs = ?
        LIMIT 1
        """,
        (str(discogs_id),)
    ).fetchone()

    if row:
        return row[0]

    return None


# ============================================================
# CREATE RELEASE
# ============================================================

def create_release(conn, data):

    discogs_id = data.get("id")

    existing_id = find_existing_release(
        conn,
        discogs_id
    )

    if existing_id:

        print()
        print(
            "Bestaande V3 release gevonden:",
            existing_id
        )

        conn.execute(
            """
            UPDATE releases
            SET storage_code = ?
            WHERE id = ?
            """,
            (
                STORAGE_CODE,
                existing_id,
            )
        )

        conn.commit()

        return existing_id

    artist = get_release_artist(data)

    title = data.get("title", "").strip()

    labels = data.get("labels") or []

    label = ""

    if labels:

        label = labels[0].get(
            "name",
            ""
        ).strip()

    catalog = data.get(
        "catno",
        ""
    ) or ""

    year = data.get("year")

    conn.execute(
        """
        INSERT INTO releases (
            artist,
            title,
            label,
            catalog,
            year,
            discogs,
            discogs_link,
            storage_code
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            artist,
            title,
            label,
            catalog,
            year,
            str(discogs_id),
            f"https://www.discogs.com/release/{discogs_id}",
            STORAGE_CODE,
        )
    )

    conn.commit()

    release_id = conn.execute(
        "SELECT last_insert_rowid()"
    ).fetchone()[0]

    print()
    print("Nieuwe release aangemaakt.")
    print("V3 Release ID:", release_id)

    return release_id


# ============================================================
# DELETE EXISTING TRACKS
# ============================================================

def clear_tracks(conn, release_id):

    conn.execute(
        """
        DELETE FROM tracks
        WHERE release_id = ?
        """,
        (release_id,)
    )

    conn.commit()


# ============================================================
# IMPORT TRACKS
# ============================================================

def import_tracks(conn, release_id, data):

    tracks = data.get("tracklist") or []

    release_artist = get_release_artist(data)

    counters = {
        "A": 0,
        "B": 0,
        "C": 0,
        "D": 0,
    }

    previous_side = None

    imported = []

    for track in tracks:

        raw_position = track.get(
            "position",
            ""
        )

        position = normalize_position(
            raw_position,
            previous_side,
            counters
        )

        if position:
            previous_side = position[0]

        title = (
            track.get("title")
            or ""
        ).strip()

        duration = (
            track.get("duration")
            or ""
        ).strip()

        artist = get_track_artist(
            track,
            release_artist
        )

        # Discogs can contain headings / notes.
        if not title:
            continue

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
                release_id,
                position,
                artist,
                title,
                duration,
            )
        )

        imported.append(
            (
                position,
                artist,
                title,
                duration,
            )
        )

    conn.commit()

    return imported


# ============================================================
# SHOW RESULT
# ============================================================

def show_result(conn, release_id):

    print()
    print("=" * 80)
    print("RESULTAAT")
    print("=" * 80)

    release = conn.execute(
        """
        SELECT
            id,
            artist,
            title,
            label,
            catalog,
            year,
            discogs,
            storage_code
        FROM releases
        WHERE id = ?
        """,
        (release_id,)
    ).fetchone()

    print()
    print("Release ID :", release[0])
    print("Artist     :", release[1])
    print("Release    :", release[2])
    print("Label      :", release[3])
    print("Catalog    :", release[4])
    print("Year       :", release[5])
    print("Discogs    :", release[6])
    print("Kastcode   :", release[7])

    print()
    print("TRACKLIST:")
    print()

    rows = conn.execute(
        """
        SELECT
            position,
            artist,
            title,
            duration
        FROM tracks
        WHERE release_id = ?
        ORDER BY id
        """,
        (release_id,)
    ).fetchall()

    for row in rows:

        print(
            f"{row[0]:<5} | "
            f"{row[1]:<35} | "
            f"{row[2]}"
            + (
                f" | {row[3]}"
                if row[3]
                else ""
            )
        )

    print()
    print("Aantal tracks:", len(rows))


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 80)
    print("KID ACID'S VINYLVAULT V3")
    print("DISCOGS RELEASE IMPORT TEST")
    print("=" * 80)

    print()
    print("DATABASE:")
    print(DB)

    ensure_storage_code()

    data = get_discogs_release()

    conn = connect()

    try:

        release_id = create_release(
            conn,
            data
        )

        # For this controlled test we rebuild
        # the Discogs tracklist for this release.
        clear_tracks(
            conn,
            release_id
        )

        imported = import_tracks(
            conn,
            release_id,
            data
        )

        print()

        for position, artist, title, duration in imported:

            print(
                f"{position:<5} | "
                f"{artist:<35} | "
                f"{title}"
                + (
                    f" | {duration}"
                    if duration
                    else ""
                )
            )

        print()
        print(
            "Nieuwe tracks:",
            len(imported)
        )

        show_result(
            conn,
            release_id
        )

    finally:

        conn.close()

    print()
    print("=" * 80)
    print("IMPORT TEST KLAAR")
    print("=" * 80)


if __name__ == "__main__":
    main()

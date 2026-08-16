import os
import sys
import sqlite3
import requests
import time


# ============================================================
# KID ACID'S VINYLVAULT V3
# DISCOGS 508 RELEASES -> TRACKS
# ============================================================


# ============================================================
# PROJECT ROOT
# ============================================================

HERE = os.path.abspath(__file__)

ROOT = os.path.dirname(HERE)

while ROOT != os.path.dirname(ROOT):

    if (
        os.path.exists(os.path.join(ROOT, "config.py"))
        and os.path.exists(os.path.join(ROOT, "data"))
    ):
        break

    ROOT = os.path.dirname(ROOT)


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
# DISCOGS API
# ============================================================

API_URL = "https://api.discogs.com"

HEADERS = {
    "User-Agent": config.DISCOGS_USER_AGENT,
    "Accept": "application/json",
}


# ============================================================
# TABLE
# ============================================================

CSV_TABLE = "discogs_vinyl"


# ============================================================
# DATABASE
# ============================================================

def connect():

    return sqlite3.connect(DB)


# ============================================================
# DISCOGS API
# ============================================================

def discogs_get(release_id):

    url = f"{API_URL}/releases/{release_id}"

    while True:

        response = requests.get(
            url,
            headers=HEADERS,
            timeout=30,
        )

        if response.status_code == 429:

            print(
                "  Rate limit - 10 seconden wachten..."
            )

            time.sleep(10)

            continue

        response.raise_for_status()

        return response.json()


# ============================================================
# ARTIST
# ============================================================

def get_release_artist(data):

    artists = data.get("artists") or []

    names = []

    for artist in artists:

        name = str(
            artist.get("name", "")
        ).strip()

        if name:

            names.append(name)

    return ", ".join(names)


# ============================================================
# TRACK ARTIST
# ============================================================

def get_track_artist(track, release_artist):

    artists = track.get("artists") or []

    names = []

    for artist in artists:

        name = str(
            artist.get("name", "")
        ).strip()

        if name:

            names.append(name)

    if names:

        return ", ".join(names)

    return release_artist


# ============================================================
# POSITIE NORMALIZER
#
# DISCOGS:
#
# A       -> eerste track kant A
# AA      -> tweede track kant A
# AAA     -> derde track kant A
#
# B       -> eerste track kant B
# BB      -> tweede track kant B
# BBB     -> derde track kant B
#
# VINYLVAULT:
#
# A1
# A2
# A3
# B1
# B2
# B3
#
# NOOIT:
#
# AA
# BB
# AAA
# BBB
#
# ============================================================

def normalize_position(position, counters, previous_side=None):

    position = str(
        position or ""
    ).strip().upper()


    # ========================================================
    # LEGE POSITIE
    # ========================================================

    if not position:

        side = previous_side

        if side not in (
            "A",
            "B",
            "C",
            "D",
        ):

            side = counters.get(
                "_SIDE",
                "A"
            )

        if side not in (
            "A",
            "B",
            "C",
            "D",
        ):

            side = "A"

        counters[side] += 1

        counters["_SIDE"] = side

        return f"{side}{counters[side]}"


    # ========================================================
    # NORMALE POSITIE A1 / A2 / B1 / B2 / C1 / D1
    # ========================================================

    if len(position) >= 2:

        side = position[0]

        number = position[1:]


        if (
            side in "ABCD"
            and number.isdigit()
        ):

            n = int(number)

            if n < 1:

                n = 1

            counters[side] = max(
                counters[side],
                n
            )

            counters["_SIDE"] = side

            return f"{side}{n}"


    # ========================================================
    # ALLEEN LETTERS
    #
    # A  -> A1
    # AA -> A2
    # AAA -> A3
    #
    # B  -> B1
    # BB -> B2
    # BBB -> B3
    # ========================================================

    if (
        position
        and all(
            char in "ABCD"
            for char in position
        )
    ):

        # Alleen geldig als alle letters hetzelfde zijn.
        if len(set(position)) == 1:

            side = position[0]

            n = len(position)

            counters[side] = max(
                counters[side],
                n
            )

            counters["_SIDE"] = side

            return f"{side}{n}"


    # ========================================================
    # NUMERIEKE POSITIES
    #
    # 1 -> A1
    # 2 -> B1
    # 3 -> C1
    # 4 -> D1
    #
    # ========================================================

    if position.isdigit():

        n = int(position)

        if n <= 1:

            side = "A"

        elif n == 2:

            side = "B"

        elif n == 3:

            side = "C"

        else:

            side = "D"


        counters[side] += 1

        counters["_SIDE"] = side

        return f"{side}{counters[side]}"


    # ========================================================
    # ONBEKENDE POSITIE
    #
    # Niet gokken.
    # Originele positie behouden.
    #
    # ========================================================

    return position


# ============================================================
# BESTAANDE RELEASE
# ============================================================

def find_release(conn, discogs_id):

    row = conn.execute(
        """
        SELECT id
        FROM releases
        WHERE discogs = ?
        LIMIT 1
        """,
        (
            str(discogs_id),
        )
    ).fetchone()


    if row:

        return row[0]


    return None


# ============================================================
# KASTCODE OPHALEN
# ============================================================

def get_storage_code(row):

    value = row["kastcodes"]

    if value is None:

        return ""

    return str(value).strip()


# ============================================================
# TRACK TABEL CONTROLEREN
# ============================================================

def check_tracks_table(conn):

    columns = [
        row[1]
        for row in conn.execute(
            "PRAGMA table_info(tracks)"
        ).fetchall()
    ]


    required = [
        "release_id",
        "position",
        "artist",
        "title",
        "duration",
    ]


    missing = [
        column
        for column in required
        if column not in columns
    ]


    if missing:

        print()
        print(
            "FOUT: ontbrekende kolommen in tracks:"
        )

        print(
            ", ".join(missing)
        )

        print()

        print(
            "Aanwezige kolommen:"
        )

        print(
            columns
        )

        return False


    return True


# ============================================================
# RELEASE TRACKS IMPORTEREN
# ============================================================

def import_tracks(conn, release_id, data):

    tracklist = data.get("tracklist") or []

    release_artist = get_release_artist(data)

    conn.execute(
        """
        DELETE FROM tracks
        WHERE release_id=?
        """,
        (release_id,)
    )

    counters = {
        "A": 0,
        "B": 0,
        "C": 0,
        "D": 0,
        "_SIDE": "A",
    }

    imported = []

    for track in tracklist:

        # --------------------------------------------------
        # Alleen echte audiotracks importeren
        # --------------------------------------------------

        if track.get("type_") != "track":
            continue

        title = str(track.get("title") or "").strip()

        if not title:
            continue

        raw_position = str(track.get("position") or "").strip().upper()

        # headings zonder positie overslaan
        if raw_position == "":
            continue

        # update huidige zijde
        if raw_position[0] in "ABCD":
            counters["_SIDE"] = raw_position[0]

        position = normalize_position(
            raw_position,
            counters,
        )

        artist = get_track_artist(
            track,
            release_artist,
        )

        duration = str(
            track.get("duration") or ""
        ).strip()

        conn.execute(
            """
            INSERT INTO tracks(
                release_id,
                position,
                artist,
                title,
                duration
            )
            VALUES(?,?,?,?,?)
            """,
            (
                release_id,
                position,
                artist,
                title,
                duration,
            ),
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

    # ========================================================
    # BESTAANDE TRACKS VAN RELEASE VERWIJDEREN
    # ========================================================

    conn.execute(
        """
        DELETE FROM tracks
        WHERE release_id = ?
        """,
        (
            release_id,
        )
    )


    # ========================================================
    # COUNTERS
    # ========================================================

    counters = {

        "A": 0,

        "B": 0,

        "C": 0,

        "D": 0,

        "_SIDE": "A",

    }


    previous_side = None


    imported = []


    # ========================================================
    # TRACKS
    # ========================================================

    for track in tracks:


        # ----------------------------------------------------
        # TITEL
        # ----------------------------------------------------

        title = str(
            track.get("title") or ""
        ).strip()


        # Discogs kan headings/notities
        # zonder echte tracktitel bevatten.

        if not title:

            continue


        # ----------------------------------------------------
        # POSITIE
        # ----------------------------------------------------

        raw_position = track.get(
            "position",
            ""
        )


        position = normalize_position(
            raw_position,
            counters,
            previous_side
        )


        # ----------------------------------------------------
        # PREVIOUS SIDE
        # ----------------------------------------------------

        if (
            position
            and position[0] in "ABCD"
        ):

            previous_side = position[0]


        # ----------------------------------------------------
        # ARTIST
        # ----------------------------------------------------

        artist = get_track_artist(
            track,
            release_artist
        )


        # ----------------------------------------------------
        # DURATION
        # ----------------------------------------------------

        duration = str(
            track.get("duration") or ""
        ).strip()


        # ----------------------------------------------------
        # DATABASE
        # ----------------------------------------------------

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
# RELEASE INFO
# ============================================================

def update_release_storage(
    conn,
    release_id,
    storage_code
):

    if not storage_code:

        return


    conn.execute(
        """
        UPDATE releases
        SET storage_code = ?
        WHERE id = ?
        """,
        (
            storage_code,
            release_id,
        )
    )


    conn.commit()


# ============================================================
# MAIN
# ============================================================

def main():

    print()

    print("=" * 80)

    print(
        "DISCOGS 508 RELEASES -> VINYLVAULT TRACK IMPORT"
    )

    print("=" * 80)

    print()


    # ========================================================
    # DATABASE
    # ========================================================

    conn = connect()

    conn.row_factory = sqlite3.Row


    # ========================================================
    # TRACK TABEL
    # ========================================================

    if not check_tracks_table(conn):

        conn.close()

        return


    # ========================================================
    # DISCOGS VINYL RECORDS
    # ========================================================

    rows = conn.execute(
        """
        SELECT
            discogs_id,
            instance_id,
            artist,
            title,
            year,
            labels,
            catalogs,
            matched_catalogs,
            kastcodes
        FROM discogs_vinyl
        WHERE discogs_id IS NOT NULL
        AND TRIM(discogs_id) <> ''
        ORDER BY artist, title
        """
    ).fetchall()


    print(
        "Discogs vinyl records:",
        len(rows)
    )

    print()


    if not rows:

        print(
            "GEEN RECORDS GEVONDEN."
        )

        conn.close()

        return


    # ========================================================
    # COUNTERS
    # ========================================================

    total_releases = 0

    total_tracks = 0

    skipped = 0

    failed = 0


    # ========================================================
    # RELEASES
    # ========================================================

    for index, row in enumerate(
        rows,
        start=1
    ):


        discogs_id = str(
            row["discogs_id"]
        ).strip()


        artist = str(
            row["artist"] or ""
        ).strip()


        title = str(
            row["title"] or ""
        ).strip()


        storage_code = get_storage_code(
            row
        )


        print(
            f"[{index}/{len(rows)}] "
            f"{artist} - {title}"
        )


        print(
            f"  Discogs ID : {discogs_id}"
        )


        # ====================================================
        # RELEASE ZOEKEN
        # ====================================================

        release_id = find_release(
            conn,
            discogs_id
        )


        if not release_id:

            print(
                "  SKIP: release niet gevonden in releases"
            )

            skipped += 1

            print()

            continue


        # ====================================================
        # DISCOGS API
        # ====================================================

        try:

            data = discogs_get(
                discogs_id
            )

        except Exception as exc:

            print(
                f"  FOUT Discogs API: {exc}"
            )

            failed += 1

            print()

            continue


        # ====================================================
        # TRACKLIST
        # ====================================================

        tracklist = data.get(
            "tracklist"
        ) or []


        if not tracklist:

            print(
                "  GEEN TRACKLIST"
            )

            skipped += 1

            print()

            time.sleep(1.1)

            continue


        # ====================================================
        # KASTCODE BEWAREN
        # ====================================================

        update_release_storage(
            conn,
            release_id,
            storage_code
        )


        # ====================================================
        # TRACKS IMPORTEREN
        # ====================================================

        try:

            imported = import_tracks(
                conn,
                release_id,
                data
            )

        except Exception as exc:

            print(
                f"  FOUT TRACK IMPORT: {exc}"
            )

            failed += 1

            print()

            continue


        total_releases += 1

        total_tracks += len(imported)


        # ====================================================
        # RESULTAAT
        # ====================================================

        print(
            f"  Tracks      : {len(imported)}"
        )


        for (
            position,
            track_artist,
            track_title,
            duration
        ) in imported:


            if duration:

                print(
                    f"    {position:<4} "
                    f"{track_artist} - "
                    f"{track_title} "
                    f"[{duration}]"
                )

            else:

                print(
                    f"    {position:<4} "
                    f"{track_artist} - "
                    f"{track_title}"
                )


        print()


        # ====================================================
        # DISCOGS RATE LIMIT
        # ====================================================

        time.sleep(1.1)


    # ========================================================
    # EINDE
    # ========================================================

    print()

    print("=" * 80)

    print("KLAAR")

    print("=" * 80)

    print()


    print(
        f"Releases verwerkt  : {total_releases}"
    )


    print(
        f"Tracks geïmporteerd: {total_tracks}"
    )


    print(
        f"Overgeslagen        : {skipped}"
    )


    print(
        f"API/database fouten : {failed}"
    )


    # ========================================================
    # DATABASE CONTROLE
    # ========================================================

    total_db = conn.execute(
        "SELECT COUNT(*) FROM tracks"
    ).fetchone()[0]


    print()

    print(
        f"Totaal tracks database: {total_db}"
    )

    print()


    conn.close()


# ============================================================
# START
# ============================================================

if __name__ == "__main__":

    main()
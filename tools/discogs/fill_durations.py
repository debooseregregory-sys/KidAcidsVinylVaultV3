import os
import sqlite3
import requests
import time
from datetime import datetime

ROOT = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__),
        "..",
        ".."
    )
)

DB = os.path.join(
    ROOT,
    "data",
    "vinylvault.db"
)

BACKUP_DIR = os.path.join(
    ROOT,
    "data",
    "backup"
)

API_URL = "https://api.discogs.com"

HEADERS = {
    "User-Agent": "KidAcidVinylVaultV3/1.0",
    "Accept": "application/json"
}


# ============================================================
# HELPERS
# ============================================================

def seconds_from_discogs(value):

    if not value:
        return 0

    value = str(value).strip()

    try:

        parts = value.split(":")

        if len(parts) == 2:

            minutes = int(parts[0])
            seconds = int(parts[1])

            return (
                minutes * 60
                + seconds
            )

        if len(parts) == 3:

            hours = int(parts[0])
            minutes = int(parts[1])
            seconds = int(parts[2])

            return (
                hours * 3600
                + minutes * 60
                + seconds
            )

    except Exception:

        return 0

    return 0


def format_duration(seconds):

    if not seconds:
        return ""

    seconds = int(seconds)

    minutes = seconds // 60
    remaining = seconds % 60

    return (
        f"{minutes}:{remaining:02d}"
    )


def normalize(text):

    if text is None:
        return ""

    return " ".join(
        str(text)
        .strip()
        .lower()
        .split()
    )


def make_backup():

    os.makedirs(
        BACKUP_DIR,
        exist_ok=True
    )

    stamp = datetime.now().strftime(
        "%Y%m%d_%H%M%S"
    )

    backup = os.path.join(
        BACKUP_DIR,
        f"vinylvault_before_durations_{stamp}.db"
    )

    source = sqlite3.connect(
        DB
    )

    destination = sqlite3.connect(
        backup
    )

    source.backup(
        destination
    )

    destination.close()
    source.close()

    return backup


# ============================================================
# DISCOGS RELEASE
# ============================================================

def get_release(
    release_id
):

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

        print(
            "HTTP:",
            response.status_code
        )

        if response.status_code == 429:

            retry_after = (
                response.headers.get(
                    "Retry-After"
                )
            )

            try:

                wait = int(
                    retry_after
                )

            except (
                TypeError,
                ValueError
            ):

                wait = 10

            print(
                f"Rate limit. "
                f"Wachten: {wait} seconden..."
            )

            time.sleep(
                wait
            )

            continue

        if response.status_code != 200:

            return None

        try:

            return response.json()

        except Exception:

            return None


# ============================================================
# DISCOGS TRACKS
# ============================================================

def discogs_tracks(
    release
):

    result = {}

    for track in release.get(
        "tracklist",
        []
    ):

        position = normalize(
            track.get(
                "position",
                ""
            )
        )

        title = normalize(
            track.get(
                "title",
                ""
            )
        )

        duration = seconds_from_discogs(
            track.get(
                "duration",
                ""
            )
        )

        if not title:
            continue

        key_position = (
            position,
            title
        )

        result[key_position] = (
            duration,
            track.get(
                "title",
                ""
            )
        )

    return result


# ============================================================
# BESTE MATCH
# ============================================================

def find_discogs_track(
    local_track,
    discogs_map
):

    local_position = normalize(
        local_track["position"]
    )

    local_title = normalize(
        local_track["title"]
    )

    # --------------------------------------------------------
    # 1. Positie + titel
    # --------------------------------------------------------

    key = (
        local_position,
        local_title
    )

    if key in discogs_map:

        return discogs_map[key]

    # --------------------------------------------------------
    # 2. Alleen titel
    # --------------------------------------------------------

    possible = []

    for (
        (
            position,
            title
        ),
        value
    ) in discogs_map.items():

        if title == local_title:

            possible.append(
                value
            )

    if len(possible) == 1:

        return possible[0]

    # --------------------------------------------------------
    # 3. Geen betrouwbare match
    # --------------------------------------------------------

    return None


# ============================================================
# MAIN
# ============================================================

def main():

    print()
    print("=" * 80)
    print(
        "KID ACID'S VINYLVAULT V3"
    )
    print(
        "DISCOGS TRACK DUUR AANVULLEN"
    )
    print("=" * 80)

    print()
    print(
        "Database:"
    )

    print(
        DB
    )

    if not os.path.exists(DB):

        print()
        print(
            "FOUT: DATABASE BESTAAT NIET."
        )

        return

    # --------------------------------------------------------
    # DATABASE
    # --------------------------------------------------------

    conn = sqlite3.connect(
        DB
    )

    conn.row_factory = sqlite3.Row

    cur = conn.cursor()

    # --------------------------------------------------------
    # TRACKS ZONDER DUUR
    # --------------------------------------------------------

    rows = cur.execute("""
        SELECT
            t.id,
            t.release_id,
            t.position,
            t.artist,
            t.title,
            t.duration,

            r.artist AS release_artist,
            r.title AS release_title,
            r.discogs,
            r.year,
            r.storage_code

        FROM tracks t

        JOIN releases r
            ON r.id = t.release_id

        WHERE
            r.discogs IS NOT NULL
            AND TRIM(r.discogs) != ''

            AND (
                t.duration IS NULL
                OR t.duration = 0
            )

        ORDER BY
            t.id
    """).fetchall()

    print()
    print("=" * 80)
    print(
        "TRACKS ZONDER DUUR"
    )
    print("=" * 80)

    print()
    print(
        "Te controleren tracks:",
        len(rows)
    )

    if not rows:

        print()
        print(
            "ALLE TRACKS HEBBEN AL EEN DUUR."
        )

        conn.close()

        return

    # --------------------------------------------------------
    # RELEASES GROEPEREN
    # --------------------------------------------------------

    releases = {}

    for row in rows:

        discogs = str(
            row["discogs"]
        ).strip()

        if discogs not in releases:

            releases[discogs] = []

        releases[discogs].append(
            row
        )

    print(
        "Discogs releases:",
        len(releases)
    )

    # --------------------------------------------------------
    # BACKUP
    # --------------------------------------------------------

    print()
    print("=" * 80)
    print(
        "BACKUP"
    )
    print("=" * 80)

    backup = make_backup()

    print()
    print(
        "Backup:"
    )

    print(
        backup
    )

    # --------------------------------------------------------
    # RESULTATEN
    # --------------------------------------------------------

    checked_releases = 0
    updated = 0
    not_found = 0
    no_duration = 0
    errors = 0

    # --------------------------------------------------------
    # RELEASES CONTROLEREN
    # --------------------------------------------------------

    for discogs_id, local_tracks in releases.items():

        checked_releases += 1

        print()
        print("=" * 80)
        print(
            f"RELEASE {checked_releases}/{len(releases)}"
        )
        print("=" * 80)

        print(
            "Discogs ID:",
            discogs_id
        )

        first = local_tracks[0]

        print(
            "Artist:",
            first["release_artist"]
        )

        print(
            "Release:",
            first["release_title"]
        )

        print(
            "Kastcode:",
            first["storage_code"] or "-"
        )

        # ----------------------------------------------------
        # DISCOGS OPHALEN
        # ----------------------------------------------------

        release = get_release(
            discogs_id
        )

        if release is None:

            print(
                "STATUS: RELEASE KON NIET WORDEN OPGEHAALD"
            )

            errors += 1

            continue

        print(
            "Discogs release:",
            release.get(
                "title",
                ""
            )
        )

        # ----------------------------------------------------
        # DISCOGS TRACK MAP
        # ----------------------------------------------------

        discogs_map = discogs_tracks(
            release
        )

        # ----------------------------------------------------
        # LOKALE TRACKS
        # ----------------------------------------------------

        for local in local_tracks:

            print()
            print(
                "Track:",
                local["position"],
                "|",
                local["title"]
            )

            match = find_discogs_track(
                local,
                discogs_map
            )

            if match is None:

                print(
                    "STATUS: GEEN BETROUWBARE MATCH"
                )

                not_found += 1

                continue

            duration_seconds = match[0]
            discogs_title = match[1]

            if duration_seconds <= 0:

                print(
                    "Discogs titel:",
                    discogs_title
                )

                print(
                    "STATUS: GEEN DUUR OP DISCOGS"
                )

                no_duration += 1

                continue

            duration_text = format_duration(
                duration_seconds
            )

            print(
                "Discogs:",
                discogs_title
            )

            print(
                "Duur:",
                duration_text
            )

            # ------------------------------------------------
            # DATABASE UPDATEN
            # ALLEEN DURATION
            # ------------------------------------------------

            cur.execute("""
                UPDATE tracks

                SET duration = ?

                WHERE id = ?
            """, (
                duration_seconds,
                local["id"]
            ))

            updated += 1

            print(
                "STATUS: DUUR TOEGEVOEGD"
            )

        # ----------------------------------------------------
        # EVEN PAUZE
        # ----------------------------------------------------

        conn.commit()

        time.sleep(
            0.25
        )

    # --------------------------------------------------------
    # EINDE
    # --------------------------------------------------------

    conn.commit()

    conn.close()

    print()
    print("=" * 80)
    print(
        "RESULTAAT"
    )
    print("=" * 80)

    print()
    print(
        "Discogs releases gecontroleerd:",
        checked_releases
    )

    print(
        "Tracks met ontbrekende duur:",
        len(rows)
    )

    print(
        "Duurtijden toegevoegd:",
        updated
    )

    print(
        "Geen betrouwbare trackmatch:",
        not_found
    )

    print(
        "Geen duur beschikbaar op Discogs:",
        no_duration
    )

    print(
        "Release/API fouten:",
        errors
    )

    print()
    print(
        "KASTCODES GEWIJZIGD: NEE"
    )

    print(
        "ARTIESTEN GEWIJZIGD: NEE"
    )

    print(
        "TRACKTITELS GEWIJZIGD: NEE"
    )

    print(
        "TRACKPOSITIES GEWIJZIGD: NEE"
    )

    print()
    print(
        "DATABASE GEWIJZIGD:",
        "JA" if updated else "NEE"
    )

    print()
    print(
        "BACKUP:"
    )

    print(
        backup
    )

    print()
    print("=" * 80)
    print(
        "KLAAR"
    )
    print("=" * 80)


if __name__ == "__main__":

    main()

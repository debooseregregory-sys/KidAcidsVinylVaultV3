import sqlite3
import requests
import time
import re
import os
import shutil
from datetime import datetime

DB = os.path.abspath(r".\data\vinylvault.db")
BACKUP_DIR = os.path.abspath(r".\data\backup")
API = "https://api.discogs.com"

HEADERS = {
    "User-Agent": "KidAcidVinylVaultV3/1.0",
    "Accept": "application/json"
}


def normalize(text):

    if not text:
        return ""

    text = str(text).lower()

    text = re.sub(
        r"[\(\)\[\]\{\},.!?:;\"'/\\_-]",
        " ",
        text
    )

    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text.strip()


def get_json(url, params=None):

    while True:

        try:

            r = requests.get(
                url,
                headers=HEADERS,
                params=params,
                timeout=30
            )

        except Exception as exc:

            print("NETWERKFOUT:", exc)
            return None

        if r.status_code == 429:

            try:
                wait = int(
                    r.headers.get(
                        "Retry-After",
                        "10"
                    )
                )
            except Exception:
                wait = 10

            print(
                f"RATE LIMIT - wachten {wait}s"
            )

            time.sleep(wait)
            continue

        if r.status_code != 200:

            return None

        try:
            return r.json()
        except Exception:
            return None


def search_discogs(artist, track):

    data = get_json(
        f"{API}/database/search",
        {
            "artist": artist,
            "track": track,
            "type": "release",
            "format": "Vinyl"
        }
    )

    if not data:
        return []

    return data.get(
        "results",
        []
    )


def get_release(release_id):

    return get_json(
        f"{API}/releases/{release_id}"
    )


def is_vinyl(release):

    for fmt in release.get(
        "formats",
        []
    ):

        if normalize(
            fmt.get("name", "")
        ) == "vinyl":

            return True

    return False


def discogs_tracks(release):

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

        duration = track.get(
            "duration",
            ""
        ).strip()

        if not title:
            continue

        result.append(
            {
                "position": position,
                "title": title,
                "normalized": normalize(title),
                "duration": duration
            }
        )

    return result


def local_tracks(cur, release_id):

    rows = cur.execute("""
        SELECT id, position, artist, title, duration
        FROM tracks
        WHERE release_id = ?
        ORDER BY id
    """, (
        release_id,
    )).fetchall()

    return rows


def find_best_match(cur, artist, release_id):

    rows = local_tracks(
        cur,
        release_id
    )

    local_titles = [
        normalize(r[3])
        for r in rows
        if normalize(r[3])
    ]

    if not local_titles:
        return None

    anchor = rows[0][3]

    results = search_discogs(
        artist,
        anchor
    )

    candidate_ids = []

    for item in results:

        rid = item.get("id")

        if rid and rid not in candidate_ids:
            candidate_ids.append(rid)

    best = None

    for rid in candidate_ids[:20]:

        release = get_release(
            rid
        )

        if not release:
            continue

        if not is_vinyl(
            release
        ):
            continue

        dtracks = discogs_tracks(
            release
        )

        if not dtracks:
            continue

        d_titles = {
            t["normalized"]
            for t in dtracks
        }

        matched = sum(
            1
            for title in local_titles
            if title in d_titles
        )

        score = matched / len(
            local_titles
        )

        if best is None or score > best["score"]:

            best = {
                "score": score,
                "matched": matched,
                "local_count": len(local_titles),
                "release": release,
                "tracks": dtracks
            }

        time.sleep(0.2)

    return best


def update_release(cur, release_id, release):

    discogs_id = str(
        release.get("id")
    )

    title = release.get(
        "title",
        ""
    )

    year = release.get(
        "year"
    )

    cur.execute("""
        UPDATE releases
        SET
            title = ?,
            discogs = ?,
            year = ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    """, (
        title,
        discogs_id,
        year,
        release_id
    ))


def update_tracks(cur, release_id, release_tracks):

    existing = cur.execute("""
        SELECT id, position, artist, title, duration
        FROM tracks
        WHERE release_id = ?
        ORDER BY id
    """, (
        release_id,
    )).fetchall()

    existing_by_title = {}

    for row in existing:

        key = normalize(
            row[3]
        )

        if key:
            existing_by_title[key] = row

    added = 0
    corrected = 0

    release_artist = ""

    artists = release_tracks

    for track in release_tracks:

        title = track["title"]
        position = track["position"]
        duration = track["duration"]

        key = normalize(
            title
        )

        if key in existing_by_title:

            row = existing_by_title[key]

            track_id = row[0]

            if row[1] != position:

                cur.execute("""
                    UPDATE tracks
                    SET position = ?
                    WHERE id = ?
                """, (
                    position,
                    track_id
                ))

                corrected += 1

            continue

        cur.execute("""
            INSERT INTO tracks
            (
                release_id,
                position,
                artist,
                title,
                duration
            )
            SELECT
                ?,
                ?,
                artist,
                ?,
                ?
            FROM releases
            WHERE id = ?
        """, (
            release_id,
            position,
            title,
            duration,
            release_id
        ))

        added += 1

    return added, corrected


def main():

    print("=" * 80)
    print("KID ACID'S VINYLVAULT V3")
    print("AUTOMATISCHE DISCOGS KOPPELING V1")
    print("=" * 80)

    print()
    print("Database:", DB)

    if not os.path.exists(DB):

        print()
        print("FOUT: database bestaat niet.")
        return

    # --------------------------------------------------------
    # BACKUP
    # --------------------------------------------------------

    os.makedirs(
        BACKUP_DIR,
        exist_ok=True
    )

    stamp = datetime.now().strftime(
        "%Y%m%d_%H%M%S"
    )

    backup = os.path.join(
        BACKUP_DIR,
        f"vinylvault_before_auto_match_{stamp}.db"
    )

    shutil.copy2(
        DB,
        backup
    )

    print()
    print("=" * 80)
    print("BACKUP")
    print("=" * 80)

    print()
    print(backup)

    # --------------------------------------------------------
    # DATABASE
    # --------------------------------------------------------

    conn = sqlite3.connect(
        DB
    )

    cur = conn.cursor()

    releases = cur.execute("""
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
        LIMIT 100000
    """).fetchall()

    print()
    print(
        "Te controleren releases:",
        len(releases)
    )

    strong = 0
    possible = 0
    skipped = 0
    changed = 0

    # --------------------------------------------------------
    # RELEASES
    # --------------------------------------------------------

    for number, row in enumerate(
        releases,
        1
    ):

        release_id = row[0]
        artist = row[1] or ""
        old_title = row[2] or ""
        storage = row[4] or ""

        print()
        print("=" * 80)
        print(
            f"[{number}/{len(releases)}]"
        )

        print(
            "V3 ID    :",
            release_id
        )

        print(
            "Artist   :",
            artist
        )

        print(
            "Titel    :",
            old_title
        )

        print(
            "Kastcode :",
            storage
        )

        if not artist or normalize(artist) == "untitled":

            print(
                "STATUS   : OVERGESLAGEN"
            )

            skipped += 1
            continue

        best = find_best_match(
            cur,
            artist,
            release_id
        )

        if not best:

            print(
                "STATUS   : GEEN MATCH"
            )

            skipped += 1
            continue

        score = best["score"]
        matched = best["matched"]
        local_count = best["local_count"]
        release = best["release"]
        dtracks = best["tracks"]

        print()
        print(
            "Discogs ID :",
            release.get("id")
        )

        print(
            "Release    :",
            release.get("title")
        )

        print(
            "Year       :",
            release.get("year")
        )

        print(
            "Match      :",
            f"{matched}/{local_count}"
        )

        print(
            "Score      :",
            f"{score * 100:.1f}%"
        )

        # ----------------------------------------------------
        # ALLEEN STERKE MATCH
        # ----------------------------------------------------

        if score < 0.90 or matched < 2:

            if score >= 0.60:

                print(
                    "STATUS     : MOGELIJKE MATCH - NIET GEWIJZIGD"
                )

                possible += 1

            else:

                print(
                    "STATUS     : TE ZWAK - NIET GEWIJZIGD"
                )

                skipped += 1

            continue

        print()
        print(
            "STATUS     : STERKE MATCH - KOPPELEN"
        )

        # ----------------------------------------------------
        # RELEASE
        # ----------------------------------------------------

        update_release(
            cur,
            release_id,
            release
        )

        # ----------------------------------------------------
        # TRACKS
        # ----------------------------------------------------

        added, corrected = update_tracks(
            cur,
            release_id,
            dtracks
        )

        print()
        print(
            "Tracks toegevoegd:",
            added
        )

        print(
            "Posities gecorrigeerd:",
            corrected
        )

        print()
        print(
            "Kastcode behouden:",
            storage
        )

        strong += 1
        changed += 1

        conn.commit()

        time.sleep(
            0.5
        )

    # --------------------------------------------------------
    # RESULTAAT
    # --------------------------------------------------------

    print()
    print("=" * 80)
    print("RESULTAAT")
    print("=" * 80)

    print()
    print(
        "Sterke matches verwerkt :",
        strong
    )

    print(
        "Mogelijke matches       :",
        possible
    )

    print(
        "Overgeslagen             :",
        skipped
    )

    print(
        "Releases gewijzigd       :",
        changed
    )

    print()
    print(
        "KASTCODES GEWIJZIGD: NEE"
    )

    print(
        "DATABASE GEWIJZIGD:",
        "JA" if changed else "NEE"
    )

    print()
    print(
        "BACKUP:"
    )

    print(
        backup
    )

    print("=" * 80)

    conn.close()


if __name__ == "__main__":
    main()

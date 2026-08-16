# ============================================================
# KID ACID'S VINYLVAULT V3
# RELEASE COMMIT V3
#
# ECHTE DATABASE COMMIT
#
# REGELS:
# - alleen EXACTE MP3 matches worden gekoppeld
# - GEEN MATCH wordt nooit gekoppeld
# - bestaande koppelingen worden niet gedupliceerd
# - database wordt alleen gewijzigd voor veilige koppelingen
# - Discogs-cover wordt automatisch gedownload
# - bestaande cover wordt niet opnieuw gedownload
# ============================================================

import os
import sys
import sqlite3
import requests
import time
import re
import unicodedata


# ============================================================
# ROOT
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
# COVERS
# ============================================================

COVERS_DIR = os.path.join(
    ROOT,
    "data",
    "covers"
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


# ============================================================
# MATCHING REGELS
# ============================================================

MIN_ARTIST_SCORE = 100
MIN_TITLE_SCORE = 100


# ============================================================
# DATABASE
# ============================================================

def get_connection():

    conn = sqlite3.connect(DB)

    conn.row_factory = sqlite3.Row

    conn.execute(
        "PRAGMA foreign_keys = ON"
    )

    return conn


# ============================================================
# NORMALIZE
# ============================================================

def normalize(value):

    if value is None:
        return ""

    text = str(value)

    text = unicodedata.normalize(
        "NFKD",
        text
    )

    text = "".join(
        char
        for char in text
        if not unicodedata.combining(char)
    )

    text = text.lower()

    text = text.replace(
        "&",
        " and "
    )

    text = re.sub(
        r"[\(\)\[\]\{\}]",
        " ",
        text
    )

    text = re.sub(
        r"[-_/\\.,'\"!?:;]+",
        " ",
        text
    )

    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text.strip()


# ============================================================
# EXACT SCORE
# ============================================================

def score_text(a, b):

    if normalize(a) == normalize(b):

        if normalize(a):
            return 100

    return 0


# ============================================================
# DISCOGS
# ============================================================

def get_discogs_release():

    print()
    print("=" * 80)
    print("DISCOGS RELEASE OPHALEN")
    print("=" * 80)

    print(
        "Release ID:",
        DISCOGS_RELEASE_ID
    )

    while True:

        response = requests.get(
            f"{API_URL}/releases/{DISCOGS_RELEASE_ID}",
            headers=HEADERS,
            timeout=30
        )

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

            print(
                f"Rate limit. Wachten: {wait} sec."
            )

            time.sleep(wait)

            continue

        response.raise_for_status()

        return response.json()


# ============================================================
# COVER BESTAAND CONTROLEREN
# ============================================================

def get_existing_cover():

    conn = get_connection()

    try:

        row = conn.execute(
            """
            SELECT cover
            FROM releases
            WHERE discogs = ?
            """,
            (
                str(DISCOGS_RELEASE_ID),
            )
        ).fetchone()

    finally:

        conn.close()

    if not row:
        return None

    return row["cover"]


# ============================================================
# COVER DOWNLOADEN
# ============================================================

def download_discogs_cover(
    release,
    release_id
):

    print()
    print("=" * 80)
    print("DISCOGS COVER")
    print("=" * 80)

    # --------------------------------------------------------
    # Eerst kijken of er al een cover geregistreerd is
    # --------------------------------------------------------

    existing_cover = get_existing_cover()

    if existing_cover:

        existing_path = existing_cover

        if not os.path.isabs(existing_path):

            existing_path = os.path.join(
                ROOT,
                existing_path
            )

        if os.path.isfile(existing_path):

            print(
                "Cover bestaat al:"
            )

            print(
                existing_cover
            )

            print(
                "ACTIE: NIET OPNIEUW DOWNLOADEN"
            )

            return existing_cover

        print(
            "Coverpad bestaat in database,"
            " maar bestand ontbreekt."
        )

        print(
            "Nieuwe download wordt uitgevoerd."
        )

    # --------------------------------------------------------
    # Discogs images
    # --------------------------------------------------------

    images = release.get(
        "images",
        []
    )

    if not images:

        print(
            "Discogs heeft geen coverafbeelding."
        )

        print(
            "ACTIE: GEEN COVER"
        )

        return None

    # --------------------------------------------------------
    # Zoek bruikbare afbeelding
    # --------------------------------------------------------

    image_url = None

    for image in images:

        uri = image.get(
            "uri"
        )

        if uri:

            image_url = uri

            break

    if not image_url:

        # fallback naar thumbnail
        for image in images:

            uri150 = image.get(
                "uri150"
            )

            if uri150:

                image_url = uri150

                break

    if not image_url:

        print(
            "Discogs image gevonden,"
            " maar geen download-URL."
        )

        return None

    print(
        "Cover URL:"
    )

    print(
        image_url
    )

    # --------------------------------------------------------
    # Cover directory
    # --------------------------------------------------------

    os.makedirs(
        COVERS_DIR,
        exist_ok=True
    )

    # --------------------------------------------------------
    # Bestandsextensie bepalen
    # --------------------------------------------------------

    extension = ".jpg"

    lowered_url = image_url.lower()

    if ".png" in lowered_url:

        extension = ".png"

    elif ".webp" in lowered_url:

        extension = ".webp"

    elif ".jpeg" in lowered_url:

        extension = ".jpeg"

    # --------------------------------------------------------
    # Lokale bestandsnaam
    # --------------------------------------------------------

    filename = (
        f"{release_id}{extension}"
    )

    local_path = os.path.join(
        COVERS_DIR,
        filename
    )

    # --------------------------------------------------------
    # Bestaat bestand al?
    # --------------------------------------------------------

    if os.path.isfile(local_path):

        print(
            "Coverbestand bestaat al:"
        )

        print(
            local_path
        )

    else:

        print(
            "Cover downloaden..."
        )

        try:

            response = requests.get(
                image_url,
                headers={
                    "User-Agent":
                        config.DISCOGS_USER_AGENT
                },
                timeout=30
            )

            response.raise_for_status()

        except requests.RequestException as error:

            print()
            print(
                "FOUT BIJ COVER DOWNLOAD:"
            )

            print(
                error
            )

            return None

        # ----------------------------------------------------
        # Bestand schrijven
        # ----------------------------------------------------

        try:

            with open(
                local_path,
                "wb"
            ) as file:

                file.write(
                    response.content
                )

        except OSError as error:

            print()
            print(
                "FOUT BIJ OPSLAAN COVER:"
            )

            print(
                error
            )

            return None

        print(
            "Cover opgeslagen:"
        )

        print(
            local_path
        )

    # --------------------------------------------------------
    # Relatief pad voor database
    # --------------------------------------------------------

    relative_path = os.path.relpath(
        local_path,
        ROOT
    )

    # Windows naar normale slash
    relative_path = relative_path.replace(
        "\\",
        "/"
    )

    # --------------------------------------------------------
    # Database bijwerken
    # --------------------------------------------------------

    conn = get_connection()

    try:

        cursor = conn.execute(
            """
            UPDATE releases
            SET cover = ?
            WHERE discogs = ?
            """,
            (
                relative_path,
                str(release_id)
            )
        )

        conn.commit()

        updated = cursor.rowcount

    except sqlite3.Error as error:

        conn.rollback()

        print()
        print(
            "FOUT BIJ OPSLAAN COVER IN DATABASE:"
        )

        print(
            error
        )

        return None

    finally:

        conn.close()

    if updated == 0:

        print()
        print(
            "WAARSCHUWING:"
        )

        print(
            "Geen release gevonden om cover aan te koppelen."
        )

        return None

    print()
    print(
        "DATABASE:"
    )

    print(
        "releases.cover =",
        relative_path
    )

    print(
        "COVER COMMIT: OK"
    )

    return relative_path


# ============================================================
# MP3 INDEX
# ============================================================

def load_mp3_index():

    print()
    print("=" * 80)
    print("MP3 DATABASE INLEZEN")
    print("=" * 80)

    conn = get_connection()

    rows = conn.execute(
        """
        SELECT
            id,
            path,
            filename,
            artist,
            title
        FROM mp3_files
        """
    ).fetchall()

    conn.close()

    print(
        "MP3's beschikbaar:",
        len(rows)
    )

    index = {}

    for row in rows:

        artist = normalize(
            row["artist"]
        )

        if not artist:
            continue

        index.setdefault(
            artist,
            []
        ).append(row)

    print(
        "Artiesten met MP3's:",
        len(index)
    )

    return index


# ============================================================
# MATCH MP3
# ============================================================

def find_exact_mp3(
    artist,
    title,
    mp3_index
):

    artist_key = normalize(
        artist
    )

    candidates = mp3_index.get(
        artist_key,
        []
    )

    best = None

    for mp3 in candidates:

        artist_score = score_text(
            artist,
            mp3["artist"]
        )

        title_score = score_text(
            title,
            mp3["title"]
        )

        score = (
            artist_score * 0.5
            +
            title_score * 0.5
        )

        candidate = {
            "mp3": mp3,
            "artist_score": artist_score,
            "title_score": title_score,
            "score": score
        }

        if (
            best is None
            or score > best["score"]
        ):

            best = candidate

    if best is None:
        return None

    if (
        best["artist_score"] >= MIN_ARTIST_SCORE
        and
        best["title_score"] >= MIN_TITLE_SCORE
    ):

        return best

    return best


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
        )

        if name:
            names.append(name)

    if names:
        return ", ".join(names)

    release_artists = (
        release.get("artists")
        or []
    )

    names = []

    for artist in release_artists:

        name = (
            artist.get("name")
            or ""
        )

        if name:
            names.append(name)

    return ", ".join(names)


# ============================================================
# FIND V3 RELEASE
# ============================================================

def get_v3_release():

    conn = get_connection()

    row = conn.execute(
        """
        SELECT *
        FROM releases
        WHERE discogs = ?
        """,
        (
            str(DISCOGS_RELEASE_ID),
        )
    ).fetchone()

    conn.close()

    return row


# ============================================================
# FIND V3 TRACK
# ============================================================

def get_v3_track(
    release_id,
    position,
    artist,
    title
):

    conn = get_connection()

    # --------------------------------------------------------
    # Eerst exacte positie
    # --------------------------------------------------------

    row = conn.execute(
        """
        SELECT *
        FROM tracks
        WHERE release_id = ?
        AND position = ?
        """,
        (
            release_id,
            position
        )
    ).fetchone()

    # --------------------------------------------------------
    # Als positie niet overeenkomt:
    # veilig zoeken op artist + title
    # --------------------------------------------------------

    if row is None:

        rows = conn.execute(
            """
            SELECT *
            FROM tracks
            WHERE release_id = ?
            """,
            (
                release_id,
            )
        ).fetchall()

        wanted_artist = normalize(
            artist
        )

        wanted_title = normalize(
            title
        )

        for candidate in rows:

            if (
                normalize(
                    candidate["artist"]
                )
                == wanted_artist
                and
                normalize(
                    candidate["title"]
                )
                == wanted_title
            ):

                row = candidate

                break

    conn.close()

    return row


# ============================================================
# CHECK EXISTING CONNECTION
# ============================================================

def existing_connection(
    track_id,
    mp3_id
):

    conn = get_connection()

    row = conn.execute(
        """
        SELECT *
        FROM track_mp3
        WHERE track_id = ?
        AND mp3_id = ?
        """,
        (
            track_id,
            mp3_id
        )
    ).fetchone()

    conn.close()

    return row


# ============================================================
# CREATE CONNECTION
# ============================================================

def create_connection(
    track_id,
    mp3_id,
    score
):

    conn = get_connection()

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
                score,
                1,
                0
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
# MAIN
# ============================================================

def main():

    print()
    print("=" * 80)
    print("KID ACID'S VINYLVAULT V3")
    print("EERSTE ECHTE RELEASE COMMIT")
    print("=" * 80)

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
        DISCOGS_RELEASE_ID
    )

    # --------------------------------------------------------
    # Database controleren
    # --------------------------------------------------------

    if not os.path.isfile(DB):

        print()
        print(
            "FOUT: DATABASE BESTAAT NIET"
        )

        return

    # --------------------------------------------------------
    # Discogs
    # --------------------------------------------------------

    release = get_discogs_release()

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

    print(
        "Artist:",
        artist
    )

    print(
        "Release:",
        release.get("title")
    )

    print(
        "Year:",
        release.get("year")
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

    # --------------------------------------------------------
    # V3 release
    # --------------------------------------------------------

    v3_release = get_v3_release()

    if not v3_release:

        print()
        print(
            "FOUT: release bestaat niet in V3."
        )

        print(
            "DATABASE GEWIJZIGD: NEE"
        )

        return

    print()
    print(
        "V3 Release ID:",
        v3_release["id"]
    )

    print(
        "V3 Artist:",
        v3_release["artist"]
    )

    print(
        "V3 Release:",
        v3_release["title"]
    )

    print(
        "V3 Discogs:",
        v3_release["discogs"]
    )

    # --------------------------------------------------------
    # COVER
    # --------------------------------------------------------

    cover_path = download_discogs_cover(
        release,
        DISCOGS_RELEASE_ID
    )

    if cover_path:

        print()
        print(
            "COVER:",
            cover_path
        )

    else:

        print()
        print(
            "COVER: NIET BESCHIKBAAR"
        )

    # --------------------------------------------------------
    # MP3 index
    # --------------------------------------------------------

    mp3_index = load_mp3_index()

    # --------------------------------------------------------
    # Tracks
    # --------------------------------------------------------

    exact = 0
    no_match = 0
    already = 0
    created = 0

    print()
    print("=" * 80)
    print("START COMMIT")
    print("=" * 80)

    for number, item in enumerate(
        release.get("tracklist", []),
        start=1
    ):

        title = (
            item.get("title")
            or ""
        )

        if not title:
            continue

        position = (
            item.get("position")
            or ""
        )

        track_artist = get_track_artist(
            item,
            release
        )

        print()
        print(
            f"[{number}] "
            f"{position} | "
            f"{track_artist} - "
            f"{title}"
        )

        # ----------------------------------------------------
        # Zoek V3 track
        # ----------------------------------------------------

        v3_track = get_v3_track(
            v3_release["id"],
            position,
            track_artist,
            title
        )

        if not v3_track:

            print(
                "V3 TRACK: NIET GEVONDEN"
            )

            print(
                "ACTIE: NIET KOPPELEN"
            )

            no_match += 1

            continue

        print(
            "Track ID:",
            v3_track["id"]
        )

        # ----------------------------------------------------
        # MP3
        # ----------------------------------------------------

        result = find_exact_mp3(
            track_artist,
            title,
            mp3_index
        )

        if result is None:

            print(
                "MP3: GEEN"
            )

            print(
                "STATUS: GEEN MATCH"
            )

            print(
                "ACTIE: NIET KOPPELEN"
            )

            no_match += 1

            continue

        mp3 = result["mp3"]

        print(
            "MP3:",
            f"{mp3['artist']} - {mp3['title']}"
        )

        print(
            "Score:",
            result["score"]
        )

        print(
            "Artiest:",
            result["artist_score"]
        )

        print(
            "Titel:",
            result["title_score"]
        )

        # ----------------------------------------------------
        # ALLEEN EXACT
        # ----------------------------------------------------

        if not (
            result["artist_score"]
            >= MIN_ARTIST_SCORE
            and
            result["title_score"]
            >= MIN_TITLE_SCORE
        ):

            print(
                "STATUS: GEEN MATCH"
            )

            print(
                "ACTIE: NIET KOPPELEN"
            )

            no_match += 1

            continue

        print(
            "STATUS: EXACT"
        )

        exact += 1

        # ----------------------------------------------------
        # Bestaande koppeling
        # ----------------------------------------------------

        existing = existing_connection(
            v3_track["id"],
            mp3["id"]
        )

        if existing:

            print(
                "KOPPELING BESTAAT AL"
            )

            already += 1

            continue

        # ----------------------------------------------------
        # ECHTE DATABASE INSERT
        # ----------------------------------------------------

        success = create_connection(
            v3_track["id"],
            mp3["id"],
            result["score"]
        )

        if success:

            print(
                "ACTIE: KOPPELING AANGEMAAKT"
            )

            created += 1

        else:

            print(
                "ACTIE: KOPPELING NIET AANGEMAAKT"
            )

    # --------------------------------------------------------
    # RESULTAAT
    # --------------------------------------------------------

    print()
    print()
    print("=" * 80)
    print("COMMIT RESULTAAT")
    print("=" * 80)

    print()

    print(
        "Release:",
        release.get("title")
    )

    print(
        "Artist :",
        artist
    )

    print(
        "Discogs:",
        DISCOGS_RELEASE_ID
    )

    print(
        "Cover  :",
        cover_path or "NIET BESCHIKBAAR"
    )

    print()

    print(
        "EXACT              :",
        exact
    )

    print(
        "GEEN MATCH         :",
        no_match
    )

    print(
        "BESTAAND           :",
        already
    )

    print(
        "NIEUWE KOPPELINGEN :",
        created
    )

    print()

    print(
        "DATABASE COMMIT: OK"
    )

    print()
    print("=" * 80)
    print("COMMIT TEST KLAAR")
    print("=" * 80)


# ============================================================
# START
# ============================================================

if __name__ == "__main__":

    main()
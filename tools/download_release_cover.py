# ============================================================
# KID ACID'S VINYLVAULT V3
# DOWNLOAD DISCOGS RELEASE COVER
#
# DOEL:
# - Discogs cover automatisch downloaden
# - Opslaan in data/covers/
# - Pad opslaan in releases.cover
#
# VEILIGHEIDSREGELS:
# - Alleen bestaande V3 release
# - Geen wijzigingen aan tracks
# - Geen wijzigingen aan MP3-koppelingen
# - Bestaande cover wordt niet overschreven
# - Geen cover = database blijft ongewijzigd
# ============================================================

import os
import sys
import sqlite3
import requests
import time


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
# COVER MAP
# ============================================================

COVER_DIR = os.path.join(
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
# DATABASE CONNECTION
# ============================================================

def get_connection():

    conn = sqlite3.connect(DB)

    conn.row_factory = sqlite3.Row

    return conn


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

    while True:

        response = requests.get(
            f"{API_URL}/releases/{release_id}",
            headers=HEADERS,
            timeout=30
        )

        if response.status_code == 429:

            retry_after = response.headers.get(
                "Retry-After"
            )

            try:
                wait = int(retry_after)
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

    conn = get_connection()

    row = conn.execute(
        """
        SELECT
            id,
            artist,
            title,
            label,
            catalog,
            year,
            discogs,
            cover
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
# BESTANDSNAAM VEILIG MAKEN
# ============================================================

def safe_filename(text):

    if not text:
        return "release"

    result = str(text)

    invalid = '<>:"/\\|?*'

    for char in invalid:
        result = result.replace(
            char,
            "_"
        )

    result = result.strip()

    if not result:
        result = "release"

    return result


# ============================================================
# COVER URL
# ============================================================

def get_cover_url(release):

    images = release.get(
        "images",
        []
    )

    if not images:
        return None

    # Eerst proberen we primary.
    for image in images:

        if image.get("type") == "primary":

            uri = (
                image.get("uri")
                or image.get("uri150")
            )

            if uri:
                return uri

    # Fallback naar eerste afbeelding.
    for image in images:

        uri = (
            image.get("uri")
            or image.get("uri150")
        )

        if uri:
            return uri

    return None


# ============================================================
# COVER DOWNLOADEN
# ============================================================

def download_cover(
    release,
    v3_release
):

    release_id = release.get(
        "id"
    )

    artist = v3_release["artist"] or ""
    title = v3_release["title"] or ""

    cover_url = get_cover_url(
        release
    )

    if not cover_url:

        print()
        print(
            "GEEN COVER BESCHIKBAAR OP DISCOGS"
        )

        return None

    print()
    print(
        "Cover URL:"
    )

    print(
        cover_url
    )

    os.makedirs(
        COVER_DIR,
        exist_ok=True
    )

    filename = (
        f"{release_id}_"
        f"{safe_filename(artist)}_"
        f"{safe_filename(title)}.jpg"
    )

    filepath = os.path.join(
        COVER_DIR,
        filename
    )

    # --------------------------------------------------------
    # Bestaand bestand
    # --------------------------------------------------------

    if os.path.isfile(filepath):

        print()
        print(
            "COVER BESTAAT AL:"
        )

        print(
            filepath
        )

        return filepath

    # --------------------------------------------------------
    # Download
    # --------------------------------------------------------

    print()
    print(
        "COVER DOWNLOADEN..."
    )

    try:

        response = requests.get(
            cover_url,
            headers=HEADERS,
            timeout=30
        )

    except requests.RequestException as error:

        print()
        print(
            "DOWNLOAD FOUT:"
        )

        print(
            error
        )

        return None

    if response.status_code != 200:

        print()
        print(
            "COVER DOWNLOAD FOUT:",
            response.status_code
        )

        return None

    if not response.content:

        print()
        print(
            "COVER IS LEEG"
        )

        return None

    try:

        with open(
            filepath,
            "wb"
        ) as file:

            file.write(
                response.content
            )

    except OSError as error:

        print()
        print(
            "BESTAND OPSLAAN MISLUKT:"
        )

        print(
            error
        )

        return None

    print()
    print(
        "COVER OPGESLAGEN:"
    )

    print(
        filepath
    )

    print(
        "Grootte:",
        len(response.content),
        "bytes"
    )

    return filepath


# ============================================================
# DATABASE BIJWERKEN
# ============================================================

def update_cover(
    release_id,
    cover_path
):

    conn = get_connection()

    try:

        # Alleen cover bijwerken.
        # Andere releasevelden worden niet aangeraakt.

        cursor = conn.execute(
            """
            UPDATE releases
            SET cover = ?
            WHERE discogs = ?
            """,
            (
                cover_path,
                str(release_id)
            )
        )

        conn.commit()

        if cursor.rowcount == 0:

            print()
            print(
                "WAARSCHUWING:"
            )

            print(
                "Geen release bijgewerkt."
            )

            return False

        return True

    except Exception:

        conn.rollback()

        raise

    finally:

        conn.close()


# ============================================================
# MAIN
# ============================================================

def main():

    print()
    print("=" * 80)
    print("KID ACID'S VINYLVAULT V3")
    print("DISCOGS COVER DOWNLOADER")
    print("=" * 80)

    print()
    print(
        "Database:"
    )

    print(
        DB
    )

    if not os.path.isfile(DB):

        print()
        print(
            "FOUT: DATABASE NIET GEVONDEN"
        )

        return

    # --------------------------------------------------------
    # RELEASE ID
    # --------------------------------------------------------

    release_input = input(
        "\nDiscogs Release ID: "
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
    # V3 RELEASE
    # --------------------------------------------------------

    v3_release = get_v3_release(
        release_id
    )

    if not v3_release:

        print()
        print(
            "FOUT:"
        )

        print(
            "Release bestaat niet in V3."
        )

        print(
            "DATABASE GEWIJZIGD: NEE"
        )

        return

    print()
    print("=" * 80)
    print("V3 RELEASE")
    print("=" * 80)

    print(
        "ID:",
        v3_release["id"]
    )

    print(
        "Artist:",
        v3_release["artist"]
    )

    print(
        "Title:",
        v3_release["title"]
    )

    print(
        "Discogs:",
        v3_release["discogs"]
    )

    print(
        "Huidige cover:",
        v3_release["cover"] or "(leeg)"
    )

    # --------------------------------------------------------
    # DISCOGS
    # --------------------------------------------------------

    release = get_release(
        release_id
    )

    if not release:

        print()
        print(
            "DATABASE GEWIJZIGD: NEE"
        )

        return

    # --------------------------------------------------------
    # CONTROLEREN
    # --------------------------------------------------------

    discogs_title = (
        release.get("title")
        or ""
    )

    print()
    print("=" * 80)
    print("CONTROLE")
    print("=" * 80)

    print(
        "V3:",
        v3_release["artist"],
        "-",
        v3_release["title"]
    )

    print(
        "Discogs:",
        ", ".join(
            artist.get("name", "")
            for artist in release.get(
                "artists",
                []
            )
        ),
        "-",
        discogs_title
    )

    # --------------------------------------------------------
    # COVER
    # --------------------------------------------------------

    cover_path = download_cover(
        release,
        v3_release
    )

    if not cover_path:

        print()
        print(
            "GEEN COVER OPGESLAGEN"
        )

        print(
            "DATABASE GEWIJZIGD: NEE"
        )

        return

    # --------------------------------------------------------
    # DATABASE
    # --------------------------------------------------------

    if v3_release["cover"]:

        print()
        print(
            "DATABASE HEEFT AL EEN COVERPAD."
        )

        print(
            "Geen bestaande cover overschreven."
        )

        print(
            "DATABASE GEWIJZIGD: NEE"
        )

        return

    success = update_cover(
        release_id,
        cover_path
    )

    if not success:

        print()
        print(
            "DATABASE UPDATE MISLUKT"
        )

        return

    # --------------------------------------------------------
    # RESULTAAT
    # --------------------------------------------------------

    print()
    print("=" * 80)
    print("COVER COMMIT RESULTAAT")
    print("=" * 80)

    print()
    print(
        "Release:",
        v3_release["title"]
    )

    print(
        "Artist:",
        v3_release["artist"]
    )

    print(
        "Discogs:",
        release_id
    )

    print(
        "Cover:",
        cover_path
    )

    print()
    print(
        "DATABASE COMMIT: OK"
    )

    print()
    print("=" * 80)
    print("COVER KLAAR")
    print("=" * 80)


# ============================================================
# START
# ============================================================

if __name__ == "__main__":

    main()
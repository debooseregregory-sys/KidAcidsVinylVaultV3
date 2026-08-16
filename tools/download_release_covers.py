# ============================================================
# KID ACID'S VINYLVAULT V3
# DOWNLOAD RELEASE COVERS
#
# REGELS:
# - Gebruikt bestaande Discogs ID uit releases.discogs
# - Alleen releases zonder cover worden verwerkt
# - Bestaande covers worden NOOIT overschreven
# - Discogs primary image heeft voorkeur
# - Als primary ontbreekt: eerste beschikbare image
# - Geen image = niets wijzigen
# - Download naar covers/
# - releases.cover bevat lokaal bestandspad
# ============================================================

import os
import sys
import sqlite3
import time
import requests


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

COVER_DIR = os.path.join(
    ROOT,
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
# SETTINGS
# ============================================================

REQUEST_DELAY = 1.2


# ============================================================
# DATABASE
# ============================================================

def get_connection():

    conn = sqlite3.connect(DB)

    conn.row_factory = sqlite3.Row

    return conn


# ============================================================
# GET RELEASES
# ============================================================

def get_releases():

    conn = get_connection()

    rows = conn.execute(
        """
        SELECT
            id,
            artist,
            title,
            discogs,
            cover
        FROM releases
        WHERE discogs IS NOT NULL
        AND TRIM(discogs) != ''
        ORDER BY id
        """
    ).fetchall()

    conn.close()

    return rows


# ============================================================
# GET DISCOGS RELEASE
# ============================================================

def get_discogs_release(
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

        except requests.RequestException as error:

            print(
                "NETWERKFOUT:",
                error
            )

            return None

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
                wait = 5

            print(
                f"RATE LIMIT - "
                f"wachten {wait} sec."
            )

            time.sleep(wait)

            continue

        if response.status_code != 200:

            print(
                "DISCOGS FOUT:",
                response.status_code
            )

            print(
                response.text[:300]
            )

            return None

        try:

            return response.json()

        except ValueError:

            print(
                "FOUT: Discogs gaf geen "
                "geldige JSON terug."
            )

            return None


# ============================================================
# FIND IMAGE
# ============================================================

def find_cover_image(
    release
):

    images = release.get(
        "images",
        []
    )

    if not images:

        return None

    # --------------------------------------------------------
    # Eerst primary
    # --------------------------------------------------------

    for image in images:

        if image.get(
            "type"
        ) == "primary":

            uri = (
                image.get("uri")
                or image.get("uri150")
            )

            if uri:

                return uri

    # --------------------------------------------------------
    # Anders eerste bruikbare image
    # --------------------------------------------------------

    for image in images:

        uri = (
            image.get("uri")
            or image.get("uri150")
        )

        if uri:

            return uri

    return None


# ============================================================
# COVER FILENAME
# ============================================================

def cover_filename(
    release_id
):

    return os.path.join(
        COVER_DIR,
        f"release_{release_id}.jpg"
    )


# ============================================================
# DOWNLOAD COVER
# ============================================================

def download_cover(
    image_url,
    release_id
):

    os.makedirs(
        COVER_DIR,
        exist_ok=True
    )

    destination = cover_filename(
        release_id
    )

    if os.path.isfile(
        destination
    ):

        print(
            "BESTAND BESTAAT AL:"
        )

        print(
            destination
        )

        return destination


    try:

        response = requests.get(
            image_url,
            headers=HEADERS,
            timeout=30
        )

    except requests.RequestException as error:

        print(
            "DOWNLOAD FOUT:",
            error
        )

        return None


    if response.status_code != 200:

        print(
            "COVER DOWNLOAD FOUT:",
            response.status_code
        )

        return None


    content_type = (
        response.headers.get(
            "Content-Type",
            ""
        ).lower()
    )


    if not response.content:

        print(
            "FOUT: lege afbeelding ontvangen."
        )

        return None


    # --------------------------------------------------------
    # Discogs kan jpg/jpeg/png leveren.
    #
    # We slaan alles bewust als .jpg op omdat
    # releases.cover één lokaal coverpad bevat.
    #
    # De ontvangen bytes worden niet geconverteerd.
    # --------------------------------------------------------

    try:

        with open(
            destination,
            "wb"
        ) as file:

            file.write(
                response.content
            )

    except OSError as error:

        print(
            "BESTAND OPSLAAN MISLUKT:",
            error
        )

        return None


    if not os.path.isfile(
        destination
    ):

        print(
            "FOUT: coverbestand bestaat niet."
        )

        return None


    size = os.path.getsize(
        destination
    )

    if size == 0:

        try:
            os.remove(
                destination
            )
        except OSError:
            pass

        print(
            "FOUT: coverbestand is leeg."
        )

        return None


    print(
        "COVER OPGESLAGEN:"
    )

    print(
        destination
    )

    print(
        "Grootte:",
        size,
        "bytes"
    )

    return destination


# ============================================================
# UPDATE DATABASE
# ============================================================

def update_cover(
    release_id,
    cover_path
):

    conn = get_connection()

    conn.execute(
        """
        UPDATE releases
        SET cover = ?
        WHERE id = ?
        """,
        (
            cover_path,
            release_id
        )
    )

    conn.commit()

    changed = conn.total_changes

    conn.close()

    return changed > 0


# ============================================================
# MAIN
# ============================================================

def main():

    print()
    print("=" * 80)
    print("KID ACID'S VINYLVAULT V3")
    print("ALGEMENE RELEASE COVER DOWNLOADER")
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
        "Cover directory:"
    )

    print(
        COVER_DIR
    )


    # ========================================================
    # DATABASE CONTROL
    # ========================================================

    if not os.path.isfile(DB):

        print()
        print(
            "FOUT: DATABASE NIET GEVONDEN"
        )

        return


    # ========================================================
    # RELEASES
    # ========================================================

    releases = get_releases()

    print()
    print(
        "Releases met Discogs ID:",
        len(releases)
    )


    if not releases:

        print()
        print(
            "GEEN RELEASES TE VERWERKEN."
        )

        return


    # ========================================================
    # COUNTERS
    # ========================================================

    existing = 0
    downloaded = 0
    no_cover = 0
    failed = 0


    # ========================================================
    # PROCESS
    # ========================================================

    for number, release in enumerate(
        releases,
        start=1
    ):

        release_db_id = release["id"]
        artist = release["artist"] or ""
        title = release["title"] or ""
        discogs_id = str(
            release["discogs"]
        ).strip()
        current_cover = (
            release["cover"]
            or ""
        ).strip()


        print()
        print("=" * 80)

        print(
            f"[{number}/{len(releases)}]"
        )

        print(
            "V3 ID:",
            release_db_id
        )

        print(
            "Artist:",
            artist
        )

        print(
            "Title:",
            title
        )

        print(
            "Discogs:",
            discogs_id
        )


        # ====================================================
        # BESTAANDE COVER
        # ====================================================

        if current_cover:

            cover_path = current_cover

            if not os.path.isabs(
                cover_path
            ):

                cover_path = os.path.join(
                    ROOT,
                    cover_path
                )

            if os.path.isfile(
                cover_path
            ):

                print(
                    "STATUS: COVER BESTAAT AL"
                )

                existing += 1

                continue

            print(
                "WAARSCHUWING: "
                "database bevat coverpad,"
            )

            print(
                "maar bestand bestaat niet."
            )

            print(
                "Nieuwe cover wordt gezocht."
            )


        # ====================================================
        # DISCOGS
        # ====================================================

        print()
        print(
            "Discogs ophalen..."
        )

        discogs_release = (
            get_discogs_release(
                discogs_id
            )
        )

        if not discogs_release:

            print(
                "STATUS: DISCOGS FOUT"
            )

            failed += 1

            time.sleep(
                REQUEST_DELAY
            )

            continue


        # ====================================================
        # COVER
        # ====================================================

        image_url = find_cover_image(
            discogs_release
        )

        if not image_url:

            print()
            print(
                "GEEN COVER BESCHIKBAAR OP DISCOGS"
            )

            print(
                "STATUS: GEEN COVER"
            )

            no_cover += 1

            time.sleep(
                REQUEST_DELAY
            )

            continue


        print()
        print(
            "Cover URL gevonden:"
        )

        print(
            image_url
        )


        # ====================================================
        # DOWNLOAD
        # ====================================================

        cover_path = download_cover(
            image_url,
            discogs_id
        )

        if not cover_path:

            print(
                "STATUS: DOWNLOAD MISLUKT"
            )

            failed += 1

            time.sleep(
                REQUEST_DELAY
            )

            continue


        # ====================================================
        # DATABASE
        # ====================================================

        if update_cover(
            release_db_id,
            cover_path
        ):

            print()
            print(
                "DATABASE:"
            )

            print(
                "releases.cover =",
                cover_path
            )

            print(
                "STATUS: COVER OPGESLAGEN"
            )

            downloaded += 1

        else:

            print(
                "STATUS: DATABASE UPDATE MISLUKT"
            )

            failed += 1


        time.sleep(
            REQUEST_DELAY
        )


    # ========================================================
    # RESULTAAT
    # ========================================================

    print()
    print()
    print("=" * 80)
    print("COVER DOWNLOAD RESULTAAT")
    print("=" * 80)

    print()

    print(
        "Totaal releases       :",
        len(releases)
    )

    print(
        "Bestaande covers      :",
        existing
    )

    print(
        "Nieuwe covers         :",
        downloaded
    )

    print(
        "Geen cover op Discogs :",
        no_cover
    )

    print(
        "Fouten                :",
        failed
    )

    print()

    print(
        "DATABASE COMMIT: OK"
    )

    print()
    print("=" * 80)
    print("COVER DOWNLOAD KLAAR")
    print("=" * 80)


# ============================================================
# START
# ============================================================

if __name__ == "__main__":

    main()
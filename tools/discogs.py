# ============================================================
# KID ACID'S VINYLVAULT V3
# DISCOGS API
# ============================================================

import sys
import time
from pathlib import Path

import requests


# ============================================================
# PROJECT ROOT
# ============================================================

V3_ROOT = Path(__file__).resolve().parent.parent

if str(V3_ROOT) not in sys.path:
    sys.path.insert(
        0,
        str(V3_ROOT)
    )


# ============================================================
# CONFIG
# ============================================================

try:

    import config

    DISCOGS_USER_AGENT = getattr(
        config,
        "DISCOGS_USER_AGENT",
        "KidAcid-VinylVault-V3/1.0"
    )

except ImportError:

    DISCOGS_USER_AGENT = (
        "KidAcid-VinylVault-V3/1.0"
    )


# ============================================================
# DISCOGS
# ============================================================

API_URL = "https://api.discogs.com"

HEADERS = {
    "User-Agent": DISCOGS_USER_AGENT,
    "Accept": "application/json",
}


# ============================================================
# REQUEST
# ============================================================

def discogs_get(
    url,
    params=None
):

    while True:

        try:

            response = requests.get(
                url,
                params=params,
                headers=HEADERS,
                timeout=30
            )

        except requests.RequestException as exc:

            raise RuntimeError(
                "Kan geen verbinding maken met Discogs.\n\n"
                f"{exc}"
            )


        # ----------------------------------------------------
        # RATE LIMIT
        # ----------------------------------------------------

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

            time.sleep(
                wait
            )

            continue


        # ----------------------------------------------------
        # ERROR
        # ----------------------------------------------------

        if response.status_code != 200:

            raise RuntimeError(
                "Discogs gaf HTTP-status "
                f"{response.status_code}.\n\n"
                f"{response.text[:500]}"
            )


        return response


# ============================================================
# GET RELEASE BY DISCOGS ID
# ============================================================

def get_release(
    release_id
):

    release_id = str(
        release_id or ""
    ).strip()

    if not release_id:

        raise ValueError(
            "Geef een Discogs Release ID in."
        )

    if not release_id.isdigit():

        raise ValueError(
            "Een Discogs Release ID moet een nummer zijn."
        )

    response = discogs_get(
        f"{API_URL}/releases/{release_id}"
    )

    return response.json()


# ============================================================
# RELEASE ARTIST
# ============================================================

def get_release_artist(
    release
):

    artists = release.get(
        "artists",
        []
    )

    names = []

    for artist in artists:

        name = artist.get(
            "name",
            ""
        )

        if name:

            names.append(
                name
            )

    return ", ".join(
        names
    )


# ============================================================
# RELEASE LABEL
# ============================================================

def get_release_label(
    release
):

    labels = release.get(
        "labels",
        []
    )

    names = []

    for label in labels:

        name = label.get(
            "name",
            ""
        )

        if name:

            names.append(
                name
            )

    return ", ".join(
        names
    )


# ============================================================
# RELEASE CATALOG
# ============================================================

def get_release_catalog(
    release
):

    labels = release.get(
        "labels",
        []
    )

    catalogs = []

    for label in labels:

        catalog = label.get(
            "catno",
            ""
        )

        if catalog:

            catalogs.append(
                catalog
            )

    return ", ".join(
        catalogs
    )


# ============================================================
# RELEASE GENRE
# ============================================================

def get_release_genre(
    release
):

    genres = release.get(
        "genres",
        []
    )

    styles = release.get(
        "styles",
        []
    )

    values = []

    for value in genres + styles:

        if value and value not in values:

            values.append(
                value
            )

    return ", ".join(
        values
    )


# ============================================================
# RELEASE COVER
# ============================================================

def get_release_cover(
    release
):

    images = release.get(
        "images",
        []
    )

    if not images:

        return ""

    for image in images:

        if image.get("type") == "primary":

            uri = (
                image.get("uri")
                or image.get("uri150")
                or ""
            )

            if uri:

                return uri

    first = images[0]

    return (
        first.get("uri")
        or first.get("uri150")
        or ""
    )


# ============================================================
# RELEASE DATA FOR VINYLVAULT
# ============================================================

def get_release_data(
    release
):

    release_id = release.get(
        "id"
    )

    artist = get_release_artist(
        release
    )

    title = release.get(
        "title",
        ""
    )

    label = get_release_label(
        release
    )

    catalog = get_release_catalog(
        release
    )

    year = release.get(
        "year"
    )

    genre = get_release_genre(
        release
    )

    country = release.get(
        "country",
        ""
    )

    cover = get_release_cover(
        release
    )

    discogs_link = ""

    if release_id:

        discogs_link = (
            f"https://www.discogs.com/release/"
            f"{release_id}"
        )

    return {
        "discogs": (
            str(release_id)
            if release_id
            else ""
        ),

        "artist": artist,

        "title": title,

        "label": label,

        "catalog": catalog,

        "year": year,

        "genre": genre,

        "country": country,

        "cover": cover,

        "discogs_link": discogs_link,

        "release": release
    }


# ============================================================
# GET RELEASE DATA BY ID
# ============================================================

def fetch_release_data(
    release_id
):

    release = get_release(
        release_id
    )

    return get_release_data(
        release
    )


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    print()
    print("=" * 70)
    print("VINYLVAULT V3 - DISCOGS TEST")
    print("=" * 70)

    release_id = input(
        "\nDiscogs Release ID: "
    ).strip()

    try:

        data = fetch_release_data(
            release_id
        )

        print()
        print(
            "Release gevonden:"
        )

        print(
            "Discogs ID:",
            data["discogs"]
        )

        print(
            "Artist:",
            data["artist"]
        )

        print(
            "Title:",
            data["title"]
        )

        print(
            "Label:",
            data["label"]
        )

        print(
            "Catalog:",
            data["catalog"]
        )

        print(
            "Year:",
            data["year"]
        )

        print(
            "Genre:",
            data["genre"]
        )

        print(
            "Country:",
            data["country"]
        )

        print(
            "Cover:",
            data["cover"]
        )

        print(
            "Discogs link:",
            data["discogs_link"]
        )

        print()
        print(
            "DISCOGS TEST OK"
        )

    except Exception as exc:

        print()
        print(
            "DISCOGS FOUT:"
        )

        print(
            exc
        )
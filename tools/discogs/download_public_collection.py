import sys
import json
import time
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[2]

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import config


USERNAME = "kid_acid"

API_URL = (
    f"https://api.discogs.com/users/"
    f"{USERNAME}/collection/folders/0/releases"
)

OUTPUT = ROOT / "data" / "discogs_public_collection.json"

PER_PAGE = 100

# Rustig genoeg om Discogs niet meteen opnieuw met 429 te laten antwoorden.
NORMAL_DELAY = 2.0
RETRY_DELAY = 15.0
MAX_RETRIES = 12

session = requests.Session()

session.headers.update({
    "User-Agent": config.DISCOGS_USER_AGENT,
    "Accept": "application/json",
})

# Je bestaande config.py wordt gebruikt.
PARAMS_BASE = {
    "key": config.DISCOGS_CONSUMER_KEY,
    "secret": config.DISCOGS_CONSUMER_SECRET,
}


def save_data(items):
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)

    temp_file = OUTPUT.with_suffix(".tmp")

    with open(
        temp_file,
        "w",
        encoding="utf-8"
    ) as f:
        json.dump(
            items,
            f,
            ensure_ascii=False,
            indent=2
        )

    temp_file.replace(OUTPUT)


def download_page(page):

    retries = 0

    while retries < MAX_RETRIES:

        params = dict(PARAMS_BASE)

        params["page"] = page
        params["per_page"] = PER_PAGE

        try:

            response = session.get(
                API_URL,
                params=params,
                timeout=60
            )

        except requests.RequestException as exc:

            retries += 1

            print()
            print(
                f"Netwerkfout op pagina {page}: {exc}"
            )

            print(
                f"Opnieuw proberen "
                f"({retries}/{MAX_RETRIES})..."
            )

            time.sleep(RETRY_DELAY)

            continue

        if response.status_code == 200:

            try:
                return response.json()

            except ValueError:

                print()
                print(
                    "FOUT: Discogs stuurde geen geldige JSON."
                )

                print(
                    response.text[:500]
                )

                return None

        if response.status_code == 429:

            retries += 1

            print()
            print(
                f"HTTP 429 op pagina {page}"
            )

            print(
                f"Discogs vraagt ons te wachten."
            )

            print(
                f"Wacht {RETRY_DELAY} seconden..."
            )

            print(
                f"Nieuwe poging "
                f"({retries}/{MAX_RETRIES})"
            )

            time.sleep(RETRY_DELAY)

            continue

        print()
        print(
            f"HTTP-fout {response.status_code} "
            f"op pagina {page}"
        )

        print(
            response.text[:500]
        )

        return None

    print()
    print(
        f"Pagina {page} kon na "
        f"{MAX_RETRIES} pogingen niet worden opgehaald."
    )

    return None


def main():

    print()
    print("=" * 78)
    print("KID ACID'S VINYLVAULT V3")
    print("OPENBARE DISCOGS COLLECTIE DOWNLOAD")
    print("=" * 78)
    print()

    print("Gebruiker :", USERNAME)
    print("Bron      :", API_URL)
    print("Opslag    :", OUTPUT)
    print()

    all_releases = []

    page = 1
    total_pages = None

    while True:

        print(
            f"Pagina {page}"
            + (
                f"/{total_pages}"
                if total_pages
                else ""
            )
            + " ophalen..."
        )

        data = download_page(page)

        if data is None:

            print()
            print("=" * 78)
            print("DOWNLOAD ONDERBROKEN")
            print("=" * 78)

            print(
                f"Tot nu toe opgeslagen: "
                f"{len(all_releases)} releases"
            )

            save_data(all_releases)

            print()
            print(
                "De reeds opgehaalde gegevens zijn opgeslagen."
            )

            print(
                "Bestand:"
            )

            print(
                OUTPUT
            )

            return

        releases = data.get(
            "releases",
            []
        )

        pagination = data.get(
            "pagination",
            {}
        )

        if total_pages is None:

            total_pages = pagination.get(
                "pages",
                1
            )

            total_items = pagination.get(
                "items",
                0
            )

            print()
            print(
                f"Totale openbare collectie volgens Discogs: "
                f"{total_items}"
            )

            print(
                f"Pagina's: {total_pages}"
            )

            print()

        if not releases:

            break

        all_releases.extend(releases)

        print(
            f"  + {len(releases)} releases"
        )

        print(
            f"  Totaal lokaal: "
            f"{len(all_releases)}"
        )

        # Na iedere pagina opslaan.
        save_data(all_releases)

        if page >= total_pages:

            break

        page += 1

        time.sleep(NORMAL_DELAY)

    print()
    print("=" * 78)
    print("DOWNLOAD KLAAR")
    print("=" * 78)
    print()

    print(
        "TOTAAL OPENBARE COLLECTIE:",
        len(all_releases)
    )

    # Kleine statistieken.
    vinyl = 0
    cds = 0
    other = 0

    for item in all_releases:

        basic = (
            item.get(
                "basic_information",
                {}
            )
            or {}
        )

        formats = (
            basic.get(
                "formats",
                []
            )
            or []
        )

        format_text = " ".join(
            str(x.get("name", ""))
            for x in formats
        ).lower()

        if "vinyl" in format_text:

            vinyl += 1

        elif (
            "cd" in format_text
            or "compact disc" in format_text
        ):

            cds += 1

        else:

            other += 1

    print(
        "Vinyl:",
        vinyl
    )

    print(
        "CD:",
        cds
    )

    print(
        "Andere:",
        other
    )

    print()
    print(
        "OPGESLAGEN IN:"
    )

    print(
        OUTPUT
    )

    print()

    print(
        "Deze lokale kopie kunnen we daarna gebruiken"
    )

    print(
        "als referentie voor de 839 releases zonder Discogs-ID."
    )

    print()


if __name__ == "__main__":
    main()

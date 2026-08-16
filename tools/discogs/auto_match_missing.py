import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

import sqlite3
import time
import requests
import config

DB_PATH = config.DB_PATH
API_URL = "https://api.discogs.com/database/search"

HEADERS = {
    "User-Agent": config.DISCOGS_USER_AGENT
}

# Alleen normale releases:
# Various Artists worden bewust overgeslagen.
MIN_SCORE = 80
DELAY = 1.2


def normalize(value):
    if not value:
        return ""

    value = str(value).lower()

    for char in "-_/.,()[]{}'\"":
        value = value.replace(char, " ")

    return " ".join(value.split())


def score_release(local_artist, local_title, result):
    artist = normalize(local_artist)
    title = normalize(local_title)

    result_title = normalize(result.get("title", ""))

    score = 0

    # --------------------------------------------------------
    # Titel
    # --------------------------------------------------------

    if title and title == result_title:
        score += 60

    elif title and (
        title in result_title
        or result_title in title
    ):
        score += 40

    # --------------------------------------------------------
    # Artiest
    # --------------------------------------------------------

    if artist:
        result_artist = result_title

        # Discogs search title is meestal:
        # Artist - Title
        if " - " in result.get("title", ""):
            result_artist = normalize(
                result.get("title", "").split(" - ", 1)[0]
            )

        if artist == result_artist:
            score += 40

        elif artist in result_artist:
            score += 25

    return score


def search_discogs(artist, title):
    params = {
        "q": f"{artist} {title}",
        "type": "release",
        "key": config.DISCOGS_CONSUMER_KEY,
        "secret": config.DISCOGS_CONSUMER_SECRET,
        "per_page": 5,
        "page": 1
    }

    try:
        response = requests.get(
            API_URL,
            params=params,
            headers=HEADERS,
            timeout=20
        )

    except requests.RequestException as exc:
        print("API FOUT:", exc)
        return []

    if response.status_code != 200:
        print(
            "HTTP FOUT:",
            response.status_code
        )
        return []

    try:
        data = response.json()

    except ValueError:
        print("Ongeldige Discogs JSON")
        return []

    return data.get("results", [])


def main():

    db = sqlite3.connect(DB_PATH)

    rows = db.execute(
        """
        SELECT
            id,
            artist,
            title
        FROM releases
        WHERE
            (discogs = '' OR discogs IS NULL)
            AND artist != ''
            AND title != ''
            AND lower(artist) != 'various artists'
        ORDER BY id
        """
    ).fetchall()

    db.close()

    total = len(rows)

    print()
    print("=" * 70)
    print("DISCOGS AUTO MATCH - DRY RUN")
    print("=" * 70)
    print()
    print("Te controleren releases:", total)
    print("Various Artists: overgeslagen")
    print("Database wijzigen: NEE")
    print()

    if total == 0:
        print("Geen releases te controleren.")
        return

    exact = 0
    possible = 0
    no_match = 0
    errors = 0

    for number, row in enumerate(rows, 1):

        release_id = row[0]
        artist = row[1]
        title = row[2]

        print()
        print(
            f"[{number}/{total}] "
            f"V3 #{release_id}"
        )
        print(
            f"  {artist} - {title}"
        )

        results = search_discogs(
            artist,
            title
        )

        if not results:

            print("  GEEN RESULTAAT")
            no_match += 1

            time.sleep(DELAY)
            continue

        scored = []

        for result in results:

            score = score_release(
                artist,
                title,
                result
            )

            scored.append(
                (
                    score,
                    result
                )
            )

        scored.sort(
            key=lambda x: x[0],
            reverse=True
        )

        best_score, best = scored[0]

        print()
        print("  Kandidaten:")

        for score, result in scored[:3]:

            print(
                f"    {score:3}% | "
                f"{result.get('id')} | "
                f"{result.get('title')} | "
                f"{result.get('catno', '')}"
            )

        print()

        if best_score >= 95:

            print(
                "  >>> STERKE MATCH"
            )

            exact += 1

        elif best_score >= MIN_SCORE:

            print(
                "  >>> MOGELIJKE MATCH"
            )

            possible += 1

        else:

            print(
                "  >>> TE ZWAK"
            )

            no_match += 1

        time.sleep(DELAY)

    print()
    print("=" * 70)
    print("RESULTAAT DRY-RUN")
    print("=" * 70)
    print()
    print(
        "Sterke matches :",
        exact
    )
    print(
        "Mogelijke matches:",
        possible
    )
    print(
        "Geen/zwakke match:",
        no_match
    )
    print(
        "Fouten:",
        errors
    )
    print()
    print("DATABASE GEWIJZIGD: NEE")
    print("=" * 70)


if __name__ == "__main__":
    main()

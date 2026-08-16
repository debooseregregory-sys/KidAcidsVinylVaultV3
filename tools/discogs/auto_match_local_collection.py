import json
import sqlite3
import re
import unicodedata
from pathlib import Path
from difflib import SequenceMatcher

ROOT = Path(__file__).resolve().parents[2]
DB = ROOT / "data" / "vinylvault.db"
JSON_FILE = ROOT / "data" / "discogs_public_collection.json"

LIMIT = 839


# ============================================================
# NORMALISEREN
# ============================================================

def normalize(value):
    if value is None:
        return ""

    value = str(value).lower().strip()

    value = unicodedata.normalize("NFKD", value)
    value = "".join(
        c for c in value
        if not unicodedata.combining(c)
    )

    value = value.replace("&", " and ")

    value = re.sub(r"\bfeat\.?\b", " ", value)
    value = re.sub(r"\bfeaturing\b", " ", value)
    value = re.sub(r"\bpres\.?\b", " ", value)
    value = re.sub(r"\bvs\.?\b", " ", value)

    value = re.sub(r"\bep\b", " ", value)
    value = re.sub(r"\b12['\"]?\b", " ", value)

    value = re.sub(r"[^a-z0-9]+", " ", value)

    return " ".join(value.split())


def similarity(a, b):
    a = normalize(a)
    b = normalize(b)

    if not a or not b:
        return 0.0

    if a == b:
        return 100.0

    return SequenceMatcher(None, a, b).ratio() * 100


# ============================================================
# ARTIEST VERGELIJKEN
# ============================================================

def artist_score(local_artist, remote_artist):
    """
    Various Artists betekent NIET dat 'Various Artists'
    als echte artiest moet worden gematcht.

    Bij VA releases gebruiken we vooral titel + catalogus.
    """

    local = normalize(local_artist)
    remote = normalize(remote_artist)

    if local in ("various artists", "various", "va"):
        if remote in ("various artists", "various", "va"):
            return 100.0
        return 50.0

    return similarity(local_artist, remote_artist)


# ============================================================
# JSON LADEN
# ============================================================

def load_collection():
    print()
    print("=" * 80)
    print("LOKALE discogs_link COLLECTIE LADEN")
    print("=" * 80)
    print(JSON_FILE)

    if not JSON_FILE.exists():
        raise FileNotFoundError(
            f"JSON niet gevonden:\n{JSON_FILE}"
        )

    with open(JSON_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Verschillende mogelijke JSON-structuren ondersteunen
    if isinstance(data, list):
        items = data

    elif isinstance(data, dict):
        if isinstance(data.get("releases"), list):
            items = data["releases"]

        elif isinstance(data.get("collection"), list):
            items = data["collection"]

        elif isinstance(data.get("items"), list):
            items = data["items"]

        else:
            # Zoek automatisch eerste grote lijst
            items = None

            for value in data.values():
                if isinstance(value, list) and value:
                    if isinstance(value[0], dict):
                        items = value
                        break

            if items is None:
                raise ValueError(
                    "Kan geen releases-lijst vinden in de JSON."
                )
    else:
        raise ValueError("Onbekende JSON structuur.")

    print(f"JSON records: {len(items)}")

    return items


# ============================================================
# discogs_link RECORD UITLEZEN
# ============================================================

def get_remote_release(item):
    """
    Probeert verschillende discogs_link JSON structuren.
    """

    basic = item.get("basic_information", item)

    if not isinstance(basic, dict):
        basic = item

    discogs_id = (
        item.get("id")
        or basic.get("id")
        or item.get("release_id")
    )

    title = (
        basic.get("title")
        or item.get("title")
        or ""
    )

    catalog = (
        basic.get("catno")
        or basic.get("catalog")
        or basic.get("catalog_number")
        or item.get("catno")
        or item.get("catalog")
        or ""
    )

    formats = basic.get("formats") or item.get("formats") or []

    format_name = ""

    if isinstance(formats, list) and formats:
        first = formats[0]

        if isinstance(first, dict):
            format_name = first.get("name", "")

    artists = (
        basic.get("artists")
        or item.get("artists")
        or []
    )

    artist_names = []

    if isinstance(artists, list):
        for artist in artists:
            if isinstance(artist, dict):
                name = artist.get("name")

                if name:
                    artist_names.append(str(name))

            elif artist:
                artist_names.append(str(artist))

    artist = ", ".join(artist_names)

    if not artist:
        artist = basic.get("artist", "") or item.get("artist", "")

    return {
        "id": discogs_id,
        "artist": artist,
        "title": title,
        "catalog": catalog,
        "format": format_name,
    }


# ============================================================
# KANDIDATEN
# ============================================================

def find_candidates(local_artist, local_title, collection):

    results = []

    local_artist_norm = normalize(local_artist)
    local_title_norm = normalize(local_title)

    is_va = local_artist_norm in (
        "various artists",
        "various",
        "va",
    )

    for item in collection:

        remote = get_remote_release(item)

        if not remote["id"]:
            continue

        remote_title = remote["title"]
        remote_artist = remote["artist"]

        title_score = similarity(
            local_title,
            remote_title
        )

        a_score = artist_score(
            local_artist,
            remote_artist
        )

        # ----------------------------------------------------
        # VA RELEASE
        # ----------------------------------------------------

        if is_va:

            # Bij Various Artists mag de titel zwaar wegen.
            score = (
                title_score * 0.80
                +
                a_score * 0.20
            )

            if title_score >= 70:
                results.append({
                    "score": score,
                    "id": remote["id"],
                    "artist": remote_artist,
                    "title": remote_title,
                    "catalog": remote["catalog"],
                    "format": remote["format"],
                    "title_score": title_score,
                    "artist_score": a_score,
                })

        # ----------------------------------------------------
        # NORMALE RELEASE
        # ----------------------------------------------------

        else:

            score = (
                title_score * 0.55
                +
                a_score * 0.45
            )

            if title_score >= 55 and a_score >= 45:
                results.append({
                    "score": score,
                    "id": remote["id"],
                    "artist": remote_artist,
                    "title": remote_title,
                    "catalog": remote["catalog"],
                    "format": remote["format"],
                    "title_score": title_score,
                    "artist_score": a_score,
                })

    results.sort(
        key=lambda x: x["score"],
        reverse=True
    )

    # Dubbele discogs_link IDs verwijderen
    unique = []
    seen = set()

    for r in results:

        rid = str(r["id"])

        if rid in seen:
            continue

        seen.add(rid)
        unique.append(r)

    return unique[:5]


# ============================================================
# DATABASE
# ============================================================

def get_columns(conn):

    cur = conn.cursor()

    cur.execute(
        "PRAGMA table_info(vinyl_items)"
    )

    return [
        row[1]
        for row in cur.fetchall()
    ]


def get_missing_releases(conn):

    columns = get_columns(conn)

    if "discogs_link" not in columns:
        raise RuntimeError(
            "Kolom 'discogs_link' bestaat niet in vinyl_items."
        )

    cur = conn.cursor()

    # Probeer alleen records zonder discogs_link ID
    cur.execute("""
        SELECT id, artist, title, catalog
        FROM vinyl_items
        WHERE discogs_link IS NULL
           OR TRIM(discogs_link) = ''
        ORDER BY id
        LIMIT ?
    """, (LIMIT,))

    rows = cur.fetchall()

    return rows


# ============================================================
# HOOFDPROGRAMMA
# ============================================================

def main():

    print("=" * 80)
    print("KID ACID'S VINYL VAULT V3")
    print("LOCAL discogs_link COLLECTION MATCH")
    print("=" * 80)

    print()
    print("DATABASE:")
    print(DB)

    print()
    print("JSON:")
    print(JSON_FILE)

    collection = load_collection()

    conn = sqlite3.connect(DB)

    try:

        rows = get_missing_releases(conn)

        print()
        print("=" * 80)
        print(f"RELEASES ZONDER discogs_link-ID: {len(rows)}")
        print("=" * 80)

        strong = 0
        doubtful = 0
        none = 0

        for index, row in enumerate(rows, 1):

            release_id, artist, title, catalog = row

            print()
            print("-" * 80)
            print(
                f"[{index}/{len(rows)}] "
                f"V3 RELEASE #{release_id}"
            )

            print(
                f"LOKAAL: {artist} - {title}"
            )

            candidates = find_candidates(
                artist,
                title,
                collection
            )

            if not candidates:

                print()
                print("GEEN KANDIDATEN")

                none += 1
                continue

            print()
            print("BESTE KANDIDATEN:")

            best = candidates[0]

            if best["score"] >= 85:
                strong += 1

            elif best["score"] >= 70:
                doubtful += 1

            else:
                none += 1

            for n, candidate in enumerate(
                candidates,
                1
            ):

                print()
                print(
                    f"#{n} "
                    f"Score: {candidate['score']:.1f}"
                )

                print(
                    f"discogs_link ID: "
                    f"{candidate['id']}"
                )

                print(
                    f"Artiest: "
                    f"{candidate['artist']}"
                )

                print(
                    f"Titel: "
                    f"{candidate['title']}"
                )

                print(
                    f"Catalog: "
                    f"{candidate['catalog'] or 'LEEG'}"
                )

                print(
                    f"Titel-score: "
                    f"{candidate['title_score']:.1f}%"
                )

                print(
                    f"Artiest-score: "
                    f"{candidate['artist_score']:.1f}%"
                )

                print(
                    f"Format: "
                    f"{candidate['format'] or 'onbekend'}"
                )

        print()
        print("=" * 80)
        print("RESULTAAT")
        print("=" * 80)

        print(
            f"Te controleren      : {len(rows)}"
        )

        print(
            f"Sterke matches      : {strong}"
        )

        print(
            f"Twijfelgevallen     : {doubtful}"
        )

        print(
            f"Geen betrouwbare   : {none}"
        )

        print()
        print("DRY RUN")
        print("DATABASE IS NIET GEWIJZIGD.")
        print()
        print("BELANGRIJK:")
        print("De discogs_link JSON wordt lokaal gebruikt.")
        print("Er wordt GEEN discogs_link API aangeroepen.")
        print("De CSV/kastcodes worden NIET gewijzigd.")
        print()
        print("=" * 80)

    finally:
        conn.close()


if __name__ == "__main__":
    main()

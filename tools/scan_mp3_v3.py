import sqlite3
import re
from pathlib import Path
from difflib import SequenceMatcher

# ============================================================
# KID ACID'S VINYLVAULT V3
# MP3 MATCHING TEST
#
# BELANGRIJK:
# Deze versie wijzigt NIETS aan de database.
# Hij leest alleen vinyl_items en mp3_files.
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent
DB = BASE_DIR / "data" / "vinylvault.db"


# ============================================================
# INSTELLINGEN
# ============================================================

TEST_ARTIST = "Planetary Assault Systems"

TEST_TITLES = [
    "Booster",
    "Mod",
    "Diesel Drudge",
]

SHOW_CANDIDATES = 5


# ============================================================
# DATABASE
# ============================================================

def connect_db():
    return sqlite3.connect(DB)


# ============================================================
# TEKST NORMALISEREN
# ============================================================

def normalize_text(text):
    if text is None:
        return ""

    text = str(text).lower().strip()

    text = text.replace("&", " and ")
    text = text.replace("'", "")

    text = re.sub(r"[^a-z0-9]+", " ", text)
    text = re.sub(r"\s+", " ", text).strip()

    return text


# ============================================================
# REMIX / VARIANT HERKENNING
# ============================================================

VARIANT_WORDS = {
    "remix",
    "remastered",
    "remaster",
    "mix",
    "edit",
    "version",
    "dub",
    "instrumental",
    "live",
    "rework",
    "extended",
    "radio",
    "club",
    "original",
    "alternate",
    "alternative",
    "acapella",
    "vip",
    "bootleg",
    "reconstruction",
}


def extract_variant(title):
    if not title:
        return ""

    normalized = normalize_text(title)
    words = normalized.split()

    found = []

    for word in words:
        if word in VARIANT_WORDS:
            found.append(word)

    return " ".join(found)


def remove_variant_words(title):
    if not title:
        return ""

    normalized = normalize_text(title)

    words = normalized.split()

    cleaned = [
        word
        for word in words
        if word not in VARIANT_WORDS
    ]

    return " ".join(cleaned)


# ============================================================
# TITEL SCORE
# ============================================================

def title_similarity(vinyl_title, mp3_title):

    a = normalize_text(vinyl_title)
    b = normalize_text(mp3_title)

    if not a or not b:
        return 0

    if a == b:
        return 100

    variant_a = extract_variant(vinyl_title)
    variant_b = extract_variant(mp3_title)

    base_a = remove_variant_words(vinyl_title)
    base_b = remove_variant_words(mp3_title)

    if base_a == base_b:

        if variant_a == variant_b:
            return 100

        if variant_a != variant_b:
            return 65

    ratio = SequenceMatcher(
        None,
        a,
        b
    ).ratio()

    return round(ratio * 100)


# ============================================================
# ARTIEST SCORE
# ============================================================

def artist_similarity(vinyl_artist, mp3_artist):

    a = normalize_text(vinyl_artist)
    b = normalize_text(mp3_artist)

    if not a or not b:
        return 0

    if a == b:
        return 100

    return round(
        SequenceMatcher(
            None,
            a,
            b
        ).ratio() * 100
    )


# ============================================================
# MATCH SCORE
# ============================================================

def calculate_match(
    vinyl_artist,
    vinyl_title,
    mp3_artist,
    mp3_title
):

    artist_score = artist_similarity(
        vinyl_artist,
        mp3_artist
    )

    title_score = title_similarity(
        vinyl_title,
        mp3_title
    )

    vinyl_variant = extract_variant(vinyl_title)
    mp3_variant = extract_variant(mp3_title)

    # --------------------------------------------------------
    # EXACT
    # --------------------------------------------------------

    if (
        normalize_text(vinyl_artist)
        == normalize_text(mp3_artist)
        and
        normalize_text(vinyl_title)
        == normalize_text(mp3_title)
    ):

        return {
            "score": 100,
            "confidence": "EXACT",
            "action": "KOPPELEN",
            "artist_score": artist_score,
            "title_score": title_score,
        }

    # --------------------------------------------------------
    # ARTIST MOET GOED ZIJN
    # --------------------------------------------------------

    if artist_score < 90:

        score = round(
            (artist_score * 0.40)
            + (title_score * 0.60)
        )

        return {
            "score": score,
            "confidence": "ONVOLDOENDE",
            "action": "NIET KOPPELEN",
            "artist_score": artist_score,
            "title_score": title_score,
        }

    # --------------------------------------------------------
    # ZELFDE BASISNUMMER, ANDERE VARIANT
    # --------------------------------------------------------

    base_vinyl = remove_variant_words(
        vinyl_title
    )

    base_mp3 = remove_variant_words(
        mp3_title
    )

    if (
        base_vinyl
        and base_vinyl == base_mp3
        and vinyl_variant != mp3_variant
    ):

        return {
            "score": 65,
            "confidence": "VARIANT",
            "action": "NIET AUTOMATISCH KOPPELEN",
            "artist_score": artist_score,
            "title_score": title_score,
        }

    # --------------------------------------------------------
    # NORMALE SCORE
    # --------------------------------------------------------

    score = round(
        (artist_score * 0.35)
        + (title_score * 0.65)
    )

    if score >= 92:

        confidence = "ZEER GOED"
        action = "KOPPELEN"

    elif score >= 80:

        confidence = "GOED"
        action = "CONTROLEREN"

    else:

        confidence = "ONVOLDOENDE"
        action = "NIET KOPPELEN"

    return {
        "score": score,
        "confidence": confidence,
        "action": action,
        "artist_score": artist_score,
        "title_score": title_score,
    }


# ============================================================
# MP3'S OPHALEN
# ============================================================

def get_mp3_files(conn):

    rows = conn.execute(
        """
        SELECT
            id,
            artist,
            title,
            path,
            filename
        FROM mp3_files
        """
    ).fetchall()

    return rows


# ============================================================
# VINYL TRACKS OPHALEN
# ============================================================

def get_vinyl_tracks(conn):

    if TEST_TITLES:

        placeholders = ",".join(
            "?" for _ in TEST_TITLES
        )

        query = f"""
            SELECT
                id,
                artist,
                title,
                catalog
            FROM vinyl_items
            WHERE lower(artist) LIKE ?
            AND lower(title) IN ({placeholders})
            ORDER BY title
        """

        params = [
            "%" + TEST_ARTIST.lower() + "%"
        ]

        params.extend(
            title.lower()
            for title in TEST_TITLES
        )

        return conn.execute(
            query,
            params
        ).fetchall()

    return conn.execute(
        """
        SELECT
            id,
            artist,
            title,
            catalog
        FROM vinyl_items
        WHERE lower(artist) LIKE ?
        ORDER BY title
        """,
        (
            "%" + TEST_ARTIST.lower() + "%",
        )
    ).fetchall()


# ============================================================
# BESTE MATCHES
# ============================================================

def find_matches(vinyl, mp3_files):

    vinyl_id, vinyl_artist, vinyl_title, catalog = vinyl

    results = []

    for mp3 in mp3_files:

        mp3_id, mp3_artist, mp3_title, path, filename = mp3

        result = calculate_match(
            vinyl_artist,
            vinyl_title,
            mp3_artist,
            mp3_title
        )

        results.append({
            "mp3": mp3,
            "result": result,
        })

    results.sort(
        key=lambda x: (
            x["result"]["score"],
            x["result"]["title_score"],
            x["result"]["artist_score"],
        ),
        reverse=True
    )

    return results


# ============================================================
# RESULTAAT TONEN
# ============================================================

def print_vinyl_result(vinyl, matches):

    vinyl_id, vinyl_artist, vinyl_title, catalog = vinyl

    print()
    print("=" * 80)
    print("VINYL TRACK")
    print("=" * 80)

    print(
        f"{vinyl_artist} - {vinyl_title}"
    )

    print(
        f"Vinyl ID : {vinyl_id}"
    )

    if catalog:
        print(
            f"Kastcode : {catalog}"
        )

    print()

    if not matches:

        print("GEEN MP3'S GEVONDEN")
        return

    best = matches[0]

    mp3_id, mp3_artist, mp3_title, path, filename = best["mp3"]

    result = best["result"]

    print("=" * 80)
    print("BESTE MP3")
    print("=" * 80)

    print(
        f"{mp3_artist} - {mp3_title}"
    )

    print(
        f"Bestand   : {filename}"
    )

    print(
        f"Pad       : {path}"
    )

    print()
    print(
        f"Score     : {result['score']}"
    )

    print(
        f"Artiest   : {result['artist_score']}"
    )

    print(
        f"Titel     : {result['title_score']}"
    )

    print(
        f"Vertrouwen: {result['confidence']}"
    )

    print(
        f"Actie     : {result['action']}"
    )

    print()

    # --------------------------------------------------------
    # ALTERNATIEVE KANDIDATEN
    # --------------------------------------------------------

    if len(matches) > 1:

        print("-" * 80)
        print(
            f"ALTERNATIEVE KANDIDATEN "
            f"(TOP {SHOW_CANDIDATES})"
        )
        print("-" * 80)

        for number, item in enumerate(
            matches[:SHOW_CANDIDATES],
            start=1
        ):

            (
                mp3_id,
                mp3_artist,
                mp3_title,
                path,
                filename
            ) = item["mp3"]

            r = item["result"]

            print(
                f"{number:02d}. "
                f"{mp3_artist} - {mp3_title}"
            )

            print(
                f"    Score={r['score']} | "
                f"Artiest={r['artist_score']} | "
                f"Titel={r['title_score']} | "
                f"{r['confidence']} | "
                f"{r['action']}"
            )

    print()


# ============================================================
# MAIN
# ============================================================

def main():

    print()
    print("=" * 80)
    print("KID ACID'S VINYLVAULT V3")
    print("MP3 MATCHING TEST")
    print("=" * 80)

    print()
    print("DATABASE:")
    print(DB)

    print()
    print("TEST ARTIST:")
    print(TEST_ARTIST)

    if TEST_TITLES:

        print()
        print("TEST TRACKS:")

        for title in TEST_TITLES:
            print(f" - {title}")

    print()
    print("BELANGRIJK:")
    print("Deze test wijzigt NIETS aan de database.")
    print()

    if not DB.exists():

        print("FOUT: database bestaat niet.")
        print(DB)
        return

    conn = connect_db()

    try:

        print("MP3'S IN DATABASE INLEZEN...")

        mp3_files = get_mp3_files(conn)

        print(
            f"MP3's beschikbaar voor matching: "
            f"{len(mp3_files)}"
        )

        print()
        print("VINYL TRACKS OPHALEN...")

        vinyl_tracks = get_vinyl_tracks(conn)

        print(
            f"Vinyl tracks gevonden: "
            f"{len(vinyl_tracks)}"
        )

        if not vinyl_tracks:

            print()
            print(
                "GEEN TESTTRACKS GEVONDEN."
            )

            print()
            print(
                "Controleer artist/title in vinyl_items."
            )

            return

        total = len(vinyl_tracks)

        print()
        print(
            f"START MATCHING: {total} TRACK(S)"
        )

        for number, vinyl in enumerate(
            vinyl_tracks,
            start=1
        ):

            print()
            print(
                f"[{number}/{total}]"
            )

            matches = find_matches(
                vinyl,
                mp3_files
            )

            print_vinyl_result(
                vinyl,
                matches
            )

        print()
        print("=" * 80)
        print("MATCHING TEST KLAAR")
        print("=" * 80)

        print()
        print("DATABASE GEWIJZIGD: NEE")
        print()

    finally:

        conn.close()


# ============================================================
# START
# ============================================================

if __name__ == "__main__":
    main()
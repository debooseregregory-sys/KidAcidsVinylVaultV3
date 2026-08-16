import sqlite3
import re
from pathlib import Path
from difflib import SequenceMatcher

# ============================================================
# KID ACID'S VINYLVAULT V3
# VOLLEDIGE MATCHING TEST
#
# BELANGRIJK:
#   - DATABASE WORDT NIET GEWIJZIGD
#   - GEEN AUTOMATISCHE KOPPELINGEN
#   - ALLE TRACKS WORDEN GETEST
#
# RESULTATEN:
#   EXACT
#   VARIANT
#   CONTROLEREN
#   GEEN MATCH
#   GEEN MP3 ARTIEST
# ============================================================


# ============================================================
# INSTELLINGEN
# ============================================================

BASE_DIR = Path(__file__).resolve().parent
DB = BASE_DIR / "data" / "vinylvault.db"

SHOW_DETAILS = True

# Zet dit op None voor ALLE tracks.
# Bijvoorbeeld 100 om eerst 100 tracks te testen.
TEST_LIMIT = None


# ============================================================
# VARIANTEN
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


# ============================================================
# DATABASE
# ============================================================

def connect_db():
    return sqlite3.connect(DB)


# ============================================================
# NORMALISEREN
# ============================================================

def normalize_text(text):

    if text is None:
        return ""

    text = str(text).lower().strip()

    text = text.replace("&", " and ")
    text = text.replace("'", "")

    text = re.sub(
        r"[^a-z0-9]+",
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
# VARIANT
# ============================================================

def extract_variant(title):

    words = normalize_text(
        title
    ).split()

    found = []

    for word in words:

        if word in VARIANT_WORDS:
            found.append(word)

    return " ".join(found)


# ============================================================
# BASIS TITEL
# ============================================================

def remove_variant_words(title):

    words = normalize_text(
        title
    ).split()

    result = []

    for word in words:

        if word not in VARIANT_WORDS:
            result.append(word)

    return " ".join(result)


# ============================================================
# TITEL SCORE
# ============================================================

def title_similarity(
    vinyl_title,
    mp3_title
):

    a = normalize_text(
        vinyl_title
    )

    b = normalize_text(
        mp3_title
    )

    if not a or not b:
        return 0

    # EXACT
    if a == b:
        return 100

    vinyl_variant = extract_variant(
        vinyl_title
    )

    mp3_variant = extract_variant(
        mp3_title
    )

    vinyl_base = remove_variant_words(
        vinyl_title
    )

    mp3_base = remove_variant_words(
        mp3_title
    )

    # Zelfde basis
    if vinyl_base == mp3_base:

        # Zelfde variant
        if vinyl_variant == mp3_variant:
            return 100

        # Andere variant
        return 65

    similarity = SequenceMatcher(
        None,
        a,
        b
    ).ratio()

    return round(
        similarity * 100
    )


# ============================================================
# MATCH
# ============================================================

def calculate_match(
    vinyl_artist,
    vinyl_title,
    mp3_artist,
    mp3_title
):

    # --------------------------------------------------------
    # ARTIEST MOET EXACT GELIJK ZIJN
    # --------------------------------------------------------

    if (
        normalize_text(vinyl_artist)
        !=
        normalize_text(mp3_artist)
    ):

        return {
            "score": 0,
            "confidence": "ANDERE ARTIEST",
            "action": "GEEN MATCH",
            "title_score": 0,
        }

    # --------------------------------------------------------
    # TITEL
    # --------------------------------------------------------

    title_score = title_similarity(
        vinyl_title,
        mp3_title
    )

    vinyl_variant = extract_variant(
        vinyl_title
    )

    mp3_variant = extract_variant(
        mp3_title
    )

    vinyl_base = remove_variant_words(
        vinyl_title
    )

    mp3_base = remove_variant_words(
        mp3_title
    )

    # --------------------------------------------------------
    # EXACT
    # --------------------------------------------------------

    if (
        normalize_text(vinyl_title)
        ==
        normalize_text(mp3_title)
    ):

        return {
            "score": 100,
            "confidence": "EXACT",
            "action": "KOPPELEN",
            "title_score": 100,
        }

    # --------------------------------------------------------
    # ZELFDE BASIS, ANDERE VARIANT
    # --------------------------------------------------------

    if (
        vinyl_base
        ==
        mp3_base
        and
        vinyl_variant
        !=
        mp3_variant
    ):

        return {
            "score": 65,
            "confidence": "VARIANT",
            "action": "CONTROLEREN",
            "title_score": title_score,
        }

    # --------------------------------------------------------
    # HOGE GELIJKENIS
    # --------------------------------------------------------

    if title_score >= 92:

        return {
            "score": title_score,
            "confidence": "ZEER GOED",
            "action": "CONTROLEREN",
            "title_score": title_score,
        }

    # --------------------------------------------------------
    # GOEDE GELIJKENIS
    # --------------------------------------------------------

    if title_score >= 80:

        return {
            "score": title_score,
            "confidence": "GOED",
            "action": "CONTROLEREN",
            "title_score": title_score,
        }

    # --------------------------------------------------------
    # GEEN MATCH
    # --------------------------------------------------------

    return {
        "score": title_score,
        "confidence": "ONVOLDOENDE",
        "action": "GEEN MATCH",
        "title_score": title_score,
    }


# ============================================================
# ALLE MP3'S
# ============================================================

def get_mp3_files(conn):

    return conn.execute(
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


# ============================================================
# ALLE VINYL TRACKS
# ============================================================

def get_tracks(conn):

    sql = """
        SELECT
            id,
            release_id,
            position,
            artist,
            title
        FROM tracks
        ORDER BY
            release_id,
            id
    """

    if TEST_LIMIT is not None:

        sql += f"""
            LIMIT {int(TEST_LIMIT)}
        """

    return conn.execute(sql).fetchall()


# ============================================================
# MP3'S PER ARTIEST INDEXEREN
# ============================================================

def build_artist_index(mp3_files):

    artist_index = {}

    for mp3 in mp3_files:

        artist = normalize_text(
            mp3[1]
        )

        if not artist:
            continue

        if artist not in artist_index:
            artist_index[artist] = []

        artist_index[artist].append(
            mp3
        )

    return artist_index


# ============================================================
# MATCH TRACK
# ============================================================

def match_track(
    track,
    artist_index
):

    track_id = track[0]
    release_id = track[1]
    position = track[2]
    artist = track[3]
    title = track[4]

    normalized_artist = normalize_text(
        artist
    )

    artist_mp3s = artist_index.get(
        normalized_artist,
        []
    )

    # --------------------------------------------------------
    # GEEN MP3 ARTIEST
    # --------------------------------------------------------

    if not artist_mp3s:

        return {
            "status": "GEEN MP3 ARTIEST",
            "action": "GEEN MATCH",
            "best": None,
            "candidates": [],
        }

    candidates = []

    for mp3 in artist_mp3s:

        result = calculate_match(
            artist,
            title,
            mp3[1],
            mp3[2]
        )

        candidates.append({
            "mp3": mp3,
            "result": result
        })

    candidates.sort(
        key=lambda item: (
            item["result"]["score"],
            item["result"]["title_score"]
        ),
        reverse=True
    )

    best = candidates[0]

    status = best["result"]["confidence"]

    action = best["result"]["action"]

    if status == "EXACT":

        final_status = "EXACT"

    elif status == "VARIANT":

        final_status = "VARIANT"

    elif status in (
        "ZEER GOED",
        "GOED"
    ):

        final_status = "CONTROLEREN"

    else:

        final_status = "GEEN MATCH"

    return {
        "status": final_status,
        "action": action,
        "best": best,
        "candidates": candidates,
    }


# ============================================================
# DETAIL PRINT
# ============================================================

def print_detail(
    number,
    total,
    track,
    result
):

    track_id = track[0]
    release_id = track[1]
    position = track[2]
    artist = track[3]
    title = track[4]

    print()
    print("-" * 80)

    print(
        f"[{number}/{total}] "
        f"{position} | "
        f"{artist} - {title}"
    )

    print(
        f"Release ID: {release_id} | "
        f"Track ID: {track_id}"
    )

    print(
        f"STATUS: {result['status']}"
    )

    print(
        f"ACTIE : {result['action']}"
    )

    best = result["best"]

    if best is None:

        print(
            "MP3: GEEN MP3'S VAN DEZE ARTIEST"
        )

        return

    mp3 = best["mp3"]
    match = best["result"]

    print(
        f"MP3: {mp3[1]} - {mp3[2]}"
    )

    print(
        f"Score: {match['score']} | "
        f"Titel: {match['title_score']}"
    )

    print(
        f"Bestand: {mp3[4]}"
    )


# ============================================================
# SAMENVATTING
# ============================================================

def print_summary(
    total,
    exact,
    variant,
    controleren,
    geen_match,
    geen_artiest
):

    print()
    print()
    print("=" * 80)
    print("VOLLEDIGE MATCHING TEST - RESULTAAT")
    print("=" * 80)

    print()
    print(
        f"Totaal vinyl tracks : {total}"
    )

    print(
        f"EXACT               : {exact}"
    )

    print(
        f"VARIANT             : {variant}"
    )

    print(
        f"CONTROLEREN         : {controleren}"
    )

    print(
        f"GEEN MATCH          : {geen_match}"
    )

    print(
        f"GEEN MP3 ARTIEST    : {geen_artiest}"
    )

    print()

    if total:

        print(
            f"Exact percentage    : "
            f"{exact / total * 100:.2f}%"
        )

        print(
            f"Match percentage    : "
            f"{(exact + variant + controleren) / total * 100:.2f}%"
        )

    print()
    print("=" * 80)
    print("DATABASE GEWIJZIGD: NEE")
    print("=" * 80)


# ============================================================
# MAIN
# ============================================================

def main():

    print()
    print("=" * 80)
    print("KID ACID'S VINYLVAULT V3")
    print("VOLLEDIGE MP3 MATCHING TEST")
    print("=" * 80)

    print()
    print(
        "DATABASE:"
    )

    print(DB)

    print()
    print(
        "DATABASE WORDT NIET GEWIJZIGD."
    )

    print()

    if not DB.exists():

        print(
            "FOUT: database bestaat niet."
        )

        return

    conn = connect_db()

    try:

        # ----------------------------------------------------
        # MP3'S
        # ----------------------------------------------------

        print(
            "MP3 DATABASE INLEZEN..."
        )

        mp3_files = get_mp3_files(
            conn
        )

        print(
            f"MP3's: {len(mp3_files)}"
        )

        print()

        # ----------------------------------------------------
        # INDEX
        # ----------------------------------------------------

        print(
            "MP3 ARTIEST INDEX MAKEN..."
        )

        artist_index = build_artist_index(
            mp3_files
        )

        print(
            f"Artiesten met MP3's: "
            f"{len(artist_index)}"
        )

        print()

        # ----------------------------------------------------
        # TRACKS
        # ----------------------------------------------------

        print(
            "VINYL TRACKS INLEZEN..."
        )

        tracks = get_tracks(
            conn
        )

        print(
            f"Vinyl tracks: "
            f"{len(tracks)}"
        )

        if not tracks:

            print(
                "GEEN TRACKS GEVONDEN."
            )

            return

        print()

        print(
            "START VOLLEDIGE MATCHING..."
        )

        # ----------------------------------------------------
        # COUNTERS
        # ----------------------------------------------------

        total = 0
        exact = 0
        variant = 0
        controleren = 0
        geen_match = 0
        geen_artiest = 0

        # ----------------------------------------------------
        # MATCHING
        # ----------------------------------------------------

        for number, track in enumerate(
            tracks,
            start=1
        ):

            result = match_track(
                track,
                artist_index
            )

            status = result["status"]

            total += 1

            if status == "EXACT":

                exact += 1

            elif status == "VARIANT":

                variant += 1

            elif status == "CONTROLEREN":

                controleren += 1

            elif status == "GEEN MP3 ARTIEST":

                geen_artiest += 1

            else:

                geen_match += 1

            if SHOW_DETAILS:

                print_detail(
                    number,
                    len(tracks),
                    track,
                    result
                )

        # ----------------------------------------------------
        # SAMENVATTING
        # ----------------------------------------------------

        print_summary(
            total,
            exact,
            variant,
            controleren,
            geen_match,
            geen_artiest
        )

    finally:

        conn.close()


# ============================================================
# START
# ============================================================

if __name__ == "__main__":
    main()
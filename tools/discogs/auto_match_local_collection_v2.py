import sqlite3
import json
import re
import unicodedata
from difflib import SequenceMatcher
from pathlib import Path


# ============================================================
# PADEN
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[2]

DB = BASE_DIR / "data" / "vinylvault.db"
JSON_FILE = BASE_DIR / "data" / "discogs_public_collection.json"


# ============================================================
# INSTELLINGEN
# ============================================================

TEST_LIMIT = 839

STRONG_THRESHOLD = 88.0
MEDIUM_THRESHOLD = 78.0

# Alleen deze velden mogen uiteindelijk automatisch wijzigen:
UPDATE_FIELDS = [
    "discogs",
    "discogs_link",
    "catalog",
]


# ============================================================
# NORMALISATIE
# ============================================================

def normalize(value):
    if value is None:
        return ""

    value = str(value)

    value = unicodedata.normalize("NFKD", value)
    value = "".join(
        c for c in value
        if not unicodedata.combining(c)
    )

    value = value.lower()

    replacements = {
        "&": " and ",
        "+": " and ",
        "/": " ",
        "\\": " ",
        "-": " ",
        "_": " ",
        ".": " ",
        ",": " ",
        ":": " ",
        ";": " ",
        "'": "",
        '"': "",
        "(": " ",
        ")": " ",
        "[": " ",
        "]": " ",
    }

    for old, new in replacements.items():
        value = value.replace(old, new)

    # DJ varianten gelijk trekken
    value = re.sub(r"\bdj\b", "dj", value)

    # EP varianten
    value = re.sub(r"\be\s*p\b", "ep", value)

    # feat varianten
    value = re.sub(r"\bfeaturing\b", "feat", value)
    value = re.sub(r"\bfeat\b", "feat", value)
    value = re.sub(r"\bft\b", "feat", value)

    # pres/presents
    value = re.sub(r"\bpresents\b", "pres", value)
    value = re.sub(r"\bpresent\b", "pres", value)

    # dubbele spaties
    value = re.sub(r"\s+", " ", value).strip()

    return value


def similarity(a, b):
    a = normalize(a)
    b = normalize(b)

    if not a or not b:
        return 0.0

    if a == b:
        return 100.0

    return SequenceMatcher(None, a, b).ratio() * 100.0


# ============================================================
# ARTIESTEN
# ============================================================

def local_artist_variants(artist):
    if not artist:
        return []

    artist = normalize(artist)

    if artist in {
        "various artists",
        "various",
        "va",
        "v a",
    }:
        return []

    parts = re.split(
        r"\s+(?:vs|versus|and|&|feat|pres)\s+",
        artist
    )

    result = []

    for part in parts:
        part = part.strip()

        if part:
            result.append(part)

    result.append(artist)

    return list(dict.fromkeys(result))


def discogs_artist_names(record):
    basic = record.get("basic_information", {})

    artists = basic.get("artists", [])

    names = []

    if isinstance(artists, list):
        for artist in artists:
            if not isinstance(artist, dict):
                continue

            name = artist.get("name")

            if name:
                names.append(normalize(name))

    return names


def artist_score(local_artist, record):
    local = normalize(local_artist)

    # Various Artists = geen artiestvergelijking
    if local in {
        "various artists",
        "various",
        "va",
        "v a",
    }:
        names = discogs_artist_names(record)

        if not names:
            return 100.0

        # Various is alleen een zachte indicator
        return 70.0

    names = discogs_artist_names(record)

    if not names:
        return 0.0

    local_variants = local_artist_variants(local_artist)

    best = 0.0

    for local_variant in local_variants:
        for remote_name in names:
            score = similarity(local_variant, remote_name)

            if score > best:
                best = score

    # Probeer gecombineerde artiesten
    combined = " ".join(names)

    best = max(
        best,
        similarity(local, combined)
    )

    return best


# ============================================================
# TITEL
# ============================================================

def title_score(local_title, record):
    basic = record.get("basic_information", {})

    remote_title = basic.get("title", "")

    return similarity(
        local_title,
        remote_title
    )


# ============================================================
# CATALOGUS
# ============================================================

def get_discogs_catalog(record):
    basic = record.get("basic_information", {})

    labels = basic.get("labels", [])

    catalogs = []

    if isinstance(labels, list):
        for label in labels:
            if not isinstance(label, dict):
                continue

            catno = label.get("catno")

            if catno:
                catalogs.append(str(catno).strip())

    return catalogs


def catalog_normalize(value):
    if not value:
        return ""

    value = normalize(value)

    # Catalogusnummer meestal belangrijker dan spaties
    value = re.sub(r"\s+", "", value)

    return value


def catalog_match(local_catalog, record):
    if not local_catalog:
        return False

    local = catalog_normalize(local_catalog)

    if not local:
        return False

    for remote in get_discogs_catalog(record):
        remote_norm = catalog_normalize(remote)

        if not remote_norm:
            continue

        if local == remote_norm:
            return True

        # Soms staat er extra prefix/suffix
        if (
            local in remote_norm
            or remote_norm in local
        ):
            if min(len(local), len(remote_norm)) >= 4:
                return True

    return False


# ============================================================
# FORMAT
# ============================================================

def discogs_formats(record):
    basic = record.get("basic_information", {})

    formats = basic.get("formats", [])

    result = []

    if isinstance(formats, list):
        for fmt in formats:
            if not isinstance(fmt, dict):
                continue

            name = fmt.get("name")

            if name:
                result.append(normalize(name))

    return result


def format_type(record):
    formats = discogs_formats(record)

    if any("vinyl" in x for x in formats):
        return "Vinyl"

    if any("cd" == x or "cd" in x for x in formats):
        return "CD"

    return "Andere"


# ============================================================
# SCORE
# ============================================================

def calculate_score(local_artist, local_title, local_catalog, record):
    a_score = artist_score(
        local_artist,
        record
    )

    t_score = title_score(
        local_title,
        record
    )

    c_match = catalog_match(
        local_catalog,
        record
    )

    # Titel is belangrijk
    score = (
        t_score * 0.50
        + a_score * 0.40
    )

    # Catalogus exact gevonden = zeer sterke bonus
    if c_match:
        score += 10.0

    return min(score, 100.0), a_score, t_score, c_match


# ============================================================
# JSON LADEN
# ============================================================

def load_json():
    print("=" * 80)
    print("LOKALE DISCOGS COLLECTIE LADEN")
    print("=" * 80)
    print(JSON_FILE)

    with open(
        JSON_FILE,
        "r",
        encoding="utf-8"
    ) as f:
        records = json.load(f)

    if not isinstance(records, list):
        raise RuntimeError(
            "Discogs JSON bevat geen lijst."
        )

    print(f"JSON records: {len(records)}")

    return records


# ============================================================
# DATABASE
# ============================================================

def check_schema(conn):
    cur = conn.cursor()

    cur.execute(
        "PRAGMA table_info(releases)"
    )

    columns = {
        row[1]
        for row in cur.fetchall()
    }

    required = {
        "id",
        "artist",
        "title",
        "catalog",
        "discogs",
        "discogs_link",
        "storage_code",
    }

    missing = required - columns

    if missing:
        raise RuntimeError(
            "Ontbrekende kolommen in releases: "
            + ", ".join(sorted(missing))
        )

    return columns


def get_missing_releases(conn):
    cur = conn.cursor()

    cur.execute(
        """
        SELECT
            id,
            artist,
            title,
            catalog,
            discogs,
            discogs_link,
            storage_code,
            label
        FROM releases
        WHERE discogs IS NULL
           OR TRIM(discogs) = ''
        ORDER BY id
        LIMIT ?
        """,
        (TEST_LIMIT,)
    )

    return cur.fetchall()


# ============================================================
# MATCHEN
# ============================================================

def find_candidates(
    local_artist,
    local_title,
    local_catalog,
    records
):
    candidates = []

    for record in records:
        if not isinstance(record, dict):
            continue

        basic = record.get(
            "basic_information",
            {}
        )

        if not isinstance(basic, dict):
            continue

        remote_id = basic.get("id")

        if not remote_id:
            continue

        score, a_score, t_score, c_match = calculate_score(
            local_artist,
            local_title,
            local_catalog,
            record
        )

        candidates.append({
            "score": score,
            "artist_score": a_score,
            "title_score": t_score,
            "catalog_match": c_match,
            "record": record,
        })

    candidates.sort(
        key=lambda x: x["score"],
        reverse=True
    )

    return candidates[:5]


# ============================================================
# WEERGAVE
# ============================================================

def print_candidate(rank, candidate):
    record = candidate["record"]
    basic = record.get(
        "basic_information",
        {}
    )

    remote_id = basic.get("id", "")

    title = basic.get(
        "title",
        ""
    )

    artists = discogs_artist_names(
        record
    )

    artist_text = ", ".join(
        artists
    )

    catalogs = get_discogs_catalog(
        record
    )

    catalog_text = ", ".join(
        catalogs
    ) if catalogs else "none"

    print(
        f"\n#{rank} Score: "
        f"{candidate['score']:.1f}"
    )

    print(
        f"Discogs ID: {remote_id}"
    )

    print(
        f"Artiest: {artist_text}"
    )

    print(
        f"Titel: {title}"
    )

    print(
        f"Catalog: {catalog_text}"
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
        "Catalog-match: "
        + (
            "JA"
            if candidate["catalog_match"]
            else "NEE"
        )
    )

    print(
        f"Format: {format_type(record)}"
    )


# ============================================================
# MAIN
# ============================================================

def main():
    print()
    print("DATABASE:")
    print(DB)
    print()

    if not DB.exists():
        raise RuntimeError(
            f"Database bestaat niet: {DB}"
        )

    if not JSON_FILE.exists():
        raise RuntimeError(
            f"JSON bestaat niet: {JSON_FILE}"
        )

    records = load_json()

    conn = sqlite3.connect(DB)

    try:
        check_schema(conn)

        rows = get_missing_releases(
            conn
        )

        print()
        print("=" * 80)
        print("MATCH TEST")
        print("=" * 80)
        print(
            f"Releases zonder Discogs-ID: "
            f"{len(rows)}"
        )
        print()
        print(
            "DATABASE WORDT NIET GEWIJZIGD."
        )

        strong = 0
        doubtful = 0
        none = 0
        catalog_matches = 0

        for index, row in enumerate(
            rows,
            1
        ):
            (
                release_id,
                artist,
                title,
                catalog,
                discogs,
                discogs_link,
                storage_code,
                label,
            ) = row

            print()
            print(
                "-" * 80
            )
            print(
                f"[{index}/{len(rows)}] "
                f"V3 RELEASE #{release_id}"
            )

            print(
                f"LOKAAL: "
                f"{artist} - {title}"
            )

            print(
                f"LOKAAL CATALOG: "
                f"{catalog or ''}"
            )

            candidates = find_candidates(
                artist,
                title,
                catalog,
                records
            )

            if not candidates:
                print(
                    "\nGEEN KANDIDATEN GEVONDEN"
                )
                none += 1
                continue

            best = candidates[0]

            if best["catalog_match"]:
                catalog_matches += 1

            if best["score"] >= STRONG_THRESHOLD:
                strong += 1
            elif best["score"] >= MEDIUM_THRESHOLD:
                doubtful += 1
            else:
                none += 1

            print(
                "\nBESTE KANDIDATEN:"
            )

            for rank, candidate in enumerate(
                candidates,
                1
            ):
                print_candidate(
                    rank,
                    candidate
                )

        print()
        print("=" * 80)
        print("KLAAR")
        print("=" * 80)

        print(
            f"Te controleren: {len(rows)}"
        )

        print(
            f"Sterke matches: {strong}"
        )

        print(
            f"Twijfelgevallen: {doubtful}"
        )

        print(
            f"Geen betrouwbare match: {none}"
        )

        print(
            f"Catalogusmatches: "
            f"{catalog_matches}"
        )

        print()
        print("DRY RUN")
        print(
            "DATABASE IS NIET GEWIJZIGD."
        )

    finally:
        conn.close()


if __name__ == "__main__":
    main()

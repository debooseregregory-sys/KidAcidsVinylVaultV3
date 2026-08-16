# ============================================================
# KID ACID'S VINYLVAULT V3
# AUTO DISCogs MATCH - SAFE
# ============================================================
#
# Gebaseerd op de bewezen werkende 10-test.
#
# AUTOMATISCH:
#   STRONG + duidelijke voorsprong -> koppelen
#
# NIET AUTOMATISCH:
#   gelijke/nahe scores
#   POSSIBLE
#   WEAK
#   GEEN RESULTAAT
#
# Alleen:
#   releases.discogs
#   releases.discogs_link
#
# worden aangepast.
#
# Eerst wordt automatisch een database-backup gemaakt.
#
# ============================================================

import sqlite3
import requests
import os
import re
import time
import shutil
from datetime import datetime
from difflib import SequenceMatcher


# ============================================================
# CONFIG
# ============================================================

SCRIPT_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

# Zoek automatisch naar de projectdatabase
DB = None

search_dirs = [
    SCRIPT_DIR,
    os.path.dirname(SCRIPT_DIR),
    os.path.dirname(os.path.dirname(SCRIPT_DIR)),
    os.path.dirname(os.path.dirname(os.path.dirname(SCRIPT_DIR))),
]

for base in search_dirs:

    candidate = os.path.join(
        base,
        "data",
        "vinylvault.db"
    )

    if os.path.exists(candidate):

        DB = os.path.abspath(candidate)

        break


if DB is None:

    DB = os.path.abspath(
        os.path.join(
            SCRIPT_DIR,
            "data",
            "vinylvault.db"
        )
    )


DISCOGS_API = "https://api.discogs.com"

USER_AGENT = (
    "KidAcidVinylVaultV3/1.0 "
    "(Safe Discogs Auto Matcher)"
)

REQUEST_DELAY = 1.1

STRONG_THRESHOLD = 85.0

MINIMUM_GAP = 5.0


# ============================================================
# NORMALIZE
# ============================================================

def normalize(value):

    if value is None:
        return ""

    value = str(value).lower()

    value = value.replace(
        "&",
        "and"
    )

    value = value.replace(
        "’",
        "'"
    )

    value = value.replace(
        "`",
        "'"
    )

    value = re.sub(
        r"[^a-z0-9à-ÿ]+",
        " ",
        value
    )

    value = re.sub(
        r"\s+",
        " ",
        value
    ).strip()

    return value


# ============================================================
# SIMILARITY
# ============================================================

def similarity(a, b):

    a = normalize(a)
    b = normalize(b)

    if not a or not b:

        return 0.0

    if a == b:

        return 1.0

    return SequenceMatcher(
        None,
        a,
        b
    ).ratio()


# ============================================================
# CATALOG SIMILARITY
# ============================================================

def catalog_similarity(
    a,
    b
):

    a = normalize(a)
    b = normalize(b)

    if not a or not b:

        return 0.0

    if a == b:

        return 1.0

    numbers_a = re.sub(
        r"[^0-9]",
        "",
        a
    )

    numbers_b = re.sub(
        r"[^0-9]",
        "",
        b
    )

    if (
        numbers_a
        and numbers_b
    ):

        if (
            numbers_a.lstrip("0")
            ==
            numbers_b.lstrip("0")
        ):

            return 1.0

    return SequenceMatcher(
        None,
        a,
        b
    ).ratio()


# ============================================================
# DATABASE
# ============================================================

def db_connect():

    print()
    print("Database:")
    print(DB)

    if not os.path.exists(DB):

        raise FileNotFoundError(
            f"Database bestaat niet:\n{DB}"
        )

    conn = sqlite3.connect(DB)

    conn.row_factory = sqlite3.Row

    return conn


# ============================================================
# BACKUP
# ============================================================

def create_backup():

    timestamp = datetime.now().strftime(
        "%Y%m%d_%H%M%S"
    )

    backup = os.path.join(
        os.path.dirname(DB),
        f"vinylvault_BEFORE_AUTOMATCH_{timestamp}.db"
    )

    shutil.copy2(
        DB,
        backup
    )

    print()
    print(
        "Database backup:"
    )

    print(
        backup
    )

    return backup


# ============================================================
# COLUMNS
# ============================================================

def get_columns(
    conn,
    table
):

    rows = conn.execute(
        f"PRAGMA table_info({table})"
    ).fetchall()

    return [
        row["name"]
        for row in rows
    ]


# ============================================================
# DISCOGS COLUMN
# ============================================================

def find_discogs_column(
    columns
):

    possible = [
        "discogs",
        "discogs_id",
        "discogs_release_id",
        "release_discogs"
    ]

    for name in possible:

        if name in columns:

            return name

    return None


# ============================================================
# LOAD RELEASES WITH EXACT 1 TRACK
# ============================================================

def load_releases(
    conn
):

    release_columns = get_columns(
        conn,
        "releases"
    )

    track_columns = get_columns(
        conn,
        "tracks"
    )

    discogs_column = find_discogs_column(
        release_columns
    )

    if not discogs_column:

        raise RuntimeError(
            "Geen Discogs kolom gevonden."
        )

    def col(
        name,
        alias
    ):

        if name in release_columns:

            return (
                f"r.{name} AS {alias}"
            )

        return (
            f"NULL AS {alias}"
        )

    sql = f"""
        SELECT
            r.id AS release_id,

            {col(
                "artist",
                "release_artist"
            )},

            {col(
                "title",
                "release_title"
            )},

            {col(
                "label",
                "release_label"
            )},

            {col(
                "catalog",
                "release_catalog"
            )},

            {col(
                "year",
                "release_year"
            )},

            r.{discogs_column}
                AS discogs_id,

            t.id AS track_id,

            t.position AS track_position,

            t.artist AS track_artist,

            t.title AS track_title

        FROM releases r

        JOIN tracks t
            ON t.release_id = r.id

        WHERE r.id IN (

            SELECT release_id

            FROM tracks

            GROUP BY release_id

            HAVING COUNT(*) = 1
        )

        AND (
            r.{discogs_column} IS NULL
            OR TRIM(
                CAST(
                    r.{discogs_column}
                    AS TEXT
                )
            ) = ''
            OR CAST(
                r.{discogs_column}
                AS TEXT
            ) = '0'
        )

        ORDER BY r.id
    """

    rows = conn.execute(
        sql
    ).fetchall()

    return rows, discogs_column


# ============================================================
# SESSION
# ============================================================

def create_session(
    token
):

    session = requests.Session()

    session.headers.update(
        {
            "User-Agent":
                USER_AGENT,

            "Accept":
                "application/json",

            "Authorization":
                f"Discogs token={token}"
        }
    )

    return session


# ============================================================
# SEARCH
# ============================================================

def discogs_search(
    session,
    artist,
    title,
    label=None,
    catalog=None
):

    params = {
        "artist": artist,
        "track": title,
        "type": "release",
        "per_page": 50,
        "page": 1
    }

    if label:

        params["label"] = label

    if catalog:

        params["catno"] = catalog

    try:

        response = session.get(
            f"{DISCOGS_API}/database/search",
            params=params,
            timeout=30
        )

    except requests.RequestException:

        return []

    if response.status_code == 401:

        raise RuntimeError(
            "Discogs token is ongeldig."
        )

    if response.status_code == 429:

        time.sleep(10)

        return discogs_search(
            session,
            artist,
            title,
            label,
            catalog
        )

    if response.status_code != 200:

        return []

    try:

        data = response.json()

    except Exception:

        return []

    time.sleep(
        REQUEST_DELAY
    )

    return data.get(
        "results",
        []
    )


# ============================================================
# SEARCH FALLBACK
# ============================================================

def search_discogs(
    session,
    artist,
    title,
    label,
    catalog
):

    # 1. Artist + track + catalog
    if (
        artist
        and title
        and catalog
    ):

        results = discogs_search(
            session,
            artist,
            title,
            label,
            catalog
        )

        if results:

            return results

    time.sleep(
        REQUEST_DELAY
    )

    # 2. Artist + track
    if (
        artist
        and title
    ):

        results = discogs_search(
            session,
            artist,
            title
        )

        if results:

            return results

    time.sleep(
        REQUEST_DELAY
    )

    # 3. Titel
    if title:

        return discogs_search(
            session,
            "",
            title
        )

    return []


# ============================================================
# RESULT HELPERS
# ============================================================

def result_title(
    result
):

    return str(
        result.get(
            "title",
            ""
        )
    )


def result_artist(
    result
):

    value = result.get(
        "artist",
        ""
    )

    if isinstance(
        value,
        list
    ):

        return " ".join(
            str(x)
            for x in value
        )

    return str(
        value or ""
    )


def result_label(
    result
):

    value = result.get(
        "label",
        []
    )

    if isinstance(
        value,
        list
    ):

        return " ".join(
            str(x)
            for x in value
        )

    return str(
        value or ""
    )


def result_catalog(
    result
):

    value = result.get(
        "catno",
        ""
    )

    if isinstance(
        value,
        list
    ):

        return " ".join(
            str(x)
            for x in value
        )

    return str(
        value or ""
    )


def result_format(
    result
):

    value = result.get(
        "format",
        []
    )

    if isinstance(
        value,
        list
    ):

        return ", ".join(
            str(x)
            for x in value
        )

    return str(
        value or ""
    )


# ============================================================
# SCORE
# ============================================================

def score_result(
    row,
    result
):

    collection_artist = (
        row["track_artist"]
        or row["release_artist"]
        or ""
    )

    collection_title = (
        row["track_title"]
        or ""
    )

    collection_label = (
        row["release_label"]
        or ""
    )

    collection_catalog = (
        row["release_catalog"]
        or ""
    )

    discogs_title = result_title(
        result
    )

    # Discogs search title:
    #
    # Artist - Track
    #
    if " - " in discogs_title:

        discogs_artist, discogs_track = (
            discogs_title.split(
                " - ",
                1
            )
        )

    else:

        discogs_artist = ""

        discogs_track = (
            discogs_title
        )

    discogs_label = result_label(
        result
    )

    discogs_catalog = result_catalog(
        result
    )

    artist_score = similarity(
        collection_artist,
        discogs_artist
    )

    track_score = similarity(
        collection_title,
        discogs_track
    )

    label_score = similarity(
        collection_label,
        discogs_label
    )

    catalog_score = catalog_similarity(
        collection_catalog,
        discogs_catalog
    )

    score = 0.0

    # EXACTE werkende gewichten
    score += track_score * 50
    score += artist_score * 25
    score += label_score * 15
    score += catalog_score * 10

    # Vinyl bonus
    format_text = normalize(
        result_format(result)
    )

    if "vinyl" in format_text:

        score += 8

    if (
        "12\"" in result_format(result)
        or "12 inch" in format_text
        or "12" in format_text
    ):

        score += 5

    if "promo" in format_text:

        score += 2

    if "white label" in format_text:

        score += 2

    if "single sided" in format_text:

        score += 2

    # Digital penalty
    if any(
        word in format_text
        for word in (
            "file",
            "mp3",
            "wav",
            "flac",
            "digital"
        )
    ):

        score -= 25

    # CD penalty
    if "cd" in format_text:

        score -= 18

    # Exact artist
    if normalize(
        collection_artist
    ) == normalize(
        discogs_artist
    ):

        score += 5

    # Exact track
    if normalize(
        collection_title
    ) == normalize(
        discogs_track
    ):

        score += 7

    # Exact/numeriek catalog
    if (
        collection_catalog
        and discogs_catalog
    ):

        if (
            normalize_catalog(
                collection_catalog
            )
            ==
            normalize_catalog(
                discogs_catalog
            )
        ):

            score += 8

        else:

            a = re.sub(
                r"[^0-9]",
                "",
                normalize(
                    collection_catalog
                )
            )

            b = re.sub(
                r"[^0-9]",
                "",
                normalize(
                    discogs_catalog
                )
            )

            if (
                a
                and b
                and a.lstrip("0")
                == b.lstrip("0")
            ):

                score += 8

    return round(
        max(
            score,
            0
        ),
        2
    )


# ============================================================
# RANK
# ============================================================

def rank_candidates(
    row,
    results
):

    candidates = []

    seen = set()

    for result in results:

        discogs_id = result.get(
            "id"
        )

        if not discogs_id:

            continue

        if discogs_id in seen:

            continue

        seen.add(
            discogs_id
        )

        score = score_result(
            row,
            result
        )

        candidates.append(
            {
                "score":
                    score,

                "id":
                    discogs_id,

                "title":
                    result_title(
                        result
                    ),

                "artist":
                    result_artist(
                        result
                    ),

                "label":
                    result_label(
                        result
                    ),

                "catalog":
                    result_catalog(
                        result
                    ),

                "year":
                    result.get(
                        "year",
                        ""
                    ),

                "country":
                    result.get(
                        "country",
                        ""
                    ),

                "format":
                    result_format(
                        result
                    ),

                "result":
                    result
            }
        )

    candidates.sort(
        key=lambda x: x["score"],
        reverse=True
    )

    return candidates


# ============================================================
# UPDATE
# ============================================================

def update_release(
    conn,
    discogs_column,
    release_id,
    discogs_id
):

    sql = f"""
        UPDATE releases

        SET
            {discogs_column} = ?,
            discogs_link = ?

        WHERE id = ?

          AND (
              {discogs_column} IS NULL
              OR TRIM(
                  CAST(
                      {discogs_column}
                      AS TEXT
                  )
              ) = ''
              OR CAST(
                  {discogs_column}
                  AS TEXT
              ) = '0'
          )
    """

    link = (
        f"https://www.discogs.com/release/"
        f"{discogs_id}"
    )

    cursor = conn.execute(
        sql,
        (
            str(discogs_id),
            link,
            release_id
        )
    )

    return cursor.rowcount


# ============================================================
# MAIN
# ============================================================

def main():

    print()
    print("=" * 80)
    print(
        "KID ACID'S VINYLVAULT V3"
    )
    print(
        "SAFE AUTOMATISCHE DISCOGS MATCH"
    )
    print("=" * 80)

    conn = db_connect()

    try:

        rows, discogs_column = (
            load_releases(
                conn
            )
        )

        print()
        print("=" * 80)

        print(
            "RELEASES ZONDER DISCOGS ID:",
            len(rows)
        )

        print(
            "Discogs kolom:",
            discogs_column
        )

        if not rows:

            print(
                "Geen releases te verwerken."
            )

            return

        token = os.environ.get(
            "DISCOGS_TOKEN"
        )

        if not token:

            print()
            print(
                "Geen DISCOGS_TOKEN gevonden."
            )

            return

        session = create_session(
            token
        )

        # ----------------------------------------------------
        # CONNECTIE TEST
        # ----------------------------------------------------

        try:

            response = session.get(
                f"{DISCOGS_API}/oauth/identity",
                timeout=30
            )

        except requests.RequestException as exc:

            print(
                "Discogs verbinding mislukt:"
            )

            print(exc)

            return

        if response.status_code != 200:

            print(
                "Discogs token/API fout:",
                response.status_code
            )

            return

        identity = response.json()

        print()
        print(
            "Discogs gebruiker:",
            identity.get(
                "username",
                "onbekend"
            )
        )

        print(
            "Discogs verbinding: OK"
        )

        # ----------------------------------------------------
        # BACKUP
        # ----------------------------------------------------

        backup_path = create_backup()

        # ----------------------------------------------------
        # STATISTICS
        # ----------------------------------------------------

        matched = 0
        ambiguous = 0
        possible = 0
        weak = 0
        none = 0
        errors = 0

        matched_items = []
        ambiguous_items = []
        possible_items = []
        weak_items = []
        none_items = []

        # ----------------------------------------------------
        # AUTOMATIC PROCESSING
        # ----------------------------------------------------

        total = len(rows)

        for index, row in enumerate(
            rows,
            start=1
        ):

            artist = (
                row["track_artist"]
                or row["release_artist"]
                or ""
            )

            title = (
                row["track_title"]
                or ""
            )

            label = (
                row["release_label"]
                or ""
            )

            catalog = (
                row["release_catalog"]
                or ""
            )

            print()
            print("-" * 80)

            print(
                f"[{index}/{total}] "
                f"ID {row['release_id']} | "
                f"{artist} - {title}"
            )

            try:

                results = search_discogs(
                    session,
                    artist,
                    title,
                    label,
                    catalog
                )

                if not results:

                    none += 1

                    none_items.append(
                        row["release_id"]
                    )

                    print(
                        "RESULTAAT: GEEN RESULTAAT"
                    )

                    continue

                candidates = rank_candidates(
                    row,
                    results
                )

                if not candidates:

                    none += 1

                    none_items.append(
                        row["release_id"]
                    )

                    print(
                        "RESULTAAT: GEEN KANDIDAAT"
                    )

                    continue

                best = candidates[0]

                second_score = (
                    candidates[1]["score"]
                    if len(candidates) > 1
                    else 0
                )

                gap = (
                    best["score"]
                    - second_score
                )

                print(
                    f"BEST: "
                    f"{best['id']} | "
                    f"{best['score']:.2f} | "
                    f"gap {gap:.2f}"
                )

                print(
                    f"      "
                    f"{best['artist']} - "
                    f"{best['title']}"
                )

                print(
                    f"      "
                    f"{best['label']} | "
                    f"{best['catalog']} | "
                    f"{best['format']}"
                )

                # ------------------------------------------------
                # VEILIGE AUTOMATISCHE BESLISSING
                # ------------------------------------------------

                if (
                    best["score"]
                    >= STRONG_THRESHOLD
                    and
                    gap
                    >= MINIMUM_GAP
                ):

                    changed = update_release(
                        conn,
                        discogs_column,
                        row["release_id"],
                        best["id"]
                    )

                    if changed:

                        conn.commit()

                        matched += 1

                        matched_items.append(
                            (
                                row["release_id"],
                                best["id"],
                                best["score"],
                                gap,
                                artist,
                                title
                            )
                        )

                        print(
                            ">>> AUTOMATISCH "
                            "GEKOPPELD"
                        )

                    else:

                        possible += 1

                        possible_items.append(
                            row["release_id"]
                        )

                        print(
                            ">>> NIET GEWIJZIGD"
                        )

                elif (
                    best["score"]
                    >= STRONG_THRESHOLD
                    and
                    gap
                    < MINIMUM_GAP
                ):

                    ambiguous += 1

                    ambiguous_items.append(
                        (
                            row["release_id"],
                            best["id"],
                            best["score"],
                            gap,
                            artist,
                            title
                        )
                    )

                    print(
                        ">>> AMBIGUOUS - "
                        "NIET GEKOPPELD"
                    )

                elif best["score"] >= 65:

                    possible += 1

                    possible_items.append(
                        row["release_id"]
                    )

                    print(
                        ">>> POSSIBLE - "
                        "NIET GEKOPPELD"
                    )

                else:

                    weak += 1

                    weak_items.append(
                        row["release_id"]
                    )

                    print(
                        ">>> WEAK - "
                        "NIET GEKOPPELD"
                    )

            except Exception as exc:

                errors += 1

                print(
                    "FOUT:",
                    exc
                )

                try:

                    conn.rollback()

                except Exception:

                    pass

        # ----------------------------------------------------
        # FINAL
        # ----------------------------------------------------

        conn.commit()

        print()
        print("=" * 80)
        print(
            "AUTOMATISCHE MATCH KLAAR"
        )
        print("=" * 80)

        print()
        print(
            "Totaal verwerkt :",
            total
        )

        print(
            "Automatisch gekoppeld:",
            matched
        )

        print(
            "Ambiguous:",
            ambiguous
        )

        print(
            "Possible:",
            possible
        )

        print(
            "Weak:",
            weak
        )

        print(
            "Geen resultaat:",
            none
        )

        print(
            "Fouten:",
            errors
        )

        print()
        print(
            "DATABASE GEWIJZIGD: JA"
        )

        print()
        print(
            "BACKUP:"
        )

        print(
            backup_path
        )

        # ----------------------------------------------------
        # RESULTAAT GEKOPPELD
        # ----------------------------------------------------

        if matched_items:

            print()
            print("=" * 80)

            print(
                "AUTOMATISCH GEKOPPELD"
            )

            print("=" * 80)

            for item in matched_items:

                (
                    release_id,
                    discogs_id,
                    score,
                    gap,
                    artist,
                    title
                ) = item

                print(
                    f"{release_id:>5} | "
                    f"{artist} - {title} | "
                    f"Discogs {discogs_id} | "
                    f"score {score:.2f} | "
                    f"gap {gap:.2f}"
                )

        # ----------------------------------------------------
        # AMBIGUOUS
        # ----------------------------------------------------

        if ambiguous_items:

            print()
            print("=" * 80)

            print(
                "AMBIGUOUS - NIET GEKOPPELD"
            )

            print("=" * 80)

            for item in ambiguous_items:

                (
                    release_id,
                    discogs_id,
                    score,
                    gap,
                    artist,
                    title
                ) = item

                print(
                    f"{release_id:>5} | "
                    f"{artist} - {title} | "
                    f"beste {discogs_id} | "
                    f"score {score:.2f} | "
                    f"gap {gap:.2f}"
                )

        # ----------------------------------------------------
        # CLOSE
        # ----------------------------------------------------

    finally:

        conn.close()


# ============================================================
# START
# ============================================================

if __name__ == "__main__":

    main()
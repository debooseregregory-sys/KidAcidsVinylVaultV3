# ============================================================
#
# KID ACID'S VINYLVAULT V3
# MANUAL DISCOGS MATCH CSV GENERATOR
#
# ============================================================
#
# DOEL:
#
# Maak één complete CSV voor handmatige Discogs-koppeling.
#
# BRON:
#
#   data\vinylvault.db
#
# GEBRUIKT:
#
#   releases
#   tracks
#   discogs_vinyl
#
# OUTPUT:
#
#   data\exports\manual_discogs_match.csv
#
# BELANGRIJK:
#
# Dit script verandert NIETS aan de database.
#
# ============================================================

import csv
import os
import re
import sqlite3
from difflib import SequenceMatcher


# ============================================================
# PROJECT / DATABASE
# ============================================================

SCRIPT_DIR = os.path.dirname(
    os.path.abspath(__file__)
)


def find_database():

    possible_paths = [

        os.path.join(
            SCRIPT_DIR,
            "data",
            "vinylvault.db"
        ),

        os.path.join(
            os.path.dirname(SCRIPT_DIR),
            "data",
            "vinylvault.db"
        ),

        os.path.join(
            os.path.dirname(
                os.path.dirname(SCRIPT_DIR)
            ),
            "data",
            "vinylvault.db"
        ),

    ]

    for path in possible_paths:

        path = os.path.abspath(path)

        if os.path.exists(path):

            return path

    raise FileNotFoundError(
        "vinylvault.db niet gevonden.\n\n"
        + "\n".join(
            possible_paths
        )
    )


DB = find_database()


# ============================================================
# OUTPUT
# ============================================================

OUTPUT_DIR = os.path.join(
    os.path.dirname(DB),
    "exports"
)

os.makedirs(
    OUTPUT_DIR,
    exist_ok=True
)

OUTPUT_CSV = os.path.join(
    OUTPUT_DIR,
    "manual_discogs_match.csv"
)


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
# DATABASE
# ============================================================

def get_connection():

    conn = sqlite3.connect(
        DB
    )

    conn.row_factory = sqlite3.Row

    return conn


# ============================================================
# TABLE EXISTS
# ============================================================

def table_exists(
    conn,
    table_name
):

    row = conn.execute(
        """
        SELECT name
        FROM sqlite_master
        WHERE type = 'table'
          AND name = ?
        """,
        (table_name,)
    ).fetchone()

    return row is not None


# ============================================================
# COLUMNS
# ============================================================

def get_columns(
    conn,
    table_name
):

    rows = conn.execute(
        f"PRAGMA table_info({table_name})"
    ).fetchall()

    return [
        row["name"]
        for row in rows
    ]


# ============================================================
# TRACK SUMMARY
# ============================================================

def load_track_summary(
    conn
):

    rows = conn.execute(
        """
        SELECT
            release_id,
            COUNT(*) AS track_count,
            GROUP_CONCAT(
                position
                || ' | '
                || artist
                || ' | '
                || title,
                ' || '
            ) AS tracks
        FROM tracks
        GROUP BY release_id
        """
    ).fetchall()

    result = {}

    for row in rows:

        result[
            row["release_id"]
        ] = {

            "track_count":
                row["track_count"] or 0,

            "tracks":
                row["tracks"] or ""
        }

    return result


# ============================================================
# LOAD LOCAL DISCOGS VINYL
# ============================================================

def load_discogs_vinyl(
    conn
):

    if not table_exists(
        conn,
        "discogs_vinyl"
    ):

        print()
        print(
            "WAARSCHUWING:"
        )

        print(
            "Tabel discogs_vinyl bestaat niet."
        )

        return [], []

    columns = get_columns(
        conn,
        "discogs_vinyl"
    )

    print()
    print(
        "Discogs vinyl kolommen:"
    )

    print(
        ", ".join(columns)
    )

    # --------------------------------------------------------
    # We gebruiken alleen de velden die werkelijk bestaan.
    # --------------------------------------------------------

    wanted = [

        "id",
        "discogs_id",
        "artist",
        "title",
        "year",
        "catalog",
        "catalog_match",
        "kastcode",
        "instance_id",
        "labels",
        "catalogs",
        "matched_catalogs",
        "kastcodes"

    ]

    available = [
        column
        for column in wanted
        if column in columns
    ]

    select_sql = ", ".join(
        available
    )

    rows = conn.execute(
        f"""
        SELECT
            {select_sql}
        FROM discogs_vinyl
        ORDER BY id
        """
    ).fetchall()

    return rows, available


# ============================================================
# SAFE ROW VALUE
# ============================================================

def row_value(
    row,
    column
):

    if column not in row.keys():

        return ""

    value = row[column]

    if value is None:

        return ""

    return str(value)


# ============================================================
# DISCOGS CANDIDATE SCORE
# ============================================================

def candidate_score(
    release,
    discogs
):

    release_artist = (
        release["artist"]
        or ""
    )

    release_title = (
        release["title"]
        or ""
    )

    release_label = (
        release["label"]
        or ""
    )

    release_catalog = (
        release["catalog"]
        or ""
    )

    discogs_artist = row_value(
        discogs,
        "artist"
    )

    discogs_title = row_value(
        discogs,
        "title"
    )

    discogs_labels = row_value(
        discogs,
        "labels"
    )

    discogs_catalogs = row_value(
        discogs,
        "catalogs"
    )

    discogs_matched_catalogs = row_value(
        discogs,
        "matched_catalogs"
    )

    # --------------------------------------------------------
    # Artist
    # --------------------------------------------------------

    artist_score = similarity(
        release_artist,
        discogs_artist
    )

    # --------------------------------------------------------
    # Title
    # --------------------------------------------------------

    title_score = similarity(
        release_title,
        discogs_title
    )

    # --------------------------------------------------------
    # Label
    # --------------------------------------------------------

    label_score = similarity(
        release_label,
        discogs_labels
    )

    # --------------------------------------------------------
    # Catalog
    # --------------------------------------------------------

    catalog_source = (
        discogs_matched_catalogs
        or discogs_catalogs
    )

    catalog_score = similarity(
        release_catalog,
        catalog_source
    )

    score = 0.0

    score += artist_score * 35
    score += title_score * 35
    score += label_score * 15
    score += catalog_score * 15

    # --------------------------------------------------------
    # Numerieke catalogus
    # --------------------------------------------------------

    if (
        release_catalog
        and catalog_source
    ):

        a = re.sub(
            r"[^0-9]",
            "",
            str(release_catalog)
        )

        b = re.sub(
            r"[^0-9]",
            "",
            str(catalog_source)
        )

        if (
            a
            and b
            and a.lstrip("0")
            == b.lstrip("0")
        ):

            score += 15

    return round(
        score,
        2
    )


# ============================================================
# FIND CANDIDATES
# ============================================================

def find_candidates(
    release,
    discogs_rows,
    maximum=3
):

    candidates = []

    for discogs in discogs_rows:

        score = candidate_score(
            release,
            discogs
        )

        # Alleen enigszins relevante kandidaten.
        if score < 35:

            continue

        candidates.append(
            (
                score,
                discogs
            )
        )

    candidates.sort(
        key=lambda x: x[0],
        reverse=True
    )

    return candidates[:maximum]


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
        "MANUAL DISCOGS MATCH CSV GENERATOR"
    )

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
        "Output:"
    )

    print(
        OUTPUT_CSV
    )

    conn = get_connection()

    try:

        # ----------------------------------------------------
        # DATABASE COUNTS
        # ----------------------------------------------------

        releases_count = conn.execute(
            "SELECT COUNT(*) FROM releases"
        ).fetchone()[0]

        tracks_count = conn.execute(
            "SELECT COUNT(*) FROM tracks"
        ).fetchone()[0]

        print()
        print(
            "Releases:",
            releases_count
        )

        print(
            "Tracks:",
            tracks_count
        )

        # ----------------------------------------------------
        # RELEASES
        # ----------------------------------------------------

        releases = conn.execute(
            """
            SELECT
                id,
                artist,
                title,
                label,
                catalog,
                year,
                genre,
                discogs,
                discogs_link,
                cover,
                notes,
                storage_code
            FROM releases
            ORDER BY id
            """
        ).fetchall()

        # ----------------------------------------------------
        # TRACKS
        # ----------------------------------------------------

        track_summary = load_track_summary(
            conn
        )

        # ----------------------------------------------------
        # DISCOGS
        # ----------------------------------------------------

        (
            discogs_rows,
            discogs_columns
        ) = load_discogs_vinyl(
            conn
        )

        print()
        print(
            "Discogs vinyl records:",
            len(discogs_rows)
        )

        if not discogs_rows:

            print()
            print(
                "GEEN lokale Discogs-data gevonden."
            )

            return

        # ====================================================
        # CSV HEADERS
        # ====================================================

        headers = [

            # ==================================================
            # VINYLVAULT
            # ==================================================

            "VAULT_ID",
            "VAULT_ARTIST",
            "VAULT_TITLE",
            "VAULT_LABEL",
            "VAULT_CATALOG",
            "VAULT_YEAR",
            "VAULT_GENRE",
            "VAULT_STORAGE_CODE",
            "VAULT_DISCOGS_ID",
            "VAULT_DISCOGS_LINK",
            "VAULT_TRACK_COUNT",
            "VAULT_TRACKS",

            # ==================================================
            # DISCogs 1
            # ==================================================

            "D1_SCORE",
            "D1_ID",
            "D1_DISCOGS_ID",
            "D1_ARTIST",
            "D1_TITLE",
            "D1_YEAR",
            "D1_CATALOG",
            "D1_CATALOG_MATCH",
            "D1_CATALOGS",
            "D1_MATCHED_CATALOGS",
            "D1_LABELS",
            "D1_KASTCODE",
            "D1_KASTCODES",
            "D1_INSTANCE_ID",

            # ==================================================
            # DISCogs 2
            # ==================================================

            "D2_SCORE",
            "D2_ID",
            "D2_DISCOGS_ID",
            "D2_ARTIST",
            "D2_TITLE",
            "D2_YEAR",
            "D2_CATALOG",
            "D2_CATALOG_MATCH",
            "D2_CATALOGS",
            "D2_MATCHED_CATALOGS",
            "D2_LABELS",
            "D2_KASTCODE",
            "D2_KASTCODES",
            "D2_INSTANCE_ID",

            # ==================================================
            # DISCogs 3
            # ==================================================

            "D3_SCORE",
            "D3_ID",
            "D3_DISCOGS_ID",
            "D3_ARTIST",
            "D3_TITLE",
            "D3_YEAR",
            "D3_CATALOG",
            "D3_CATALOG_MATCH",
            "D3_CATALOGS",
            "D3_MATCHED_CATALOGS",
            "D3_LABELS",
            "D3_KASTCODE",
            "D3_KASTCODES",
            "D3_INSTANCE_ID",

            # ==================================================
            # HANDMATIG
            # ==================================================

            "MANUAL_MATCH",
            "MANUAL_DISCOGS_ID",
            "MANUAL_NOTES"
        ]

        # ====================================================
        # CSV SCHRIJVEN
        # ====================================================

        with open(
            OUTPUT_CSV,
            "w",
            encoding="utf-8-sig",
            newline=""
        ) as csv_file:

            writer = csv.DictWriter(
                csv_file,
                fieldnames=headers,
                delimiter=";",
                extrasaction="ignore"
            )

            writer.writeheader()

            # ------------------------------------------------
            # RELEASES
            # ------------------------------------------------

            for index, release in enumerate(
                releases,
                start=1
            ):

                release_id = release[
                    "id"
                ]

                track_info = track_summary.get(
                    release_id,
                    {
                        "track_count": 0,
                        "tracks": ""
                    }
                )

                candidates = find_candidates(
                    release,
                    discogs_rows,
                    maximum=3
                )

                row = {

                    # ----------------------------------------
                    # VINYLVAULT
                    # ----------------------------------------

                    "VAULT_ID":
                        release_id,

                    "VAULT_ARTIST":
                        release["artist"] or "",

                    "VAULT_TITLE":
                        release["title"] or "",

                    "VAULT_LABEL":
                        release["label"] or "",

                    "VAULT_CATALOG":
                        release["catalog"] or "",

                    "VAULT_YEAR":
                        release["year"] or "",

                    "VAULT_GENRE":
                        release["genre"] or "",

                    "VAULT_STORAGE_CODE":
                        release["storage_code"] or "",

                    "VAULT_DISCOGS_ID":
                        release["discogs"] or "",

                    "VAULT_DISCOGS_LINK":
                        release["discogs_link"] or "",

                    "VAULT_TRACK_COUNT":
                        track_info["track_count"],

                    "VAULT_TRACKS":
                        track_info["tracks"],

                    # ----------------------------------------
                    # HANDMATIG
                    # ----------------------------------------

                    "MANUAL_MATCH":
                        "",

                    "MANUAL_DISCOGS_ID":
                        "",

                    "MANUAL_NOTES":
                        ""
                }

                # ------------------------------------------------
                # Kandidaten invullen
                # ------------------------------------------------

                for number, (
                    score,
                    discogs
                ) in enumerate(
                    candidates,
                    start=1
                ):

                    prefix = (
                        f"D{number}_"
                    )

                    row[
                        prefix + "SCORE"
                    ] = score

                    row[
                        prefix + "ID"
                    ] = row_value(
                        discogs,
                        "id"
                    )

                    row[
                        prefix + "DISCOGS_ID"
                    ] = row_value(
                        discogs,
                        "discogs_id"
                    )

                    row[
                        prefix + "ARTIST"
                    ] = row_value(
                        discogs,
                        "artist"
                    )

                    row[
                        prefix + "TITLE"
                    ] = row_value(
                        discogs,
                        "title"
                    )

                    row[
                        prefix + "YEAR"
                    ] = row_value(
                        discogs,
                        "year"
                    )

                    row[
                        prefix + "CATALOG"
                    ] = row_value(
                        discogs,
                        "catalog"
                    )

                    row[
                        prefix + "CATALOG_MATCH"
                    ] = row_value(
                        discogs,
                        "catalog_match"
                    )

                    row[
                        prefix + "CATALOGS"
                    ] = row_value(
                        discogs,
                        "catalogs"
                    )

                    row[
                        prefix + "MATCHED_CATALOGS"
                    ] = row_value(
                        discogs,
                        "matched_catalogs"
                    )

                    row[
                        prefix + "LABELS"
                    ] = row_value(
                        discogs,
                        "labels"
                    )

                    row[
                        prefix + "KASTCODE"
                    ] = row_value(
                        discogs,
                        "kastcode"
                    )

                    row[
                        prefix + "KASTCODES"
                    ] = row_value(
                        discogs,
                        "kastcodes"
                    )

                    row[
                        prefix + "INSTANCE_ID"
                    ] = row_value(
                        discogs,
                        "instance_id"
                    )

                writer.writerow(
                    row
                )

                # ------------------------------------------------
                # PROGRESS
                # ------------------------------------------------

                if (
                    index % 100 == 0
                    or index == len(releases)
                ):

                    print(
                        f"CSV: "
                        f"{index}/"
                        f"{len(releases)}"
                    )

        # ====================================================
        # KLAAR
        # ====================================================

        print()
        print("=" * 80)

        print(
            "CSV GENERATOR KLAAR"
        )

        print("=" * 80)

        print()
        print(
            "Aantal VinylVault releases:",
            len(releases)
        )

        print(
            "Aantal tracks:",
            tracks_count
        )

        print(
            "Lokale Discogs records:",
            len(discogs_rows)
        )

        print()
        print(
            "CSV:"
        )

        print(
            OUTPUT_CSV
        )

        print()
        print(
            "DATABASE GEWIJZIGD: NEE"
        )

        print()
        print(
            "Handmatig invullen:"
        )

        print(
            "MANUAL_MATCH = YES"
        )

        print(
            "MANUAL_DISCOGS_ID = juiste Discogs ID"
        )

        print()
        print(
            "Daarna kunnen we een aparte "
            "veilige importeur maken."
        )

    finally:

        conn.close()


# ============================================================
# START
# ============================================================

if __name__ == "__main__":

    main()
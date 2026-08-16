# ============================================================
# KID ACID'S VINYLVAULT V3
# AUTOMATIC COLLECTION BATCH IMPORTER
# ============================================================

import os
import sys
import time
import sqlite3

ROOT = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from collection_search_import import (
    collection_summary,
    search_collection_release,
    verify_discogs_candidates,
    get_discogs_release,
    calculate_release_match,
)

from import_release_v3 import (
    DB,
    import_release,
)


# ============================================================
# INSTELLINGEN
# ============================================================

BATCH_SIZE = 20

AUTO_IMPORT_SCORE = 80.0

REVIEW_SCORE = 50.0

DELAY_BETWEEN_RELEASES = 3

MAX_CANDIDATES_TO_VERIFY = 10


# ============================================================
# DATABASE
# ============================================================

def database_connection():

    conn = sqlite3.connect(DB)

    conn.row_factory = sqlite3.Row

    conn.execute(
        "PRAGMA foreign_keys = ON"
    )

    return conn


# ============================================================
# BESTAANDE RELEASE
# ============================================================

def already_imported(conn, discogs_id):

    row = conn.execute(
        """
        SELECT id
        FROM releases
        WHERE discogs = ?
        LIMIT 1
        """,
        (str(discogs_id),)
    ).fetchone()

    return row is not None


# ============================================================
# BESTE KANDIDAAT
# ============================================================

def best_candidate(verified):

    if not verified:
        return None

    verified = sorted(
        verified,
        key=lambda item:
            item.get(
                "_vv_match",
                {}
            ).get(
                "score",
                0
            ),
        reverse=True
    )

    return verified[0]


# ============================================================
# RELEASE RAPPORT
# ============================================================

def print_release_header(number, total, group):

    print()
    print("=" * 90)

    print(
        f"RELEASE {number}/{total}"
    )

    print("=" * 90)

    print(
        "Artist :",
        group["artist"]
    )

    print(
        "Label  :",
        group["label_catalog"]
    )

    print(
        "Code   :",
        group["code"]
    )

    print(
        "Tracks :",
        len(group["tracks"])
    )


# ============================================================
# IMPORT
# ============================================================

def import_best_release(
    conn,
    group,
    candidate
):

    release = candidate.get(
        "_vv_release"
    )

    if not release:
        return False

    release_id = release.get(
        "id"
    )

    if not release_id:
        return False

    match = candidate.get(
        "_vv_match",
        {}
    )

    score = match.get(
        "score",
        0
    )

    print()
    print(
        ">>> AUTOMATISCH IMPORTEREN"
    )

    print(
        "Discogs ID:",
        release_id
    )

    print(
        "Titel:",
        release.get(
            "title",
            ""
        )
    )

    print(
        "Jaar:",
        release.get(
            "year",
            ""
        )
    )

    print(
        "Score:",
        score,
        "%"
    )

    print(
        "Tracks:",
        f"{match.get('matched_tracks', 0)}/"
        f"{match.get('total_tracks', 0)}"
    )

    print(
        "Catalog:",
        "JA"
        if match.get("catalog_match")
        else "NEE"
    )

    print(
        "Label:",
        "JA"
        if match.get("label_match")
        else "NEE"
    )

    try:

        import_release(
            release,
            conn
        )

        conn.commit()

        print()
        print(
            ">>> IMPORT GESLAAGD"
        )

        return True

    except Exception as exc:

        conn.rollback()

        print()
        print(
            ">>> IMPORT FOUT:"
        )

        print(
            type(exc).__name__,
            exc
        )

        return False


# ============================================================
# BATCH
# ============================================================

def run_batch(
    start=0,
    batch_size=BATCH_SIZE
):

    groups = collection_summary()

    total = len(groups)

    end = min(
        start + batch_size,
        total
    )

    print()
    print("=" * 90)
    print("VINYLVAULT V3 AUTOMATISCHE BATCH IMPORT")
    print("=" * 90)

    print(
        "Totaal releases:",
        total
    )

    print(
        "Start:",
        start + 1
    )

    print(
        "Einde:",
        end
    )

    print(
        "Batch:",
        batch_size
    )

    print(
        "Auto import:",
        f">= {AUTO_IMPORT_SCORE}%"
    )

    print(
        "Review:",
        f"{REVIEW_SCORE}% - "
        f"{AUTO_IMPORT_SCORE - 0.1:.1f}%"
    )

    print("=" * 90)

    conn = database_connection()

    imported = 0
    skipped = 0
    review = 0
    failed = 0

    try:

        for index in range(
            start,
            end
        ):

            group = groups[index]

            print_release_header(
                index + 1,
                total,
                group
            )

            # =================================================
            # ZOEKEN
            # =================================================

            try:

                candidates = (
                    search_collection_release(
                        group
                    )
                )

            except Exception as exc:

                print()
                print(
                    "ZOEKFOUT:",
                    type(exc).__name__,
                    exc
                )

                failed += 1

                continue

            if not candidates:

                print()
                print(
                    "GEEN DISCOGS KANDIDATEN"
                )

                skipped += 1

                continue

            # =================================================
            # ALLEEN BESTE KANDIDATEN CONTROLEREN
            # =================================================

            candidates = candidates[
                :MAX_CANDIDATES_TO_VERIFY
            ]

            print()
            print(
                "Volledige releases controleren:",
                len(candidates)
            )

            try:

                verified = (
                    verify_discogs_candidates(
                        group,
                        candidates
                    )
                )

            except Exception as exc:

                print()
                print(
                    "VERIFICATIEFOUT:",
                    type(exc).__name__,
                    exc
                )

                failed += 1

                continue

            candidate = best_candidate(
                verified
            )

            if not candidate:

                print()
                print(
                    "GEEN VERIFIEERDE KANDIDAAT"
                )

                skipped += 1

                continue

            release = candidate.get(
                "_vv_release",
                {}
            )

            match = candidate.get(
                "_vv_match",
                {}
            )

            release_id = release.get(
                "id"
            )

            score = match.get(
                "score",
                0
            )

            print()
            print("=" * 90)
            print("BESTE MATCH")
            print("=" * 90)

            print(
                "Discogs ID:",
                release_id
            )

            print(
                "Titel:",
                release.get(
                    "title",
                    ""
                )
            )

            print(
                "Jaar:",
                release.get(
                    "year",
                    ""
                )
            )

            print(
                "Score:",
                score,
                "%"
            )

            print(
                "Tracks:",
                f"{match.get('matched_tracks', 0)}/"
                f"{match.get('total_tracks', 0)}"
            )

            print(
                "Catalog:",
                "JA"
                if match.get("catalog_match")
                else "NEE"
            )

            print(
                "Label:",
                "JA"
                if match.get("label_match")
                else "NEE"
            )

            # =================================================
            # BESTAAT AL?
            # =================================================

            if already_imported(
                conn,
                release_id
            ):

                print()
                print(
                    "AL BESTAAND IN VINYLVAULT -> OVERSLAAN"
                )

                skipped += 1

                continue

            # =================================================
            # AUTOMATISCHE BESLISSING
            # =================================================

            if score >= AUTO_IMPORT_SCORE:

                if import_best_release(
                    conn,
                    group,
                    candidate
                ):

                    imported += 1

                else:

                    failed += 1

            elif score >= REVIEW_SCORE:

                print()
                print(
                    ">>> TWIJFELGEVAL"
                )

                print(
                    "Deze release wordt NIET "
                    "automatisch geïmporteerd."
                )

                print(
                    "Score:",
                    score,
                    "%"
                )

                review += 1

            else:

                print()
                print(
                    ">>> SCORE TE LAAG"
                )

                print(
                    "Release wordt overgeslagen."
                )

                skipped += 1

            # =================================================
            # WACHTEN
            # =================================================

            if index < end - 1:

                print()
                print(
                    f"Wachten "
                    f"{DELAY_BETWEEN_RELEASES} seconden..."
                )

                time.sleep(
                    DELAY_BETWEEN_RELEASES
                )

    finally:

        conn.close()

    # =========================================================
    # RESULTAAT
    # =========================================================

    print()
    print()
    print("=" * 90)
    print("BATCH KLAAR")
    print("=" * 90)

    print(
        "Verwerkt        :",
        end - start
    )

    print(
        "Automatisch     :",
        imported
    )

    print(
        "Overgeslagen    :",
        skipped
    )

    print(
        "Te beoordelen   :",
        review
    )

    print(
        "Fouten          :",
        failed
    )

    print("=" * 90)


# ============================================================
# START
# ============================================================

if __name__ == "__main__":

    run_batch(
        start=0,
        batch_size=BATCH_SIZE
    )

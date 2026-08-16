import sqlite3
import shutil
from datetime import datetime

DB = "data/vinylvault.db"

# ============================================================
# VEILIGE UNIEKE MATCHES
# Alleen records die al gecontroleerd zijn.
# ============================================================

MATCHES = [
    # id, discogs_id, catalog
    (664, 413131, "8714866 531 12"),
    (861, 2005678, "CR007"),

    (924, 219979, "541416 501144"),
    (925, 219972, "541416 501140"),
    (926, 220032, "541416 501141"),
    (927, 219980, "541416 501145"),
    (928, 219977, "541416 501143"),
    (929, 219976, "541416 501142"),
    (931, 91861, "541416 500908"),
    (932, 91860, "541416 500911"),

    (1952, 1452670, "gorsch-101G"),
    (2101, 331792, "Highball 04/026"),
    (2103, 94731, "Highball 03/009"),

    (2467, 22054, "KD 18"),

    (2931, 666720, "MINUS40X"),

    (3530, 11181, "PMTEN 014"),
    (3673, 6767, "PRMT 005"),
    (3682, 33340, "PMTEN 007"),

    (3855, 169080, "RM 021"),

    (4469, 355268, "SUBVERT007"),

    (4610, 557059, "TEMPL8.R002"),

    (4682, 351024, "tw0008"),

    (4704, 11463, "PAIN 020"),
    (4706, 11464, "PAIN 016"),
    (4707, 13910, "PAIN 015"),

    (5407, 1927235, "HD037"),
    (5409, 2109875, "AHVN006"),
]


def main():
    print("=" * 100)
    print("SAFE UNIQUE DISCOGS MATCH")
    print("=" * 100)

    # --------------------------------------------------------
    # BACKUP
    # --------------------------------------------------------

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup = f"data/vinylvault_BEFORE_SAFE_UNIQUE_{timestamp}.db"

    shutil.copy2(DB, backup)

    print()
    print("BACKUP:")
    print(backup)
    print()

    conn = sqlite3.connect(DB)
    cur = conn.cursor()

    changed = 0
    skipped = 0

    print("CONTROLE:")
    print("-" * 100)

    for release_id, discogs_id, catalog in MATCHES:

        row = cur.execute(
            """
            SELECT
                id,
                artist,
                title,
                label,
                catalog,
                discogs,
                storage_code
            FROM releases
            WHERE id = ?
            """,
            (release_id,),
        ).fetchone()

        if not row:
            print(f"NIET GEVONDEN | ID={release_id}")
            skipped += 1
            continue

        (
            rid,
            artist,
            title,
            label,
            old_catalog,
            old_discogs,
            storage,
        ) = row

        # ----------------------------------------------------
        # VEILIGHEIDSREGEL:
        # alleen invullen wanneer beide velden nog leeg zijn.
        # ----------------------------------------------------

        if old_catalog and str(old_catalog).strip():
            print(
                f"OVERGESLAGEN | {rid} | "
                f"{artist} | {title} | "
                f"catalogus bestaat al: {old_catalog}"
            )
            skipped += 1
            continue

        if old_discogs and str(old_discogs).strip():
            print(
                f"OVERGESLAGEN | {rid} | "
                f"{artist} | {title} | "
                f"Discogs bestaat al: {old_discogs}"
            )
            skipped += 1
            continue

        cur.execute(
            """
            UPDATE releases
            SET
                discogs = ?,
                catalog = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
              AND (discogs IS NULL OR TRIM(discogs) = '')
              AND (catalog IS NULL OR TRIM(catalog) = '')
            """,
            (
                str(discogs_id),
                catalog,
                release_id,
            ),
        )

        if cur.rowcount == 1:
            changed += 1

            print(
                f"GEWIJZIGD | {rid} | "
                f"{artist} | {title} | "
                f"LABEL={label} | "
                f"CATALOG={catalog} | "
                f"DISCOGS={discogs_id} | "
                f"STORAGE={storage}"
            )
        else:
            skipped += 1

    conn.commit()

    # --------------------------------------------------------
    # EINDCONTROLE
    # --------------------------------------------------------

    remaining = cur.execute(
        """
        SELECT COUNT(*)
        FROM releases
        WHERE
            (discogs IS NULL OR TRIM(discogs) = '')
            AND
            (catalog IS NULL OR TRIM(catalog) = '')
        """
    ).fetchone()[0]

    filled_discogs = cur.execute(
        """
        SELECT COUNT(*)
        FROM releases
        WHERE discogs IS NOT NULL
          AND TRIM(discogs) <> ''
        """
    ).fetchone()[0]

    filled_catalog = cur.execute(
        """
        SELECT COUNT(*)
        FROM releases
        WHERE catalog IS NOT NULL
          AND TRIM(catalog) <> ''
        """
    ).fetchone()[0]

    conn.close()

    print()
    print("=" * 100)
    print("KLAAR")
    print("=" * 100)
    print()
    print(f"GEWIJZIGD       : {changed}")
    print(f"OVERGESLAGEN    : {skipped}")
    print(f"NOG ZONDER DATA : {remaining}")
    print(f"MET CATALOGUS   : {filled_catalog}")
    print(f"MET DISCOGS     : {filled_discogs}")
    print()
    print(f"BACKUP          : {backup}")
    print()
    print("=" * 100)


if __name__ == "__main__":
    main()
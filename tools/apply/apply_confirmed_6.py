import sqlite3
import shutil
import datetime

DB = "data/vinylvault.db"

MATCHES = [
    (86, "1014179", "abstract 010b"),
    (146, "246629", "4973791"),
    (147, "350437", "069497192-1"),
    (457, "4867", "KILLA 002"),
    (459, "265833", "Emetic 005"),
    (460, "292137", "Emetic 002"),
]

timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
backup = f"data/vinylvault_BEFORE_6_CONFIRMED_{timestamp}.db"

shutil.copy2(DB, backup)

conn = sqlite3.connect(DB)
cur = conn.cursor()

changed = 0

for local_id, discogs_id, catalog in MATCHES:

    row = cur.execute(
        """
        SELECT id, artist, title, label, storage_code
        FROM releases
        WHERE id = ?
        """,
        (local_id,)
    ).fetchone()

    if not row:
        print(f"NIET GEVONDEN | ID={local_id}")
        continue

    print(
        f"GEWIJZIGD | {row[0]} | {row[1]} | {row[2]} "
        f"| CATALOG={catalog} | DISCOGS={discogs_id} "
        f"| STORAGE={row[4]}"
    )

    cur.execute(
        """
        UPDATE releases
        SET discogs = ?,
            catalog = ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """,
        (discogs_id, catalog, local_id)
    )

    changed += cur.rowcount

conn.commit()

remaining = cur.execute(
    """
    SELECT COUNT(*)
    FROM releases
    WHERE (discogs IS NULL OR TRIM(discogs) = '')
      AND (catalog IS NULL OR TRIM(catalog) = '')
    """
).fetchone()[0]

with_catalog = cur.execute(
    """
    SELECT COUNT(*)
    FROM releases
    WHERE catalog IS NOT NULL
      AND TRIM(catalog) <> ''
    """
).fetchone()[0]

with_discogs = cur.execute(
    """
    SELECT COUNT(*)
    FROM releases
    WHERE discogs IS NOT NULL
      AND TRIM(discogs) <> ''
    """
).fetchone()[0]

conn.close()

print()
print("=" * 80)
print("RESULTAAT")
print("=" * 80)
print(f"GEWIJZIGD       : {changed}")
print(f"NOG ZONDER DATA : {remaining}")
print(f"MET CATALOGUS   : {with_catalog}")
print(f"MET DISCOGS     : {with_discogs}")
print(f"BACKUP          : {backup}")
print()
print("ID 284 NIET GEWIJZIGD.")
print("DATABASE VEILIG BIJGEWERKT.")
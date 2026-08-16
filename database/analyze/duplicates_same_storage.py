import sqlite3
from pathlib import Path

DB = Path(__file__).resolve().parents[2] / "data" / "vinylvault.db"

print("=" * 70)
print("VINYLVAULT V3 - DUBBELE RELEASES MET DEZELFDE STORAGE")
print("=" * 70)
print()
print(f"Database: {DB}")
print()

conn = sqlite3.connect(DB)
cur = conn.cursor()

cur.execute("""
    SELECT storage, COUNT(*) AS aantal
    FROM vinyl_items
    WHERE storage IS NOT NULL
      AND TRIM(storage) <> ''
      AND UPPER(TRIM(storage)) <> 'SOLD'
    GROUP BY UPPER(TRIM(storage))
    HAVING COUNT(*) > 1
    ORDER BY aantal DESC, UPPER(TRIM(storage))
""")

groups = cur.fetchall()

print(f"GEVONDEN DUBBELE STORAGE-LOCATIES: {len(groups)}")
print()

if not groups:
    print("Geen dubbele Storage-locaties gevonden.")
else:
    for storage, aantal in groups:
        print("-" * 70)
        print(f"STORAGE: {storage} - {aantal} RECORDS")

        cur.execute("""
            SELECT id, artist, title, label, catalog, discogs, storage
            FROM vinyl_items
            WHERE UPPER(TRIM(storage)) = UPPER(TRIM(?))
            ORDER BY id
        """, (storage,))

        for row in cur.fetchall():
            print(
                f"ID={row[0]} | {row[1]} | {row[2]} | "
                f"{row[3]} | {row[4]} | Discogs={row[5]} | Storage={row[6]}"
            )

print()
print("=" * 70)

conn.close()

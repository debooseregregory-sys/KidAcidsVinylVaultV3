import sqlite3
from pathlib import Path

DB = Path(__file__).resolve().parent / "data" / "vinylvault.db"

conn = sqlite3.connect(str(DB))
conn.row_factory = sqlite3.Row

print()
print("=" * 80)
print("KID ACID'S VINYLVAULT V3")
print("DIAGNOSE RELEASES MET EXACT 1 TRACK")
print("=" * 80)
print()
print("Database:", DB)
print()

rows = conn.execute("""
    SELECT
        r.id,
        r.artist,
        r.title,
        r.label,
        r.catalog,
        r.year,
        r.discogs,
        COUNT(t.id) AS track_count
    FROM releases r
    LEFT JOIN tracks t
        ON t.release_id = r.id
    GROUP BY r.id
    HAVING COUNT(t.id) = 1
    ORDER BY r.id
""").fetchall()

print("Totaal releases met exact 1 track:", len(rows))
print()

with_discogs = 0
without_discogs = 0

for row in rows:
    if row["discogs"] and str(row["discogs"]).strip():
        with_discogs += 1
    else:
        without_discogs += 1

print("MET Discogs ID    :", with_discogs)
print("ZONDER Discogs ID :", without_discogs)
print()

print("=" * 80)
print("RELEASES MET 1 TRACK")
print("=" * 80)

for row in rows:

    discogs = row["discogs"] or "-"

    track = conn.execute("""
        SELECT
            position,
            artist,
            title,
            duration
        FROM tracks
        WHERE release_id = ?
        ORDER BY id
        LIMIT 1
    """, (row["id"],)).fetchone()

    print()
    print(
        f"ID={row['id']} | "
        f"{row['artist'] or '-'} | "
        f"{row['title'] or '-'} | "
        f"{row['label'] or '-'} | "
        f"{row['catalog'] or '-'} | "
        f"Discogs={discogs}"
    )

    if track:
        print(
            f"    TRACK: "
            f"{track['position'] or '-'} | "
            f"{track['artist'] or '-'} | "
            f"{track['title'] or '-'}"
        )

print()
print("=" * 80)
print("EINDE DIAGNOSE")
print("=" * 80)

conn.close()

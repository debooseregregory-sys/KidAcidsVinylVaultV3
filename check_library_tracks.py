import sqlite3
from pathlib import Path

DB_PATH = Path(r"C:\Users\andyb\Desktop\KidAcidsVinylVaultV3\data\vinylvault.db")

print()
print("=" * 70)
print("VINYLVAULT V3 - LIBRARY TRACK CHECK")
print("=" * 70)
print()
print("Database:", DB_PATH)
print()

if not DB_PATH.exists():
    print("FOUT: database bestaat niet!")
    print()
    print(DB_PATH)
    raise SystemExit(1)

conn = sqlite3.connect(str(DB_PATH))
conn.row_factory = sqlite3.Row

print("Database geopend OK")
print()

total_releases = conn.execute(
    "SELECT COUNT(*) FROM releases"
).fetchone()[0]

total_tracks = conn.execute(
    "SELECT COUNT(*) FROM tracks"
).fetchone()[0]

print("Releases :", total_releases)
print("Tracks   :", total_tracks)
print()

rows = conn.execute("""
    SELECT
        r.id,
        r.artist,
        r.title,
        r.label,
        r.catalog,
        r.discogs,
        r.storage_code,
        COUNT(t.id) AS track_count
    FROM releases r
    LEFT JOIN tracks t
        ON t.release_id = r.id
    GROUP BY r.id
    ORDER BY track_count ASC, r.id
""").fetchall()

zero = [r for r in rows if r["track_count"] == 0]
one = [r for r in rows if r["track_count"] == 1]
two = [r for r in rows if r["track_count"] == 2]
three = [r for r in rows if r["track_count"] == 3]
four_plus = [r for r in rows if r["track_count"] >= 4]

print("=" * 70)
print("TRACK VERDELING")
print("=" * 70)
print()
print("0 tracks :", len(zero))
print("1 track  :", len(one))
print("2 tracks :", len(two))
print("3 tracks :", len(three))
print("4+ tracks:", len(four_plus))
print()

print("=" * 70)
print("RELEASES MET 0 TRACKS")
print("=" * 70)
print()

for r in zero[:100]:
    print(
        f"ID={r['id']} | "
        f"{r['artist'] or ''} | "
        f"{r['title'] or ''} | "
        f"{r['label'] or ''} | "
        f"{r['catalog'] or ''} | "
        f"Discogs={r['discogs'] or '-'} | "
        f"Storage={r['storage_code'] or '-'}"
    )

print()

print("=" * 70)
print("RELEASES MET EXACT 1 TRACK")
print("=" * 70)
print()

for r in one[:150]:

    track = conn.execute("""
        SELECT position, artist, title, duration
        FROM tracks
        WHERE release_id = ?
        ORDER BY id
    """, (r["id"],)).fetchone()

    if track:
        track_info = (
            f"{track['position'] or '-'} | "
            f"{track['artist'] or ''} | "
            f"{track['title'] or ''}"
        )
    else:
        track_info = "-"

    print(
        f"ID={r['id']} | "
        f"{r['artist'] or ''} | "
        f"{r['title'] or ''} | "
        f"Catalog={r['catalog'] or ''} | "
        f"TRACK={track_info}"
    )

print()

print("=" * 70)
print("DISCOGS")
print("=" * 70)
print()

with_discogs = conn.execute("""
    SELECT COUNT(*)
    FROM releases
    WHERE discogs IS NOT NULL
    AND LENGTH(TRIM(discogs)) > 0
""").fetchone()[0]

without_discogs = conn.execute("""
    SELECT COUNT(*)
    FROM releases
    WHERE discogs IS NULL
    OR LENGTH(TRIM(discogs)) = 0
""").fetchone()[0]

print("Met Discogs ID    :", with_discogs)
print("Zonder Discogs ID :", without_discogs)
print()

print("=" * 70)
print("CHECK KLAAR")
print("=" * 70)
print()

conn.close()

import csv
import sqlite3
from pathlib import Path

ROOT = Path(r"C:\Users\andyb\Desktop\KidAcidsVinylVaultV3")
CSV_FILE = ROOT / "data" / "discogs_vinyl_definitive.csv"
DB_FILE = ROOT / "data" / "vinylvault.db"

print("=" * 70)
print("DISCOGS VINYL -> VINYLVAULT IMPORT")
print("=" * 70)

if not CSV_FILE.exists():
    raise SystemExit(f"CSV niet gevonden: {CSV_FILE}")

if not DB_FILE.exists():
    raise SystemExit(f"Database niet gevonden: {DB_FILE}")

conn = sqlite3.connect(DB_FILE)
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS discogs_vinyl (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    discogs_id TEXT UNIQUE,
    instance_id TEXT,
    artist TEXT,
    title TEXT,
    year TEXT,
    labels TEXT,
    catalogs TEXT,
    matched_catalogs TEXT,
    kastcodes TEXT
)
""")

with open(CSV_FILE, "r", encoding="utf-8-sig", newline="") as f:
    rows = list(csv.DictReader(f))

print("CSV records:", len(rows))
print()

inserted = 0
updated = 0

for row in rows:

    discogs_id = row.get("discogs_id", "").strip()

    if not discogs_id:
        continue

    values = (
        row.get("instance_id", "").strip(),
        row.get("artist", "").strip(),
        row.get("title", "").strip(),
        row.get("year", "").strip(),
        row.get("labels", "").strip(),
        row.get("catalogs", "").strip(),
        row.get("matched_catalogs", "").strip(),
        row.get("kastcodes", "").strip(),
    )

    cur.execute(
        "SELECT id FROM discogs_vinyl WHERE discogs_id = ?",
        (discogs_id,)
    )

    existing = cur.fetchone()

    if existing:

        cur.execute("""
            UPDATE discogs_vinyl
            SET instance_id = ?,
                artist = ?,
                title = ?,
                year = ?,
                labels = ?,
                catalogs = ?,
                matched_catalogs = ?,
                kastcodes = ?
            WHERE discogs_id = ?
        """, values + (discogs_id,))

        updated += 1

    else:

        cur.execute("""
            INSERT INTO discogs_vinyl
            (
                discogs_id,
                instance_id,
                artist,
                title,
                year,
                labels,
                catalogs,
                matched_catalogs,
                kastcodes
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (discogs_id,) + values)

        inserted += 1

conn.commit()

cur.execute("SELECT COUNT(*) FROM discogs_vinyl")
total = cur.fetchone()[0]

print("Nieuw toegevoegd :", inserted)
print("Bijgewerkt        :", updated)
print("Totaal database   :", total)

print()
print("EERSTE 20")
print("=" * 70)

cur.execute("""
    SELECT
        artist,
        title,
        catalogs,
        matched_catalogs,
        kastcodes,
        year
    FROM discogs_vinyl
    ORDER BY artist COLLATE NOCASE,
             title COLLATE NOCASE
    LIMIT 20
""")

for i, row in enumerate(cur.fetchall(), 1):

    artist, title, catalogs, matched, kastcodes, year = row

    print()
    print(f"{i}. {artist} - {title}")
    print(f"   Catalog : {catalogs}")
    print(f"   Match   : {matched}")
    print(f"   Kast    : {kastcodes}")
    print(f"   Jaar    : {year}")

conn.close()

print()
print("=" * 70)
print("IMPORT KLAAR")
print("=" * 70)

import sqlite3

DB = r"C:\Users\andyb\Desktop\KidAcidsVinylVaultV3\data\vinylvault.db"

c = sqlite3.connect(DB)

print("=" * 80)
print("VINYLVAULT V3 - TIJDELIJKE DISCOGS TEST OPRUIMEN")
print("=" * 80)

# Controle
row = c.execute("""
    SELECT id, artist, title, label, catalog, discogs, storage_code
    FROM releases
    WHERE id = 1
""").fetchone()

print()
print("Gevonden release:")
print(row)

if not row:
    print()
    print("Release ID 1 bestaat niet.")
    c.close()
    raise SystemExit

# Alleen verwijderen als het inderdaad onze testrelease is
if (
    row[0] == 1
    and row[5] == "5942009"
    and row[1] == "Planetary Assault Systems"
    and row[2] == "Planetary Funk Vol. 4"
):
    print()
    print("Dit is de tijdelijke Discogs-testrelease.")
    print("Tracks verwijderen...")

    deleted_tracks = c.execute("""
        DELETE FROM tracks
        WHERE release_id = 1
    """).rowcount

    print("Tracks verwijderd:", deleted_tracks)

    deleted_release = c.execute("""
        DELETE FROM releases
        WHERE id = 1
    """).rowcount

    print("Release verwijderd:", deleted_release)

    c.commit()

else:
    print()
    print("VEILIGHEIDSSTOP!")
    print("Release ID 1 komt niet overeen met de verwachte testrelease.")
    print("Er is niets verwijderd.")
    c.close()
    raise SystemExit

print()
print("=== CONTROLE XCV 11 ===")

rows = c.execute("""
    SELECT
        r.id,
        r.artist,
        r.title,
        r.label,
        r.catalog,
        r.discogs,
        r.storage_code,
        COUNT(t.id)
    FROM releases r
    LEFT JOIN tracks t ON t.release_id = r.id
    WHERE r.storage_code = 'XCV 11'
    GROUP BY r.id
    ORDER BY r.id
""").fetchall()

for row in rows:
    print(row)

print()
print("=== TOTALEN ===")

print(
    "Releases:",
    c.execute("SELECT COUNT(*) FROM releases").fetchone()[0]
)

print(
    "Tracks:",
    c.execute("SELECT COUNT(*) FROM tracks").fetchone()[0]
)

print()
print("=== KASTCODE CONTROLE ===")

for code in ("RAPCASE", "Little Box", "SOLD"):
    aantal = c.execute("""
        SELECT COUNT(*)
        FROM releases
        WHERE storage_code = ?
    """, (code,)).fetchone()[0]

    print(f"{code}: {aantal} releases")

c.close()

print()
print("=" * 80)
print("OPRUIMING KLAAR")
print("=" * 80)

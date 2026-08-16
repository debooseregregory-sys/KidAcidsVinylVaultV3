import sqlite3

DB = r"C:\Users\andyb\Desktop\KidAcidsVinylVaultV3\data\vinylvault.db"

c = sqlite3.connect(DB)

print("=" * 80)
print("VINYLVAULT V3 - IMPORT CONTROLE")
print("=" * 80)

print()
print("RELEASES :", c.execute("SELECT COUNT(*) FROM releases").fetchone()[0])
print("TRACKS   :", c.execute("SELECT COUNT(*) FROM tracks").fetchone()[0])

print()
print("=== XCV 11 ===")

rows = c.execute("""
    SELECT
        r.id,
        r.artist,
        r.title,
        r.label,
        r.catalog,
        r.storage_code,
        t.position,
        t.artist,
        t.title
    FROM releases r
    LEFT JOIN tracks t ON t.release_id = r.id
    WHERE r.storage_code = 'XCV 11'
    ORDER BY t.id
""").fetchall()

for row in rows:
    print(
        f"RELEASE {row[0]} | "
        f"{row[1]} | {row[2]} | "
        f"{row[3]} | {row[4]} | {row[5]}"
    )
    print(
        f"    {row[6]} | {row[7]} | {row[8]}"
    )

print()
print("=== PLANETARY ASSAULT SYSTEMS ===")

rows = c.execute("""
    SELECT
        t.id,
        t.position,
        t.artist,
        t.title,
        r.id,
        r.storage_code,
        r.discogs
    FROM tracks t
    JOIN releases r ON r.id = t.release_id
    WHERE lower(t.artist) LIKE '%planetary assault systems%'
    ORDER BY t.id
""").fetchall()

for row in rows:
    print(row)

c.close()

print()
print("=" * 80)
print("CONTROLE KLAAR")
print("=" * 80)

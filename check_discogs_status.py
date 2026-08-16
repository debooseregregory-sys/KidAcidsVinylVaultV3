import sqlite3

DB = r"C:\Users\andyb\Desktop\KidAcidsVinylVaultV3\data\vinylvault.db"

c = sqlite3.connect(DB)

print("=" * 80)
print("VINYLVAULT V3 - DISCOGS STATUS")
print("=" * 80)

totaal = c.execute("""
    SELECT COUNT(*)
    FROM releases
""").fetchone()[0]

met_discogs = c.execute("""
    SELECT COUNT(*)
    FROM releases
    WHERE TRIM(COALESCE(discogs, '')) != ''
""").fetchone()[0]

zonder_discogs = c.execute("""
    SELECT COUNT(*)
    FROM releases
    WHERE TRIM(COALESCE(discogs, '')) = ''
""").fetchone()[0]

met_cover = c.execute("""
    SELECT COUNT(*)
    FROM releases
    WHERE TRIM(COALESCE(cover, '')) != ''
""").fetchone()[0]

met_jaar = c.execute("""
    SELECT COUNT(*)
    FROM releases
    WHERE year IS NOT NULL
      AND year > 0
""").fetchone()[0]

print()
print("Totaal releases       :", totaal)
print("Met Discogs ID        :", met_discogs)
print("Zonder Discogs ID     :", zonder_discogs)
print("Met cover             :", met_cover)
print("Met jaar              :", met_jaar)

print()
print("=== VOORBEELD RELEASES ===")

rows = c.execute("""
    SELECT
        id,
        artist,
        title,
        label,
        catalog,
        storage_code,
        discogs,
        year,
        cover
    FROM releases
    ORDER BY id
    LIMIT 10
""").fetchall()

for row in rows:
    print()
    print("ID      :", row[0])
    print("Artist  :", row[1])
    print("Title   :", row[2])
    print("Label   :", row[3])
    print("Catalog :", row[4])
    print("Kast    :", row[5])
    print("Discogs :", row[6])
    print("Year    :", row[7])
    print("Cover   :", row[8])

c.close()

print()
print("=" * 80)
print("CONTROLE KLAAR")
print("=" * 80)

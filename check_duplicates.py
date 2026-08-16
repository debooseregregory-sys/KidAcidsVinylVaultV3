import sqlite3

DB = r"C:\Users\andyb\Desktop\KidAcidsVinylVaultV3\data\vinylvault.db"

c = sqlite3.connect(DB)

print("=" * 80)
print("VINYLVAULT V3 - DUBBELE KASTCODES")
print("=" * 80)

rows = c.execute("""
    SELECT
        storage_code,
        COUNT(*) AS aantal
    FROM releases
    WHERE TRIM(storage_code) <> ''
    GROUP BY storage_code
    HAVING COUNT(*) > 1
    ORDER BY storage_code
""").fetchall()

print("Kastcodes met meerdere releases:", len(rows))
print()

for storage, aantal in rows[:100]:
    print(f"{storage} -> {aantal} releases")

print()
print("=== XCV 11 DETAIL ===")

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

c.close()

print()
print("=" * 80)
print("CONTROLE KLAAR")
print("=" * 80)

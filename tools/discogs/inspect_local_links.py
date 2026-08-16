import sqlite3

db = r".\data\vinylvault.db"

c = sqlite3.connect(db)

print("=== LOKALE DATABASE ===")

checks = [
    ("Releases", "SELECT COUNT(*) FROM releases"),
    ("Met Discogs ID", """
        SELECT COUNT(*)
        FROM releases
        WHERE discogs IS NOT NULL
        AND TRIM(discogs) <> ''
    """),
    ("Met Discogs link", """
        SELECT COUNT(*)
        FROM releases
        WHERE discogs_link IS NOT NULL
        AND TRIM(discogs_link) <> ''
    """),
    ("Met catalog", """
        SELECT COUNT(*)
        FROM releases
        WHERE catalog IS NOT NULL
        AND TRIM(catalog) <> ''
    """),
    ("Met kastcode", """
        SELECT COUNT(*)
        FROM releases
        WHERE storage_code IS NOT NULL
        AND TRIM(storage_code) <> ''
    """),
    ("Met artist", """
        SELECT COUNT(*)
        FROM releases
        WHERE artist IS NOT NULL
        AND TRIM(artist) <> ''
    """),
    ("Met title", """
        SELECT COUNT(*)
        FROM releases
        WHERE title IS NOT NULL
        AND TRIM(title) <> ''
    """),
]

for name, sql in checks:
    value = c.execute(sql).fetchone()[0]
    print(f"{name}: {value}")

c.close()

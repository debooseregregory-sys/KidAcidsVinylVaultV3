import sqlite3, os

db = os.path.abspath(r".\data\vinylvault.db")
c = sqlite3.connect(db)

print("=" * 70)
print("KID ACID'S VINYLVAULT V3 - SNELLE DATABASE AUDIT")
print("=" * 70)
print("Database:", db)
print()

def q(sql):
    return c.execute(sql).fetchone()[0]

releases = q("SELECT COUNT(*) FROM releases")
tracks = q("SELECT COUNT(*) FROM tracks")

print("Releases :", releases)
print("Tracks   :", tracks)
print()

checks = [
    ("Releases zonder artist",
     "SELECT COUNT(*) FROM releases WHERE artist IS NULL OR TRIM(artist)=''"),

    ("Releases zonder titel",
     "SELECT COUNT(*) FROM releases WHERE title IS NULL OR TRIM(title)=''"),

    ("Releases zonder tracks",
     """SELECT COUNT(*) FROM releases r
        WHERE NOT EXISTS (SELECT 1 FROM tracks t WHERE t.release_id=r.id)"""),

    ("Tracks zonder release",
     """SELECT COUNT(*) FROM tracks t
        WHERE NOT EXISTS (SELECT 1 FROM releases r WHERE r.id=t.release_id)"""),

    ("Tracks zonder titel",
     "SELECT COUNT(*) FROM tracks WHERE title IS NULL OR TRIM(title)=''"),

    ("Tracks zonder positie",
     "SELECT COUNT(*) FROM tracks WHERE position IS NULL OR TRIM(position)=''"),

    ("Dubbele Discogs IDs",
     """SELECT COUNT(*) FROM (
        SELECT discogs FROM releases
        WHERE discogs IS NOT NULL AND TRIM(discogs)!=''
        GROUP BY discogs HAVING COUNT(*)>1)"""),

    ("Dubbele kastcodes",
     """SELECT COUNT(*) FROM (
        SELECT storage_code FROM releases
        WHERE storage_code IS NOT NULL AND TRIM(storage_code)!=''
        GROUP BY storage_code HAVING COUNT(*)>1)"""),

    ("Dubbele trackposities",
     """SELECT COUNT(*) FROM (
        SELECT release_id,position FROM tracks
        WHERE position IS NOT NULL AND TRIM(position)!=''
        GROUP BY release_id,position HAVING COUNT(*)>1)"""),
]

for name, sql in checks:
    value = q(sql)
    print(f"{name:<30}: {value}")

print()
print("=" * 70)
print("DATABASE GEWIJZIGD: NEE")
print("=" * 70)

c.close()

import sqlite3
from pathlib import Path

DB = Path(r"C:\Users\andyb\Desktop\KidAcidsVinylVaultV3\data\vinylvault.db")

conn = sqlite3.connect(DB)
cur = conn.cursor()

cur.execute("""
    UPDATE releases
    SET discogs_link =
        'https://www.discogs.com/release/' || TRIM(discogs),
        updated_at = datetime('now')
    WHERE discogs IS NOT NULL
      AND TRIM(discogs) <> ''
""")

changed = cur.rowcount

conn.commit()

cur.execute("""
    SELECT COUNT(*)
    FROM releases
    WHERE discogs IS NOT NULL
      AND TRIM(discogs) <> ''
      AND discogs_link IS NOT NULL
      AND TRIM(discogs_link) <> ''
""")

links = cur.fetchone()[0]

print()
print("=" * 80)
print("DISCOGS LINKS AUTOMATISCH GEVULD")
print("=" * 80)
print()
print(f"Links bijgewerkt : {changed}")
print(f"Releases met ID  : {links}")
print()
print("KASTCODES NIET AANGERAAKT.")
print("TRACKS NIET AANGERAAKT.")
print("MP3-KOPPELINGEN NIET AANGERAAKT.")
print()

conn.close()

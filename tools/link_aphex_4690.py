import sqlite3
import shutil
import os
from datetime import datetime

DB = os.path.abspath(r".\data\vinylvault.db")
BACKUP_DIR = os.path.abspath(r".\data\backup")

os.makedirs(BACKUP_DIR, exist_ok=True)

stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
backup = os.path.join(
    BACKUP_DIR,
    f"vinylvault_before_aphex_{stamp}.db"
)

print("=" * 80)
print("KID ACID'S VINYLVAULT V3")
print("APHEX TWIN - EXACTE DISCOGS KOPPELING")
print("=" * 80)

print()
print("Database:", DB)

# ------------------------------------------------------------
# BACKUP
# ------------------------------------------------------------

shutil.copy2(DB, backup)

print()
print("BACKUP:")
print(backup)

# ------------------------------------------------------------
# DATABASE
# ------------------------------------------------------------

conn = sqlite3.connect(DB)
cur = conn.cursor()

# ------------------------------------------------------------
# RELEASE
# ------------------------------------------------------------

release = cur.execute("""
SELECT id, artist, title, discogs, storage_code
FROM releases
WHERE id = 9
""").fetchone()

if not release:
    print()
    print("FOUT: release 9 bestaat niet.")
    conn.close()
    raise SystemExit

release_id, artist, old_title, old_discogs, storage_code = release

print()
print("BESTAANDE RELEASE")
print()
print("V3 ID     :", release_id)
print("Artist    :", artist)
print("Titel     :", old_title)
print("Discogs   :", old_discogs)
print("Kastcode  :", storage_code)

# ------------------------------------------------------------
# DISCOGS GEGEVENS
# ------------------------------------------------------------

discogs_id = "4690"
new_title = "Digeridoo"
year = 1992

print()
print("NIEUWE DISCOGS GEGEVENS")
print()
print("Discogs   :", discogs_id)
print("Titel     :", new_title)
print("Jaar      :", year)

# ------------------------------------------------------------
# RELEASE BIJWERKEN
# ------------------------------------------------------------

cur.execute("""
UPDATE releases
SET
    title = ?,
    discogs = ?,
    year = ?,
    updated_at = CURRENT_TIMESTAMP
WHERE id = ?
""", (
    new_title,
    discogs_id,
    year,
    release_id
))

# ------------------------------------------------------------
# BESTAANDE TRACKS
# ------------------------------------------------------------

tracks = cur.execute("""
SELECT id, position, artist, title, duration
FROM tracks
WHERE release_id = ?
ORDER BY id
""", (release_id,)).fetchall()

print()
print("TRACKS VOOR CORRECTIE")
print()

for t in tracks:
    print(
        t[0],
        "|",
        t[1],
        "|",
        t[3]
    )

# ------------------------------------------------------------
# POSITIES CORRIGEREN
# ------------------------------------------------------------

position_map = {
    "Didgeridoo": "A1",
    "Flap Head": "A2",
    "Phloam": "B1",
    "Isoprophlex": "B2",
}

for track_id, old_position, track_artist, title, duration in tracks:

    new_position = position_map.get(title)

    if new_position:

        cur.execute("""
        UPDATE tracks
        SET position = ?
        WHERE id = ?
        """, (
            new_position,
            track_id
        ))

# ------------------------------------------------------------
# COMMIT
# ------------------------------------------------------------

conn.commit()

# ------------------------------------------------------------
# CONTROLE
# ------------------------------------------------------------

print()
print("=" * 80)
print("DEFINITIEVE RELEASE")
print("=" * 80)

release = cur.execute("""
SELECT id, artist, title, discogs, year, storage_code
FROM releases
WHERE id = ?
""", (release_id,)).fetchone()

print()
print("Release ID :", release[0])
print("Artist     :", release[1])
print("Titel      :", release[2])
print("Discogs ID :", release[3])
print("Jaar       :", release[4])
print("Kastcode   :", release[5])

print()
print("TRACKS:")

tracks = cur.execute("""
SELECT position, artist, title, duration
FROM tracks
WHERE release_id = ?
ORDER BY id
""", (release_id,)).fetchall()

for position, track_artist, title, duration in tracks:

    print(
        f"{position:4} | "
        f"{track_artist:25} | "
        f"{title}"
    )

print()
print("=" * 80)
print("KOPPELING GESLAAGD")
print("=" * 80)

print()
print(
    f"{artist} -> {new_title} -> "
    f"Discogs {discogs_id} -> Kastcode {storage_code}"
)

print()
print("DATABASE GEWIJZIGD: JA")
print("BACKUP:", backup)

print("=" * 80)

conn.close()

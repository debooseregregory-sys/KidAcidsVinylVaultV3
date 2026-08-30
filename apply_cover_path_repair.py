import sqlite3
import os

DB = r".\data\vinylvault.db"

OLD_ROOT = r"C:\Users\andyb\Desktop\KidAcidsVinylVaultV3\covers"
NEW_ROOT = os.path.abspath(r".\covers")

conn = sqlite3.connect(DB)

rows = conn.execute("""
    SELECT id, cover
    FROM releases
    WHERE cover IS NOT NULL
      AND TRIM(cover) != ''
""").fetchall()

changed = 0
skipped = 0

for release_id, cover in rows:
    if not cover.lower().startswith(OLD_ROOT.lower()):
        skipped += 1
        continue

    filename = os.path.basename(cover)
    new_path = os.path.join(NEW_ROOT, filename)

    if not os.path.isfile(new_path):
        print(f"OVERGESLAGEN - bestand bestaat niet: ID {release_id}")
        print(new_path)
        continue

    conn.execute(
        "UPDATE releases SET cover = ? WHERE id = ?",
        (new_path, release_id)
    )

    changed += 1

conn.commit()

print()
print("=" * 70)
print("COVER PAD REPARATIE VOLTOOID")
print("=" * 70)
print("Aangepast :", changed)
print("Overgeslagen:", skipped)
print()

# Controle
remaining = conn.execute("""
    SELECT COUNT(*)
    FROM releases
    WHERE cover LIKE ?
""", (OLD_ROOT + "%",)).fetchone()[0]

valid = 0

for (cover,) in conn.execute("""
    SELECT cover
    FROM releases
    WHERE cover IS NOT NULL
      AND TRIM(cover) != ''
"""):
    if os.path.isfile(cover):
        valid += 1

total = conn.execute("""
    SELECT COUNT(*)
    FROM releases
    WHERE cover IS NOT NULL
      AND TRIM(cover) != ''
""").fetchone()[0]

print("Resterende oude paden :", remaining)
print("Totaal cover-paden    :", total)
print("Bestaande cover-files :", valid)

conn.close()
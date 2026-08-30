import sqlite3
import os
import shutil
from datetime import datetime

DB = r".\data\vinylvault.db"

OLD_ROOT = r"C:\Users\andyb\Desktop\KidAcidsVinylVaultV3\covers"
NEW_ROOT = os.path.abspath(r".\covers")

print("DATABASE :", os.path.abspath(DB))
print("OUDE MAP :", OLD_ROOT)
print("NIEUWE MAP:", NEW_ROOT)
print()

conn = sqlite3.connect(DB)

rows = conn.execute("""
    SELECT id, artist, title, cover
    FROM releases
    WHERE cover IS NOT NULL
      AND TRIM(cover) != ''
""").fetchall()

print("TOTAAL RELEASES MET COVER:", len(rows))
print()

matches = 0
missing = 0

for release_id, artist, title, cover in rows:
    filename = os.path.basename(cover)

    if cover.lower().startswith(OLD_ROOT.lower()):
        new_path = os.path.join(NEW_ROOT, filename)

        if os.path.isfile(new_path):
            matches += 1
        else:
            missing += 1

print("KUNNEN WORDEN HERSTELD:", matches)
print("BESTAND NIET GEVONDEN:", missing)

print()
print("VOORBEELDEN:")
print("-" * 80)

shown = 0

for release_id, artist, title, cover in rows:
    if cover.lower().startswith(OLD_ROOT.lower()):
        filename = os.path.basename(cover)
        new_path = os.path.join(NEW_ROOT, filename)

        if os.path.isfile(new_path):
            print(f"ID {release_id}: {artist} - {title}")
            print(" oud:", cover)
            print(" nieuw:", new_path)
            print()

            shown += 1
            if shown >= 10:
                break

conn.close()

print("-" * 80)
print()
print("DIT WAS ALLEEN EEN CONTROLE.")
print("ER IS NOG NIETS AANGEPAST.")
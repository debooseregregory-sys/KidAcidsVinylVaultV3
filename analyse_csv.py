import csv
from collections import Counter, defaultdict

CSV = r"C:\Users\andyb\Desktop\vinyl_collectie.csv"

with open(CSV, encoding="cp1252", newline="") as f:
    rows = list(csv.reader(f))

data = rows[1:]

# Verschillende mogelijke sleutels tellen
keys_storage = set()
keys_label_storage = set()
keys_artist_label_storage = set()
keys_artist_label_code_storage = set()

for row in data:
    if len(row) < 4:
        continue

    artist = row[0].strip()
    label = row[2].strip()
    storage = row[3].strip()

    if not storage:
        continue

    keys_storage.add(storage)
    keys_label_storage.add((label, storage))
    keys_artist_label_storage.add((artist, label, storage))
    keys_artist_label_code_storage.add(
        (artist, label, storage)
    )

print("=" * 80)
print("VINYLVAULT CSV STRUCTUUR ANALYSE")
print("=" * 80)
print()
print("CSV regels                 :", len(data))
print("Unieke kastcodes           :", len(keys_storage))
print("Uniek Label/Catalog + kast :", len(keys_label_storage))
print("Uniek Artist + Label + kast:", len(keys_artist_label_storage))
print()

print("=== D 071 ===")
print()

for i, row in enumerate(data, 1):
    if len(row) >= 4 and row[3].strip() == "D 071":
        print(
            f"{i:5} | "
            f"{row[0].strip():35} | "
            f"{row[1].strip():35} | "
            f"{row[2].strip():25} | "
            f"{row[3].strip()}"
        )

print()
print("=== XCV 11 ===")
print()

for i, row in enumerate(data, 1):
    if len(row) >= 4 and row[3].strip() == "XCV 11":
        print(
            f"{i:5} | "
            f"{row[0].strip():35} | "
            f"{row[1].strip():35} | "
            f"{row[2].strip():25} | "
            f"{row[3].strip()}"
        )

print()
print("=" * 80)

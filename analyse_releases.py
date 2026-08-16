import csv
from collections import defaultdict

CSV = r"C:\Users\andyb\Desktop\vinyl_collectie.csv"

with open(CSV, encoding="cp1252", newline="") as f:
    rows = list(csv.reader(f))[1:]

groups = defaultdict(list)

for row in rows:
    if len(row) < 4:
        continue

    artist = row[0].strip()
    track = row[1].strip()
    label = row[2].strip()
    storage = row[3].strip()

    if not storage:
        continue

    groups[(label, storage)].append(
        (artist, track)
    )

print("=" * 80)
print("VINYLVAULT RELEASE GROEPERING ANALYSE")
print("=" * 80)
print()

print("CSV regels:", len(rows))
print("Unieke Label/Catalog + kast:", len(groups))
print()

# Toon groepen waarbij dezelfde kastcode meerdere verschillende
# Label/Catalog combinaties bevat.
by_storage = defaultdict(list)

for (label, storage), tracks in groups.items():
    by_storage[storage].append(
        (label, tracks)
    )

multi = {
    storage: releases
    for storage, releases in by_storage.items()
    if len(releases) > 1
}

print("Kastcodes met meerdere Label/Catalog groepen:", len(multi))
print()

print("=== VOORBEELDEN ===")
print()

count = 0

for storage, releases in multi.items():
    print("KASTCODE:", storage)

    for label, tracks in releases:
        print("  LABEL/CATALOG:", label)
        print("  REGELS:", len(tracks))

        for artist, track in tracks[:5]:
            print("     ", artist, "|", track)

        if len(tracks) > 5:
            print("      ...")

    print()

    count += 1

    if count >= 30:
        break

print("=" * 80)

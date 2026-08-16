from pathlib import Path

ROOT = Path(r"D:\01. MP3's")

print("=" * 70)
print("KID ACID'S VINYLVAULT V3")
print("RECHTSTREEKS MP3-BESTANDEN ZOEKEN")
print("=" * 70)
print()

searches = [
    "diesel drudge",
    "planetary assault systems",
]

found = []

print("Zoeken in:")
print(ROOT)
print()

if not ROOT.exists():
    print("FOUT: MP3-map bestaat niet:")
    print(ROOT)
    raise SystemExit

for path in ROOT.rglob("*.mp3"):

    filename = path.name.lower()
    fullpath = str(path).lower()

    matched = False

    for search in searches:
        if search in filename or search in fullpath:
            matched = True
            break

    if matched:
        found.append(path)


print("=" * 70)
print("RESULTAAT")
print("=" * 70)
print()

print("Aantal gevonden:", len(found))
print()

for path in found:
    print(path)

print()
print("=" * 70)
print("ZOEKOPDRACHT KLAAR")
print("=" * 70)
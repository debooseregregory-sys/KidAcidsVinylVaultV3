import sqlite3
import re

DB = "data/vinylvault.db"


def normalize(text):
    if not text:
        return ""

    text = str(text).lower().strip()
    text = text.replace("&", " and ")

    text = re.sub(
        r"[\(\)\[\]\{\}\.,;:'\"!?\-_\/\\]+",
        " ",
        text
    )

    return " ".join(text.split())


db = sqlite3.connect(DB)
db.row_factory = sqlite3.Row


print()
print("=" * 70)
print("KID ACID'S VINYLVAULT V3")
print("MP3 MATCH TEST")
print("=" * 70)


# ------------------------------------------------------------
# MP3 INDEX
# ------------------------------------------------------------

print()
print("MP3 DATABASE INLEZEN...")

mp3_rows = db.execute(
    """
    SELECT id, artist, title, path
    FROM mp3_files
    WHERE artist != ''
      AND artist IS NOT NULL
      AND title != ''
      AND title IS NOT NULL
    """
).fetchall()


mp3_index = {}

for mp3 in mp3_rows:

    key = (
        normalize(mp3["artist"]),
        normalize(mp3["title"])
    )

    mp3_index.setdefault(
        key,
        []
    ).append(mp3)


print(
    "Bruikbare MP3's:",
    len(mp3_rows)
)


# ------------------------------------------------------------
# TRACKS
# ------------------------------------------------------------

tracks = db.execute(
    """
    SELECT id, position, artist, title
    FROM tracks
    ORDER BY id
    """
).fetchall()


print(
    "Vinyltracks:",
    len(tracks)
)


# ------------------------------------------------------------
# MATCHEN
# ------------------------------------------------------------

matched = 0
unmatched = 0
multiple = 0


print()
print("=" * 70)
print("MATCH RESULTAAT")
print("=" * 70)


for track in tracks:

    key = (
        normalize(track["artist"]),
        normalize(track["title"])
    )

    candidates = mp3_index.get(
        key,
        []
    )

    if not candidates:

        unmatched += 1

        continue


    if len(candidates) > 1:

        multiple += 1


    matched += 1


print()
print("=" * 70)
print("RESULTAAT")
print("=" * 70)

print(
    "Tracks:",
    len(tracks)
)

print(
    "Exacte matches:",
    matched
)

print(
    "Geen match:",
    unmatched
)

print(
    "Meerdere MP3's:",
    multiple
)

print()
print(
    "Database NIET gewijzigd."
)


db.close()
import sqlite3
import re

DB = "data/vinylvault.db"


def norm(text):
    if not text:
        return ""

    text = str(text).lower()

    text = text.replace("&", " and ")
    text = text.replace("'", "")
    text = text.replace("’", "")

    text = re.sub(r"[^a-z0-9]+", " ", text)

    return " ".join(text.split())


db = sqlite3.connect(DB)
db.row_factory = sqlite3.Row


# ------------------------------------------------------------
# MP3 INDEX
# ------------------------------------------------------------

mp3s = db.execute(
    """
    SELECT id, artist, title, path
    FROM mp3_files
    WHERE artist != ''
      AND artist IS NOT NULL
      AND title != ''
      AND title IS NOT NULL
    """
).fetchall()


index = {}

for mp3 in mp3s:

    key = (
        norm(mp3["artist"]),
        norm(mp3["title"])
    )

    index.setdefault(key, []).append(mp3)


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


exact = 0
multiple = 0
none = 0


print()
print("=" * 70)
print("MP3 MATCH RAPPORT")
print("=" * 70)

print("MP3's :", len(mp3s))
print("Tracks:", len(tracks))
print()


for track in tracks:

    key = (
        norm(track["artist"]),
        norm(track["title"])
    )

    found = index.get(key, [])


    if len(found) == 1:

        exact += 1


    elif len(found) > 1:

        multiple += 1


    else:

        none += 1


print("=" * 70)
print("RESULTAAT")
print("=" * 70)

print("Exacte match :", exact)
print("Meerdere MP3 :", multiple)
print("Geen match    :", none)

print()
print("DATABASE NIET GEWIJZIGD.")

db.close()
from database.database import get_connection


def normalize(value):
    if not value:
        return ""

    value = str(value).lower().strip()

    for char in "-_.,'\"()[]{}":
        value = value.replace(char, " ")

    return " ".join(value.split())


connection = get_connection()

print("=" * 70)
print("KID ACID'S VINYLVAULT V3")
print("MP3 MATCHING CONTROLE")
print("=" * 70)
print()

tracks = connection.execute("""
    SELECT
        t.id,
        t.release_id,
        t.position,
        t.artist,
        t.title,
        r.artist AS release_artist,
        r.title AS release_title
    FROM tracks t
    JOIN releases r
        ON r.id = t.release_id
    ORDER BY r.artist, r.title, t.id
""").fetchall()

mp3s = connection.execute("""
    SELECT
        id,
        artist,
        title,
        filename,
        path
    FROM mp3_files
    ORDER BY artist, title
""").fetchall()

print("Tracks:", len(tracks))
print("MP3s:", len(mp3s))
print()

exact_matches = []
possible_matches = []
no_matches = []

for track in tracks:

    track_artist = normalize(track["artist"] or track["release_artist"])
    track_title = normalize(track["title"])

    exact = []
    possible = []

    for mp3 in mp3s:

        mp3_artist = normalize(mp3["artist"])
        mp3_title = normalize(mp3["title"])

        if (
            mp3_artist == track_artist
            and mp3_title == track_title
        ):
            exact.append(mp3)

        elif (
            mp3_title == track_title
            and track_title
        ):
            possible.append(mp3)

    if exact:
        exact_matches.append(
            (track, exact)
        )

    elif possible:
        possible_matches.append(
            (track, possible)
        )

    else:
        no_matches.append(track)


print("=" * 70)
print("EXACTE MATCHES")
print("=" * 70)
print()

print("Aantal tracks met exacte match:", len(exact_matches))
print()

for track, matches in exact_matches[:100]:

    print(
        f"{track['position']} | "
        f"{track['release_artist']} - "
        f"{track['title']}"
    )

    for mp3 in matches:
        print(
            f"    MP3 #{mp3['id']} | "
            f"{mp3['artist']} - "
            f"{mp3['title']}"
        )

    print()


print("=" * 70)
print("MOGELIJKE MATCHES OP TITEL")
print("=" * 70)
print()

print(
    "Aantal tracks met alleen titel-match:",
    len(possible_matches)
)

print()

for track, matches in possible_matches[:100]:

    print(
        f"{track['position']} | "
        f"{track['release_artist']} - "
        f"{track['title']}"
    )

    for mp3 in matches:
        print(
            f"    MP3 #{mp3['id']} | "
            f"{mp3['artist']} - "
            f"{mp3['title']}"
        )

    print()


print("=" * 70)
print("GEEN MATCH")
print("=" * 70)
print()

print(
    "Aantal tracks zonder MP3-match:",
    len(no_matches)
)

print()

for track in no_matches[:100]:

    print(
        f"{track['position']} | "
        f"{track['release_artist']} - "
        f"{track['title']}"
    )


print()
print("=" * 70)
print("CONTROLE KLAAR")
print("=" * 70)

connection.close()
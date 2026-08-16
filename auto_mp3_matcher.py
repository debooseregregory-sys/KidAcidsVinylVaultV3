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
print("VEILIGE AUTOMATISCHE MP3 MATCHER")
print("=" * 70)
print()

tracks = connection.execute("""
    SELECT
        t.id,
        t.release_id,
        t.position,
        t.artist,
        t.title,
        r.artist AS release_artist
    FROM tracks t
    JOIN releases r
        ON r.id = t.release_id
    ORDER BY t.id
""").fetchall()

mp3s = connection.execute("""
    SELECT
        id,
        artist,
        title,
        filename,
        path
    FROM mp3_files
""").fetchall()

print("Tracks:", len(tracks))
print("MP3s:", len(mp3s))
print()

created = 0
existing = 0
ambiguous = 0
not_found = 0

for track in tracks:

    track_artist = normalize(
        track["artist"] or track["release_artist"]
    )

    track_title = normalize(
        track["title"]
    )

    if not track_artist or not track_title:
        not_found += 1
        continue

    matches = []

    for mp3 in mp3s:

        mp3_artist = normalize(
            mp3["artist"]
        )

        mp3_title = normalize(
            mp3["title"]
        )

        if (
            mp3_artist == track_artist
            and mp3_title == track_title
        ):
            matches.append(mp3)

    if not matches:
        not_found += 1
        continue

    for mp3 in matches:

        link = connection.execute(
            """
            SELECT 1
            FROM track_mp3
            WHERE track_id = ?
              AND mp3_id = ?
            """,
            (
                track["id"],
                mp3["id"],
            )
        ).fetchone()

        if link:
            existing += 1
            continue

        connection.execute(
            """
            INSERT INTO track_mp3
            (
                track_id,
                mp3_id
            )
            VALUES (?, ?)
            """,
            (
                track["id"],
                mp3["id"],
            )
        )

        created += 1

        print(
            f"[LINK] "
            f"{track['position']} | "
            f"{track_artist} - "
            f"{track['title']}"
        )

        print(
            f"       -> "
            f"MP3 #{mp3['id']} | "
            f"{mp3['filename']}"
        )

connection.commit()

print()
print("=" * 70)
print("RESULTAAT")
print("=" * 70)
print()
print("Nieuwe links :", created)
print("Bestaande links:", existing)
print("Niet gevonden:", not_found)
print("Ambigu:", ambiguous)
print()

print("=" * 70)
print("MATCHER KLAAR")
print("=" * 70)

connection.close()

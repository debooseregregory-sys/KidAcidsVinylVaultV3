import os
import sqlite3
from database.database import get_connection

SEARCH_ROOT = r"D:\01. MP3's"

def norm(value):
    return " ".join(str(value or "").lower().replace("_", " ").replace("-", " ").split())

def main():
    artist = "Planetary Assault Systems"
    title = "Diesel Drudge"

    print("=" * 70)
    print("KID ACID'S VINYLVAULT V3")
    print("HANDMATIGE MP3 ZOEKER")
    print("=" * 70)
    print()
    print("Track:")
    print(f"  {artist} - {title}")
    print()
    print("Database:", "data\\vinylvault.db")
    print("Zoekmap :", SEARCH_ROOT)
    print()

    conn = get_connection()

    try:
        rows = conn.execute(
            """
            SELECT
                id,
                artist,
                title,
                filename,
                path
            FROM mp3_files
            """
        ).fetchall()
    finally:
        conn.close()

    artist_n = norm(artist)
    title_n = norm(title)

    exact = []
    title_matches = []
    artist_matches = []
    filename_matches = []

    for row in rows:
        mp3_artist = norm(row["artist"])
        mp3_title = norm(row["title"])
        filename = norm(row["filename"])
        path = str(row["path"] or "")

        if mp3_artist == artist_n and mp3_title == title_n:
            exact.append(row)
            continue

        if mp3_title == title_n:
            title_matches.append(row)
            continue

        if artist_n in mp3_artist and artist_n:
            artist_matches.append(row)
            continue

        if title_n and title_n in filename:
            filename_matches.append(row)

    print("=" * 70)
    print("DATABASE ZOEKRESULTAAT")
    print("=" * 70)
    print()

    if exact:
        print("EXACTE MATCHES:", len(exact))
        for row in exact:
            print(f"ID     : {row['id']}")
            print(f"Artist : {row['artist']}")
            print(f"Title  : {row['title']}")
            print(f"File   : {row['filename']}")
            print(f"Path   : {row['path']}")
            print("-" * 70)
    else:
        print("Geen exacte database-match.")

    print()
    print("TITEL-MATCHES:", len(title_matches))

    for row in title_matches:
        print(
            f"ID {row['id']} | "
            f"{row['artist']} - {row['title']} | "
            f"{row['path']}"
        )

    print()
    print("ARTIEST-MATCHES:", len(artist_matches))

    for row in artist_matches[:30]:
        print(
            f"ID {row['id']} | "
            f"{row['artist']} - {row['title']} | "
            f"{row['path']}"
        )

    print()
    print("=" * 70)
    print("RECHTSTREEKS IN D:\\01. MP3'S ZOEKEN")
    print("=" * 70)
    print()

    filesystem_matches = []

    if os.path.isdir(SEARCH_ROOT):
        for root, dirs, files in os.walk(SEARCH_ROOT):
            for filename in files:
                if not filename.lower().endswith(".mp3"):
                    continue

                full_path = os.path.join(root, filename)
                name_n = norm(os.path.splitext(filename)[0])

                artist_in = artist_n in name_n
                title_in = title_n in name_n

                if artist_in and title_in:
                    filesystem_matches.append(full_path)
    else:
        print("ZOEKMAP BESTAAT NIET:")
        print(SEARCH_ROOT)

    print("Bestandsmatches:", len(filesystem_matches))
    print()

    if filesystem_matches:
        for path in filesystem_matches:
            print(path)
    else:
        print("Geen bestand gevonden met zowel artiest als titel.")

    print()
    print("=" * 70)
    print("ZOEKOPDRACHT KLAAR")
    print("=" * 70)

if __name__ == "__main__":
    main()

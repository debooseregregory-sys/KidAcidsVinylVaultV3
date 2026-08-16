import sqlite3
import os
import re
import unicodedata
from difflib import SequenceMatcher


DB = os.path.join("data", "vinylvault.db")

MIN_SCORE = 70
PREFERRED_SCORE = 85


def normalize(text):
    """Maak tekst geschikt voor betrouwbare vergelijking."""

    if not text:
        return ""

    text = str(text)

    # Accenten verwijderen
    text = unicodedata.normalize("NFKD", text)
    text = "".join(
        char for char in text
        if not unicodedata.combining(char)
    )

    text = text.lower()

    # & = and
    text = text.replace("&", " and ")

    # Typische separators
    text = re.sub(r"[_\-]+", " ", text)

    # Haakjes behouden als informatie,
    # maar speciale tekens verwijderen
    text = re.sub(r"[()\[\]{}]", " ", text)

    # Speciale tekens verwijderen
    text = re.sub(r"[^a-z0-9]+", " ", text)

    # Dubbele spaties
    text = re.sub(r"\s+", " ", text).strip()

    return text


def similarity(a, b):
    if not a or not b:
        return 0.0

    return SequenceMatcher(None, a, b).ratio() * 100


def artist_score(track_artist, mp3_artist):
    if not track_artist or not mp3_artist:
        return 0

    a = normalize(track_artist)
    b = normalize(mp3_artist)

    if not a or not b:
        return 0

    if a == b:
        return 100

    return similarity(a, b)


def title_score(track_title, mp3_title):
    if not track_title or not mp3_title:
        return 0

    a = normalize(track_title)
    b = normalize(mp3_title)

    if not a or not b:
        return 0

    if a == b:
        return 100

    return similarity(a, b)


def calculate_score(track, mp3):
    """
    Bereken totaalscore.

    Titel krijgt meer gewicht dan artiest.
    """

    track_artist = track["artist"] or ""
    track_title = track["title"] or ""

    mp3_artist = mp3["artist"] or ""
    mp3_title = mp3["title"] or ""

    a_score = artist_score(track_artist, mp3_artist)
    t_score = title_score(track_title, mp3_title)

    # Titel is belangrijker
    total = (t_score * 0.70) + (a_score * 0.30)

    # Exacte match extra sterk
    if normalize(track_artist) == normalize(mp3_artist):
        if normalize(track_title) == normalize(mp3_title):
            total = 100

    return round(total, 2)


def get_existing_links(conn):
    """
    Tracks die al een preferred MP3 hebben.
    Die laten we met rust.
    """

    rows = conn.execute(
        """
        SELECT track_id
        FROM track_mp3
        WHERE is_preferred = 1
        """
    ).fetchall()

    return {row[0] for row in rows}


def get_tracks(conn):
    conn.row_factory = sqlite3.Row

    return conn.execute(
        """
        SELECT
            id,
            release_id,
            position,
            artist,
            title,
            duration
        FROM tracks
        ORDER BY id
        """
    ).fetchall()


def get_mp3s(conn):
    conn.row_factory = sqlite3.Row

    return conn.execute(
        """
        SELECT
            id,
            path,
            filename,
            artist,
            title,
            album,
            duration,
            bpm,
            genre,
            year
        FROM mp3_files
        ORDER BY id
        """
    ).fetchall()


def get_release_info(conn, release_id):
    row = conn.execute(
        """
        SELECT
            id,
            artist,
            title,
            label,
            catalog,
            year,
            discogs,
            storage_code
        FROM releases
        WHERE id = ?
        """,
        (release_id,)
    ).fetchone()

    return row


def already_linked(conn, track_id, mp3_id):
    row = conn.execute(
        """
        SELECT id
        FROM track_mp3
        WHERE track_id = ?
          AND mp3_id = ?
        LIMIT 1
        """,
        (track_id, mp3_id)
    ).fetchone()

    return row is not None


def create_link(conn, track_id, mp3_id, score):
    """
    Maak koppeling indien ze nog niet bestaat.
    """

    if already_linked(conn, track_id, mp3_id):
        return False

    preferred = 1 if score >= PREFERRED_SCORE else 0

    conn.execute(
        """
        INSERT INTO track_mp3
        (
            track_id,
            mp3_id,
            score,
            is_preferred,
            manually_added
        )
        VALUES (?, ?, ?, ?, 0)
        """,
        (
            track_id,
            mp3_id,
            score,
            preferred
        )
    )

    return True


def find_best_match(track, mp3s):
    """
    Zoek beste MP3 voor een track.
    """

    best_mp3 = None
    best_score = 0

    track_artist = normalize(track["artist"])
    track_title = normalize(track["title"])

    # Eerst snelle exacte zoekactie
    for mp3 in mp3s:

        mp3_artist = normalize(mp3["artist"])
        mp3_title = normalize(mp3["title"])

        if (
            track_artist
            and track_title
            and track_artist == mp3_artist
            and track_title == mp3_title
        ):
            return mp3, 100.0

    # Daarna fuzzy matching
    for mp3 in mp3s:

        score = calculate_score(track, mp3)

        if score > best_score:
            best_score = score
            best_mp3 = mp3

    return best_mp3, best_score


def main():

    print("=" * 80)
    print("KID ACID'S VINYLVAULT V3")
    print("AUTOMATISCHE MP3 KOPPELMOTOR")
    print("=" * 80)
    print()

    print("DATABASE:")
    print(os.path.abspath(DB))
    print()

    if not os.path.exists(DB):
        print("FOUT: database niet gevonden.")
        return

    conn = sqlite3.connect(DB)

    conn.row_factory = sqlite3.Row

    # Controleren of tabellen bestaan
    tables = {
        row[0]
        for row in conn.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type='table'
            """
        ).fetchall()
    }

    required = {
        "tracks",
        "mp3_files",
        "track_mp3",
        "releases"
    }

    missing = required - tables

    if missing:
        print("FOUT: ontbrekende tabellen:")
        print(missing)
        conn.close()
        return

    tracks = get_tracks(conn)
    mp3s = get_mp3s(conn)

    existing_links = get_existing_links(conn)

    print("Tracks :", len(tracks))
    print("MP3's  :", len(mp3s))
    print(
        "Bestaande preferred koppelingen :",
        len(existing_links)
    )
    print()

    if not tracks:
        print("Geen tracks gevonden.")
        conn.close()
        return

    if not mp3s:
        print("Geen MP3-bestanden gevonden.")
        conn.close()
        return

    matched = 0
    skipped = 0
    weak = 0
    errors = 0

    print("=" * 80)
    print("MATCHING START")
    print("=" * 80)
    print()

    for number, track in enumerate(tracks, start=1):

        track_id = track["id"]

        if track_id in existing_links:

            skipped += 1

            print(
                f"[{number}/{len(tracks)}] "
                f"SKIP | "
                f"{track['position']} | "
                f"{track['artist']} - {track['title']} "
                f"| bestaande koppeling"
            )

            continue

        try:

            best_mp3, score = find_best_match(
                track,
                mp3s
            )

            if best_mp3 is None:
                print(
                    f"[{number}/{len(tracks)}] "
                    f"GEEN MATCH | "
                    f"{track['artist']} - {track['title']}"
                )
                continue

            if score < MIN_SCORE:

                weak += 1

                print(
                    f"[{number}/{len(tracks)}] "
                    f"TWijfelachtig | "
                    f"{track['position']} | "
                    f"{track['artist']} - {track['title']} "
                    f"| SCORE {score}"
                )

                continue

            inserted = create_link(
                conn,
                track_id,
                best_mp3["id"],
                score
            )

            if inserted:

                matched += 1

                preferred_text = (
                    "PREFERRED"
                    if score >= PREFERRED_SCORE
                    else "MATCH"
                )

                print(
                    f"[{number}/{len(tracks)}] "
                    f"{preferred_text} | "
                    f"{score:5.1f} | "
                    f"{track['position']} | "
                    f"{track['artist']} - {track['title']}"
                )

                print(
                    f"      MP3: "
                    f"{best_mp3['path']}"
                )

            else:

                skipped += 1

        except Exception as exc:

            errors += 1

            print(
                f"[{number}/{len(tracks)}] "
                f"FOUT: {exc}"
            )

    conn.commit()

    print()
    print("=" * 80)
    print("MATCHING KLAAR")
    print("=" * 80)
    print()

    print("Nieuwe koppelingen :", matched)
    print("Overgeslagen       :", skipped)
    print("Twijfelachtig      :", weak)
    print("Fouten             :", errors)

    total_links = conn.execute(
        """
        SELECT COUNT(*)
        FROM track_mp3
        """
    ).fetchone()[0]

    preferred_links = conn.execute(
        """
        SELECT COUNT(*)
        FROM track_mp3
        WHERE is_preferred = 1
        """
    ).fetchone()[0]

    print()
    print("Totaal koppelingen :", total_links)
    print("Preferred MP3's    :", preferred_links)

    print()
    print("=" * 80)
    print("VOORBEELD BOOSTER")
    print("=" * 80)

    rows = conn.execute(
        """
        SELECT
            t.position,
            t.artist,
            t.title,
            m.path,
            tm.score,
            tm.is_preferred
        FROM track_mp3 tm
        JOIN tracks t
            ON t.id = tm.track_id
        JOIN mp3_files m
            ON m.id = tm.mp3_id
        WHERE lower(t.title) = 'booster'
        ORDER BY tm.score DESC
        """
    ).fetchall()

    for row in rows:

        print(
            f"{row[0]} | "
            f"{row[1]} | "
            f"{row[2]} | "
            f"Score {row[4]} | "
            f"Preferred {row[5]}"
        )

        print(
            f"    {row[3]}"
        )

    conn.close()

    print()
    print("=" * 80)
    print("KLAAR")
    print("=" * 80)


if __name__ == "__main__":
    main()
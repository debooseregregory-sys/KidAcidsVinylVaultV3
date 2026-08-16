from database.database import get_connection
from pathlib import Path
from datetime import datetime
import shutil
import re

print("=" * 70)
print("KID ACID'S VINYLVAULT V3")
print("VEILIGE AUTOMATISCHE MP3 MATCHER")
print("=" * 70)
print()

DB_PATH = Path("data/vinylvault.db")
BACKUP_DIR = Path("data/backups")
BACKUP_DIR.mkdir(parents=True, exist_ok=True)

# ============================================================
# DATABASE BACKUP
# ============================================================

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
backup_path = BACKUP_DIR / f"vinylvault_before_auto_match_{timestamp}.db"

if DB_PATH.exists():
    shutil.copy2(DB_PATH, backup_path)
    print(f"Database backup:")
    print(f"  {backup_path}")
else:
    print("FOUT: database niet gevonden:")
    print(f"  {DB_PATH}")
    raise SystemExit(1)

print()

# ============================================================
# NORMALISEREN
# ============================================================

def normalize(value):
    if value is None:
        return ""

    value = str(value).lower()

    value = value.replace("&", "and")

    # accenten zo goed mogelijk verwijderen
    import unicodedata
    value = unicodedata.normalize("NFKD", value)
    value = "".join(
        c for c in value
        if not unicodedata.combining(c)
    )

    # haakjes / leestekens vervangen
    value = re.sub(r"[\(\)\[\]\{\}_\-]+", " ", value)
    value = re.sub(r"[^a-z0-9]+", " ", value)

    value = re.sub(r"\s+", " ", value).strip()

    return value


# ============================================================
# DATABASE
# ============================================================

conn = get_connection()

try:
    tracks = conn.execute(
        """
        SELECT
            id,
            release_id,
            position,
            artist,
            title
        FROM tracks
        ORDER BY id
        """
    ).fetchall()

    mp3s = conn.execute(
        """
        SELECT
            id,
            artist,
            title,
            filename,
            path
        FROM mp3_files
        ORDER BY id
        """
    ).fetchall()

    print(f"Tracks : {len(tracks)}")
    print(f"MP3s   : {len(mp3s)}")
    print()

    # ========================================================
    # MP3 INDEX
    # ========================================================

    mp3_index = {}

    for mp3 in mp3s:

        artist = normalize(mp3["artist"])
        title = normalize(mp3["title"])

        if not artist or not title:
            continue

        key = (artist, title)

        mp3_index.setdefault(key, []).append(mp3)

    print(f"Unieke artist/title MP3-combinaties: {len(mp3_index)}")
    print()

    # ========================================================
    # BESTAANDE LINKS
    # ========================================================

    existing_links = set()

    rows = conn.execute(
        """
        SELECT
            track_id,
            mp3_id
        FROM track_mp3
        """
    ).fetchall()

    for row in rows:
        existing_links.add(
            (row["track_id"], row["mp3_id"])
        )

    # ========================================================
    # MATCHEN
    # ========================================================

    new_links = 0
    existing = 0
    not_found = 0
    ambiguous = 0

    matched_examples = []
    missing_examples = []

    for track in tracks:

        artist = normalize(track["artist"])
        title = normalize(track["title"])

        if not artist or not title:
            continue

        key = (artist, title)

        candidates = mp3_index.get(key, [])

        if not candidates:
            not_found += 1

            if len(missing_examples) < 50:
                missing_examples.append(
                    (
                        track["position"],
                        track["artist"],
                        track["title"]
                    )
                )

            continue

        if len(candidates) > 1:
            ambiguous += 1

            print()
            print("AMBIGU MATCH:")
            print(
                f"{track['position']} | "
                f"{track['artist']} - {track['title']}"
            )

            for mp3 in candidates:
                print(
                    f"   MP3 #{mp3['id']} | "
                    f"{mp3['filename']}"
                )

            continue

        mp3 = candidates[0]

        link_key = (
            track["id"],
            mp3["id"]
        )

        if link_key in existing_links:
            existing += 1
            continue

        # ====================================================
        # VEILIGE NIEUWE KOPPELING
        # ====================================================

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
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                track["id"],
                mp3["id"],
                100.0,
                1,
                0
            )
        )

        existing_links.add(link_key)

        new_links += 1

        if len(matched_examples) < 50:
            matched_examples.append(
                (
                    track["position"],
                    track["artist"],
                    track["title"],
                    mp3["id"],
                    mp3["filename"]
                )
            )

    conn.commit()

    # ========================================================
    # RESULTAAT
    # ========================================================

    print()
    print("=" * 70)
    print("RESULTAAT")
    print("=" * 70)
    print()

    print(f"Nieuwe links     : {new_links}")
    print(f"Bestaande links  : {existing}")
    print(f"Niet gevonden    : {not_found}")
    print(f"Ambigu           : {ambiguous}")

    # ========================================================
    # NIEUWE MATCHES
    # ========================================================

    print()
    print("=" * 70)
    print("NIEUWE MATCHES")
    print("=" * 70)

    if matched_examples:
        for (
            position,
            artist,
            title,
            mp3_id,
            filename
        ) in matched_examples:

            print(
                f"{position} | "
                f"{artist} - {title}"
            )

            print(
                f"   -> MP3 #{mp3_id} | {filename}"
            )
    else:
        print("Geen nieuwe matches.")

    # ========================================================
    # NIET GEVONDEN
    # ========================================================

    print()
    print("=" * 70)
    print("NIET GEVONDEN")
    print("=" * 70)

    if missing_examples:
        for position, artist, title in missing_examples:
            print(
                f"{position} | "
                f"{artist} - {title}"
            )

        if not_found > len(missing_examples):
            print()
            print(
                f"... en nog "
                f"{not_found - len(missing_examples)} andere."
            )
    else:
        print("Alle tracks met geldige artist/title hebben een match.")

    # ========================================================
    # AMBIGU
    # ========================================================

    if ambiguous:
        print()
        print("=" * 70)
        print("AMBIGUE MATCHES")
        print("=" * 70)
        print(
            "Deze zijn bewust NIET automatisch gekoppeld."
        )
        print(
            "Zo voorkomen we verkeerde MP3-koppelingen."
        )

    print()
    print("=" * 70)
    print("MATCHER KLAAR")
    print("=" * 70)
    print()
    print(f"Backup staat hier:")
    print(f"{backup_path}")
    print()

finally:
    conn.close()

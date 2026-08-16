import os
import sqlite3
import shutil
import requests
from datetime import datetime

ROOT = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__),
        "..",
        ".."
    )
)

DB = os.path.join(
    ROOT,
    "data",
    "vinylvault.db"
)

DISCOGS_ID = "4497"

HEADERS = {
    "User-Agent": "KidAcidVinylVaultV3/1.0",
    "Accept": "application/json",
}

print()
print("=" * 80)
print("KID ACID'S VINYLVAULT V3")
print("VOLLEDIGE RELEASE KOPPELEN")
print("=" * 80)

print()
print("Discogs ID:", DISCOGS_ID)
print("Database  :", DB)

# ============================================================
# DATABASE
# ============================================================

if not os.path.exists(DB):

    print()
    print("FOUT: database bestaat niet.")
    raise SystemExit

# ============================================================
# BACKUP
# ============================================================

backup_dir = os.path.join(
    ROOT,
    "data",
    "backup"
)

os.makedirs(
    backup_dir,
    exist_ok=True
)

timestamp = datetime.now().strftime(
    "%Y%m%d_%H%M%S"
)

backup_file = os.path.join(
    backup_dir,
    f"vinylvault_before_full_release_{timestamp}.db"
)

shutil.copy2(
    DB,
    backup_file
)

print()
print("=" * 80)
print("BACKUP")
print("=" * 80)

print()
print("Backup:", backup_file)

# ============================================================
# RELEASE UIT DATABASE
# ============================================================

conn = sqlite3.connect(DB)

conn.row_factory = sqlite3.Row

release = conn.execute(
    """
    SELECT *
    FROM releases
    WHERE discogs = ?
    """,
    (
        DISCOGS_ID,
    )
).fetchone()

if release is None:

    print()
    print("FOUT: release 4497 staat niet in VinylVault.")
    conn.close()
    raise SystemExit

release_db_id = release["id"]

print()
print("=" * 80)
print("BESTAANDE RELEASE")
print("=" * 80)

print()
print("V3 Release ID :", release_db_id)
print("Artist        :", release["artist"])
print("Release       :", release["title"])
print("Discogs       :", release["discogs"])
print("Kastcode      :", release["storage_code"])

# ============================================================
# DISCOGS OPHALEN
# ============================================================

print()
print("=" * 80)
print("DISCOGS RELEASE OPHALEN")
print("=" * 80)

url = (
    "https://api.discogs.com/releases/"
    + DISCOGS_ID
)

try:

    response = requests.get(
        url,
        headers=HEADERS,
        timeout=30
    )

except Exception as exc:

    print()
    print("NETWERKFOUT:")
    print(exc)

    conn.close()
    raise SystemExit

print()
print("HTTP:", response.status_code)

if response.status_code != 200:

    print()
    print("DISCOGS FOUT:")
    print(response.text)

    conn.close()
    raise SystemExit

discogs_release = response.json()

# ============================================================
# CONTROLE ARTIST
# ============================================================

discogs_artists = []

for artist in discogs_release.get(
    "artists",
    []
):

    name = str(
        artist.get(
            "name",
            ""
        )
    ).strip()

    if name:
        discogs_artists.append(name)

discogs_artist = ", ".join(
    discogs_artists
)

print()
print("Artist :", discogs_artist)
print("Release:", discogs_release.get("title"))
print("Year   :", discogs_release.get("year"))

if discogs_artist.lower() != str(
    release["artist"]
).lower():

    print()
    print("FOUT: ARTIST KOMT NIET OVEREEN.")

    conn.close()
    raise SystemExit

# ============================================================
# TRACKLIST
# ============================================================

tracklist = discogs_release.get(
    "tracklist",
    []
)

print()
print("=" * 80)
print("DISCOGS TRACKLIST")
print("=" * 80)

print()

valid_tracks = []

for track in tracklist:

    position = str(
        track.get(
            "position",
            ""
        )
    ).strip()

    title = str(
        track.get(
            "title",
            ""
        )
    ).strip()

    duration_text = str(
        track.get(
            "duration",
            ""
        )
    ).strip()

    if not title:
        continue

    valid_tracks.append(
        (
            position,
            title,
            duration_text,
            track
        )
    )

    print(
        f"{position:5} | "
        f"{title}"
        f"{' | ' + duration_text if duration_text else ''}"
    )

print()
print(
    "Discogs tracks:",
    len(valid_tracks)
)

# ============================================================
# BESTAANDE VINYLVAULT TRACKS
# ============================================================

print()
print("=" * 80)
print("BESTAANDE VINYLVAULT TRACKS")
print("=" * 80)

existing_tracks = conn.execute(
    """
    SELECT *
    FROM tracks
    WHERE release_id = ?
    ORDER BY id
    """,
    (
        release_db_id,
    )
).fetchall()

print()

for track in existing_tracks:

    print(
        f"{track['position']:5} | "
        f"{track['title']}"
    )

print()
print(
    "Bestaande tracks:",
    len(existing_tracks)
)

# ============================================================
# DUUR
# ============================================================

def duration_to_seconds(text):

    if not text:
        return 0

    try:

        parts = text.split(":")

        if len(parts) == 2:

            return (
                int(parts[0]) * 60
                + int(parts[1])
            )

        if len(parts) == 3:

            return (
                int(parts[0]) * 3600
                + int(parts[1]) * 60
                + int(parts[2])
            )

    except ValueError:

        return 0

    return 0

# ============================================================
# TRACK ARTIST
# ============================================================

def get_track_artist(
    track,
    release
):

    artists = track.get(
        "artists",
        []
    )

    names = []

    for artist in artists:

        name = str(
            artist.get(
                "name",
                ""
            )
        ).strip()

        if name:
            names.append(name)

    if names:

        return ", ".join(names)

    return discogs_artist

# ============================================================
# ONTBREKENDE TRACKS TOEVOEGEN
# ============================================================

print()
print("=" * 80)
print("ONTBREKENDE TRACKS TOEVOEGEN")
print("=" * 80)

added = 0
skipped = 0

for position, title, duration_text, track in valid_tracks:

    existing = conn.execute(
        """
        SELECT id
        FROM tracks
        WHERE release_id = ?
        AND position = ?
        """,
        (
            release_db_id,
            position
        )
    ).fetchone()

    if existing:

        print(
            f"{position:5} | "
            f"{title:45} | BESTAAT"
        )

        skipped += 1
        continue

    artist = get_track_artist(
        track,
        discogs_release
    )

    duration = duration_to_seconds(
        duration_text
    )

    conn.execute(
        """
        INSERT INTO tracks (
            release_id,
            position,
            artist,
            title,
            duration
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            release_db_id,
            position,
            artist,
            title,
            duration
        )
    )

    added += 1

    print(
        f"{position:5} | "
        f"{title:45} | TOEGEVOEGD"
    )

# ============================================================
# COMMIT
# ============================================================

conn.commit()

# ============================================================
# DEFINITIEVE CONTROLE
# ============================================================

final_tracks = conn.execute(
    """
    SELECT
        id,
        release_id,
        position,
        artist,
        title,
        duration
    FROM tracks
    WHERE release_id = ?
    ORDER BY id
    """,
    (
        release_db_id,
    )
).fetchall()

conn.close()

# ============================================================
# RESULTAAT
# ============================================================

print()
print("=" * 80)
print("RESULTAAT")
print("=" * 80)

print()
print("Release :", release["title"])
print("Artist  :", release["artist"])
print("Kastcode:", release["storage_code"])

print()
print("Tracks Discogs :", len(valid_tracks))
print("Tracks V3      :", len(final_tracks))
print("Nieuw toegevoegd:", added)
print("Bestonden al    :", skipped)

print()
print("=" * 80)
print("VOLLEDIGE RELEASE")
print("=" * 80)

print()

for track in final_tracks:

    seconds = track["duration"]

    if seconds:

        minutes = seconds // 60
        secs = seconds % 60

        duration = (
            f"{minutes}:{secs:02d}"
        )

    else:

        duration = ""

    print(
        f"{track['position']:5} | "
        f"{track['artist']:35} | "
        f"{track['title']}"
        f"{' | ' + duration if duration else ''}"
    )

print()
print("=" * 80)
print("DEFINITIEVE KOPPELING")
print("=" * 80)

print()

print(
    release["artist"],
    "->",
    release["title"],
    "->",
    "Kastcode",
    release["storage_code"]
)

print()
print(
    "DATABASE GEWIJZIGD: JA"
)

print()
print(
    "Backup:",
    backup_file
)

print()
print("=" * 80)
print("KLAAR")
print("=" * 80)

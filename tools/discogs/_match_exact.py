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
KASTCODE = "XCV 11"

ARTIST = "Planetary Assault Systems"
TRACK_TITLE = "In From The Night"
TRACK_POSITION = "A1"

API_URL = "https://api.discogs.com"

HEADERS = {
    "User-Agent": "KidAcidVinylVaultV3/1.0",
    "Accept": "application/json",
}

print()
print("=" * 80)
print("KID ACID'S VINYLVAULT V3")
print("EXACTE MATCH KOPPELEN")
print("=" * 80)

print()
print("Database :", DB)
print("Discogs  :", DISCOGS_ID)
print("Artist   :", ARTIST)
print("Track    :", TRACK_POSITION, "|", TRACK_TITLE)
print("Kastcode :", KASTCODE)

# ============================================================
# DATABASE
# ============================================================

if not os.path.exists(DB):

    print()
    print("FOUT: database bestaat niet:")
    print(DB)

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
    f"vinylvault_before_match_{timestamp}.db"
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
print("Backup:")
print(backup_file)

# ============================================================
# DISCOGS RELEASE
# ============================================================

print()
print("=" * 80)
print("DISCOGS RELEASE CONTROLEREN")
print("=" * 80)

url = (
    f"{API_URL}/releases/"
    f"{DISCOGS_ID}"
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

    raise SystemExit

print()
print(
    "HTTP:",
    response.status_code
)

if response.status_code != 200:

    print()
    print("DISCOGS FOUT:")
    print(response.text)

    raise SystemExit

release = response.json()

# ============================================================
# ARTIST
# ============================================================

artist_names = []

for artist in release.get(
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
        artist_names.append(name)

release_artist = ", ".join(
    artist_names
)

release_title = str(
    release.get(
        "title",
        ""
    )
).strip()

release_year = release.get(
    "year"
)

print()
print("Artist :", release_artist)
print("Release:", release_title)
print("Year   :", release_year)

# ============================================================
# ARTIST CONTROL
# ============================================================

if release_artist.lower() != ARTIST.lower():

    print()
    print("FOUT: ARTIST KOMT NIET OVEREEN.")
    raise SystemExit

# ============================================================
# VINYL CONTROL
# ============================================================

vinyl = False

for fmt in release.get(
    "formats",
    []
):

    name = str(
        fmt.get(
            "name",
            ""
        )
    ).strip().lower()

    if name == "vinyl":

        vinyl = True
        break

if not vinyl:

    print()
    print("FOUT: RELEASE IS GEEN VINYL.")
    raise SystemExit

print()
print("Format : VINYL")

# ============================================================
# TRACK CONTROL
# ============================================================

matched_track = None

for track in release.get(
    "tracklist",
    []
):

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

    if (
        position.upper()
        == TRACK_POSITION.upper()
        and
        title.lower()
        == TRACK_TITLE.lower()
    ):

        matched_track = track
        break

if matched_track is None:

    print()
    print("FOUT: EXACTE TRACK NIET GEVONDEN.")
    raise SystemExit

print()
print("EXACTE TRACK:")
print(
    matched_track.get("position"),
    "|",
    matched_track.get("title")
)

# ============================================================
# DATABASE OPENEN
# ============================================================

conn = sqlite3.connect(DB)

conn.row_factory = sqlite3.Row

# ============================================================
# BESTAANDE RELEASE CONTROLEREN
# ============================================================

existing = conn.execute(
    """
    SELECT *
    FROM releases
    WHERE discogs = ?
    """,
    (
        DISCOGS_ID,
    )
).fetchone()

if existing:

    release_db_id = existing["id"]

    print()
    print(
        "Release bestaat al."
    )

    print(
        "V3 Release ID:",
        release_db_id
    )

else:

    # --------------------------------------------------------
    # LABEL
    # --------------------------------------------------------

    label_names = []
    catalog = ""

    for label in release.get(
        "labels",
        []
    ):

        name = str(
            label.get(
                "name",
                ""
            )
        ).strip()

        if name:
            label_names.append(name)

        if not catalog:

            catalog = str(
                label.get(
                    "catno",
                    ""
                )
            ).strip()

    label_name = ", ".join(
        label_names
    )

    # --------------------------------------------------------
    # GENRE
    # --------------------------------------------------------

    genre_names = release.get(
        "genres",
        []
    )

    genre = ", ".join(
        str(x)
        for x in genre_names
        if x
    )

    # --------------------------------------------------------
    # URL
    # --------------------------------------------------------

    discogs_link = (
        f"https://www.discogs.com/release/"
        f"{DISCOGS_ID}"
    )

    # --------------------------------------------------------
    # RELEASE INSERT
    # --------------------------------------------------------

    cursor = conn.execute(
        """
        INSERT INTO releases (
            artist,
            title,
            label,
            catalog,
            year,
            genre,
            discogs,
            discogs_link,
            notes,
            storage_code
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            release_artist,
            release_title,
            label_name,
            catalog,
            release_year,
            genre,
            DISCOGS_ID,
            discogs_link,
            "",
            KASTCODE
        )
    )

    release_db_id = cursor.lastrowid

    print()
    print(
        "NIEUWE RELEASE AANGEMAAKT."
    )

    print(
        "V3 Release ID:",
        release_db_id
    )

# ============================================================
# KASTCODE
# ============================================================

conn.execute(
    """
    UPDATE releases
    SET storage_code = ?
    WHERE id = ?
    """,
    (
        KASTCODE,
        release_db_id
    )
)

# ============================================================
# TRACK BESTAAT AL?
# ============================================================

existing_track = conn.execute(
    """
    SELECT *
    FROM tracks
    WHERE release_id = ?
    AND position = ?
    """,
    (
        release_db_id,
        TRACK_POSITION
    )
).fetchone()

if existing_track:

    track_id = existing_track["id"]

    print()
    print(
        "Track bestaat al."
    )

    print(
        "Track ID:",
        track_id
    )

else:

    duration_text = str(
        matched_track.get(
            "duration",
            ""
        )
    ).strip()

    duration = 0

    if duration_text:

        parts = duration_text.split(":")

        try:

            if len(parts) == 2:

                duration = (
                    int(parts[0]) * 60
                    + int(parts[1])
                )

            elif len(parts) == 3:

                duration = (
                    int(parts[0]) * 3600
                    + int(parts[1]) * 60
                    + int(parts[2])
                )

        except ValueError:

            duration = 0

    track_cursor = conn.execute(
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
            TRACK_POSITION,
            release_artist,
            TRACK_TITLE,
            duration
        )
    )

    track_id = track_cursor.lastrowid

    print()
    print(
        "NIEUWE TRACK AANGEMAAKT."
    )

    print(
        "Track ID:",
        track_id
    )

# ============================================================
# COMMIT
# ============================================================

conn.commit()

# ============================================================
# DEFINITIEVE CONTROLE
# ============================================================

final_release = conn.execute(
    """
    SELECT
        id,
        artist,
        title,
        discogs,
        storage_code
    FROM releases
    WHERE id = ?
    """,
    (
        release_db_id,
    )
).fetchone()

final_track = conn.execute(
    """
    SELECT
        id,
        release_id,
        position,
        artist,
        title,
        duration
    FROM tracks
    WHERE id = ?
    """,
    (
        track_id,
    )
).fetchone()

conn.close()

# ============================================================
# RESULTAAT
# ============================================================

print()
print("=" * 80)
print("KOPPELING GESLAAGD")
print("=" * 80)

print()
print("RELEASE")
print(
    "V3 ID      :",
    final_release["id"]
)

print(
    "Discogs ID :",
    final_release["discogs"]
)

print(
    "Artist     :",
    final_release["artist"]
)

print(
    "Release    :",
    final_release["title"]
)

print(
    "Kastcode   :",
    final_release["storage_code"]
)

print()
print("TRACK")

print(
    "Track ID   :",
    final_track["id"]
)

print(
    "Positie    :",
    final_track["position"]
)

print(
    "Artist     :",
    final_track["artist"]
)

print(
    "Titel      :",
    final_track["title"]
)

print()
print("=" * 80)
print("DEFINITIEVE KOPPELING")
print("=" * 80)

print()

print(
    f"{final_release['artist']} "
    f"-> "
    f"{final_release['title']} "
    f"-> "
    f"{final_track['position']} "
    f"-> "
    f"{final_track['title']} "
    f"-> "
    f"Kastcode {final_release['storage_code']}"
)

print()
print("DATABASE GEWIJZIGD: JA")
print()
print("Backup:")
print(backup_file)

print()
print("=" * 80)
print("KLAAR")
print("=" * 80)

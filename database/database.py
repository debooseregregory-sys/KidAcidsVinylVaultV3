# ============================================================
# KID ACID'S VINYLVAULT V3
# DATABASE ENGINE
# ============================================================

import sqlite3
from pathlib import Path


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

DATA_DIR = BASE_DIR / "data"

DB_PATH = DATA_DIR / "vinylvault.db"


# ============================================================
# DATABASE CONNECTION
# ============================================================

def get_connection():

    DATA_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    connection = sqlite3.connect(
        DB_PATH
    )

    connection.row_factory = sqlite3.Row

    connection.execute(
        "PRAGMA foreign_keys = ON"
    )

    return connection


# ============================================================
# DATABASE SCHEMA HELPERS
# ============================================================

def _column_exists(
    connection,
    table_name,
    column_name
):

    rows = connection.execute(
        f"PRAGMA table_info({table_name})"
    ).fetchall()

    for row in rows:

        if row["name"] == column_name:
            return True

    return False


def _ensure_column(
    connection,
    table_name,
    column_name,
    definition
):

    if not _column_exists(
        connection,
        table_name,
        column_name
    ):

        connection.execute(
            f"""
            ALTER TABLE {table_name}
            ADD COLUMN {column_name} {definition}
            """
        )


# ============================================================
# DATABASE MIGRATION
# ============================================================

def migrate_database():

    connection = get_connection()

    try:

        # ----------------------------------------------------
        # RELEASES
        # ----------------------------------------------------

        _ensure_column(
            connection,
            "releases",
            "storage_code",
            "TEXT DEFAULT ''"
        )

        _ensure_column(
            connection,
            "releases",
            "genre",
            "TEXT DEFAULT ''"
        )

        _ensure_column(
            connection,
            "releases",
            "discogs",
            "TEXT DEFAULT ''"
        )

        _ensure_column(
            connection,
            "releases",
            "discogs_link",
            "TEXT DEFAULT ''"
        )

        _ensure_column(
            connection,
            "releases",
            "cover",
            "TEXT DEFAULT ''"
        )

        _ensure_column(
            connection,
            "releases",
            "notes",
            "TEXT DEFAULT ''"
        )

        _ensure_column(
            connection,
            "releases",
            "checked",
            "INTEGER DEFAULT 0"
        )

        # ----------------------------------------------------
        # TRACKS
        # ----------------------------------------------------

        _ensure_column(
            connection,
            "tracks",
            "artist",
            "TEXT DEFAULT ''"
        )

        _ensure_column(
            connection,
            "tracks",
            "duration",
            "INTEGER DEFAULT 0"
        )

        _ensure_column(
            connection,
            "tracks",
            "bpm",
            "REAL"
        )

        _ensure_column(
            connection,
            "tracks",
            "genre",
            "TEXT DEFAULT ''"
        )

        _ensure_column(
            connection,
            "tracks",
            "notes",
            "TEXT DEFAULT ''"
        )

        # ----------------------------------------------------
        # MP3 FILES
        # ----------------------------------------------------

        _ensure_column(
            connection,
            "mp3_files",
            "filename",
            "TEXT DEFAULT ''"
        )

        _ensure_column(
            connection,
            "mp3_files",
            "artist",
            "TEXT DEFAULT ''"
        )

        _ensure_column(
            connection,
            "mp3_files",
            "title",
            "TEXT DEFAULT ''"
        )

        _ensure_column(
            connection,
            "mp3_files",
            "album",
            "TEXT DEFAULT ''"
        )

        _ensure_column(
            connection,
            "mp3_files",
            "duration",
            "INTEGER DEFAULT 0"
        )

        _ensure_column(
            connection,
            "mp3_files",
            "bitrate",
            "INTEGER DEFAULT 0"
        )

        _ensure_column(
            connection,
            "mp3_files",
            "sample_rate",
            "INTEGER DEFAULT 0"
        )

        _ensure_column(
            connection,
            "mp3_files",
            "bpm",
            "REAL"
        )

        _ensure_column(
            connection,
            "mp3_files",
            "genre",
            "TEXT DEFAULT ''"
        )

        _ensure_column(
            connection,
            "mp3_files",
            "year",
            "INTEGER"
        )

        _ensure_column(
            connection,
            "mp3_files",
            "filesize",
            "INTEGER DEFAULT 0"
        )

        connection.commit()

    finally:

        connection.close()


# ============================================================
# RELEASES
# ============================================================

def get_all_releases():

    connection = get_connection()

    try:

        rows = connection.execute(
            """
            SELECT
                r.id,
                r.artist,
                r.title,
                r.label,
                r.catalog,
                r.year,
                r.genre,
                r.discogs,
                r.discogs_link,
                r.cover,
                r.notes,
                r.storage_code,
                r.checked,

                COUNT(DISTINCT t.id) AS track_count,

                COUNT(
                    DISTINCT CASE
                        WHEN tm.id IS NOT NULL
                        THEN tm.id
                    END
                ) AS mp3_link_count

            FROM releases r

            LEFT JOIN tracks t
                ON t.release_id = r.id

            LEFT JOIN track_mp3 tm
                ON tm.track_id = t.id

            GROUP BY r.id

            ORDER BY
                r.artist COLLATE NOCASE,
                r.title COLLATE NOCASE
            """
        ).fetchall()

        return rows

    finally:

        connection.close()


# ============================================================
# RELEASE BY ID
# ============================================================

def get_release_by_id(
    release_id
):

    connection = get_connection()

    try:

        row = connection.execute(
            """
            SELECT
                id,
                artist,
                title,
                label,
                catalog,
                year,
                genre,
                discogs,
                discogs_link,
                cover,
                notes,
                storage_code,
                checked
            FROM releases
            WHERE id = ?
            """,
            (
                release_id,
            )
        ).fetchone()

        return row

    finally:

        connection.close()


# ============================================================
# UPDATE RELEASE
# ============================================================

def update_release(
    release_id,
    artist,
    title,
    label,
    catalog,
    year,
    genre,
    storage_code,
    discogs,
    discogs_link,
    cover,
    notes
):
    """
    Updates only the release information.

    Tracks and MP3 links are NOT touched.
    """

    connection = get_connection()

    try:

        connection.execute(
            """
            UPDATE releases

            SET
                artist = ?,
                title = ?,
                label = ?,
                catalog = ?,
                year = ?,
                genre = ?,
                storage_code = ?,
                discogs = ?,
                discogs_link = ?,
                cover = ?,
                notes = ?,
                updated_at = CURRENT_TIMESTAMP

            WHERE id = ?
            """,
            (
                artist or "",
                title or "",
                label or "",
                catalog or "",
                year,
                genre or "",
                storage_code or "",
                discogs or "",
                discogs_link or "",
                cover or "",
                notes or "",
                release_id
            )
        )

        connection.commit()

        return True

    except Exception:

        connection.rollback()

        raise

    finally:

        connection.close()


# ============================================================
# SEARCH RELEASES
# ============================================================

def search_releases(
    search_text
):

    search_text = (
        search_text or ""
    ).strip()

    if not search_text:

        return get_all_releases()

    pattern = f"%{search_text}%"

    connection = get_connection()

    try:

        rows = connection.execute(
            """
            SELECT
                r.id,
                r.artist,
                r.title,
                r.label,
                r.catalog,
                r.year,
                r.genre,
                r.discogs,
                r.discogs_link,
                r.cover,
                r.notes,
                r.storage_code,
                r.checked,

                COUNT(DISTINCT t.id) AS track_count,

                COUNT(
                    DISTINCT CASE
                        WHEN tm.id IS NOT NULL
                        THEN tm.id
                    END
                ) AS mp3_link_count

            FROM releases r

            LEFT JOIN tracks t
                ON t.release_id = r.id

            LEFT JOIN track_mp3 tm
                ON tm.track_id = t.id

            WHERE
                r.artist LIKE ?
                OR r.title LIKE ?
                OR r.label LIKE ?
                OR r.catalog LIKE ?
                OR r.discogs LIKE ?
                OR r.storage_code LIKE ?

            GROUP BY r.id

            ORDER BY
                r.artist COLLATE NOCASE,
                r.title COLLATE NOCASE
            """,
            (
                pattern,
                pattern,
                pattern,
                pattern,
                pattern,
                pattern
            )
        ).fetchall()

        return rows

    finally:

        connection.close()


# ============================================================
# TRACKS FOR RELEASE
# ============================================================

def get_tracks_for_release(
    release_id
):

    connection = get_connection()

    try:

        rows = connection.execute(
            """
            SELECT
                id,
                release_id,
                position,
                artist,
                title,
                duration,
                bpm,
                genre,
                notes

            FROM tracks

            WHERE release_id = ?

            ORDER BY id
            """,
            (
                release_id,
            )
        ).fetchall()

        return rows

    finally:

        connection.close()


# ============================================================
# TRACK BY ID
# ============================================================

def get_track_by_id(
    track_id
):

    connection = get_connection()

    try:

        row = connection.execute(
            """
            SELECT
                id,
                release_id,
                position,
                artist,
                title,
                duration,
                bpm,
                genre,
                notes

            FROM tracks

            WHERE id = ?
            """,
            (
                track_id,
            )
        ).fetchone()

        return row

    finally:

        connection.close()


# ============================================================
# MP3S FOR TRACK
# ============================================================

def get_mp3s_for_track(
    track_id
):

    connection = get_connection()

    try:

        rows = connection.execute(
            """
            SELECT
                m.id,
                m.path,
                m.filename,
                m.artist,
                m.title,
                m.album,
                m.duration,
                m.bitrate,
                m.sample_rate,
                m.bpm,
                m.genre,
                m.year,
                m.filesize,

                x.id AS link_id,
                x.score,
                x.is_preferred,
                x.manually_added

            FROM track_mp3 x

            INNER JOIN mp3_files m
                ON m.id = x.mp3_id

            WHERE x.track_id = ?

            ORDER BY
                x.is_preferred DESC,
                x.score DESC,
                m.filename COLLATE NOCASE
            """,
            (
                track_id,
            )
        ).fetchall()

        return rows

    finally:

        connection.close()


# ============================================================
# PREFERRED MP3
# ============================================================

def get_preferred_mp3(
    track_id
):

    connection = get_connection()

    try:

        row = connection.execute(
            """
            SELECT
                m.id,
                m.path,
                m.filename,
                m.artist,
                m.title,
                m.album,
                m.duration,
                m.bitrate,
                m.sample_rate,
                m.bpm,
                m.genre,
                m.year,
                m.filesize,

                x.id AS link_id,
                x.score,
                x.is_preferred,
                x.manually_added

            FROM track_mp3 x

            INNER JOIN mp3_files m
                ON m.id = x.mp3_id

            WHERE x.track_id = ?

            ORDER BY
                x.is_preferred DESC,
                x.score DESC,
                m.id

            LIMIT 1
            """,
            (
                track_id,
            )
        ).fetchone()

        return row

    finally:

        connection.close()


# ============================================================
# COMPLETE RELEASE DETAILS
# ============================================================

def get_release_details(
    release_id
):

    release = get_release_by_id(
        release_id
    )

    if not release:

        return None

    tracks = get_tracks_for_release(
        release_id
    )

    result = {
        "release": release,
        "tracks": []
    }

    for track in tracks:

        mp3s = get_mp3s_for_track(
            track["id"]
        )

        result["tracks"].append(
            {
                "track": track,
                "mp3s": mp3s
            }
        )

    return result


# ============================================================
# SET PREFERRED MP3
# ============================================================

def set_preferred_mp3(
    track_id,
    link_id
):

    connection = get_connection()

    try:

        existing = connection.execute(
            """
            SELECT id
            FROM track_mp3
            WHERE id = ?
              AND track_id = ?
            """,
            (
                link_id,
                track_id
            )
        ).fetchone()

        if not existing:

            raise ValueError(
                "Deze MP3 is niet aan deze track gekoppeld."
            )

        connection.execute(
            """
            UPDATE track_mp3
            SET is_preferred = 0
            WHERE track_id = ?
            """,
            (
                track_id,
            )
        )

        connection.execute(
            """
            UPDATE track_mp3
            SET is_preferred = 1
            WHERE id = ?
              AND track_id = ?
            """,
            (
                link_id,
                track_id
            )
        )

        connection.commit()

    except Exception:

        connection.rollback()

        raise

    finally:

        connection.close()


# ============================================================
# UNLINK MP3 FROM TRACK
# ============================================================

def unlink_mp3_from_track(
    link_id
):

    connection = get_connection()

    try:

        existing = connection.execute(
            """
            SELECT
                id,
                track_id,
                mp3_id,
                is_preferred

            FROM track_mp3

            WHERE id = ?
            """,
            (
                link_id,
            )
        ).fetchone()

        if not existing:

            return False

        track_id = existing["track_id"]

        was_preferred = (
            existing["is_preferred"] == 1
        )

        connection.execute(
            """
            DELETE FROM track_mp3
            WHERE id = ?
            """,
            (
                link_id,
            )
        )

        if was_preferred:

            next_mp3 = connection.execute(
                """
                SELECT id
                FROM track_mp3

                WHERE track_id = ?

                ORDER BY
                    score DESC,
                    id

                LIMIT 1
                """,
                (
                    track_id,
                )
            ).fetchone()

            if next_mp3:

                connection.execute(
                    """
                    UPDATE track_mp3
                    SET is_preferred = 1
                    WHERE id = ?
                    """,
                    (
                        next_mp3["id"],
                    )
                )

        connection.commit()

        return True

    except Exception:

        connection.rollback()

        raise

    finally:

        connection.close()


# ============================================================
# DATABASE COUNTS
# ============================================================

def get_database_counts():

    connection = get_connection()

    try:

        releases = connection.execute(
            "SELECT COUNT(*) FROM releases"
        ).fetchone()[0]

        tracks = connection.execute(
            "SELECT COUNT(*) FROM tracks"
        ).fetchone()[0]

        mp3s = connection.execute(
            "SELECT COUNT(*) FROM mp3_files"
        ).fetchone()[0]

        links = connection.execute(
            "SELECT COUNT(*) FROM track_mp3"
        ).fetchone()[0]

        preferred = connection.execute(
            """
            SELECT COUNT(*)
            FROM track_mp3
            WHERE is_preferred = 1
            """
        ).fetchone()[0]

        return {
            "releases": releases,
            "tracks": tracks,
            "mp3s": mp3s,
            "links": links,
            "preferred": preferred
        }

    finally:

        connection.close()


# ============================================================
# RELEASE STATISTICS
# ============================================================

def get_release_statistics(
    release_id
):

    connection = get_connection()

    try:

        row = connection.execute(
            """
            SELECT

                COUNT(
                    DISTINCT t.id
                ) AS tracks,

                COUNT(
                    DISTINCT tm.id
                ) AS mp3_links,

                COUNT(
                    DISTINCT CASE
                        WHEN tm.is_preferred = 1
                        THEN tm.id
                    END
                ) AS preferred_mp3s

            FROM releases r

            LEFT JOIN tracks t
                ON t.release_id = r.id

            LEFT JOIN track_mp3 tm
                ON tm.track_id = t.id

            WHERE r.id = ?
            """,
            (
                release_id,
            )
        ).fetchone()

        return row

    finally:

        connection.close()


# ============================================================
# DATABASE INITIALIZATION
# ============================================================

def initialize_database():

    connection = get_connection()

    try:

        cursor = connection.cursor()

        # ----------------------------------------------------
        # RELEASES
        # ----------------------------------------------------

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS releases (

                id INTEGER PRIMARY KEY AUTOINCREMENT,

                artist TEXT NOT NULL DEFAULT '',

                title TEXT NOT NULL DEFAULT '',

                label TEXT DEFAULT '',

                catalog TEXT DEFAULT '',

                year INTEGER,

                genre TEXT DEFAULT '',

                discogs TEXT DEFAULT '',

                discogs_link TEXT DEFAULT '',

                cover TEXT DEFAULT '',

                notes TEXT DEFAULT '',

                storage_code TEXT DEFAULT '',

                created_at TEXT
                    DEFAULT CURRENT_TIMESTAMP,

                updated_at TEXT
                    DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        # ----------------------------------------------------
        # TRACKS
        # ----------------------------------------------------

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS tracks (

                id INTEGER PRIMARY KEY AUTOINCREMENT,

                release_id INTEGER NOT NULL,

                position TEXT NOT NULL DEFAULT '',

                artist TEXT DEFAULT '',

                title TEXT NOT NULL DEFAULT '',

                duration INTEGER DEFAULT 0,

                bpm REAL,

                genre TEXT DEFAULT '',

                notes TEXT DEFAULT '',

                created_at TEXT
                    DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (
                    release_id
                )
                REFERENCES releases(id)
                ON DELETE CASCADE
            )
            """
        )

        # ----------------------------------------------------
        # MP3 FILES
        # ----------------------------------------------------

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS mp3_files (

                id INTEGER PRIMARY KEY AUTOINCREMENT,

                path TEXT NOT NULL UNIQUE,

                filename TEXT DEFAULT '',

                artist TEXT DEFAULT '',

                title TEXT DEFAULT '',

                album TEXT DEFAULT '',

                duration INTEGER DEFAULT 0,

                bitrate INTEGER DEFAULT 0,

                sample_rate INTEGER DEFAULT 0,

                bpm REAL,

                genre TEXT DEFAULT '',

                year INTEGER,

                filesize INTEGER DEFAULT 0,

                created_at TEXT
                    DEFAULT CURRENT_TIMESTAMP,

                updated_at TEXT
                    DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        # ----------------------------------------------------
        # TRACK <-> MP3
        # ----------------------------------------------------

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS track_mp3 (

                id INTEGER PRIMARY KEY AUTOINCREMENT,

                track_id INTEGER NOT NULL,

                mp3_id INTEGER NOT NULL,

                score REAL DEFAULT 0,

                is_preferred INTEGER DEFAULT 0,

                manually_added INTEGER DEFAULT 0,

                created_at TEXT
                    DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (
                    track_id
                )
                REFERENCES tracks(id)
                ON DELETE CASCADE,

                FOREIGN KEY (
                    mp3_id
                )
                REFERENCES mp3_files(id)
                ON DELETE CASCADE,

                UNIQUE (
                    track_id,
                    mp3_id
                )
            )
            """
        )

        # ----------------------------------------------------
        # FAVORITES
        # ----------------------------------------------------

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS favorites (

                id INTEGER PRIMARY KEY AUTOINCREMENT,

                release_id INTEGER,

                track_id INTEGER,

                created_at TEXT
                    DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (
                    release_id
                )
                REFERENCES releases(id)
                ON DELETE CASCADE,

                FOREIGN KEY (
                    track_id
                )
                REFERENCES tracks(id)
                ON DELETE CASCADE
            )
            """
        )

        # ----------------------------------------------------
        # INDEXES
        # ----------------------------------------------------

        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS
            idx_tracks_release

            ON tracks(release_id)
            """
        )

        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS
            idx_mp3_artist

            ON mp3_files(artist)
            """
        )

        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS
            idx_mp3_title

            ON mp3_files(title)
            """
        )

        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS
            idx_track_mp3_track

            ON track_mp3(track_id)
            """
        )

        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS
            idx_track_mp3_mp3

            ON track_mp3(mp3_id)
            """
        )

        connection.commit()

    finally:

        connection.close()

    migrate_database()


# ============================================================
# DATABASE TEST
# ============================================================

def test_database():

    connection = get_connection()

    try:

        rows = connection.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
            ORDER BY name
            """
        ).fetchall()

        tables = [
            row["name"]
            for row in rows
        ]

    finally:

        connection.close()

    expected = [
        "favorites",
        "mp3_files",
        "releases",
        "track_mp3",
        "tracks"
    ]

    missing = [
        table
        for table in expected
        if table not in tables
    ]

    print()
    print("=" * 60)
    print("VINYLVAULT V3 DATABASE TEST")
    print("=" * 60)
    print()

    print(
        "Database:"
    )

    print(
        DB_PATH
    )

    print()

    if missing:

        print(
            "DATABASE TEST FAILED"
        )

        print()

        print(
            "Ontbrekende tabellen:"
        )

        for table in missing:

            print(
                f"  - {table}"
            )

        print()

        return False

    print(
        "Tabellen:"
    )

    for table in tables:

        print(
            f"  OK  {table}"
        )

    print()

    print(
        "DATABASE TEST OK"
    )

    print(
        "=" * 60
    )

    return True


# ============================================================
# DATABASE STATUS
# ============================================================

def print_database_status():

    counts = get_database_counts()

    print()
    print("=" * 60)
    print("VINYLVAULT V3 STATUS")
    print("=" * 60)
    print()

    print(
        "Database:",
        DB_PATH
    )

    print(
        "Releases:",
        counts["releases"]
    )

    print(
        "Tracks:",
        counts["tracks"]
    )

    print(
        "MP3s:",
        counts["mp3s"]
    )

    print(
        "Koppelingen:",
        counts["links"]
    )

    print(
        "Preferred MP3s:",
        counts["preferred"]
    )

    print()

    print(
        "DATABASE STATUS OK"
    )

    print(
        "=" * 60
    )


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    print()
    print(
        "VinylVault V3 database controleren..."
    )
    print()

    initialize_database()

    test_database()

    print_database_status()
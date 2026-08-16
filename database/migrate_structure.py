import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "vinylvault.db"
BACKUP_PATH = BASE_DIR / "data" / "vinylvault_BEFORE_MIGRATION.db"

def table_columns(connection, table_name):
    return [
        row["name"]
        for row in connection.execute(
            f"PRAGMA table_info({table_name})"
        ).fetchall()
    ]

def migrate():
    print()
    print("=" * 60)
    print("VINYLVAULT V3 - STRUCTURE MIGRATION")
    print("=" * 60)
    print()

    if not DB_PATH.exists():
        print("FOUT: database bestaat niet:")
        print(DB_PATH)
        return

    print("Database:")
    print(DB_PATH)
    print()

    if not BACKUP_PATH.exists():
        source = sqlite3.connect(DB_PATH)
        backup = sqlite3.connect(BACKUP_PATH)
        source.backup(backup)
        backup.close()
        source.close()

        print("Backup gemaakt:")
        print(BACKUP_PATH)
    else:
        print("Backup bestaat al:")
        print(BACKUP_PATH)

    print()

    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")

    try:
        releases_columns = table_columns(connection, "releases")

        print("RELEASES KOLOMMEN:")
        print(", ".join(releases_columns))
        print()

        if "storage_code" not in releases_columns:
            print("storage_code ontbreekt - toevoegen...")

            connection.execute(
                """
                ALTER TABLE releases
                ADD COLUMN storage_code TEXT DEFAULT ''
                """
            )

        tracks_columns = table_columns(connection, "tracks")

        print("TRACKS KOLOMMEN:")
        print(", ".join(tracks_columns))
        print()

        mp3_columns = table_columns(connection, "mp3_files")

        print("MP3 KOLOMMEN:")
        print(", ".join(mp3_columns))
        print()

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS track_mp3 (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                track_id INTEGER NOT NULL,
                mp3_id INTEGER NOT NULL,
                score REAL DEFAULT 0,
                is_preferred INTEGER DEFAULT 0,
                manually_added INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (track_id)
                    REFERENCES tracks(id)
                    ON DELETE CASCADE,

                FOREIGN KEY (mp3_id)
                    REFERENCES mp3_files(id)
                    ON DELETE CASCADE,

                UNIQUE(track_id, mp3_id)
            )
            """
        )

        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_tracks_release
            ON tracks(release_id)
            """
        )

        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_mp3_artist
            ON mp3_files(artist)
            """
        )

        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_mp3_title
            ON mp3_files(title)
            """
        )

        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_track_mp3_track
            ON track_mp3(track_id)
            """
        )

        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_track_mp3_mp3
            ON track_mp3(mp3_id)
            """
        )

        connection.commit()

        print("=" * 60)
        print("MIGRATION KLAAR")
        print("=" * 60)
        print()
        print("Er zijn GEEN releases of tracks verwijderd.")
        print("Bestaande data is behouden.")
        print("MP3-bestanden zijn niet gewijzigd.")
        print()

    except Exception as error:
        connection.rollback()
        print("MIGRATION FOUT:")
        print(error)
        raise

    finally:
        connection.close()

if __name__ == "__main__":
    migrate()

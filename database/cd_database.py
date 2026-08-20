# ============================================================
# KID ACID'S VINYLVAULT V3
# CD DATABASE MODULE
# ============================================================

import sqlite3
from database.database import get_connection


CD_SCHEMA = """
CREATE TABLE IF NOT EXISTS cd_releases (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    artist TEXT NOT NULL DEFAULT '',
    title TEXT NOT NULL DEFAULT '',
    media_type TEXT NOT NULL DEFAULT 'CD',
    label TEXT NOT NULL DEFAULT '',
    catalog TEXT NOT NULL DEFAULT '',
    year INTEGER,
    genre TEXT NOT NULL DEFAULT '',
    discogs TEXT NOT NULL DEFAULT '',
    discogs_link TEXT NOT NULL DEFAULT '',
    cover TEXT NOT NULL DEFAULT '',
    notes TEXT NOT NULL DEFAULT '',
    checked INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(artist, title, media_type)
)
"""


def ensure_cd_schema(connection=None):
    own_connection = connection is None
    connection = connection or get_connection()
    try:
        connection.execute(CD_SCHEMA)
        connection.execute(
            "CREATE INDEX IF NOT EXISTS idx_cd_releases_artist ON cd_releases(artist COLLATE NOCASE)"
        )
        connection.execute(
            "CREATE INDEX IF NOT EXISTS idx_cd_releases_title ON cd_releases(title COLLATE NOCASE)"
        )
        connection.commit()
    finally:
        if own_connection:
            connection.close()


def get_cd_releases():
    connection = get_connection()
    try:
        ensure_cd_schema(connection)
        return connection.execute(
            """
            SELECT id, artist, title, media_type, label, catalog, year,
                   genre, discogs, discogs_link, cover, notes, checked
            FROM cd_releases
            ORDER BY artist COLLATE NOCASE, title COLLATE NOCASE, id
            """
        ).fetchall()
    finally:
        connection.close()


def count_cd_releases():
    connection = get_connection()
    try:
        ensure_cd_schema(connection)
        return connection.execute("SELECT COUNT(*) FROM cd_releases").fetchone()[0]
    finally:
        connection.close()


def import_cd_rows(rows):
    """Insert CD rows safely; existing artist/title/type combinations are skipped."""
    connection = get_connection()
    inserted = 0
    skipped = 0
    try:
        ensure_cd_schema(connection)
        for row in rows:
            artist = str(row.get("artist", "") or "").strip()
            title = str(row.get("title", "") or "").strip()
            media_type = str(row.get("media_type", "CD") or "CD").strip() or "CD"
            if not artist or not title:
                skipped += 1
                continue

            cursor = connection.execute(
                """
                INSERT OR IGNORE INTO cd_releases
                    (artist, title, media_type, label, catalog, year, genre,
                     discogs, discogs_link, cover, notes, checked)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    artist,
                    title,
                    media_type,
                    str(row.get("label", "") or "").strip(),
                    str(row.get("catalog", "") or "").strip(),
                    row.get("year"),
                    str(row.get("genre", "") or "").strip(),
                    str(row.get("discogs", "") or "").strip(),
                    str(row.get("discogs_link", "") or "").strip(),
                    str(row.get("cover", "") or "").strip(),
                    str(row.get("notes", "") or "").strip(),
                    int(row.get("checked", 0) or 0),
                ),
            )
            if cursor.rowcount:
                inserted += 1
            else:
                skipped += 1

        connection.commit()
        return inserted, skipped
    finally:
        connection.close()

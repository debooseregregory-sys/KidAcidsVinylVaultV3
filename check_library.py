import sqlite3

DB = r"data\vinylvault.db"

connection = sqlite3.connect(DB)

try:
    print()
    print("=" * 60)
    print("VINYLVAULT LIBRARY ANALYSE")
    print("=" * 60)
    print()

    releases = connection.execute(
        "SELECT COUNT(*) FROM releases"
    ).fetchone()[0]

    discogs = connection.execute(
        "SELECT COUNT(*) FROM discogs_vinyl"
    ).fetchone()[0]

    with_discogs = connection.execute(
        """
        SELECT COUNT(*)
        FROM releases
        WHERE discogs IS NOT NULL
        AND LENGTH(TRIM(discogs)) > 0
        """
    ).fetchone()[0]

    without_discogs = connection.execute(
        """
        SELECT COUNT(*)
        FROM releases
        WHERE discogs IS NULL
        OR LENGTH(TRIM(discogs)) = 0
        """
    ).fetchone()[0]

    artist_title_matches = connection.execute(
        """
        SELECT COUNT(*)
        FROM releases r
        JOIN discogs_vinyl d
          ON LOWER(TRIM(r.artist))
             = LOWER(TRIM(d.artist))
         AND LOWER(TRIM(r.title))
             = LOWER(TRIM(d.title))
        """
    ).fetchone()[0]

    print("Releases                 :", releases)
    print("Discogs vinyl             :", discogs)
    print("Met Discogs ID            :", with_discogs)
    print("Zonder Discogs ID         :", without_discogs)
    print("Match artiest + titel     :", artist_title_matches)

    print()
    print("-" * 60)
    print("VOORBEELDEN RELEASES")
    print("-" * 60)

    rows = connection.execute(
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
        ORDER BY id
        LIMIT 20
        """
    ).fetchall()

    for row in rows:

        print()
        print("ID      :", row[0])
        print("Artist  :", row[1])
        print("Title   :", row[2])
        print("Label   :", row[3])
        print("Catalog :", row[4])
        print("Year    :", row[5])
        print("Discogs :", row[6])
        print("Storage :", row[7])

    print()
    print("=" * 60)
    print("ANALYSE KLAAR")
    print("=" * 60)

finally:
    connection.close()
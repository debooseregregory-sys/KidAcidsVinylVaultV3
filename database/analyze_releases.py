import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "vinylvault.db"


def main():
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row

    try:
        print()
        print("=" * 70)
        print("VINYLVAULT V3 - RELEASE NORMALISATIE ANALYSE")
        print("=" * 70)
        print()

        releases = connection.execute(
            """
            SELECT
                r.id,
                r.artist,
                r.title,
                r.label,
                r.catalog,
                r.year,
                r.discogs,
                COUNT(t.id) AS track_count
            FROM releases r
            LEFT JOIN tracks t
                ON t.release_id = r.id
            GROUP BY r.id
            ORDER BY
                r.artist COLLATE NOCASE,
                r.title COLLATE NOCASE,
                r.id
            """
        ).fetchall()

        print(f"TOTAAL RELEASES: {len(releases)}")
        print()

        print("=== RELEASES MET 1 TRACK ===")
        print()

        one_track = [
            r for r in releases
            if r["track_count"] == 1
        ]

        print(f"Aantal: {len(one_track)}")
        print()

        for r in one_track[:200]:
            print(
                f'{r["id"]:5} | '
                f'{r["artist"]} | '
                f'{r["title"]} | '
                f'{r["label"]} | '
                f'{r["catalog"]} | '
                f'{r["year"]} | '
                f'Discogs={r["discogs"]}'
            )

        print()
        print("=== RELEASES ZONDER TITEL ===")
        print()

        no_title = [
            r for r in releases
            if not (r["title"] or "").strip()
        ]

        print(f"Aantal: {len(no_title)}")
        print()

        for r in no_title[:200]:
            print(
                f'{r["id"]:5} | '
                f'{r["artist"]} | '
                f'{r["label"]} | '
                f'{r["catalog"]} | '
                f'{r["year"]} | '
                f'Discogs={r["discogs"]} | '
                f'TRACKS={r["track_count"]}'
            )

        print()
        print("=== RELEASES MET DISCOGS-ID ===")
        print()

        with_discogs = [
            r for r in releases
            if (r["discogs"] or "").strip()
        ]

        print(f"Aantal: {len(with_discogs)}")
        print()

        for r in with_discogs[:100]:
            print(
                f'{r["id"]:5} | '
                f'{r["artist"]} | '
                f'{r["title"]} | '
                f'{r["label"]} | '
                f'{r["catalog"]} | '
                f'{r["year"]} | '
                f'Discogs={r["discogs"]} | '
                f'TRACKS={r["track_count"]}'
            )

        print()
        print("=" * 70)
        print("ANALYSE KLAAR - ER IS NIETS GEWIJZIGD")
        print("=" * 70)
        print()

    finally:
        connection.close()


if __name__ == "__main__":
    main()

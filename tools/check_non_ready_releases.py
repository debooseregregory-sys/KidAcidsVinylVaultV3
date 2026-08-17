from pathlib import Path
import sqlite3

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "vinylvault.db"
OUT_DIR = BASE_DIR / "reports"
OUT_CSV = OUT_DIR / "niet_klaar_releases.csv"
OUT_TXT = OUT_DIR / "niet_klaar_releases.txt"


def text(value):
    if value is None:
        return ""
    return str(value).strip()


def main():
    if not DB_PATH.exists():
        raise SystemExit(f"Database niet gevonden: {DB_PATH}")

    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row

    try:
        releases = connection.execute(
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
                storage_code,
                checked
            FROM releases
            WHERE COALESCE(checked, 0) = 0
            ORDER BY artist COLLATE NOCASE, title COLLATE NOCASE, id
            """
        ).fetchall()

        report_rows = []

        for release in releases:
            release_id = release["id"]
            tracks = connection.execute(
                """
                SELECT id, position, artist, title
                FROM tracks
                WHERE release_id = ?
                ORDER BY id
                """,
                (release_id,),
            ).fetchall()

            missing = []
            position_seen = {}
            duplicate_positions = []
            tracks_without_mp3 = []
            mp3_link_count = 0

            required_release_fields = [
                ("ARTIST", release["artist"]),
                ("TITEL", release["title"]),
                ("LABEL", release["label"]),
                ("CATALOG", release["catalog"]),
                ("JAAR", release["year"]),
                ("KASTCODE", release["storage_code"]),
                ("DISCOGS", release["discogs"]),
            ]

            for field_name, value in required_release_fields:
                if not text(value):
                    missing.append(field_name)

            if not tracks:
                missing.append("TRACKS")

            for track in tracks:
                position = text(track["position"])
                track_title = text(track["title"])

                if not position:
                    missing.append(f"TRACK {track['id']}: POSITIE")
                else:
                    key = position.upper()
                    position_seen.setdefault(key, []).append(track["id"])

                if not track_title:
                    missing.append(f"TRACK {track['id']}: TITEL")

                mp3_count = connection.execute(
                    "SELECT COUNT(*) FROM track_mp3 WHERE track_id = ?",
                    (track["id"],),
                ).fetchone()[0]

                mp3_link_count += mp3_count

                if mp3_count == 0:
                    tracks_without_mp3.append(
                        f"{position or '?'} {track_title or '[GEEN TITEL]'}"
                    )

            for position, ids in position_seen.items():
                if len(ids) > 1:
                    duplicate_positions.append(position)

            if duplicate_positions:
                missing.append(
                    "DUBBELE POSITIES: " + ", ".join(sorted(duplicate_positions))
                )

            if tracks_without_mp3:
                missing.append(
                    f"MP3 ONTBREEKT BIJ {len(tracks_without_mp3)} TRACK(S)"
                )

            report_rows.append(
                {
                    "id": release_id,
                    "artist": text(release["artist"]),
                    "title": text(release["title"]),
                    "label": text(release["label"]),
                    "catalog": text(release["catalog"]),
                    "year": text(release["year"]),
                    "storage_code": text(release["storage_code"]),
                    "discogs": text(release["discogs"]),
                    "track_count": len(tracks),
                    "mp3_link_count": mp3_link_count,
                    "missing": missing,
                }
            )

        OUT_DIR.mkdir(parents=True, exist_ok=True)

        with OUT_CSV.open("w", encoding="utf-8-sig", newline="") as handle:
            handle.write(
                "ID;ARTIST;RELEASE;LABEL;CATALOG;YEAR;KASTCODE;DISCOGS;TRACKS;MP3_KOPPELINGEN;ONTBREKEND\n"
            )
            for row in report_rows:
                missing = " | ".join(row["missing"])
                values = [
                    row["id"], row["artist"], row["title"], row["label"],
                    row["catalog"], row["year"], row["storage_code"],
                    row["discogs"], row["track_count"], row["mp3_link_count"],
                    missing,
                ]
                handle.write(";".join(str(v).replace(";", ",") for v in values) + "\n")

        with OUT_TXT.open("w", encoding="utf-8") as handle:
            handle.write("VINYLVAULT - NIET KLAAR RELEASES\n")
            handle.write("=" * 78 + "\n\n")
            handle.write(f"Aantal niet-klaar releases: {len(report_rows)}\n\n")

            for row in report_rows:
                handle.write(
                    f"[{row['id']}] {row['artist']} - {row['title']}\n"
                )
                handle.write(
                    f"  Label: {row['label']} | Catalog: {row['catalog']} | Jaar: {row['year']} | Kast: {row['storage_code']}\n"
                )
                handle.write(
                    f"  Discogs: {row['discogs']} | Tracks: {row['track_count']} | MP3 koppelingen: {row['mp3_link_count']}\n"
                )
                if row["missing"]:
                    for item in row["missing"]:
                        handle.write(f"  - {item}\n")
                handle.write("\n")

        print("=" * 78)
        print("VINYLVAULT - NIET KLAAR CONTROLE")
        print("=" * 78)
        print(f"Niet-klaar releases : {len(report_rows)}")
        print(f"CSV rapport         : {OUT_CSV}")
        print(f"Tekst rapport       : {OUT_TXT}")
        print("Database gewijzigd  : NEE")
        print("=" * 78)

    finally:
        connection.close()


if __name__ == "__main__":
    main()

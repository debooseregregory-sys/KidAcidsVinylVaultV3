from pathlib import Path
import shutil
import sqlite3
from datetime import datetime

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "vinylvault.db"
BACKUP_DIR = BASE_DIR / "reports" / "db_backups"

TARGET_LINK_IDS = (16, 2712, 14)
PROTECTED_LINK_ID = 3245


def main():
    if not DB_PATH.exists():
        raise SystemExit(f"Database niet gevonden: {DB_PATH}")

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    try:
        placeholders = ",".join("?" for _ in TARGET_LINK_IDS)
        rows = conn.execute(
            f"""
            SELECT
                tm.id AS link_id,
                tm.track_id,
                tm.mp3_id,
                tm.score,
                tm.is_preferred,
                tm.manually_added,
                m.path,
                r.id AS release_id,
                r.artist,
                r.title AS release_title,
                t.position,
                t.title AS track_title,
                r.checked
            FROM track_mp3 tm
            JOIN mp3_files m ON m.id = tm.mp3_id
            JOIN tracks t ON t.id = tm.track_id
            JOIN releases r ON r.id = t.release_id
            WHERE tm.id IN ({placeholders})
            ORDER BY tm.id
            """,
            TARGET_LINK_IDS,
        ).fetchall()

        print("=" * 80)
        print("VINYLVAULT - VEILIGE OPKUISING DODE MP3-LINKS")
        print("=" * 80)
        print(f"Te verwijderen links : {len(rows)}")
        print(f"Beschermde link      : {PROTECTED_LINK_ID}")

        if len(rows) != len(TARGET_LINK_IDS):
            raise SystemExit("STOP: niet alle verwachte links bestaan. Database onaangeraakt.")

        for row in rows:
            if row["is_preferred"] or row["manually_added"] or float(row["score"] or 0) != 0:
                raise SystemExit(
                    f"STOP: link {row['link_id']} is niet veilig om automatisch te verwijderen."
                )

            print(
                f"VERWIJDER {row['link_id']} | RELEASE {row['release_id']} | "
                f"{row['artist']} - {row['release_title']} | "
                f"{row['position']} {row['track_title']}"
            )

        protected = conn.execute(
            """
            SELECT id, track_id, mp3_id, score, is_preferred, manually_added
            FROM track_mp3
            WHERE id = ?
            """,
            (PROTECTED_LINK_ID,),
        ).fetchone()

        if protected is None:
            raise SystemExit("STOP: beschermde link 3245 ontbreekt. Database onaangeraakt.")

        if not protected["is_preferred"] or not protected["manually_added"] or float(protected["score"] or 0) != 100.0:
            raise SystemExit("STOP: beschermde link 3245 heeft onverwachte metadata. Database onaangeraakt.")

        BACKUP_DIR.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup = BACKUP_DIR / f"vinylvault_before_dead_mp3_cleanup_{stamp}.db"
        shutil.copy2(DB_PATH, backup)

        conn.execute("BEGIN")
        conn.execute(
            f"DELETE FROM track_mp3 WHERE id IN ({placeholders})",
            TARGET_LINK_IDS,
        )
        conn.commit()

        print()
        print(f"Verwijderd            : {len(rows)}")
        print(f"Beschermd             : {PROTECTED_LINK_ID}")
        print(f"Backup                : {backup}")
        print("Scores gewijzigd      : NEE")
        print("Preferred gewijzigd   : NEE")
        print("Database gewijzigd    : JA")
        print("=" * 80)

    finally:
        conn.close()


if __name__ == "__main__":
    main()

import sqlite3
from pathlib import Path

root = Path(r"C:\Users\andyb\Desktop\KidAcidsVinylVaultV3")

print()
print("=" * 120)
print("ALLE DATABASES IN VINYLVAULT")
print("=" * 120)

found = []

for db in root.rglob("*.db"):
    try:
        c = sqlite3.connect(str(db))

        checked = c.execute(
            "SELECT COUNT(*) FROM releases WHERE checked=1"
        ).fetchone()[0]

        releases_mp3 = c.execute(
            """
            SELECT COUNT(DISTINCT t.release_id)
            FROM tracks t
            JOIN track_mp3 tm ON tm.track_id=t.id
            """
        ).fetchone()[0]

        track_mp3 = c.execute(
            "SELECT COUNT(*) FROM track_mp3"
        ).fetchone()[0]

        releases = c.execute(
            "SELECT COUNT(*) FROM releases"
        ).fetchone()[0]

        c.close()

        found.append(
            (
                checked,
                releases_mp3,
                track_mp3,
                releases,
                str(db)
            )
        )

    except Exception:
        pass

found.sort(
    key=lambda x: (x[0], x[1], x[2]),
    reverse=True
)

for checked, releases_mp3, track_mp3, releases, db in found:
    print(
        f"KLAAR={checked:4} | "
        f"MP3_RELEASES={releases_mp3:4} | "
        f"TRACK_MP3={track_mp3:5} | "
        f"RELEASES={releases:5} | "
        f"{db}"
    )

print()
print("DATABASES GEVONDEN:", len(found))

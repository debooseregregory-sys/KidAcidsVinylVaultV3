import sqlite3

DB = r"data\vinylvault.db"

conn = sqlite3.connect(DB)

conn.execute(
    """
    UPDATE releases
    SET discogs = ?,
        discogs_link = ?
    WHERE id = ?
    """,
    (
        "931014",
        "https://www.discogs.com/release/931014-Max-Walder-I-Can-Be-Hard-EP",
        4690
    )
)

conn.execute(
    "DELETE FROM tracks WHERE release_id = ?",
    (4690,)
)

tracks = [
    (4690, "A1", "Max Walder", "Digeridoo", 431),
    (4690, "A2", "Max Walder", "Flap Head", 401),
    (4690, "B1", "Max Walder", "Phloam", 331),
    (4690, "B2", "Max Walder", "Isoprophlex", 382),
]

conn.executemany(
    """
    INSERT INTO tracks
    (release_id, position, artist, title, duration)
    VALUES (?, ?, ?, ?, ?)
    """,
    tracks
)

conn.commit()

rows = conn.execute(
    """
    SELECT position, artist, title, duration
    FROM tracks
    WHERE release_id = ?
    ORDER BY id
    """,
    (4690,)
).fetchall()

print()
print("RELEASE 4690 HERSTELD")
print()

for row in rows:
    minutes = row[3] // 60
    seconds = row[3] % 60
    print(f"{row[0]} | {row[1]} | {row[2]} | {minutes}:{seconds:02d}")

conn.close()
import sqlite3

db = "data/vinylvault.db"
conn = sqlite3.connect(db)

print("=== RELEASES KOLOMMEN ===")
for row in conn.execute("PRAGMA table_info(releases)"):
    print(row)

print()
print("=== TRACKS KOLOMMEN ===")
for row in conn.execute("PRAGMA table_info(tracks)"):
    print(row)

conn.close()

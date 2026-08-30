import sqlite3

db = r".\data\vinylvault.db"

c = sqlite3.connect(db)

print("ECHTE DATABASE:", db)
print("RELEASES TABEL:", c.execute(
    "SELECT name FROM sqlite_master WHERE type='table' AND name='releases'"
).fetchone())

print("AANTAL RELEASES:", c.execute(
    "SELECT COUNT(*) FROM releases"
).fetchone()[0])

print("\nALLE TABELLEN:")
for row in c.execute(
    "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
):
    print(" ", row[0])

c.close()
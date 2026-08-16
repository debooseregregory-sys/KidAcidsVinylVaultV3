import sqlite3

db = r".\data\vinylvault.db"

c = sqlite3.connect(db)

print("DATABASE:", db)
print()
print("TABELLEN:")
print("=" * 60)

rows = c.execute(
    "SELECT name FROM sqlite_master WHERE type = 'table' ORDER BY name"
).fetchall()

for row in rows:
    print(row[0])

c.close()

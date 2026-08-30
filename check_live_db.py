import sqlite3

p = r".\data\vinylvault.db"

c = sqlite3.connect(p)

print("DATABASE:", p)
print("RELEASES:", c.execute("SELECT COUNT(*) FROM releases").fetchone()[0])

print("TABELLEN:")
for row in c.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"):
    print(" ", row[0])

c.close()

import sqlite3

p = r"dist\KidAcidsMusicVault\data\vinylvault.db"

c = sqlite3.connect(p)

print("DATABASE:", p)
print("TABELLEN:")
for row in c.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"):
    print(" ", row[0])

try:
    print("RELEASES:", c.execute("SELECT COUNT(*) FROM releases").fetchone()[0])
except Exception as e:
    print("RELEASES FOUT:", e)

c.close()

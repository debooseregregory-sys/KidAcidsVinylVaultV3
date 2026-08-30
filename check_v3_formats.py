import sqlite3

p = r".\release\KidAcidsMusicVault\_internal\data\vinylvault_v3.db"
c = sqlite3.connect(p)

print("FORMATEN:")
for row in c.execute("""
    SELECT COALESCE(format,''), COUNT(*)
    FROM releases
    GROUP BY format
    ORDER BY COUNT(*) DESC
"""):
    print(row)

c.close()

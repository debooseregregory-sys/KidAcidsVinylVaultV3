import sqlite3

db = "data/vinylvault.db"

conn = sqlite3.connect(db)

print("=== TABELLEN ===")
for row in conn.execute("""
    SELECT name
    FROM sqlite_master
    WHERE type = 'table'
    ORDER BY name
"""):
    print(row[0])

print()
print("=== VINYL_ITEMS KOLOMMEN ===")

for row in conn.execute("PRAGMA table_info(vinyl_items)"):
    print(row)

conn.close()

import sqlite3

DB = r".\data\vinylvault.db"

conn = sqlite3.connect(DB)
cur = conn.cursor()

print("=" * 90)
print("RELEASES — ECHTE DATABASESTRUCTUUR")
print("=" * 90)

rows = cur.execute("PRAGMA table_info(releases)").fetchall()

for row in rows:
    cid, name, col_type, notnull, default, pk = row
    print(
        f"{cid:2} | "
        f"{name:25} | "
        f"{col_type:15} | "
        f"PK={pk}"
    )

print()
print("=" * 90)
print("VOORBEELD RECORD")
print("=" * 90)

columns = [row[1] for row in rows]

record = cur.execute(
    "SELECT * FROM releases LIMIT 1"
).fetchone()

for name, value in zip(columns, record):
    print(f"{name:25} : {value}")

conn.close()

print()
print("=" * 90)
print("KLAAR — DATABASE IS NIET GEWIJZIGD")
print("=" * 90)

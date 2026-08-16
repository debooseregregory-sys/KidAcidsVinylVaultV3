import sqlite3

DB = r".\data\vinylvault.db"

conn = sqlite3.connect(DB)
cur = conn.cursor()

print("=" * 80)
print("DATABASE STRUCTUUR")
print("=" * 80)

print("\nTABELLEN:")
for row in cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"):
    print(" -", row[0])

print("\nVINYL_ITEMS KOLOMMEN:")
print("-" * 80)

try:
    rows = cur.execute("PRAGMA table_info(vinyl_items)").fetchall()

    if not rows:
        print("GEEN TABEL vinyl_items GEVONDEN")
    else:
        for row in rows:
            cid, name, col_type, notnull, default, pk = row
            print(
                f"{cid:2} | "
                f"{name:20} | "
                f"{col_type:12} | "
                f"PK={pk}"
            )

except Exception as e:
    print("FOUT:", e)

conn.close()

print("\n" + "=" * 80)
print("KLAAR - DATABASE IS NIET GEWIJZIGD")
print("=" * 80)

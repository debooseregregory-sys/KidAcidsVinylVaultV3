import sqlite3, os
con = sqlite3.connect("data/vinylvault.db")
cur = con.cursor()
cur.execute("PRAGMA table_info(releases)")
cols = [c[1] for c in cur.fetchall()]
print("COLUMNS:", cols)

cover_cols = [c for c in cols if "cover" in c.lower() or "image" in c.lower()]
print("COVER COLUMNS:", cover_cols)

if cover_cols:
    col = cover_cols[0]
    cur.execute(f"SELECT id, {col} FROM releases WHERE {col} IS NOT NULL AND {col} != '' LIMIT 5")
    rows = cur.fetchall()
    for r in rows:
        path = r[1]
        exists = os.path.exists(path)
        print(f"id={r[0]} path={path!r} exists_as_is={exists}")

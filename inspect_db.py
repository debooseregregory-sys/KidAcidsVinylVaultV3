import sqlite3

DB = r"data\vinylvault.db"

conn = sqlite3.connect(DB)
cur = conn.cursor()

tables = cur.execute("""
    SELECT name
    FROM sqlite_master
    WHERE type='table'
    ORDER BY name
""").fetchall()

for (table,) in tables:
    print("\n" + "=" * 80)
    print(f"TABLE: {table}")
    print("=" * 80)

    columns = cur.execute(f'PRAGMA table_info("{table}")').fetchall()

    print("\nKOLOMMEN:")
    for col in columns:
        print(
            f"  {col[1]:25} "
            f"type={col[2]:12} "
            f"notnull={col[3]} "
            f"default={col[4]} "
            f"pk={col[5]}"
        )

    try:
        count = cur.execute(
            f'SELECT COUNT(*) FROM "{table}"'
        ).fetchone()[0]

        print(f"\nAANTAL: {count}")

    except Exception as e:
        print("COUNT FOUT:", e)

    # Alleen voor echte tabellen met data
    if table not in ("sqlite_sequence",):

        try:
            rows = cur.execute(
                f'SELECT * FROM "{table}" LIMIT 3'
            ).fetchall()

            print("\nVOORBEELD:")
            for row in rows:
                print(row)

        except Exception as e:
            print("VOORBEELD FOUT:", e)

conn.close()

print("\n" + "=" * 80)
print("INSPECTIE KLAAR")
print("=" * 80)
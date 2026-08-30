import sqlite3
import glob
import os

files = glob.glob(r"data\*.db") + glob.glob(r"data\backups\*.db")

print("--- RELEASE 62 STATUS IN ALLE DATABASES ---")

for f in sorted(files):
    try:
        con = sqlite3.connect(f)
        tables = [r[0] for r in con.execute(
            "select name from sqlite_master where type='table'"
        ).fetchall()]

        if "releases" not in tables:
            con.close()
            continue

        row = con.execute(
            "select id, artist, title, review_status, reviewed_at, checked "
            "from releases where id=62"
        ).fetchone()

        con.close()

        if row:
            print(os.path.basename(f), "->", row)

    except Exception as e:
        print(os.path.basename(f), "ERROR:", e)

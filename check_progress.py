import sqlite3
import glob
import os

for db in glob.glob(r".\**\vinylvault.db", recursive=True):
    print("\nDATABASE:", os.path.abspath(db))
    con = sqlite3.connect(db)
    for field in ["storage_code", "checked", "review_status", "mp3_pad", "mp3_path"]:
        try:
            value = con.execute(
                f"SELECT COUNT(*) FROM releases WHERE {field} != ''"
            ).fetchone()[0]
            print(f"  {field}: {value}")
        except Exception as e:
            print(f"  {field}: FOUT {e}")
    con.close()

import sqlite3, glob, os

files = [r".\data\vinylvault.db"] + glob.glob(r".\data\backups\*.db")

for f in files:
    try:
        c = sqlite3.connect(f)
        cols = [x[1] for x in c.execute("PRAGMA table_info(releases)").fetchall()]
        releases = c.execute("SELECT COUNT(*) FROM releases").fetchone()[0]

        if "media_type" in cols:
            vinyl = c.execute(
                "SELECT COUNT(*) FROM releases WHERE media_type='VINYL'"
            ).fetchone()[0]
        else:
            vinyl = "N/A"

        print(os.path.basename(f), "RELEASES=", releases, "VINYL=", vinyl)
        c.close()
    except Exception as e:
        print(os.path.basename(f), "ERROR", e)

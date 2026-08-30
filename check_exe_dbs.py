import sqlite3, glob, os, datetime

candidates = glob.glob("dist/**/vinylvault.db", recursive=True) + glob.glob("release/**/vinylvault.db", recursive=True)

for db in candidates:
    mtime = os.path.getmtime(db)
    mtime_str = datetime.datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M:%S")
    try:
        con = sqlite3.connect(db)
        cur = con.cursor()
        cur.execute("SELECT COUNT(*) FROM releases WHERE checked=1")
        klaar = cur.fetchone()[0]
    except Exception as e:
        klaar = "ERR: " + str(e)
    print(mtime_str, "|", db, "| klaar:", klaar)

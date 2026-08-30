import sqlite3, glob, os, datetime

candidates = sorted(glob.glob("data/*.db") + glob.glob("data/backup/*.db") + glob.glob("data/backups/*.db"), key=os.path.getmtime)

for db in candidates:
    mtime = os.path.getmtime(db)
    mtime_str = datetime.datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M:%S")
    if not mtime_str.startswith("2026-08-30") and not mtime_str.startswith("2026-08-24"):
        continue
    try:
        con = sqlite3.connect(db)
        cur = con.cursor()
        cur.execute("SELECT COUNT(*) FROM releases WHERE checked=1")
        klaar = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM releases")
        total = cur.fetchone()[0]
    except Exception as e:
        klaar = "ERR"
        total = "ERR"
    print(mtime_str, "|", db, "| totaal:", total, "| klaar:", klaar)

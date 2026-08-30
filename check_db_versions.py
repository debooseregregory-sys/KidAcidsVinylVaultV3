import sqlite3, glob, os, datetime

candidates = sorted(glob.glob("data/*.db") + glob.glob("data/backup/*.db") + glob.glob("data/backups/*.db"))

def count(db_path, query):
    try:
        con = sqlite3.connect(db_path)
        cur = con.cursor()
        cur.execute(query)
        return cur.fetchone()[0]
    except Exception as e:
        return "ERR: " + str(e)

header = "{:<70} {:<20} {:<10} {:<8} {:<10}".format("BESTAND", "MTIME", "RELEASES", "KLAAR", "LIVESETS")
print(header)
print("-" * 120)
for db in candidates:
    mtime = os.path.getmtime(db)
    mtime_str = datetime.datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M")
    total = count(db, "SELECT COUNT(*) FROM releases")
    klaar = count(db, "SELECT COUNT(*) FROM releases WHERE checked=1 OR review_status='KLAAR' OR review_status='klaar'")
    try:
        con = sqlite3.connect(db)
        cur = con.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%liveset%'")
        liveset_tables = cur.fetchall()
        if liveset_tables:
            tname = liveset_tables[0][0]
            cur.execute("SELECT COUNT(*) FROM " + tname)
            livesets = cur.fetchone()[0]
        else:
            livesets = "no table"
    except Exception as e:
        livesets = "ERR: " + str(e)
    line = "{:<70} {:<20} {:<10} {:<8} {:<10}".format(db, mtime_str, str(total), str(klaar), str(livesets))
    print(line)

import sqlite3
con = sqlite3.connect("data/vinylvault.db")
cur = con.cursor()
cur.execute("SELECT review_status, COUNT(*) FROM releases GROUP BY review_status")
for r in cur.fetchall():
    print(r)
cur.execute("SELECT checked, COUNT(*) FROM releases GROUP BY checked")
for r in cur.fetchall():
    print(r)

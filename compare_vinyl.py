import sqlite3
from pathlib import Path

db1 = Path(r".\data\backups\vinylvault_backup_20260823_025708.db")
db2 = Path(r".\dist\KidAcidsMusicVault\_internal\data\vinylvault.db")

def get_vinyl(db):
    c = sqlite3.connect(db)
    rows = c.execute("""
        SELECT id, artist, title
        FROM releases
        WHERE UPPER(COALESCE(media_type,'')) = 'VINYL'
        ORDER BY id
    """).fetchall()
    c.close()
    return rows

a = get_vinyl(db1)
b = get_vinyl(db2)

sa = {x[0] for x in a}
sb = {x[0] for x in b}

print("BACKUP VINYL:", len(a))
print("HUIDIGE VINYL:", len(b))
print("ALLEEN BACKUP:", len(sa-sb))
print("ALLEEN HUIDIG:", len(sb-sa))

if sa-sb:
    print("\nOntbreekt in huidige database:")
    for r in a:
        if r[0] in sa-sb:
            print(r)

import sqlite3

huidig = r".\release\KidAcidsMusicVault\_internal\data\vinylvault.db"
v3 = r".\release\KidAcidsMusicVault\_internal\data\vinylvault_v3.db"

def get_rows(path):
    c = sqlite3.connect(path)
    rows = c.execute("SELECT id, artist, title FROM releases").fetchall()
    c.close()
    return rows

a = get_rows(huidig)
b = get_rows(v3)

ids_huidig = {r[0] for r in a}

verschil = [r for r in b if r[0] not in ids_huidig]

print("HUIDIG:", len(a))
print("V3:", len(b))
print("ALLEEN IN V3:", len(verschil))
print()
print("EERSTE 30:")
for r in verschil[:30]:
    print(r)

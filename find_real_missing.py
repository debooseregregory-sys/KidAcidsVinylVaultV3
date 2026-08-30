import sqlite3

huidig = r".\release\KidAcidsMusicVault\_internal\data\vinylvault.db"
v3 = r".\release\KidAcidsMusicVault\_internal\data\vinylvault_v3.db"

def get_keys(path):
    c = sqlite3.connect(path)
    rows = c.execute("SELECT artist, title FROM releases").fetchall()
    c.close()
    return set((str(a).strip().lower(), str(t).strip().lower()) for a, t in rows)

h = get_keys(huidig)
v = get_keys(v3)

missing = sorted(v - h)

print("HUIDIG:", len(h))
print("V3:", len(v))
print("ECHT ONTBREKEND OP ARTIST + TITLE:", len(missing))
print()

for artist, title in missing[:50]:
    print(artist, " - ", title)

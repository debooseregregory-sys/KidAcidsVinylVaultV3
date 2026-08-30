import sqlite3

huidig = r".\release\KidAcidsMusicVault\_internal\data\vinylvault.db"
v3 = r".\release\KidAcidsMusicVault\_internal\data\vinylvault_v3.db"

for naam, pad in [("HUIDIG", huidig), ("V3", v3)]:
    c = sqlite3.connect(pad)
    totaal = c.execute("SELECT COUNT(*) FROM releases").fetchone()[0]
    try:
        vinyl = c.execute("SELECT COUNT(*) FROM releases WHERE media_type='VINYL'").fetchone()[0]
    except:
        vinyl = "geen media_type"
    print(naam, "RELEASES:", totaal, "VINYL:", vinyl)
    c.close()

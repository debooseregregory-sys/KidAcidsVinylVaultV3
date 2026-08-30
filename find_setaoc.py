import sqlite3, json
con = sqlite3.connect("data/vinylvault.db")
cur = con.cursor()
cur.execute("SELECT id, artist, title, checked, review_status FROM releases WHERE title LIKE ? OR artist LIKE ?", ("%Setaoc%", "%Setaoc%"))
for r in cur.fetchall():
    print("RELEASE:", dict(zip(["id","artist","title","checked","review_status"], r)))

with open("data/livesets.json", encoding="utf-8") as f:
    livesets = json.load(f)
for ls in livesets:
    if "setaoc" in (ls.get("title","") + ls.get("artist","") + ls.get("audio","")).lower():
        print("LIVESET:", ls)

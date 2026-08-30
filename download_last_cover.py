import sqlite3
import requests
import os

DB = r".\data\vinylvault.db"
COVERS = r".\covers"

release_id = 2512
filename = f"release_{release_id}.jpg"
output = os.path.join(COVERS, filename)

conn = sqlite3.connect(DB)
row = conn.execute(
    "SELECT id, artist, title, cover FROM releases WHERE id=?",
    (release_id,)
).fetchone()

if not row:
    print("Release niet gevonden.")
    conn.close()
    raise SystemExit(1)

release_id, artist, title, url = row

print("Release :", artist, "-", title)
print("URL     :", url)
print("Doel    :", output)

if os.path.exists(output):
    print("Bestand bestaat al:", output)
else:
    print("Downloaden...")

    r = requests.get(
        url,
        timeout=30,
        headers={"User-Agent": "KidAcidVinylVault/1.0"}
    )
    r.raise_for_status()

    with open(output, "wb") as f:
        f.write(r.content)

    print("Gedownload:", len(r.content), "bytes")

if not os.path.isfile(output):
    print("FOUT: coverbestand bestaat niet.")
    conn.close()
    raise SystemExit(1)

conn.execute(
    "UPDATE releases SET cover=? WHERE id=?",
    (os.path.abspath(output), release_id)
)
conn.commit()

print("Database bijgewerkt.")
print("Nieuw pad:", os.path.abspath(output))

conn.close()
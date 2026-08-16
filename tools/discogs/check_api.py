import json
import sqlite3
import urllib.request
import urllib.error
import time
from pathlib import Path

BASE = Path(r"C:\Users\andyb\Desktop\KidAcidsVinylVaultV3")
DB = BASE / "data" / "vinylvault.db"

# PLAATS HIER JE NIEUWE CONSUMER KEY
CONSUMER_KEY = "HIER_JE_NIEUWE_CONSUMER_KEY"

print("=" * 80)
print("KID ACID'S VINYL VAULT V3")
print("DISCOGS API TEST")
print("=" * 80)
print()

db = sqlite3.connect(DB)

rows = db.execute("""
    SELECT id, artist, title, discogs
    FROM releases
    WHERE discogs IS NOT NULL
      AND TRIM(discogs) <> ''
    ORDER BY id
""").fetchall()

print("Discogs-ID's in database :", len(rows))
print()

# Zoek specifiek release 27829
test = next((r for r in rows if str(r[3]).strip() == "27829"), None)

if test is None:
    print("TEST RELEASE 27829 NIET GEVONDEN.")
    db.close()
    raise SystemExit(1)

db.close()

db_id, artist, title, discogs_id = test

print("TEST RELEASE")
print("-" * 80)
print("Database ID :", db_id)
print("Artist      :", artist)
print("Title       :", title)
print("Discogs ID  :", discogs_id)
print()

url = f"https://api.discogs.com/releases/{discogs_id}"

print("API URL:")
print(url)
print()

request = urllib.request.Request(
    url,
    headers={
        "User-Agent": "KidAcidsVinylVaultV3/1.0",
        "Accept": "application/json",
    }
)

try:
    with urllib.request.urlopen(request, timeout=30) as response:
        raw = response.read().decode("utf-8")
        data = json.loads(raw)

    print("=" * 80)
    print("API ANTWOORD ONTVANGEN")
    print("=" * 80)
    print()

    print("Discogs ID :", data.get("id"))
    print("Title      :", data.get("title"))
    print("Year       :", data.get("year"))

    artists = data.get("artists") or []
    if artists:
        print("Artist     :", artists[0].get("name"))

    labels = data.get("labels") or []
    if labels:
        print("Label      :", labels[0].get("name"))
        print("Catalog    :", labels[0].get("catno"))

    genres = data.get("genres") or []
    print("Genre      :", ", ".join(genres))

    images = data.get("images") or []
    if images:
        print("Cover      :", images[0].get("uri"))

    print()
    print("=" * 80)
    print("TEST GESLAAGD")
    print("=" * 80)
    print()
    print("DATABASE IS NIET GEWIJZIGD.")

except urllib.error.HTTPError as e:
    print("=" * 80)
    print("DISCOGS API FOUT")
    print("=" * 80)
    print()
    print("HTTP status :", e.code)
    print("Melding     :", e.reason)
    print()

    try:
        print(e.read().decode("utf-8", errors="replace"))
    except Exception:
        pass

except Exception as e:
    print("=" * 80)
    print("FOUT")
    print("=" * 80)
    print()
    print(type(e).__name__ + ":", e)
    print()
    print("DATABASE IS NIET GEWIJZIGD.")

finally:
    print()
    print("=" * 80)
    print("TEST KLAAR")
    print("=" * 80)

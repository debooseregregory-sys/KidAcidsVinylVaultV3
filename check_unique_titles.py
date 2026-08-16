import sqlite3
import json
import re
import collections

DB = "data/vinylvault.db"
JSON_FILE = "data/discogs/kid_acid_collection.json"


def norm(value):
    return re.sub(r"[^a-z0-9]", "", str(value or "").lower())


# --------------------------------------------------
# DATABASE
# --------------------------------------------------

conn = sqlite3.connect(DB)

rows = conn.execute("""
    SELECT id, artist, title, label, storage_code
    FROM releases
    WHERE (discogs IS NULL OR TRIM(discogs) = '')
      AND (catalog IS NULL OR TRIM(catalog) = '')
      AND TRIM(title) <> ''
    ORDER BY id
""").fetchall()

conn.close()


# --------------------------------------------------
# DISCOGS COLLECTION
# --------------------------------------------------

with open(JSON_FILE, encoding="utf-8") as f:
    discogs = json.load(f)


index = collections.defaultdict(list)

for item in discogs:
    basic = item.get("basic_information") or {}
    title = basic.get("title", "")

    index[norm(title)].append(item)


# --------------------------------------------------
# UNIQUE TITLE MATCHES
# --------------------------------------------------

unique = []

for row in rows:
    key = norm(row[2])
    matches = index.get(key, [])

    if len(matches) == 1:
        unique.append((row, matches[0]))


# --------------------------------------------------
# RESULT
# --------------------------------------------------

print()
print("=" * 120)
print("UNIEKE TITEL-CONTROLE")
print("=" * 120)
print()
print("RESTEREND:", len(rows))
print("UNIEK OP TITEL:", len(unique))
print()

for row, match in unique[:200]:

    basic = match.get("basic_information") or {}

    labels = basic.get("labels") or []

    if labels:
        discogs_label = labels[0].get("name", "")
        catno = labels[0].get("catno", "")
    else:
        discogs_label = ""
        catno = ""

    print(
        f"{row[0]} | "
        f"{row[1]} | "
        f"{row[2]} | "
        f"LABEL={row[3]} | "
        f"STORAGE={row[4]} | "
        f"-> DISCOGS={match.get('id')} | "
        f"CATNO={catno} | "
        f"DISCOGS LABEL={discogs_label}"
    )

print()
print("=" * 120)
print("GEEN DATABASE-WIJZIGING UITGEVOERD")
print("=" * 120)
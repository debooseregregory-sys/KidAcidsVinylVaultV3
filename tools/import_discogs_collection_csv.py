import csv
import sqlite3
import re
from pathlib import Path

# ============================================================
# KID ACID'S VINYLVAULT V3
# CSV -> RELEASES + TRACKS
# ============================================================

ROOT = Path(r"C:\Users\andyb\Desktop\KidAcidsVinylVaultV3")
DB = ROOT / "data" / "vinylvault.db"
CSV_FILE = Path(r"C:\Users\andyb\Desktop\vinyl_collectie.csv")

print("=" * 80)
print("KID ACID'S VINYLVAULT V3")
print("CSV COLLECTION IMPORT")
print("=" * 80)

print()
print("DATABASE:")
print(DB)

print()
print("CSV:")
print(CSV_FILE)

if not DB.exists():
    raise FileNotFoundError(f"Database niet gevonden: {DB}")

if not CSV_FILE.exists():
    raise FileNotFoundError(f"CSV niet gevonden: {CSV_FILE}")


# ============================================================
# HULPFUNCTIES
# ============================================================

def clean(value):
    if value is None:
        return ""

    value = str(value)

    # BOM verwijderen
    value = value.replace("\ufeff", "")

    # Niet-printbare tekens
    value = "".join(
        ch for ch in value
        if ch == "\t" or ch == "\n" or ch == "\r" or ord(ch) >= 32
    )

    return value.strip()


def normalize(value):
    value = clean(value)

    # Meerdere spaties samenvoegen
    value = re.sub(r"\s+", " ", value)

    return value.strip()


def norm_key(value):
    value = normalize(value).lower()

    # typografische verschillen normaliseren
    value = value.replace("–", "-")
    value = value.replace("—", "-")

    value = re.sub(r"\s+", " ", value)

    return value.strip()


def read_csv():
    encodings = [
        "cp1252",
        "utf-8-sig",
        "utf-8",
        "latin1",
    ]

    last_error = None

    for encoding in encodings:

        try:

            with open(
                CSV_FILE,
                "r",
                encoding=encoding,
                newline=""
            ) as f:

                rows = list(csv.reader(f))

            print()
            print("CSV encoding :", encoding)
            print("CSV rijen    :", len(rows))

            return rows

        except UnicodeDecodeError as e:

            last_error = e

    raise RuntimeError(
        f"CSV kon niet gelezen worden: {last_error}"
    )


# ============================================================
# CSV INLEZEN
# ============================================================

rows = read_csv()

if not rows:
    raise RuntimeError("CSV is leeg.")

header = [
    normalize(x)
    for x in rows[0]
]

print()
print("CSV KOLOMMEN:")
for i, col in enumerate(header):
    print(f"{i}: {repr(col)}")


# ============================================================
# KOLOMMEN VINDEN
# ============================================================

def find_column(name):
    wanted = norm_key(name)

    for i, col in enumerate(header):

        if norm_key(col) == wanted:
            return i

    return None


artist_col = find_column("Artist")
track_col = find_column("Tracks")
label_col = find_column("Label / Catalog")
storage_col = find_column("ID - CODE")

if artist_col is None:
    raise RuntimeError("Kolom Artist niet gevonden.")

if track_col is None:
    raise RuntimeError("Kolom Tracks niet gevonden.")

if label_col is None:
    raise RuntimeError("Kolom Label / Catalog niet gevonden.")

if storage_col is None:
    raise RuntimeError("Kolom ID - CODE niet gevonden.")


print()
print("GEVONDEN KOLOMMEN:")
print("Artist       :", artist_col)
print("Tracks       :", track_col)
print("Label/Catalog:", label_col)
print("Storage      :", storage_col)


# ============================================================
# DATA OPBOUWEN
# ============================================================

data_rows = []

for line_no, row in enumerate(rows[1:], start=2):

    # Lege rij
    if not row:
        continue

    # Zorg dat er voldoende kolommen zijn
    while len(row) <= max(
        artist_col,
        track_col,
        label_col,
        storage_col
    ):
        row.append("")

    artist = normalize(row[artist_col])
    track = normalize(row[track_col])
    label = normalize(row[label_col])
    storage = normalize(row[storage_col])

    # Volledig lege rij overslaan
    if not artist and not track and not label and not storage:
        continue

    data_rows.append({
        "line": line_no,
        "artist": artist,
        "track": track,
        "label": label,
        "storage": storage,
    })


print()
print("Bruikbare CSV regels:", len(data_rows))


# ============================================================
# RELEASE GROEPERING
#
# BELANGRIJK:
# Niet alleen storage gebruiken.
#
# release_key =
#     Label/Catalog + Storage
# ============================================================

groups = {}

for item in data_rows:

    label = item["label"]
    storage = item["storage"]

    key = (
        norm_key(label),
        norm_key(storage),
    )

    if key not in groups:

        groups[key] = {
            "label": label,
            "storage": storage,
            "rows": [],
        }

    groups[key]["rows"].append(item)


print()
print("=" * 80)
print("RELEASE GROEPERING")
print("=" * 80)

print()
print("CSV regels       :", len(data_rows))
print("Unieke releases  :", len(groups))


# ============================================================
# DATABASE
# ============================================================

conn = sqlite3.connect(DB)
conn.row_factory = sqlite3.Row

# Foreign keys
conn.execute("PRAGMA foreign_keys = ON")


# ============================================================
# BESTAANDE RELEASES
#
# We herkennen bestaande releases via:
#
# label + catalog + storage
#
# Omdat de database label/catalog apart heeft.
# ============================================================

existing = {}

db_rows = conn.execute(
    """
    SELECT
        id,
        artist,
        title,
        label,
        catalog,
        storage_code
    FROM releases
    """
).fetchall()

for r in db_rows:

    label_catalog = normalize(
        f"{r['label'] or ''} {r['catalog'] or ''}"
    )

    key = (
        norm_key(label_catalog),
        norm_key(r["storage_code"] or ""),
    )

    existing[key] = r["id"]


print()
print("Bestaande releases :", len(existing))


# ============================================================
# LABEL / CATALOG SPLITSEN
#
# CSV heeft:
#
# Label / Catalog
#
# Voorbeeld:
# 541 (NEWS) 541416 501474
#
# We bewaren dit voorlopig als label.
#
# Waarom?
# Omdat we later via Discogs de correcte label/catalog
# afzonderlijk kunnen invullen.
# ============================================================

def split_label_catalog(value):

    value = normalize(value)

    return value, ""


# ============================================================
# RELEASE TITEL HERKENNEN
# ============================================================

def looks_like_release_header(artist, track):

    a = norm_key(artist)
    t = normalize(track)

    if not t:
        return False

    # typische header
    if a in (
        "various artists",
        "various",
        "va",
    ):
        return True

    # EP / LP / album-achtige headers
    upper = t.upper()

    if upper.endswith(" E.P."):
        return True

    if upper.endswith(" EP"):
        return True

    if upper.endswith(" LP"):
        return True

    if "ALBUM" in upper and "(" not in upper:
        return True

    return False


# ============================================================
# TRACK POSITIES
# ============================================================

def generate_positions(count):

    positions = []

    # Eerste twee:
    # A1, B1
    #
    # Daarna:
    # A2, B2
    #
    # Voor grotere releases:
    # A1 B1 C1 D1 ...

    sides = [
        "A", "B", "C", "D",
        "E", "F", "G", "H",
    ]

    for i in range(count):

        side = sides[i % len(sides)]
        number = (i // len(sides)) + 1

        positions.append(
            f"{side}{number}"
        )

    return positions


# ============================================================
# IMPORT
# ============================================================

new_releases = 0
existing_releases = 0
new_tracks = 0
existing_tracks = 0

errors = 0

preview = []


for index, group in enumerate(
    groups.values(),
    start=1
):

    label = group["label"]
    storage = group["storage"]
    items = group["rows"]

    try:

        # ----------------------------------------------------
        # HEADER / RELEASE INFO
        # ----------------------------------------------------

        release_artist = ""
        release_title = ""

        for item in items:

            artist = item["artist"]
            track = item["track"]

            if looks_like_release_header(
                artist,
                track
            ):

                release_artist = artist
                release_title = track

                break

        # Als er geen header is:
        # eerste artiest gebruiken.
        if not release_artist:

            release_artist = items[0]["artist"]

        # Als er nog geen titel is:
        # leeg laten.
        #
        # Discogs kan dit later invullen.
        # Dit is beter dan een track als release-titel
        # te misbruiken.

        # ----------------------------------------------------
        # LABEL / CATALOG
        # ----------------------------------------------------

        db_label, db_catalog = split_label_catalog(label)

        # ----------------------------------------------------
        # BESTAANDE RELEASE?
        # ----------------------------------------------------

        key = (
            norm_key(label),
            norm_key(storage),
        )

        release_id = existing.get(key)

        if release_id is not None:

            existing_releases += 1

        else:

            cur = conn.execute(
                """
                INSERT INTO releases
                (
                    artist,
                    title,
                    label,
                    catalog,
                    year,
                    genre,
                    discogs,
                    discogs_link,
                    cover,
                    notes,
                    storage_code
                )
                VALUES
                (
                    ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
                )
                """,
                (
                    release_artist,
                    release_title,
                    db_label,
                    db_catalog,
                    None,
                    "",
                    "",
                    "",
                    "",
                    "",
                    storage,
                )
            )

            release_id = cur.lastrowid

            existing[key] = release_id

            new_releases += 1

        # ----------------------------------------------------
        # TRACKS
        # ----------------------------------------------------

        # Bestaande tracks ophalen
        existing_track_keys = set()

        track_rows = conn.execute(
            """
            SELECT artist, title, position
            FROM tracks
            WHERE release_id = ?
            """,
            (release_id,)
        ).fetchall()

        for t in track_rows:

            existing_track_keys.add(
                (
                    norm_key(t["artist"]),
                    norm_key(t["title"]),
                    norm_key(t["position"]),
                )
            )

        # ----------------------------------------------------
        # EERSTE REGEL ALS HEADER?
        #
        # Een Various Artists header is GEEN track.
        # ----------------------------------------------------

        track_items = []

        for item in items:

            if looks_like_release_header(
                item["artist"],
                item["track"]
            ):

                # Header niet als track importeren
                continue

            if not item["track"]:
                continue

            track_items.append(item)

        positions = generate_positions(
            len(track_items)
        )

        for position, item in zip(
            positions,
            track_items
        ):

            artist = item["artist"]
            title = item["track"]

            track_key = (
                norm_key(artist),
                norm_key(title),
                norm_key(position),
            )

            if track_key in existing_track_keys:

                existing_tracks += 1
                continue

            conn.execute(
                """
                INSERT INTO tracks
                (
                    release_id,
                    position,
                    artist,
                    title,
                    duration,
                    bpm,
                    genre,
                    notes
                )
                VALUES
                (
                    ?, ?, ?, ?, ?, ?, ?, ?
                )
                """,
                (
                    release_id,
                    position,
                    artist,
                    title,
                    0,
                    None,
                    "",
                    "",
                )
            )

            existing_track_keys.add(track_key)

            new_tracks += 1

        # ----------------------------------------------------
        # PREVIEW
        # ----------------------------------------------------

        if len(preview) < 10:

            preview.append({
                "release_id": release_id,
                "artist": release_artist,
                "title": release_title,
                "label": label,
                "storage": storage,
                "tracks": len(track_items),
            })

        # Commit iedere 100 releases
        if index % 100 == 0:

            conn.commit()

            print(
                f"[{index}/{len(groups)}] "
                f"Releases nieuw: {new_releases} | "
                f"Tracks nieuw: {new_tracks}"
            )

    except Exception as e:

        errors += 1

        print()
        print("FOUT BIJ GROEP:", index)
        print("Label   :", label)
        print("Kast    :", storage)
        print("Fout    :", e)

        conn.rollback()


# ============================================================
# DEFINITIEVE COMMIT
# ============================================================

conn.commit()


# ============================================================
# RESULTAAT
# ============================================================

print()
print("=" * 80)
print("IMPORT KLAAR")
print("=" * 80)

print()
print("CSV regels          :", len(data_rows))
print("CSV releasegroepen  :", len(groups))

print()
print("Nieuwe releases     :", new_releases)
print("Bestaande releases  :", existing_releases)

print()
print("Nieuwe tracks       :", new_tracks)
print("Bestaande tracks    :", existing_tracks)

print()
print("Fouten              :", errors)


# ============================================================
# PREVIEW
# ============================================================

print()
print("=" * 80)
print("EERSTE 10 RELEASES")
print("=" * 80)

for i, r in enumerate(preview, start=1):

    print()
    print(
        f"{i}. "
        f"{r['artist']} | "
        f"{r['title']} | "
        f"{r['label']} | "
        f"{r['storage']} | "
        f"{r['tracks']} tracks"
    )


# ============================================================
# CONTROLE DATABASE
# ============================================================

release_count = conn.execute(
    "SELECT COUNT(*) FROM releases"
).fetchone()[0]

track_count = conn.execute(
    "SELECT COUNT(*) FROM tracks"
).fetchone()[0]

print()
print("=" * 80)
print("DATABASE NA IMPORT")
print("=" * 80)

print()
print("Totaal releases :", release_count)
print("Totaal tracks   :", track_count)


conn.close()

print()
print("=" * 80)
print("KLAAR")
print("=" * 80)

from pathlib import Path
import os
import sys
import csv
import sqlite3
import requests
import time
import re


# ============================================================
# KID ACID'S VINYLVAULT V3
# DISCOGS COLLECTION BATCH IMPORT
# ============================================================

ROOT = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import config


# ============================================================
# CONFIG
# ============================================================

DB = os.path.join(
    ROOT,
    "data",
    "vinylvault.db"
)

API_URL = "https://api.discogs.com"

HEADERS = {
    "User-Agent": config.DISCOGS_USER_AGENT,
    "Accept": "application/json",
}

BATCH_SIZE = 10

REQUEST_DELAY = 1.2


# ============================================================
# FIND CSV
# ============================================================

def find_csv():

    candidates = []

    for root, dirs, files in os.walk(ROOT):

        for filename in files:

            if filename.lower().endswith(".csv"):

                path = os.path.join(
                    root,
                    filename
                )

                candidates.append(path)

    if not candidates:

        raise FileNotFoundError(
            "Geen CSV-bestand gevonden."
        )

    # Prefer collection/export files.
    preferred = [
        p for p in candidates
        if any(
            word in os.path.basename(p).lower()
            for word in [
                "vinyl",
                "collectie",
                "collection",
                "export",
            ]
        )
    ]

    if preferred:
        candidates = preferred

    candidates.sort()

    print()
    print("CSV gevonden:")
    print(candidates[0])

    return candidates[0]


# ============================================================
# CSV READ
# ============================================================

def read_csv(path):

    encodings = [
        "utf-8-sig",
        "utf-8",
        "cp1252",
        "latin-1",
    ]

    last_error = None

    for encoding in encodings:

        try:

            with open(
                path,
                "r",
                encoding=encoding,
                newline=""
            ) as f:

                reader = csv.DictReader(f)

                rows = list(reader)

            print()
            print(
                "CSV encoding:",
                encoding
            )

            print(
                "CSV rijen:",
                len(rows)
            )

            return rows

        except UnicodeDecodeError as e:

            last_error = e

    raise last_error


# ============================================================
# NORMALIZE FIELD
# ============================================================

def clean(value):

    if value is None:
        return ""

    return str(value).strip()


# ============================================================
# DETECT CSV COLUMNS
# ============================================================

def find_column(fieldnames, names):

    normalized = {
        re.sub(
            r"[^a-z0-9]",
            "",
            f.lower()
        ): f
        for f in fieldnames
    }

    for name in names:

        key = re.sub(
            r"[^a-z0-9]",
            "",
            name.lower()
        )

        if key in normalized:
            return normalized[key]

    return None


# ============================================================
# BUILD UNIQUE RELEASES
# ============================================================

def build_releases(rows):

    if not rows:
        return []

    fields = list(rows[0].keys())

    artist_col = find_column(
        fields,
        [
            "artist",
            "artiest",
        ]
    )

    title_col = find_column(
        fields,
        [
            "title",
            "release",
            "release title",
            "album",
        ]
    )

    label_col = find_column(
        fields,
        [
            "label",
            "labelcode",
        ]
    )

    catalog_col = find_column(
        fields,
        [
            "catalog",
            "cat",
            "catalogue",
        ]
    )

    storage_col = find_column(
        fields,
        [
            "location",
            "storage",
            "storage code",
            "kastcode",
            "locatie",
        ]
    )

    print()
    print("CSV KOLOMMEN")
    print("-" * 60)
    print("Artist  :", artist_col)
    print("Title   :", title_col)
    print("Label   :", label_col)
    print("Catalog :", catalog_col)
    print("Storage :", storage_col)

    if not artist_col or not title_col:
        raise RuntimeError(
            "Artist/title kolommen konden niet worden gevonden."
        )

    unique = {}

    for row in rows:

        artist = clean(
            row.get(artist_col)
        )

        title = clean(
            row.get(title_col)
        )

        label = clean(
            row.get(label_col)
            if label_col
            else ""
        )

        catalog = clean(
            row.get(catalog_col)
            if catalog_col
            else ""
        )

        storage_code = clean(
            row.get(storage_col)
            if storage_col
            else ""
        )

        key = (
            artist.lower(),
            title.lower(),
            label.lower(),
            catalog.lower(),
            storage_code.lower(),
        )

        if key not in unique:

            unique[key] = {
                "artist": artist,
                "title": title,
                "label": label,
                "catalog": catalog,
                "storage_code": storage_code,
            }

    releases = list(unique.values())

    print()
    print(
        "Unieke releases:",
        len(releases)
    )

    return releases


# ============================================================
# DISCOGS GET
# ============================================================

def discogs_get(url):

    while True:

        response = requests.get(
            url,
            headers=HEADERS,
            timeout=30,
        )

        if response.status_code == 429:

            print()
            print(
                "RATE LIMIT - 15 seconden wachten..."
            )

            time.sleep(15)

            continue

        if response.status_code != 200:

            print(
                "HTTP",
                response.status_code
            )

            return None

        time.sleep(
            REQUEST_DELAY
        )

        return response.json()


# ============================================================
# DISCOGS SEARCH
# ============================================================

def search_discogs(item):

    params = {
        "type": "release",
        "per_page": 20,
        "page": 1,
        "artist": item["artist"],
        "release_title": item["title"],
    }

    # IMPORTANT:
    # storage_code is NEVER sent to Discogs.

    url = API_URL + "/database/search"

    response = requests.get(
        url,
        params=params,
        headers=HEADERS,
        timeout=30,
    )

    if response.status_code == 429:

        print(
            "RATE LIMIT - 15 seconden..."
        )

        time.sleep(15)

        return search_discogs(item)

    if response.status_code != 200:

        print(
            "HTTP STATUS:",
            response.status_code
        )

        return []

    time.sleep(
        REQUEST_DELAY
    )

    data = response.json()

    return data.get(
        "results",
        []
    )


# ============================================================
# RESULT SCORE
# ============================================================

def score_result(item, result):

    score = 0

    artist = clean(
        result.get("artist")
        or ""
    )

    title = clean(
        result.get("title")
        or ""
    )

    label = clean(
        result.get("label")
        or ""
    )

    item_artist = item["artist"].lower()
    item_title = item["title"].lower()
    item_label = item["label"].lower()

    if item_artist and item_artist in artist.lower():
        score += 40

    if item_title and item_title in title.lower():
        score += 40

    if item_label and item_label in label.lower():
        score += 20

    # Physical vinyl is strongly preferred.
    formats = result.get(
        "format",
        []
    )

    format_text = " ".join(
        formats
    ).lower()

    if "vinyl" in format_text:
        score += 20

    if "12\"" in format_text:
        score += 10

    if "file" in format_text:
        score -= 30

    if "cd" in format_text:
        score -= 20

    return score


# ============================================================
# SELECT VINYL RELEASE
# ============================================================

def select_release(item, results):

    if not results:
        return None

    scored = []

    for result in results:

        scored.append(
            (
                score_result(
                    item,
                    result
                ),
                result
            )
        )

    scored.sort(
        key=lambda x: x[0],
        reverse=True
    )

    print()
    print("Discogs kandidaten:")

    for score, result in scored[:5]:

        print(
            f"[{score:3}] "
            f"{result.get('title', '')} "
            f"| ID {result.get('id')} "
            f"| {result.get('catno', '')}"
        )

    best_score, best = scored[0]

    # Safety threshold.
    if best_score < 60:

        print()
        print(
            "GEEN BETROUWBARE MATCH."
        )

        return None

    formats = " ".join(
        best.get("format", [])
    ).lower()

    if "vinyl" not in formats:

        print()
        print(
            "Beste resultaat is geen vinyl."
        )

        return None

    return best


# ============================================================
# GET FULL RELEASE
# ============================================================

def get_release(release_id):

    print()
    print(
        "Release ophalen:",
        release_id
    )

    return discogs_get(
        f"{API_URL}/releases/{release_id}"
    )


# ============================================================
# ARTIST
# ============================================================

def release_artist(data):

    artists = data.get(
        "artists"
    ) or []

    names = []

    for artist in artists:

        name = clean(
            artist.get("name")
        )

        if name:
            names.append(name)

    return ", ".join(names)


# ============================================================
# TRACK ARTIST
# ============================================================

def track_artist(track, fallback):

    artists = track.get(
        "artists"
    ) or []

    names = []

    for artist in artists:

        name = clean(
            artist.get("name")
        )

        if name:
            names.append(name)

    if names:
        return ", ".join(names)

    return fallback


# ============================================================
# NORMALIZE POSITION
# ============================================================

def normalize_position(raw, counters):

    raw = clean(raw).upper()

    if not raw:
        return ""

    # Already A1 / A2 / B1 / B2
    if re.match(
        r"^[A-D][0-9]+$",
        raw
    ):
        side = raw[0]
        number = int(raw[1:])

        counters[side] = max(
            counters[side],
            number
        )

        return raw

    # A / B / C / D
    if raw in "ABCD":

        counters[raw] += 1

        return (
            f"{raw}"
            f"{counters[raw]}"
        )

    return raw


# ============================================================
# IMPORT DATABASE
# ============================================================

def import_release(conn, item, data):

    discogs_id = data.get("id")

    existing = conn.execute(
        """
        SELECT id
        FROM releases
        WHERE discogs = ?
        LIMIT 1
        """,
        (str(discogs_id),)
    ).fetchone()

    if existing:

        release_id = existing[0]

        print(
            "Bestaande release:",
            release_id
        )

        conn.execute(
            """
            UPDATE releases
            SET storage_code = ?
            WHERE id = ?
            """,
            (
                item["storage_code"],
                release_id,
            )
        )

    else:

        artist = release_artist(
            data
        )

        title = clean(
            data.get("title")
        )

        labels = data.get(
            "labels"
        ) or []

        label = ""

        if labels:
            label = clean(
                labels[0].get("name")
            )

        catno = ""

        if labels:
            catno = clean(
                labels[0].get("catno")
            )

        year = data.get(
            "year"
        )

        conn.execute(
            """
            INSERT INTO releases (
                artist,
                title,
                label,
                catalog,
                year,
                discogs,
                discogs_link,
                storage_code
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                artist,
                title,
                label,
                catno,
                year,
                str(discogs_id),
                f"https://www.discogs.com/release/{discogs_id}",
                item["storage_code"],
            )
        )

        release_id = conn.execute(
            "SELECT last_insert_rowid()"
        ).fetchone()[0]

        print(
            "Nieuwe release:",
            release_id
        )

    # Do not duplicate tracks.
    existing_tracks = conn.execute(
        """
        SELECT COUNT(*)
        FROM tracks
        WHERE release_id = ?
        """,
        (release_id,)
    ).fetchone()[0]

    if existing_tracks:

        print(
            "Tracks bestaan al:",
            existing_tracks
        )

        conn.commit()

        return release_id, 0

    artist_fallback = release_artist(
        data
    )

    counters = {
        "A": 0,
        "B": 0,
        "C": 0,
        "D": 0,
    }

    imported = 0

    for track in data.get(
        "tracklist",
        []
    ):

        title = clean(
            track.get("title")
        )

        if not title:
            continue

        position = normalize_position(
            track.get("position"),
            counters
        )

        artist = track_artist(
            track,
            artist_fallback
        )

        duration = clean(
            track.get("duration")
        )

        conn.execute(
            """
            INSERT INTO tracks (
                release_id,
                position,
                artist,
                title,
                duration
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                release_id,
                position,
                artist,
                title,
                duration,
            )
        )

        imported += 1

    conn.commit()

    return release_id, imported


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 80)
    print("KID ACID'S VINYLVAULT V3")
    print("DISCOGS COLLECTION IMPORT")
    print("=" * 80)

    print()
    print("DATABASE:")
    print(DB)

    csv_path = Path(r"C:\Users\andyb\Desktop\vinyl_collectie.csv")

    rows = read_csv(
        csv_path
    )

    releases = build_releases(
        rows
    )

    print()
    print("=" * 80)
    print(
        f"EERSTE {BATCH_SIZE} RELEASES"
    )
    print("=" * 80)

    conn = sqlite3.connect(
        DB
    )

    stats = {
        "processed": 0,
        "imported": 0,
        "existing": 0,
        "no_search": 0,
        "no_match": 0,
        "errors": 0,
    }

    try:

        for index, item in enumerate(
            releases[:BATCH_SIZE],
            start=1
        ):

            print()
            print("=" * 80)
            print(
                f"[{index}/{BATCH_SIZE}]"
            )
            print("=" * 80)

            print(
                "Artist    :",
                item["artist"]
            )

            print(
                "Title     :",
                item["title"]
            )

            print(
                "Label     :",
                item["label"]
            )

            print(
                "Catalog   :",
                item["catalog"]
            )

            print(
                "Kastcode  :",
                item["storage_code"]
            )

            try:

                results = search_discogs(
                    item
                )

                if not results:

                    print(
                        "Geen Discogs resultaten."
                    )

                    stats["no_search"] += 1
                    continue

                best = select_release(
                    item,
                    results
                )

                if not best:

                    stats["no_match"] += 1
                    continue

                discogs_id = best.get(
                    "id"
                )

                print()
                print(
                    "GEKOZEN:"
                )

                print(
                    "Discogs ID:",
                    discogs_id
                )

                print(
                    "Release:",
                    best.get("title")
                )

                data = get_release(
                    discogs_id
                )

                if not data:

                    stats["errors"] += 1
                    continue

                release_id, count = import_release(
                    conn,
                    item,
                    data
                )

                stats["processed"] += 1

                if count:
                    stats["imported"] += 1

                print()
                print(
                    "Tracks ge�mporteerd:",
                    count
                )

            except Exception as e:

                print()
                print(
                    "FOUT:",
                    repr(e)
                )

                stats["errors"] += 1

    finally:

        conn.close()

    print()
    print("=" * 80)
    print("BATCH KLAAR")
    print("=" * 80)

    print(
        "Verwerkt       :",
        stats["processed"]
    )

    print(
        "Nieuwe releases:",
        stats["imported"]
    )

    print(
        "Geen resultaten:",
        stats["no_search"]
    )

    print(
        "Geen match     :",
        stats["no_match"]
    )

    print(
        "Fouten         :",
        stats["errors"]
    )

    print()
    print(
        "Volgende batch kan later hervat worden."
    )


if __name__ == "__main__":
    main()

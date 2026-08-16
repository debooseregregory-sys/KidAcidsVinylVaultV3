from pathlib import Path
import csv
import json
import sqlite3
import re

ROOT = Path(__file__).resolve().parent

DISCOGS_FILE = ROOT / "discogs" / "public_data" / "collection.json"
CSV_FILE = Path(r"C:\Users\andyb\Desktop\vinyl_collectie.csv")
DB_FILE = ROOT / "data" / "vinylvault_v3.db"


def clean(value):
    if value is None:
        return ""
    return str(value).strip()


def normalize(value):
    value = clean(value).lower()
    value = value.replace("–", "-").replace("—", "-")
    value = re.sub(r"\s+", " ", value)
    return value.strip()


def catalog_key(value):
    value = normalize(value)
    return re.sub(r"[\s\-_]+", "", value)


def split_label_catalog(value):
    value = clean(value)

    if not value:
        return "", ""

    # Meest voorkomende scheiding
    if " | " in value:
        parts = value.split(" | ", 1)
        return parts[0].strip(), parts[1].strip()

    # Anders proberen met lange streep
    if " – " in value:
        parts = value.split(" – ", 1)
        return parts[0].strip(), parts[1].strip()

    if " - " in value:
        parts = value.split(" - ", 1)
        return parts[0].strip(), parts[1].strip()

    return value, ""


def read_discogs():

    with open(
        DISCOGS_FILE,
        "r",
        encoding="utf-8"
    ) as f:
        data = json.load(f)

    releases = data.get("releases", [])

    print()
    print("=" * 80)
    print("DISCOGS COLLECTIE")
    print("=" * 80)
    print("Items:", len(releases))

    return releases


def read_csv():

    encodings = [
        "cp1252",
        "latin-1",
        "utf-8-sig",
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

                reader = csv.DictReader(f)
                rows = list(reader)

                print()
                print("=" * 80)
                print("KASTCODE CSV")
                print("=" * 80)
                print("CSV rijen:", len(rows))
                print("Kolommen:", reader.fieldnames)

                return rows

        except UnicodeDecodeError as exc:
            last_error = exc

    raise last_error


def build_csv_index(rows):

    index = {}

    for row in rows:

        artist = clean(
            row.get("Artist", "")
        )

        label_catalog = clean(
            row.get("Label / Catalog", "")
        )

        kastcode = clean(
            row.get("ID - CODE", "")
        )

        label, catalog = split_label_catalog(
            label_catalog
        )

        if not kastcode:
            continue

        key = (
            normalize(artist),
            normalize(label),
            catalog_key(catalog),
        )

        if key not in index:
            index[key] = {
                "artist": artist,
                "label": label,
                "catalog": catalog,
                "kastcode": kastcode,
            }

    return index


def extract_release(item):

    basic = item.get(
        "basic_information",
        {}
    )

    artists = basic.get(
        "artists",
        []
    )

    labels = basic.get(
        "labels",
        []
    )

    formats = basic.get(
        "formats",
        []
    )

    genres = basic.get(
        "genres",
        []
    )

    styles = basic.get(
        "styles",
        []
    )

    artist_names = []

    for artist in artists:

        name = clean(
            artist.get("name", "")
        )

        if name:
            artist_names.append(name)

    artist = ", ".join(
        artist_names
    )

    label_names = []
    catalogs = []

    for label in labels:

        name = clean(
            label.get("name", "")
        )

        catno = clean(
            label.get("catno", "")
        )

        if name:
            label_names.append(name)

        if catno:
            catalogs.append(catno)

    label = ", ".join(label_names)
    catalog = ", ".join(catalogs)

    format_names = []

    for fmt in formats:

        name = clean(
            fmt.get("name", "")
        )

        qty = clean(
            fmt.get("qty", "")
        )

        if name:
            if qty:
                format_names.append(
                    f"{name} x{qty}"
                )
            else:
                format_names.append(name)

    return {
        "discogs_id": basic.get(
            "id",
            item.get("id")
        ),

        "instance_id": item.get(
            "instance_id"
        ),

        "artist": artist,

        "title": clean(
            basic.get("title", "")
        ),

        "label": label,

        "catalog": catalog,

        "year": basic.get(
            "year",
            ""
        ),

        "format": ", ".join(
            format_names
        ),

        "genre": ", ".join(
            genres
        ),

        "styles": ", ".join(
            styles
        ),

        "thumb": clean(
            basic.get("thumb", "")
        ),

        "cover": clean(
            basic.get("cover_image", "")
        ),

        "resource_url": clean(
            basic.get("resource_url", "")
        ),

        "master_id": basic.get(
            "master_id",
            ""
        ),
    }


def create_database():

    DB_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    if DB_FILE.exists():
        DB_FILE.unlink()

    conn = sqlite3.connect(
        DB_FILE
    )

    conn.execute(
        "PRAGMA foreign_keys = ON"
    )

    conn.executescript(
        """
        CREATE TABLE releases (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            discogs_id INTEGER,
            instance_id INTEGER,

            artist TEXT,
            title TEXT,

            label TEXT,
            catalog TEXT,

            kastcode TEXT,

            year TEXT,
            format TEXT,
            genre TEXT,
            styles TEXT,

            thumb TEXT,
            cover TEXT,
            resource_url TEXT,

            master_id INTEGER,

            has_kastcode INTEGER DEFAULT 0
        );


        CREATE INDEX idx_release_artist
        ON releases(artist);

        CREATE INDEX idx_release_title
        ON releases(title);

        CREATE INDEX idx_release_label
        ON releases(label);

        CREATE INDEX idx_release_catalog
        ON releases(catalog);

        CREATE INDEX idx_release_kastcode
        ON releases(kastcode);
        """
    )

    conn.commit()

    return conn


def build_database():

    discogs = read_discogs()
    csv_rows = read_csv()

    csv_index = build_csv_index(
        csv_rows
    )

    print()
    print("=" * 80)
    print("DATABASE OPBOUWEN")
    print("=" * 80)

    print(
        "Discogs releases:",
        len(discogs)
    )

    print(
        "CSV unieke kastcodes:",
        len(csv_index)
    )

    conn = create_database()

    cur = conn.cursor()

    matched = 0

    for item in discogs:

        release = extract_release(
            item
        )

        artist = release["artist"]
        label = release["label"]
        catalog = release["catalog"]

        key = (
            normalize(artist),
            normalize(label),
            catalog_key(catalog),
        )

        csv_match = csv_index.get(key)

        kastcode = ""

        if csv_match:
            kastcode = csv_match["kastcode"]
            matched += 1

        cur.execute(
            """
            INSERT INTO releases (
                discogs_id,
                instance_id,
                artist,
                title,
                label,
                catalog,
                kastcode,
                year,
                format,
                genre,
                styles,
                thumb,
                cover,
                resource_url,
                master_id,
                has_kastcode
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                release["discogs_id"],
                release["instance_id"],
                release["artist"],
                release["title"],
                release["label"],
                release["catalog"],
                kastcode,
                release["year"],
                release["format"],
                release["genre"],
                release["styles"],
                release["thumb"],
                release["cover"],
                release["resource_url"],
                release["master_id"],
                1 if kastcode else 0,
            )
        )

    conn.commit()

    total = cur.execute(
        "SELECT COUNT(*) FROM releases"
    ).fetchone()[0]

    with_kastcode = cur.execute(
        """
        SELECT COUNT(*)
        FROM releases
        WHERE has_kastcode = 1
        """
    ).fetchone()[0]

    without_kastcode = total - with_kastcode

    print()
    print("=" * 80)
    print("VINYLVAULT V3 DATABASE KLAAR")
    print("=" * 80)

    print(
        "Discogs releases :",
        total
    )

    print(
        "Met kastcode     :",
        with_kastcode
    )

    print(
        "Zonder kastcode  :",
        without_kastcode
    )

    print(
        "Database          :",
        DB_FILE
    )

    print()
    print("=" * 80)
    print("EERSTE 10 RELEASES")
    print("=" * 80)

    rows = cur.execute(
        """
        SELECT
            artist,
            title,
            label,
            catalog,
            kastcode,
            year
        FROM releases
        ORDER BY id
        LIMIT 10
        """
    ).fetchall()

    for number, row in enumerate(
        rows,
        1
    ):

        print()
        print(
            f"{number}. {row[0]} - {row[1]}"
        )

        print(
            "   Label  :",
            row[2]
        )

        print(
            "   Catalog:",
            row[3]
        )

        print(
            "   Kast   :",
            row[4] or "-"
        )

        print(
            "   Jaar   :",
            row[5] or "-"
        )

    conn.close()

    print()
    print("=" * 80)
    print("KLAAR.")
    print("=" * 80)


if __name__ == "__main__":
    build_database()

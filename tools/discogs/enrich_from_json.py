import json
import sqlite3
import shutil
from pathlib import Path
from datetime import datetime

# ============================================================
# KID ACID'S VINYL VAULT V3
# DISCOGS ENRICHMENT UIT LOKALE JSON
# ============================================================

BASE = Path(r"C:\Users\andyb\Desktop\KidAcidsVinylVaultV3")

JSON_FILE = BASE / "data" / "discogs" / "kid_acid_collection.json"
DB_FILE = BASE / "data" / "vinylvault.db"

BACKUP_DIR = BASE / "data" / "backup"

# ============================================================
# HULPFUNCTIES
# ============================================================

def clean(value):
    if value is None:
        return ""

    if isinstance(value, str):
        return value.strip()

    return str(value).strip()


def discogs_id(value):
    try:
        if value is None:
            return None

        text = str(value).strip()

        if not text:
            return None

        # Soms staat er een volledige URL
        if "/release/" in text:
            text = text.split("/release/", 1)[1]
            text = text.split("/", 1)[0]

        return int(text)

    except Exception:
        return None


def first_artist(item):
    artists = item.get("basic_information", {}).get("artists", [])

    if not artists:
        return ""

    names = []

    for artist in artists:
        if isinstance(artist, dict):
            name = clean(artist.get("name"))
        else:
            name = clean(artist)

        if name:
            names.append(name)

    return ", ".join(names)


def first_label(item):
    labels = item.get("basic_information", {}).get("labels", [])

    if not labels:
        return "", ""

    label = labels[0]

    if isinstance(label, dict):
        return (
            clean(label.get("name")),
            clean(label.get("catno"))
        )

    return clean(label), ""


def get_cover(item):
    basic = item.get("basic_information", {})

    cover = clean(basic.get("cover_image"))

    if cover:
        return cover

    return clean(basic.get("thumb"))


def get_genre(item):
    basic = item.get("basic_information", {})

    genres = basic.get("genres", [])

    if genres:
        return clean(genres[0])

    return ""


def get_year(item):
    basic = item.get("basic_information", {})

    year = basic.get("year")

    try:
        return int(year) if year else None
    except Exception:
        return None


def get_title(item):
    return clean(
        item.get("basic_information", {}).get("title")
    )


def load_json():
    print()
    print("=" * 78)
    print("JSON LADEN")
    print("=" * 78)

    print()
    print("Bestand:")
    print(JSON_FILE)

    if not JSON_FILE.exists():
        raise RuntimeError(
            "JSON-bestand niet gevonden:\n"
            + str(JSON_FILE)
        )

    with JSON_FILE.open(
        "r",
        encoding="utf-8"
    ) as f:
        data = json.load(f)

    if not isinstance(data, list):
        raise RuntimeError(
            "JSON heeft niet het verwachte formaat: LIST"
        )

    print("JSON records:", len(data))

    return data


def build_index(data):
    print()
    print("Discogs index bouwen...")

    index = {}

    for item in data:

        if not isinstance(item, dict):
            continue

        rid = discogs_id(item.get("id"))

        if rid is None:
            rid = discogs_id(
                item.get("basic_information", {}).get("id")
            )

        if rid is not None:
            index[rid] = item

    print("Unieke Discogs IDs:", len(index))

    return index


# ============================================================
# DATABASE
# ============================================================

def get_columns(conn):

    rows = conn.execute(
        "PRAGMA table_info(releases)"
    ).fetchall()

    return {
        row[1]
        for row in rows
    }


def backup_database():

    BACKUP_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    stamp = datetime.now().strftime(
        "%Y%m%d_%H%M%S"
    )

    backup = (
        BACKUP_DIR
        / f"vinylvault_before_discogs_enrich_{stamp}.db"
    )

    shutil.copy2(
        DB_FILE,
        backup
    )

    return backup


# ============================================================
# MAIN
# ============================================================

def main():

    print()
    print("=" * 78)
    print("KID ACID'S VINYL VAULT V3")
    print("DISCOGS ENRICHMENT UIT LOKALE JSON")
    print("=" * 78)

    # --------------------------------------------------------
    # JSON
    # --------------------------------------------------------

    data = load_json()

    index = build_index(data)

    # --------------------------------------------------------
    # DATABASE
    # --------------------------------------------------------

    print()
    print("Database laden...")
    print()
    print("Database:")
    print(DB_FILE)

    if not DB_FILE.exists():
        raise RuntimeError(
            "Database niet gevonden:\n"
            + str(DB_FILE)
        )

    conn = sqlite3.connect(DB_FILE)

    columns = get_columns(conn)

    if "releases" not in [
        row[0]
        for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
    ]:
        conn.close()

        raise RuntimeError(
            "Tabel 'releases' ontbreekt in de database."
        )

    required = {
        "id",
        "artist",
        "title",
        "label",
        "catalog",
        "year",
        "genre",
        "discogs",
        "discogs_link",
        "cover",
        "storage_code",
    }

    missing = required - columns

    if missing:
        conn.close()

        raise RuntimeError(
            "Ontbrekende kolommen in releases: "
            + ", ".join(sorted(missing))
        )

    # --------------------------------------------------------
    # DATABASE INFO
    # --------------------------------------------------------

    total = conn.execute(
        "SELECT COUNT(*) FROM releases"
    ).fetchone()[0]

    with_id = conn.execute(
        """
        SELECT COUNT(*)
        FROM releases
        WHERE discogs IS NOT NULL
        AND TRIM(discogs) <> ''
        """
    ).fetchone()[0]

    with_link = conn.execute(
        """
        SELECT COUNT(*)
        FROM releases
        WHERE discogs_link IS NOT NULL
        AND TRIM(discogs_link) <> ''
        """
    ).fetchone()[0]

    with_cover = conn.execute(
        """
        SELECT COUNT(*)
        FROM releases
        WHERE cover IS NOT NULL
        AND TRIM(cover) <> ''
        """
    ).fetchone()[0]

    with_storage = conn.execute(
        """
        SELECT COUNT(*)
        FROM releases
        WHERE storage_code IS NOT NULL
        AND TRIM(storage_code) <> ''
        """
    ).fetchone()[0]

    print()
    print("=" * 78)
    print("DATABASE")
    print("=" * 78)

    print("Releases        :", total)
    print("Met Discogs ID  :", with_id)
    print("Met Discogs link:", with_link)
    print("Met cover       :", with_cover)
    print("Met kastcode    :", with_storage)

    # --------------------------------------------------------
    # BACKUP
    # --------------------------------------------------------

    print()
    print("Database backup maken...")

    backup = backup_database()

    print("Backup:")
    print(backup)

    # --------------------------------------------------------
    # ALLEEN BESTAANDE DISCOGS IDS
    # --------------------------------------------------------

    rows = conn.execute(
        """
        SELECT
            id,
            artist,
            title,
            label,
            catalog,
            year,
            genre,
            discogs,
            discogs_link,
            cover,
            storage_code
        FROM releases
        WHERE discogs IS NOT NULL
        AND TRIM(discogs) <> ''
        ORDER BY id
        """
    ).fetchall()

    print()
    print("=" * 78)
    print("VERWERKING")
    print("=" * 78)

    print()
    print("Alleen bestaande Discogs-ID's worden verwerkt.")
    print("Kastcodes worden NIET aangepast.")
    print()

    matched = 0
    not_found = 0
    changed = 0

    links_added = 0
    covers_added = 0
    artists_added = 0
    titles_added = 0
    labels_added = 0
    catalogs_added = 0
    years_added = 0
    genres_added = 0

    total_to_process = len(rows)

    for checked, row in enumerate(
        rows,
        start=1
    ):

        (
            local_id,
            artist,
            title,
            label,
            catalog,
            year,
            genre,
            discogs,
            discogs_link,
            cover,
            storage_code,
        ) = row

        rid = discogs_id(discogs)

        if rid is None:
            continue

        item = index.get(rid)

        if item is None:
            not_found += 1
            continue

        matched += 1

        basic = item.get(
            "basic_information",
            {}
        )

        json_artist = first_artist(item)
        json_title = get_title(item)
        json_label, json_catalog = first_label(item)
        json_year = get_year(item)
        json_genre = get_genre(item)
        json_cover = get_cover(item)

        json_link = clean(
            basic.get("resource_url")
        )

        # ----------------------------------------------------
        # BELANGRIJK:
        # ALLEEN LEGE DATABASEVELDEN WORDEN AANGEVULD
        # ----------------------------------------------------

        updates = {}
        counters = []

        if not clean(artist) and json_artist:
            updates["artist"] = json_artist
            counters.append("artist")

        if not clean(title) and json_title:
            updates["title"] = json_title
            counters.append("title")

        if not clean(label) and json_label:
            updates["label"] = json_label
            counters.append("label")

        if not clean(catalog) and json_catalog:
            updates["catalog"] = json_catalog
            counters.append("catalog")

        if not year and json_year:
            updates["year"] = json_year
            counters.append("year")

        if not clean(genre) and json_genre:
            updates["genre"] = json_genre
            counters.append("genre")

        if not clean(discogs_link) and json_link:
            updates["discogs_link"] = (
                f"https://www.discogs.com/release/{rid}"
            )
            counters.append("discogs_link")

        if not clean(cover) and json_cover:
            updates["cover"] = json_cover
            counters.append("cover")

        # ----------------------------------------------------
        # DATABASE UPDATE
        # ----------------------------------------------------

        if updates:

            fields = list(updates.keys())

            sql = (
                "UPDATE releases SET "
                + ", ".join(
                    f"{field} = ?"
                    for field in fields
                )
                + ", updated_at = CURRENT_TIMESTAMP "
                + "WHERE id = ?"
            )

            values = [
                updates[field]
                for field in fields
            ]

            values.append(local_id)

            conn.execute(
                sql,
                values
            )

            changed += 1

            for field in counters:

                if field == "discogs_link":
                    links_added += 1

                elif field == "cover":
                    covers_added += 1

                elif field == "artist":
                    artists_added += 1

                elif field == "title":
                    titles_added += 1

                elif field == "label":
                    labels_added += 1

                elif field == "catalog":
                    catalogs_added += 1

                elif field == "year":
                    years_added += 1

                elif field == "genre":
                    genres_added += 1

        # ----------------------------------------------------
        # VOORTGANG
        # ----------------------------------------------------

        if checked % 100 == 0:

            conn.commit()

            print(
                f"{checked}/{total_to_process} | "
                f"matched={matched} | "
                f"changed={changed} | "
                f"links={links_added} | "
                f"covers={covers_added}",
                flush=True
            )

    conn.commit()

    # --------------------------------------------------------
    # EINDCONTROLE
    # --------------------------------------------------------

    final_total = conn.execute(
        "SELECT COUNT(*) FROM releases"
    ).fetchone()[0]

    final_ids = conn.execute(
        """
        SELECT COUNT(*)
        FROM releases
        WHERE discogs IS NOT NULL
        AND TRIM(discogs) <> ''
        """
    ).fetchone()[0]

    final_links = conn.execute(
        """
        SELECT COUNT(*)
        FROM releases
        WHERE discogs_link IS NOT NULL
        AND TRIM(discogs_link) <> ''
        """
    ).fetchone()[0]

    final_covers = conn.execute(
        """
        SELECT COUNT(*)
        FROM releases
        WHERE cover IS NOT NULL
        AND TRIM(cover) <> ''
        """
    ).fetchone()[0]

    final_storage = conn.execute(
        """
        SELECT COUNT(*)
        FROM releases
        WHERE storage_code IS NOT NULL
        AND TRIM(storage_code) <> ''
        """
    ).fetchone()[0]

    conn.close()

    # --------------------------------------------------------
    # RESULTAAT
    # --------------------------------------------------------

    print()
    print("=" * 78)
    print("KLAAR")
    print("=" * 78)

    print()
    print("JSON records              :", len(data))
    print("Unieke Discogs IDs        :", len(index))
    print("Lokale releases           :", final_total)
    print("Releases met Discogs ID   :", final_ids)
    print("JSON matches              :", matched)
    print("ID niet gevonden          :", not_found)
    print()
    print("Releases gewijzigd        :", changed)
    print()
    print("Discogs links toegevoegd  :", links_added)
    print("Covers toegevoegd         :", covers_added)
    print("Artiesten toegevoegd      :", artists_added)
    print("Titels toegevoegd         :", titles_added)
    print("Labels toegevoegd         :", labels_added)
    print("Catalogi toegevoegd       :", catalogs_added)
    print("Jaren toegevoegd          :", years_added)
    print("Genres toegevoegd         :", genres_added)

    print()
    print("Releases        :", final_total)
    print("Met Discogs ID  :", final_ids)
    print("Met Discogs link:", final_links)
    print("Met cover       :", final_covers)
    print("Met kastcode    :", final_storage)

    print()
    print("KASTCODES       : NIET AANGERAAKT")
    print("TRACKS          : NIET AANGERAAKT")
    print("MP3_FILES       : NIET AANGERAAKT")
    print("TRACK_MP3       : NIET AANGERAAKT")
    print("FAVORITES       : NIET AANGERAAKT")

    print()
    print("BACKUP:")
    print(backup)

    print()
    print("DATABASE IS BIJGEWERKT.")


if __name__ == "__main__":
    try:
        main()

    except Exception as exc:

        print()
        print("=" * 78)
        print("FOUT")
        print("=" * 78)
        print()
        print(type(exc).__name__ + ":", exc)
        raise

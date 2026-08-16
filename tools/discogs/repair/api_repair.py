import sqlite3
import urllib.request
import urllib.error
import json
import shutil
import time
from pathlib import Path
from datetime import datetime

BASE = Path(r"C:\Users\andyb\Desktop\KidAcidsVinylVaultV3")
DB = BASE / "data" / "vinylvault.db"

API_DELAY = 1.2

def clean(value):
    if value is None:
        return ""
    return str(value).strip()

def api_get_release(discogs_id):
    url = f"https://api.discogs.com/releases/{discogs_id}"

    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "KidAcidsVinylVaultV3/1.0",
            "Accept": "application/json",
        },
    )

    with urllib.request.urlopen(req, timeout=30) as response:
        raw = response.read().decode("utf-8")

    return json.loads(raw)

def backup_database():
    backup_dir = BASE / "data" / "backup"
    backup_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup = backup_dir / f"vinylvault_before_discogs_api_repair_{timestamp}.db"

    shutil.copy2(DB, backup)

    return backup

def main():

    print("=" * 80)
    print("KID ACID'S VINYL VAULT V3")
    print("DISCOGS API REPAIR")
    print("=" * 80)
    print()

    if not DB.exists():
        raise RuntimeError(f"Database bestaat niet:\n{DB}")

    print("Database:")
    print(DB)
    print()

    db = sqlite3.connect(DB)
    db.row_factory = sqlite3.Row

    # ------------------------------------------------------------
    # CONTROLE DATABASE
    # ------------------------------------------------------------

    columns = {
        row["name"]
        for row in db.execute("PRAGMA table_info(releases)")
    }

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
        db.close()
        raise RuntimeError(
            "Ontbrekende databasekolommen: "
            + ", ".join(sorted(missing))
        )

    # ------------------------------------------------------------
    # VIND ONTBREKENDE DISCOGS IDS
    # ------------------------------------------------------------

    rows = db.execute("""
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
    """).fetchall()

    total_discogs = len(rows)

    print("=" * 80)
    print("DATABASE")
    print("=" * 80)
    print()
    print(f"Releases met Discogs ID : {total_discogs}")
    print()

    # ------------------------------------------------------------
    # TEST OF RELEASES AL VIA JSON/LOCAL DATA BESTAAN
    # ------------------------------------------------------------

    json_candidates = [
        BASE / "data" / "discogs" / "kid_acid_collection.json",
        BASE / "data" / "discogs" / "_public_collection.json",
        BASE / "discogs" / "public_data" / "collection.json",
    ]

    json_file = None

    for candidate in json_candidates:
        if candidate.exists():
            json_file = candidate
            break

    json_ids = set()

    if json_file:
        print("JSON gevonden:")
        print(json_file)
        print()

        try:
            with open(json_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            if isinstance(data, list):
                for item in data:
                    if not isinstance(item, dict):
                        continue

                    rid = item.get("id")

                    if rid is None:
                        basic = item.get("basic_information") or {}
                        rid = basic.get("id")

                    if rid is not None:
                        try:
                            json_ids.add(int(rid))
                        except Exception:
                            pass

            print(f"JSON Discogs IDs : {len(json_ids)}")
            print()

        except Exception as e:
            print("JSON kon niet worden gelezen.")
            print("Fout:", e)
            print()

    # ------------------------------------------------------------
    # BEPAAL ONTBREKENDE IDS
    # ------------------------------------------------------------

    missing_rows = []

    for row in rows:

        try:
            discogs_id = int(str(row["discogs"]).strip())
        except Exception:
            continue

        if discogs_id not in json_ids:
            missing_rows.append(row)

    print("=" * 80)
    print("TE HERSTELLEN")
    print("=" * 80)
    print()

    print("Database Discogs IDs :", total_discogs)
    print("IDs in JSON          :", len(json_ids))
    print("Niet in JSON         :", len(missing_rows))
    print()

    if not missing_rows:
        print("ER ZIJN GEEN ONTBREKENDE IDS.")
        print()
        print("DATABASE IS NIET GEWIJZIGD.")
        db.close()
        return

    print("Deze releases worden rechtstreeks via Discogs API opgehaald.")
    print()

    # ------------------------------------------------------------
    # LIJST
    # ------------------------------------------------------------

    for number, row in enumerate(missing_rows, 1):
        print(
            f"{number:03d} | "
            f"DB ID={row['id']} | "
            f"Discogs={row['discogs']} | "
            f"{row['artist']} | "
            f"{row['title']}"
        )

    print()

    # ------------------------------------------------------------
    # BACKUP
    # ------------------------------------------------------------

    print("=" * 80)
    print("DATABASE BACKUP")
    print("=" * 80)
    print()

    db.close()

    backup = backup_database()

    print("Backup:")
    print(backup)
    print()

    db = sqlite3.connect(DB)
    db.row_factory = sqlite3.Row

    # ------------------------------------------------------------
    # VERWERKING
    # ------------------------------------------------------------

    print("=" * 80)
    print("DISCOGS API VERWERKING")
    print("=" * 80)
    print()

    changed = 0
    failed = 0
    processed = 0

    artist_changes = 0
    title_changes = 0
    label_changes = 0
    catalog_changes = 0
    year_changes = 0
    genre_changes = 0
    link_changes = 0
    cover_changes = 0

    failures = []

    for number, row in enumerate(missing_rows, 1):

        discogs_id = int(str(row["discogs"]).strip())

        try:

            data = api_get_release(discogs_id)

            basic = data.get("basic_information") or {}

            # Discogs release endpoint heeft deze gegevens meestal
            # rechtstreeks op rootniveau.

            title = clean(data.get("title"))

            year = data.get("year")

            if not year:
                year = basic.get("year")

            artists = data.get("artists") or []

            artist = ""

            if artists:
                names = []

                for a in artists:
                    if isinstance(a, dict):
                        name = clean(a.get("name"))
                        if name:
                            names.append(name)

                artist = ", ".join(names)

            labels = data.get("labels") or []

            label = ""
            catalog = ""

            if labels:
                first_label = labels[0]

                if isinstance(first_label, dict):
                    label = clean(first_label.get("name"))
                    catalog = clean(first_label.get("catno"))

            genres = data.get("genres") or []

            genre = ""

            if genres:
                genre = ", ".join(
                    clean(g)
                    for g in genres
                    if clean(g)
                )

            discogs_link = (
                f"https://www.discogs.com/release/{discogs_id}"
            )

            cover = ""

            images = data.get("images") or []

            if images:
                for image in images:

                    if not isinstance(image, dict):
                        continue

                    uri = clean(image.get("uri"))

                    if uri:
                        cover = uri
                        break

            # ----------------------------------------------------
            # ALLEEN VELDEN DIE VERBETERD KUNNEN WORDEN
            # ----------------------------------------------------

            updates = {}

            old_artist = clean(row["artist"])
            old_title = clean(row["title"])
            old_label = clean(row["label"])
            old_catalog = clean(row["catalog"])
            old_year = row["year"]
            old_genre = clean(row["genre"])
            old_link = clean(row["discogs_link"])
            old_cover = clean(row["cover"])

            if artist and artist != old_artist:
                updates["artist"] = artist
                artist_changes += 1

            if title and title != old_title:
                updates["title"] = title
                title_changes += 1

            if label and label != old_label:
                updates["label"] = label
                label_changes += 1

            if catalog and catalog != old_catalog:
                updates["catalog"] = catalog
                catalog_changes += 1

            if year:
                try:
                    year_int = int(year)

                    if old_year != year_int:
                        updates["year"] = year_int
                        year_changes += 1

                except Exception:
                    pass

            if genre and genre != old_genre:
                updates["genre"] = genre
                genre_changes += 1

            if discogs_link and discogs_link != old_link:
                updates["discogs_link"] = discogs_link
                link_changes += 1

            if cover and cover != old_cover:
                updates["cover"] = cover
                cover_changes += 1

            # ----------------------------------------------------
            # UPDATE
            # ----------------------------------------------------

            if updates:

                set_clause = ", ".join(
                    f"{column} = ?"
                    for column in updates
                )

                values = list(updates.values())
                values.append(row["id"])

                db.execute(
                    f"""
                    UPDATE releases
                    SET {set_clause},
                        updated_at = datetime('now')
                    WHERE id = ?
                    """,
                    values
                )

                changed += 1

            processed += 1

            if number % 10 == 0 or number == len(missing_rows):

                print(
                    f"{number}/{len(missing_rows)} | "
                    f"processed={processed} | "
                    f"changed={changed} | "
                    f"failed={failed}"
                )

            time.sleep(API_DELAY)

        except urllib.error.HTTPError as e:

            failed += 1

            message = f"HTTP {e.code}: {e.reason}"

            failures.append(
                (
                    row["id"],
                    discogs_id,
                    row["artist"],
                    row["title"],
                    message,
                )
            )

            print(
                f"FOUT {number}/{len(missing_rows)} | "
                f"Discogs={discogs_id} | "
                f"{message}"
            )

            if e.code == 429:
                print()
                print("RATE LIMIT.")
                print("Wacht 60 seconden...")
                print()

                time.sleep(60)

        except Exception as e:

            failed += 1

            message = f"{type(e).__name__}: {e}"

            failures.append(
                (
                    row["id"],
                    discogs_id,
                    row["artist"],
                    row["title"],
                    message,
                )
            )

            print(
                f"FOUT {number}/{len(missing_rows)} | "
                f"Discogs={discogs_id} | "
                f"{message}"
            )

    # ------------------------------------------------------------
    # COMMIT
    # ------------------------------------------------------------

    db.commit()

    # ------------------------------------------------------------
    # EINDCONTROLE
    # ------------------------------------------------------------

    print()
    print("=" * 80)
    print("KLAAR")
    print("=" * 80)
    print()

    print(f"Te verwerken IDs       : {len(missing_rows)}")
    print(f"Verwerkt               : {processed}")
    print(f"Database releases      : {changed}")
    print(f"Mislukt                : {failed}")
    print()

    print("VELDWIJZIGINGEN")
    print("-" * 80)
    print(f"Artiesten              : {artist_changes}")
    print(f"Titels                 : {title_changes}")
    print(f"Labels                 : {label_changes}")
    print(f"Catalogi               : {catalog_changes}")
    print(f"Jaren                  : {year_changes}")
    print(f"Genres                 : {genre_changes}")
    print(f"Discogs links          : {link_changes}")
    print(f"Covers                 : {cover_changes}")
    print()

    print("=" * 80)
    print("BEVEILIGDE TABELLEN / VELDEN")
    print("=" * 80)
    print()
    print("storage_code           : NIET AANGERAAKT")
    print("tracks                 : NIET AANGERAAKT")
    print("mp3_files              : NIET AANGERAAKT")
    print("track_mp3              : NIET AANGERAAKT")
    print("favorites              : NIET AANGERAAKT")
    print()

    if failures:

        print("=" * 80)
        print("MISLUKTE RELEASES")
        print("=" * 80)
        print()

        for item in failures:

            db_id, discogs_id, artist, title, error = item

            print(
                f"DB ID={db_id} | "
                f"Discogs={discogs_id} | "
                f"{artist} | "
                f"{title}"
            )

            print(f"  {error}")

        print()

    print("=" * 80)
    print("BACKUP")
    print("=" * 80)
    print()
    print(backup)
    print()

    print("DATABASE IS BIJGEWERKT.")

    db.close()


if __name__ == "__main__":
    main()

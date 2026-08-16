from pathlib import Path
import sqlite3
import json
import re
import unicodedata
from difflib import SequenceMatcher

BASE = Path(__file__).resolve().parents[2]
DB = BASE / "data" / "vinylvault.db"
JSON_FILE = BASE / "data" / "discogs_public_collection.json"

MIN_SAFE = 90.0


def norm(s):
    if not s:
        return ""

    s = unicodedata.normalize("NFKD", str(s))
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = s.lower()

    s = s.replace("&", " and ")
    s = s.replace("+", " and ")
    s = s.replace("/", " ")
    s = s.replace("\\", " ")
    s = s.replace("-", " ")
    s = s.replace("_", " ")
    s = s.replace(".", " ")
    s = s.replace(",", " ")
    s = s.replace(":", " ")
    s = s.replace(";", " ")
    s = s.replace("(", " ")
    s = s.replace(")", " ")

    s = re.sub(r"\bvarious artists\b", "various", s)

    s = re.sub(r"\bfeaturing\b", "feat", s)
    s = re.sub(r"\bft\b", "feat", s)

    s = re.sub(r"\bversus\b", "vs", s)

    s = re.sub(r"\be\s+p\b", "ep", s)

    s = re.sub(r"\s+", " ", s).strip()

    return s


def sim(a, b):
    a = norm(a)
    b = norm(b)

    if not a or not b:
        return 0.0

    if a == b:
        return 100.0

    return SequenceMatcher(None, a, b).ratio() * 100


def tokens(s):
    return set(norm(s).split())


def token_score(a, b):
    ta = tokens(a)
    tb = tokens(b)

    if not ta or not tb:
        return 0.0

    common = len(ta & tb)
    total = len(ta | tb)

    return (common / total) * 100


def title_score(local, remote):
    exact = sim(local, remote)
    tok = token_score(local, remote)

    return max(exact, tok)


def discogs_artists(record):
    basic = record.get("basic_information", {})
    artists = basic.get("artists", [])

    result = []

    for artist in artists:
        if isinstance(artist, dict):
            name = artist.get("name")
            if name:
                result.append(name)

    return result


def artist_score(local, record):
    local_n = norm(local)

    # Various Artists is NOT an artist match.
    if local_n in ("various", "va"):
        remote = discogs_artists(record)

        if not remote:
            return 100.0

        return 100.0 if any(
            norm(x) == "various"
            for x in remote
        ) else 80.0

    remote_artists = discogs_artists(record)

    if not remote_artists:
        return 0.0

    best = 0.0

    for remote in remote_artists:
        best = max(
            best,
            sim(local, remote)
        )

    remote_joined = " ".join(remote_artists)

    best = max(
        best,
        sim(local, remote_joined),
        token_score(local, remote_joined)
    )

    return best


def get_format(record):
    basic = record.get("basic_information", {})
    formats = basic.get("formats", [])

    names = []

    for fmt in formats:
        if isinstance(fmt, dict):
            name = fmt.get("name")
            if name:
                names.append(norm(name))

    if any("vinyl" in x for x in names):
        return "Vinyl"

    if any("cd" == x or "cd" in x for x in names):
        return "CD"

    return "Andere"


def local_format(row):
    # De huidige database heeft geen format-kolom.
    # Voor releases zonder formatinformatie behandelen
    # we het als onbekend.
    return None


def get_catalogs(record):
    basic = record.get("basic_information", {})
    labels = basic.get("labels", [])

    result = []

    for label in labels:
        if isinstance(label, dict):
            cat = label.get("catno")
            if cat:
                result.append(str(cat).strip())

    return result


def catalog_norm(s):
    if not s:
        return ""

    return re.sub(
        r"[^a-z0-9]",
        "",
        norm(s)
    )


def catalog_match(local_catalog, record):
    if not local_catalog:
        return False

    local = catalog_norm(local_catalog)

    if not local:
        return False

    for remote in get_catalogs(record):
        remote_n = catalog_norm(remote)

        if local == remote_n:
            return True

    return False


def release_score(local, record):
    release_id, artist, title, catalog, discogs, link, storage, label = local

    remote_title = record.get(
        "basic_information", {}
    ).get("title", "")

    ts = title_score(
        title,
        remote_title
    )

    ass = artist_score(
        artist,
        record
    )

    cm = catalog_match(
        catalog,
        record
    )

    # Titel is het belangrijkste.
    score = (
        ts * 0.60
        + ass * 0.40
    )

    if cm:
        score += 15

    return min(score, 100), ts, ass, cm


def load_json():
    print("=" * 80)
    print("OPENBARE DISCOGS COLLECTIE")
    print("=" * 80)

    with open(
        JSON_FILE,
        "r",
        encoding="utf-8"
    ) as f:
        data = json.load(f)

    print(
        f"JSON records: {len(data)}"
    )

    return data


def main():
    print()
    print("DATABASE:")
    print(DB)

    print()
    print("JSON:")
    print(JSON_FILE)

    records = load_json()

    conn = sqlite3.connect(DB)

    try:
        cur = conn.cursor()

        cur.execute(
            """
            SELECT
                id,
                artist,
                title,
                catalog,
                discogs,
                discogs_link,
                storage_code,
                label
            FROM releases
            """
        )

        locals_ = cur.fetchall()

        print()
        print(
            f"Lokale releases: {len(locals_)}"
        )

        results = []

        print()
        print("=" * 80)
        print("OPENBARE COLLECTIE → LOKALE COLLECTIE")
        print("=" * 80)

        for n, record in enumerate(
            records,
            1
        ):
            basic = record.get(
                "basic_information",
                {}
            )

            remote_id = basic.get(
                "id"
            )

            if not remote_id:
                continue

            remote_title = basic.get(
                "title",
                ""
            )

            remote_artists = discogs_artists(
                record
            )

            remote_artist = ", ".join(
                remote_artists
            )

            remote_format = get_format(
                record
            )

            best = None

            for local in locals_:
                score, ts, ass, cm = release_score(
                    local,
                    record
                )

                if best is None or score > best[0]:
                    best = (
                        score,
                        ts,
                        ass,
                        cm,
                        local
                    )

            if best is None:
                continue

            score, ts, ass, cm, local = best

            if score < MIN_SAFE:
                continue

            results.append(
                (
                    score,
                    record,
                    local,
                    ts,
                    ass,
                    cm
                )
            )

        results.sort(
            key=lambda x: x[0],
            reverse=True
        )

        print()
        print(
            f"VEILIGE MATCHES: {len(results)}"
        )

        print()
        print("=" * 80)
        print("EERSTE 100 VEILIGE MATCHES")
        print("=" * 80)

        for i, item in enumerate(
            results[:100],
            1
        ):
            score, record, local, ts, ass, cm = item

            basic = record[
                "basic_information"
            ]

            remote_id = basic.get(
                "id",
                ""
            )

            remote_title = basic.get(
                "title",
                ""
            )

            remote_artists = ", ".join(
                discogs_artists(record)
            )

            remote_catalog = ", ".join(
                get_catalogs(record)
            )

            remote_format = get_format(
                record
            )

            (
                local_id,
                local_artist,
                local_title,
                local_catalog,
                local_discogs,
                local_link,
                storage_code,
                label
            ) = local

            print()
            print(
                f"[{i}] SCORE {score:.1f}%"
            )

            print(
                f"LOCAL : {local_artist} - {local_title}"
            )

            print(
                f"DISC : {remote_artists} - {remote_title}"
            )

            print(
                f"ID    : {remote_id}"
            )

            print(
                f"CAT   : {remote_catalog or 'none'}"
            )

            print(
                f"FORMAT: {remote_format}"
            )

            print(
                f"TITLE : {ts:.1f}%"
            )

            print(
                f"ARTIST: {ass:.1f}%"
            )

            print(
                f"CATALOG MATCH: "
                + ("JA" if cm else "NEE")
            )

            print(
                f"KASTCODE: {storage_code or ''}"
            )

        print()
        print("=" * 80)
        print("RESULTAAT")
        print("=" * 80)

        print(
            f"Veilige matches: {len(results)}"
        )

        print()
        print(
            "DRY RUN — DATABASE IS NIET GEWIJZIGD."
        )

        print()
        print(
            "De volgende stap is pas de import "
            "van deze veilige matches."
        )

    finally:
        conn.close()


if __name__ == "__main__":
    main()

from pathlib import Path
import sqlite3
import json
import re
import unicodedata
from difflib import SequenceMatcher

BASE = Path(__file__).resolve().parents[2]
DB = BASE / "data" / "vinylvault.db"
JSON_FILE = BASE / "data" / "discogs_public_collection.json"

SAFE_SCORE = 88.0


def norm(value):
    if not value:
        return ""

    s = unicodedata.normalize("NFKD", str(value))
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = s.lower()

    for a, b in {
        "&": " and ",
        "+": " and ",
        "/": " ",
        "\\": " ",
        "-": " ",
        "_": " ",
        ".": " ",
        ",": " ",
        ":": " ",
        ";": " ",
        "(": " ",
        ")": " ",
        "[": " ",
        "]": " ",
    }.items():
        s = s.replace(a, b)

    s = re.sub(r"\bvarious artists?\b", "various", s)
    s = re.sub(r"\bfeaturing\b", "feat", s)
    s = re.sub(r"\bfeat\.\b", "feat", s)
    s = re.sub(r"\bft\.\b", "feat", s)
    s = re.sub(r"\bft\b", "feat", s)
    s = re.sub(r"\bversus\b", "vs", s)
    s = re.sub(r"\be\s*p\b", "ep", s)

    s = re.sub(r"\s+", " ", s).strip()

    return s


def compact(value):
    return re.sub(r"[^a-z0-9]", "", norm(value))


def similarity(a, b):
    a = norm(a)
    b = norm(b)

    if not a or not b:
        return 0.0

    if a == b:
        return 100.0

    return SequenceMatcher(None, a, b).ratio() * 100.0


def token_similarity(a, b):
    a = set(norm(a).split())
    b = set(norm(b).split())

    if not a or not b:
        return 0.0

    return len(a & b) / len(a | b) * 100.0


def combined_similarity(a, b):
    return max(
        similarity(a, b),
        token_similarity(a, b)
    )


def json_artists(record):
    basic = record.get("basic_information", {})
    artists = basic.get("artists", [])

    result = []

    for artist in artists:
        if isinstance(artist, dict):
            name = artist.get("name")

            if name:
                result.append(str(name))

    return result


def json_artist_text(record):
    return " ".join(json_artists(record))


def json_catalogs(record):
    basic = record.get("basic_information", {})
    labels = basic.get("labels", [])

    result = []

    for label in labels:
        if isinstance(label, dict):
            cat = label.get("catno")

            if cat:
                result.append(str(cat).strip())

    return result


def json_format(record):
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

    if any(x == "cd" or "cd" in x for x in names):
        return "CD"

    return "Andere"


def catalog_match(local_catalog, record):
    if not local_catalog:
        return False

    local = compact(local_catalog)

    if not local:
        return False

    for remote in json_catalogs(record):
        if local == compact(remote):
            return True

    return False


def catalog_partial(local_catalog, record):
    if not local_catalog:
        return False

    local = compact(local_catalog)

    if len(local) < 4:
        return False

    for remote in json_catalogs(record):

        remote_n = compact(remote)

        if not remote_n:
            continue

        if local in remote_n or remote_n in local:
            return True

    return False


def title_score(local_title, record):

    remote_title = record.get(
        "basic_information",
        {}
    ).get("title", "")

    return combined_similarity(
        local_title,
        remote_title
    )


def artist_score(local_artist, record):

    local = norm(local_artist)

    if local in ("",):
        return 0.0

    if local in ("various", "various artists", "va"):

        remote = json_artists(record)

        if not remote:
            return 100.0

        if any(
            norm(x) in (
                "various",
                "various artists"
            )
            for x in remote
        ):
            return 100.0

        # Various Artists is a container name,
        # not an actual artist. Don't punish it
        # heavily when Discogs contains the real artists.
        return 70.0

    remote = json_artist_text(record)

    if not remote:
        return 0.0

    return combined_similarity(
        local,
        remote
    )


def build_indexes(records):

    title_index = {}
    artist_index = {}
    catalog_index = {}

    for record in records:

        basic = record.get(
            "basic_information",
            {}
        )

        title = basic.get(
            "title",
            ""
        )

        title_key = compact(title)

        if title_key:
            title_index.setdefault(
                title_key,
                []
            ).append(record)

        for artist in json_artists(record):

            artist_key = compact(artist)

            if artist_key:
                artist_index.setdefault(
                    artist_key,
                    []
                ).append(record)

        for catalog in json_catalogs(record):

            catalog_key = compact(catalog)

            if catalog_key:
                catalog_index.setdefault(
                    catalog_key,
                    []
                ).append(record)

    return (
        title_index,
        artist_index,
        catalog_index
    )


def candidate_records(
    local_artist,
    local_title,
    local_catalog,
    title_index,
    artist_index,
    catalog_index
):

    candidates = {}

    # 1. EXACT CATALOG
    if local_catalog:

        key = compact(local_catalog)

        for record in catalog_index.get(
            key,
            []
        ):
            candidates[id(record)] = record

    # 2. EXACT TITLE
    title_key = compact(local_title)

    for record in title_index.get(
        title_key,
        []
    ):
        candidates[id(record)] = record

    # 3. EXACT ARTIST
    artist_key = compact(local_artist)

    if artist_key not in (
        "",
        "various",
        "va",
        "variousartists"
    ):

        for record in artist_index.get(
            artist_key,
            []
        ):
            candidates[id(record)] = record

    # 4. TITLE TOKEN SEARCH
    title_tokens = set(
        norm(local_title).split()
    )

    if title_tokens:

        for key, records in title_index.items():

            key_tokens = set(
                norm(key).split()
            )

            overlap = len(
                title_tokens & key_tokens
            )

            if overlap >= 1:

                for record in records:
                    candidates[id(record)] = record

    return list(candidates.values())


def score_candidate(local, record):

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

    ts = title_score(
        local_title,
        record
    )

    ass = artist_score(
        local_artist,
        record
    )

    exact_cat = catalog_match(
        local_catalog,
        record
    )

    partial_cat = catalog_partial(
        local_catalog,
        record
    )

    if exact_cat:

        score = (
            ts * 0.40
            + ass * 0.25
            + 35.0
        )

    elif partial_cat:

        score = (
            ts * 0.50
            + ass * 0.30
            + 20.0
        )

    else:

        score = (
            ts * 0.60
            + ass * 0.40
        )

    score = min(
        score,
        100.0
    )

    return (
        score,
        ts,
        ass,
        exact_cat,
        partial_cat
    )


def main():

    print("=" * 80)
    print("V3 SNELLE OPENBARE COLLECTIE MATCHER")
    print("=" * 80)

    print()
    print("DATABASE:")
    print(DB)

    print()
    print("JSON:")
    print(JSON_FILE)

    if not DB.exists():
        raise RuntimeError(
            f"Database bestaat niet: {DB}"
        )

    if not JSON_FILE.exists():
        raise RuntimeError(
            f"JSON bestaat niet: {JSON_FILE}"
        )

    with open(
        JSON_FILE,
        "r",
        encoding="utf-8"
    ) as f:

        records = json.load(f)

    if not isinstance(records, list):
        raise RuntimeError(
            "JSON bevat geen lijst."
        )

    print()
    print(
        f"JSON records: {len(records)}"
    )

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

        print(
            f"Lokale releases: {len(locals_)}"
        )

        print()
        print("Indexen bouwen...")

        (
            title_index,
            artist_index,
            catalog_index
        ) = build_indexes(records)

        print(
            f"Unieke titels: {len(title_index)}"
        )

        print(
            f"Unieke artiesten: {len(artist_index)}"
        )

        print(
            f"Unieke catalogi: {len(catalog_index)}"
        )

        print()
        print(
            "Volledige lokale collectie controleren..."
        )

        strong = []
        doubtful = []
        none = []

        processed = 0

        for local in locals_:

            processed += 1

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

            candidates = candidate_records(
                local_artist,
                local_title,
                local_catalog,
                title_index,
                artist_index,
                catalog_index
            )

            best = None
            second = None

            for record in candidates:

                result = score_candidate(
                    local,
                    record
                )

                # BELANGRIJKE FIX:
                # result is een tuple.
                # We moeten result[0] vergelijken,
                # niet result zelf met best.
                candidate_score = result[0]

                if (
                    best is None
                    or candidate_score > best[0][0]
                ):

                    second = best

                    best = (
                        result,
                        record
                    )

                elif (
                    second is None
                    or candidate_score > second[0][0]
                ):

                    second = (
                        result,
                        record
                    )

            if best is None:

                none.append(local)

            else:

                result, record = best

                score = result[0]

                if second is not None:
                    gap = (
                        score -
                        second[0][0]
                    )
                else:
                    gap = score

                item = (
                    score,
                    gap,
                    local,
                    record,
                    result
                )

                if (
                    score >= SAFE_SCORE
                    and gap >= 5
                ):

                    strong.append(item)

                elif score >= 70:

                    doubtful.append(item)

                else:

                    none.append(local)

            if processed % 250 == 0:

                print(
                    f"  {processed}/{len(locals_)}"
                )

        strong.sort(
            key=lambda x: x[0],
            reverse=True
        )

        doubtful.sort(
            key=lambda x: x[0],
            reverse=True
        )

        print()
        print("=" * 80)
        print("RESULTAAT VOLLEDIGE COLLECTIE")
        print("=" * 80)

        print(
            f"Lokale releases gecontroleerd: "
            f"{processed}"
        )

        print(
            f"Sterke matches: {len(strong)}"
        )

        print(
            f"Twijfelgevallen: {len(doubtful)}"
        )

        print(
            f"Geen betrouwbare match: {len(none)}"
        )

        print()
        print("DATABASE IS NIET GEWIJZIGD.")

        print()
        print("=" * 80)
        print("STERKE MATCHES — EERSTE 100")
        print("=" * 80)

        for n, item in enumerate(
            strong[:100],
            1
        ):

            (
                score,
                gap,
                local,
                record,
                result
            ) = item

            ts = result[1]
            ass = result[2]
            exact_cat = result[3]
            partial_cat = result[4]

            basic = record.get(
                "basic_information",
                {}
            )

            remote_id = basic.get(
                "id",
                ""
            )

            remote_title = basic.get(
                "title",
                ""
            )

            remote_artist = ", ".join(
                json_artists(record)
            )

            remote_catalog = ", ".join(
                json_catalogs(record)
            )

            remote_format = json_format(
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
                f"[{n}] SCORE {score:.1f}% "
                f"GAP {gap:.1f}"
            )

            print(
                f"LOCAL : "
                f"{local_artist} - {local_title}"
            )

            print(
                f"DISC  : "
                f"{remote_artist} - {remote_title}"
            )

            print(
                f"ID    : {remote_id}"
            )

            print(
                f"CAT   : "
                f"{remote_catalog or 'none'}"
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

            if exact_cat:
                cat_status = "JA"
            elif partial_cat:
                cat_status = "DEELS"
            else:
                cat_status = "NEE"

            print(
                f"CATALOG MATCH: {cat_status}"
            )

            print(
                f"KASTCODE: "
                f"{storage_code or ''}"
            )

        print()
        print("=" * 80)
        print("KLAAR")
        print("=" * 80)

        print()
        print(
            "DRY RUN — GEEN DATABASEWIJZIGING."
        )

    finally:

        conn.close()


if __name__ == "__main__":
    main()

from pathlib import Path


# ============================================================
# VINYLVAULT V3 - FIX SEARCH COLLECTION RELEASE
# ============================================================

ROOT = Path(__file__).resolve().parent

matches = list(ROOT.rglob("*KASTCODE.py"))

if not matches:
    raise FileNotFoundError(
        "KASTCODE.py niet gevonden."
    )

if len(matches) > 1:
    print("MEERDERE KASTCODE-BESTANDEN GEVONDEN:")
    for item in matches:
        print(" -", item)

    raise RuntimeError(
        "Er zijn meerdere KASTCODE.py bestanden gevonden."
    )

target = matches[0]

print("KASTCODE:", target)


# ============================================================
# LEES BESTAND
# ============================================================

source = target.read_text(
    encoding="utf-8"
)


# ============================================================
# BACKUP
# ============================================================

backup = target.with_name(
    target.stem + "_BEFORE_SEARCH_FIX.py"
)

backup.write_text(
    source,
    encoding="utf-8"
)

print("BACKUP:", backup)


# ============================================================
# ZOEK FUNCTIE
# ============================================================

start_marker = "def search_collection_release(group):"

end_marker = (
    "# ============================================================\n"
    "# GET COMPLETE DISCOGS RELEASE"
)

start = source.find(
    start_marker
)

if start == -1:
    raise RuntimeError(
        "search_collection_release() niet gevonden."
    )

end = source.find(
    end_marker,
    start
)

if end == -1:
    raise RuntimeError(
        "Einde van search_collection_release() niet gevonden."
    )


# ============================================================
# NIEUWE FUNCTIE
# ============================================================

new_function = '''def search_collection_release(group):

    collection_artist = group["artist"]

    tracks = get_real_tracks(
        group
    )

    print()
    print("=" * 80)
    print("DISCOGS ZOEKOPDRACHT")
    print("=" * 80)

    print(
        "Artist :",
        collection_artist
    )

    print(
        "Label  :",
        group["label_catalog"]
    )

    print(
        "Code   :",
        group["code"]
    )

    print(
        "Tracks :",
        len(tracks)
    )

    print()
    print("ECHTE TRACKS:")

    for track in tracks:

        print(
            "-",
            track["artist"],
            "|",
            track["title"]
        )

    candidates = {}

    # ========================================================
    # HULPFUNCTIE KANDIDATEN
    # ========================================================

    def add_candidates(
        results,
        query_name
    ):

        for result in results:

            result_id = result.get(
                "id"
            )

            if not result_id:
                continue

            if result_id not in candidates:

                candidates[result_id] = {
                    "result": result,
                    "search_hits": 0,
                    "queries": [],
                }

            candidates[result_id][
                "search_hits"
            ] += 1

            candidates[result_id][
                "queries"
            ].append(
                query_name
            )

    # ========================================================
    # 1. CATALOGUSCODE - BELANGRIJKSTE ZOEKOPDRACHT
    # ========================================================

    catalog = normalize(
        group.get(
            "code",
            ""
        )
    )

    if catalog:

        print()
        print(
            "CATALOGUS ZOEKEN:",
            catalog
        )

        try:

            results = discogs_search(
                catalog=catalog
            )

            add_candidates(
                results,
                "CATALOG"
            )

        except Exception as exc:

            print(
                "Catalogus zoekfout:",
                exc
            )

    # ========================================================
    # 2. EERSTE TRACK + CATALOGUS
    # ========================================================

    if tracks:

        first_track = tracks[0]

        print()
        print(
            "TRACK + CATALOG:",
            first_track["artist"],
            "-",
            first_track["title"],
            "|",
            catalog
        )

        try:

            results = discogs_search(
                artist=first_track["artist"],
                title=first_track["title"],
                catalog=catalog,
            )

            add_candidates(
                results,
                "TRACK+CATALOG"
            )

        except Exception as exc:

            print(
                "Track/catalog zoekfout:",
                exc
            )

    # ========================================================
    # 3. LABEL/CATALOGUS + TRACKS
    # ========================================================

    for track in tracks[:3]:

        print()
        print(
            "TRACK ZOEKEN:",
            track["artist"],
            "-",
            track["title"]
        )

        try:

            results = discogs_search(
                artist=track["artist"],
                title=track["title"],
            )

            add_candidates(
                results,
                "TRACK"
            )

        except Exception as exc:

            print(
                "Track zoekfout:",
                exc
            )

    # ========================================================
    # KANDIDATEN
    # ========================================================

    ordered = []

    for item in candidates.values():

        result = item["result"]

        ordered.append(
            {
                "result":
                    result,

                "search_hits":
                    item["search_hits"],

                "queries":
                    item["queries"],
            }
        )

    ordered.sort(
        key=lambda item:
        item["search_hits"],
        reverse=True
    )

    print()
    print("=" * 80)
    print("DISCOGS KANDIDATEN")
    print("=" * 80)

    print(
        "Kandidaten:",
        len(ordered)
    )

    final_results = []

    for item in ordered[:20]:

        result = item["result"]

        print()
        print(
            "Search hits:",
            item["search_hits"]
        )

        print(
            "ID:",
            result.get("id")
        )

        print(
            "Titel:",
            result.get("title")
        )

        print(
            "Jaar:",
            result.get("year")
        )

        print(
            "Label:",
            result.get("label")
        )

        print(
            "Catalog:",
            result.get("catno")
        )

        print(
            "Queries:",
            ", ".join(
                item["queries"]
            )
        )

        result["_vv_search_hits"] = (
            item["search_hits"]
        )

        final_results.append(
            result
        )

    return final_results


'''


# ============================================================
# SCHRIJF AANGEPAST BESTAND
# ============================================================

updated = (
    source[:start]
    +
    new_function
    +
    source[end:]
)

target.write_text(
    updated,
    encoding="utf-8"
)

print()
print("=" * 80)
print("KASTCODE AANGEPAST")
print("=" * 80)
print(
    "Bestand:",
    target
)
print(
    "Backup:",
    backup
)
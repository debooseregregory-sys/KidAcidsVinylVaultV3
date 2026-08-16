import requests

HEADERS = {
    "User-Agent": "KidAcidVinylVaultV3/1.0",
    "Accept": "application/json",
}

RELEASE_IDS = [
    4497,
    6051,
]

WANTED = "booster"


print()
print("=" * 80)
print("PLANETARY ASSAULT SYSTEMS - TRACKLIST CONTROLE")
print("=" * 80)


for release_id in RELEASE_IDS:

    print()
    print("=" * 80)
    print("RELEASE ID:", release_id)
    print("=" * 80)

    url = f"https://api.discogs.com/releases/{release_id}"

    try:
        response = requests.get(
            url,
            headers=HEADERS,
            timeout=30,
        )
    except Exception as exc:
        print("NETWERKFOUT:")
        print(exc)
        continue

    print("HTTP:", response.status_code)

    if response.status_code != 200:
        print(response.text[:500])
        continue

    release = response.json()

    print()
    print("Artist :", ", ".join(
        artist.get("name", "")
        for artist in release.get("artists", [])
    ))

    print("Release:", release.get("title"))
    print("Year   :", release.get("year"))

    print()
    print("FORMAT:")

    for fmt in release.get("formats", []):

        name = fmt.get("name", "")
        descriptions = fmt.get("descriptions", [])

        print(
            " ",
            name,
            " ".join(descriptions)
        )

    print()
    print("TRACKLIST")
    print("-" * 80)

    booster_found = False

    for track in release.get("tracklist", []):

        position = track.get(
            "position",
            ""
        )

        title = track.get(
            "title",
            ""
        )

        duration = track.get(
            "duration",
            ""
        )

        print(
            f"{position:5} | "
            f"{title}"
            f"{' | ' + duration if duration else ''}"
        )

        if WANTED.lower() in title.lower():

            booster_found = True

    print()
    print(
        "BOOSTER:",
        "GEVONDEN" if booster_found else "NIET GEVONDEN"
    )


print()
print("=" * 80)
print("CONTROLE KLAAR")
print("=" * 80)

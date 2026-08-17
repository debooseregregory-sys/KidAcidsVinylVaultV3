from pathlib import Path

FILES = [
    Path("gui/main_window.py"),
    Path("gui/release_library_page.py"),
    Path("gui/release_detail_page.py"),
]

REPLACEMENTS = {
    # Global dark backgrounds -> clean light neutrals
    "#0b0b0f": "#f7f4fa",
    "#0f0f12": "#f7f4fa",
    "#0f0f14": "#ffffff",
    "#101010": "#ffffff",
    "#101014": "#f1eef4",
    "#10151a": "#eef8f0",
    "#111116": "#eee9f2",
    "#121218": "#ffffff",
    "#141419": "#ffffff",
    "#151515": "#ffffff",
    "#15151a": "#f1eef4",
    "#15151c": "#faf8fc",
    "#171717": "#ffffff",
    "#17171d": "#ffffff",
    "#17181d": "#ffffff",
    "#18131a": "#f8e9f1",
    "#18181d": "#ffffff",
    "#1b1820": "#f3edf6",
    "#1b1b22": "#ffffff",
    "#1c1726": "#ffffff",
    "#1d1920": "#fff4f9",
    "#1d1d23": "#ffffff",
    "#202020": "#eeeaf2",
    "#23352b": "#cfe6d4",
    "#24242d": "#ddd7e4",
    "#25252f": "#ddd7e4",
    "#252525": "#ffffff",
    "#271522": "#f8e3ef",
    "#292929": "#e0dbe5",
    "#29202a": "#f6e8f1",
    "#2b1a25": "#f7e8f0",
    "#2d2731": "#d7c8d2",
    "#30303a": "#c9c1ce",
    "#352d46": "#d9cfdf",
    "#363640": "#c0b7c8",
    "#383842": "#c9c1cf",
    "#3a3a44": "#c9c1cf",
    "#3f2635": "#e3bfd0",
    "#484851": "#a9a1ae",
    "#493040": "#d7b3c5",
    "#4b2a3d": "#dfb6cb",
    "#4d4d57": "#8f8895",
    "#55466d": "#b7a8c2",
    "#5d2947": "#d89ab9",
    "#626b65": "#6f776f",
    "#666672": "#77717d",
    "#686873": "#746d79",
    "#777783": "#716a78",
    "#858590": "#6f6875",
    "#888888": "#6f6875",
    "#999999": "#6f6875",
    "#aaaaaa": "#655d6b",
    "#a8a8b3": "#5f5967",
    "#a9a9b4": "#655e6c",
    "#b9c6bc": "#48604d",
    "#bbbbbb": "#625a68",
    "#d84b91": "#c23d82",
    "#e05299": "#c23d82",
    "#ededf2": "#302a35",
    "#eeeeee": "#302a35",
    "#f2f2f2": "#302a35",
    "#f3effa": "#302a35",
    "#ffffff": "#2f2934",
}

# Keep white text where it is explicitly intended for dark badges/buttons after
# the global pass by restoring key selectors that are meant to remain accent-colored.
RESTORE = {
    'color: #302a35;\n                font-size: 25px;': 'color: #2f2934;\n                font-size: 25px;',
}

for path in FILES:
    text = path.read_text(encoding="utf-8-sig")
    original = text

    for old, new in REPLACEMENTS.items():
        text = text.replace(old, new)

    # Specific bright-theme accents for controls/checks.
    text = text.replace(
        'background-color: #234d23;',
        'background-color: #dff3e3;'
    )
    text = text.replace(
        'color: #302a35;\n                border: 1px solid #3d7a3d;',
        'color: #35613e;\n                border: 1px solid #86bd92;'
    )
    text = text.replace(
        'background-color: #316831;',
        'background-color: #c9e8cf;'
    )
    text = text.replace(
        'background-color: #1b3b1b;',
        'background-color: #b9ddbF;'
    )

    # Checklist: light green / light red visual language.
    text = text.replace(
        'background-color: #18181d;\n                border: 1px solid #383842;',
        'background-color: #fff9fd;\n                border: 1px solid #d8cedc;'
    )

    if text == original:
        print(f"WAARSCHUWING: geen themakleuren gevonden in {path}")
    else:
        path.write_text(text, encoding="utf-8-sig")
        print(f"BRIGHT THEME TOEGEPAST: {path}")

print("KLAAR: VinylVault bright theme")

from pathlib import Path
import re

FILES = [
    Path("gui/main_window.py"),
    Path("gui/release_library_page.py"),
    Path("gui/release_detail_page.py"),
]

BG = {
    "#0b0b0f": "#f7f4fa", "#0f0f12": "#f7f4fa", "#0f0f14": "#ffffff",
    "#101010": "#ffffff", "#101014": "#f1eef4", "#10151a": "#eef8f0",
    "#111116": "#eee9f2", "#121218": "#ffffff", "#141419": "#ffffff",
    "#151515": "#ffffff", "#15151a": "#f1eef4", "#15151c": "#faf8fc",
    "#171717": "#ffffff", "#17171d": "#ffffff", "#17181d": "#ffffff",
    "#18131a": "#f8e9f1", "#18181d": "#ffffff", "#1b1820": "#f3edf6",
    "#1b1b22": "#ffffff", "#1c1726": "#ffffff", "#1d1920": "#fff4f9",
    "#1d1d23": "#ffffff", "#202020": "#eeeaf2", "#25252f": "#ddd7e4",
    "#252525": "#ffffff", "#271522": "#f8e3ef", "#292929": "#e0dbe5",
    "#29202a": "#f6e8f1", "#2b1a25": "#f7e8f0", "#30303a": "#c9c1ce",
    "#352d46": "#d9cfdf", "#363640": "#c0b7c8", "#383842": "#c9c1cf",
    "#3a3a44": "#c9c1cf",
}

BORDER = {
    "#24242d": "#ddd7e4", "#25252f": "#ddd7e4", "#23352b": "#cfe6d4",
    "#2d2731": "#d7c8d2", "#30303a": "#c9c1ce", "#383842": "#c9c1cf",
    "#3f2635": "#e3bfd0", "#4b2a3d": "#dfb6cb", "#55466d": "#b7a8c2",
    "#5d2947": "#d89ab9",
}

TEXT = {
    "#ffffff": "#2f2934", "#f2f2f2": "#2f2934", "#f3effa": "#2f2934",
    "#ededf2": "#302a35", "#eeeeee": "#302a35", "#aaaaaa": "#655d6b",
    "#a8a8b3": "#5f5967", "#a9a9b4": "#655e6c", "#999999": "#6f6875",
    "#888888": "#6f6875", "#858590": "#6f6875", "#777783": "#716a78",
    "#686873": "#746d79", "#666672": "#77717d", "#626b65": "#6f776f",
    "#bbbbbb": "#625a68",
}

for path in FILES:
    text = path.read_text(encoding="utf-8-sig")
    original = text

    for old, new in BG.items():
        text = text.replace(f"background-color: {old};", f"background-color: {new};")
        text = text.replace(f"background: {old};", f"background: {new};")

    for old, new in BORDER.items():
        text = text.replace(f"border: 1px solid {old};", f"border: 1px solid {new};")
        text = text.replace(f"border-right: 1px solid {old};", f"border-right: 1px solid {new};")
        text = text.replace(f"border-bottom: 1px solid {old};", f"border-bottom: 1px solid {new};")

    for old, new in TEXT.items():
        text = re.sub(
            rf"(\bcolor:\s*){re.escape(old)}(;)",
            rf"\g<1>{new}\g<2>",
            text,
        )

    # Preserve semantic states while making them softer/lighter.
    text = text.replace("background-color: #234d23;", "background-color: #dff3e3;")
    text = text.replace("background-color: #316831;", "background-color: #c9e8cf;")
    text = text.replace("background-color: #1b3b1b;", "background-color: #b9ddbf;")
    text = text.replace("border: 1px solid #3d7a3d;", "border: 1px solid #86bd92;")

    if text == original:
        print(f"GEEN WIJZIGING: {path}")
    else:
        path.write_text(text, encoding="utf-8-sig")
        print(f"BRIGHT THEME TOEGEPAST: {path}")

print("KLAAR: lichte VinylVault UI")
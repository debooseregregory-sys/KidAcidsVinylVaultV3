from pathlib import Path

FILES = [
    Path("gui/main_window.py"),
    Path("gui/release_library_page.py"),
    Path("gui/release_detail_page.py"),
]

REPLACEMENTS = {
    "#0f0f12": "#17151c",
    "#101010": "#f4f1f6",
    "#111111": "#f4f1f6",
    "#141419": "#ffffff",
    "#151515": "#faf8fb",
    "#171717": "#ffffff",
    "#18181d": "#f7f3f8",
    "#181818": "#f7f3f8",
    "#1c1726": "#fffafd",
    "#1d1d23": "#ffffff",
    "#202020": "#f0e8f0",
    "#222222": "#ffffff",
    "#252525": "#f5eef5",
    "#292929": "#ded5df",
    "#2b1a25": "#f9eaf4",
    "#303030": "#d6c8d8",
    "#352d46": "#ead5e5",
    "#383838": "#cdbbcf",
    "#383842": "#cdbbcf",
    "#3a3a44": "#c9b8cc",
    "#444444": "#cbbdcc",
    "#55466d": "#c49ab6",
    "#888888": "#756a78",
    "#9688aa": "#7f627b",
    "#999999": "#6f6470",
    "#aaaaaa": "#6d6370",
    "#bbbbbb": "#625866",
    "#d84b91": "#c43d83",
    "#eeeeee": "#2a222c",
    "#f2f2f2": "#2a222c",
    "#f3effa": "#2a222c",
    "#f05ca4": "#c43d83",
    "#ffffff": "#2a222c",
}

for path in FILES:
    text = path.read_text(encoding="utf-8-sig")
    for old, new in REPLACEMENTS.items():
        text = text.replace(old, new)
    path.write_text(text, encoding="utf-8-sig")
    print(f"THEME AANGEPAST: {path}")

print("HELDERE VINYLVAULT THEME TOEGEPAST")

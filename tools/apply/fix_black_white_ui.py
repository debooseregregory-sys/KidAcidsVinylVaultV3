from pathlib import Path

FILES = [
    Path("gui/main_window.py"),
    Path("gui/release_library_page.py"),
    Path("gui/release_detail_page.py"),
]

# Normalize both the old dark palette and the accidental light/pink palette
# into one black/charcoal + white + restrained pink accent palette.
COLOR_MAP = {
    # Light accidental backgrounds
    "#f7f4fa": "#09090b",
    "#ffffff": "#101014",
    "#faf8fc": "#14141a",
    "#fff9fd": "#16161c",
    "#fff4f9": "#17121a",
    "#f8e9f1": "#17131a",
    "#f8e3ef": "#17131a",
    "#f3edf6": "#15151b",
    "#f1eef4": "#101014",
    "#eee9f2": "#111116",
    "#eeeaf2": "#111116",
    "#eef8f0": "#101810",
    "#dff3e3": "#17331d",
    "#c9e8cf": "#21482a",
    "#b9ddbf": "#2b5d35",
    "#d7c8d2": "#37313b",
    "#d8cedc": "#302a34",
    "#d9cfdf": "#322c37",
    "#c9c1ce": "#3a3440",
    "#c9c1cf": "#3a3440",
    "#b7a8c2": "#4a414f",
    "#dfb6cb": "#553343",
    "#e3bfd0": "#5a3549",
    "#d89ab9": "#743554",
    # Existing dark backgrounds kept consistent
    "#0b0b0f": "#09090b",
    "#0f0f12": "#0b0b0e",
    "#0f0f14": "#0c0c10",
    "#101010": "#111116",
    "#101014": "#111116",
    "#10151a": "#111711",
    "#111116": "#0e0e12",
    "#121218": "#15151b",
    "#141419": "#16161d",
    "#151515": "#15151b",
    "#15151a": "#15151b",
    "#15151c": "#17171d",
    "#171717": "#17171d",
    "#17171d": "#18181f",
    "#17181d": "#18181f",
    "#18131a": "#17131a",
    "#18181d": "#19191f",
    "#1b1820": "#202025",
    "#1b1b22": "#1b1b22",
    "#1c1726": "#1b1820",
    "#1d1920": "#1c171d",
    "#1d1d23": "#1c1c23",
    "#202020": "#24242c",
    "#23352b": "#29412e",
    "#24242d": "#292932",
    "#25252f": "#2b2b34",
    "#252525": "#24242c",
    "#271522": "#24131d",
    "#292929": "#303039",
    "#29202a": "#2a2028",
    "#2b1a25": "#2d2029",
    "#2d2731": "#37303a",
    "#30303a": "#3a3942",
    "#352d46": "#3d3546",
    "#363640": "#46454f",
    "#383842": "#41404a",
    "#3a3a44": "#41404a",
    "#3f2635": "#4a2638",
    "#484851": "#55545f",
    "#493040": "#543243",
    "#4b2a3d": "#5b3048",
    "#4d4d57": "#666570",
    "#55466d": "#5b5067",
    "#5d2947": "#6f2f51",
    "#626b65": "#6f7772",
    "#666672": "#777780",
    "#686873": "#777682",
    "#777783": "#8b8a95",
    "#858590": "#9c9ba6",
    "#888888": "#a1a0aa",
    "#999999": "#b0aeb8",
    "#aaaaaa": "#c3c1ca",
    "#a8a8b3": "#d1cfd8",
    "#a9a9b4": "#c5c3cd",
    "#b9c6bc": "#c4d4c7",
    "#bbbbbb": "#c8c6cf",
    "#ededf2": "#f2f1f5",
    "#eeeeee": "#f2f1f5",
    "#f2f2f2": "#f4f3f6",
    "#f3effa": "#f4f3f6",
    # Pink accent: restrained, never used as a page background
    "#d84b91": "#e05a9d",
    "#e05299": "#e05a9d",
    "#c23d82": "#e05a9d",
}

NAV_BLOCK_OLD = '''            QPushButton#navButton {
                background-color: transparent;
                color: #a8a8b3;
                border: 1px solid transparent;
                border-radius: 8px;
                text-align: left;
                min-height: 48px;
            }
'''

NAV_BLOCK_NEW = '''            QPushButton#navButton {
                background-color: #111116;
                color: #f4f3f6;
                border: 1px solid transparent;
                border-radius: 10px;
                text-align: left;
                min-height: 56px;
                padding: 4px 10px;
            }
'''

NAV_ACTIVE_OLD = '''            QPushButton#navButton[active="true"] {
                background-color: #24131d;
                color: #ffffff;
                border: 1px solid #6f2f51;
            }
'''

NAV_ACTIVE_NEW = '''            QPushButton#navButton[active="true"] {
                background-color: #202026;
                color: #ffffff;
                border: 1px solid #6f2f51;
            }
'''

NAV_ICON_OLD = '''            QLabel#navIcon {
                background: transparent;
                color: #8b8a95;
                font-size: 18px;
                font-weight: bold;
            }
'''

NAV_ICON_NEW = '''            QLabel#navIcon {
                background: transparent;
                color: #c9c7d0;
                font-size: 28px;
                font-weight: 700;
            }
'''

NAV_TEXT_OLD = '''            QLabel#navText {
                background: transparent;
                color: inherit;
                font-size: 13px;
                font-weight: 600;
            }
'''

NAV_TEXT_NEW = '''            QLabel#navText {
                background: transparent;
                color: #f4f3f6;
                font-size: 15px;
                font-weight: 600;
            }
'''

for path in FILES:
    text = path.read_text(encoding="utf-8-sig")

    for old, new in COLOR_MAP.items():
        text = text.replace(old, new)

    if path.name == "main_window.py":
        text = text.replace(NAV_BLOCK_OLD, NAV_BLOCK_NEW)
        text = text.replace(NAV_ACTIVE_OLD, NAV_ACTIVE_NEW)
        text = text.replace(NAV_ICON_OLD, NAV_ICON_NEW)
        text = text.replace(NAV_TEXT_OLD, NAV_TEXT_NEW)

        # Make the actual icon widget wider so the larger glyphs have room.
        text = text.replace(
            '''        icon_label.setFixedWidth(\n            24\n        )\n''',
            '''        icon_label.setFixedWidth(\n            42\n        )\n'''
        )

    path.write_text(text, encoding="utf-8-sig")
    print(f"BLACK/WHITE THEME: {path}")

print("KID ACID DARK UI AANGEPAST")

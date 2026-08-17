from pathlib import Path

FILES = [
    Path("gui/main_window.py"),
    Path("gui/release_library_page.py"),
    Path("gui/release_detail_page.py"),
]

# Restore a true black/charcoal UI if a previous bright-theme installer
# changed the local files. These replacements are intentionally limited to
# presentation colours and do not touch application logic.
COLOR_REPLACEMENTS = {
    "#f7f4fa": "#09090b",
    "#ffffff": "#ffffff",
    "#f1eef4": "#111116",
    "#eef8f0": "#111a14",
    "#eee9f2": "#111116",
    "#faf8fc": "#121218",
    "#fff9fd": "#16161c",
    "#fff4f9": "#21121b",
    "#f8e9f1": "#25131e",
    "#f8e3ef": "#24131d",
    "#f6e8f1": "#24151e",
    "#f7e8f0": "#24151e",
    "#eeeaf2": "#1b1b22",
    "#e0dbe5": "#2b2b34",
    "#ddd7e4": "#2a2a33",
    "#d9cfdf": "#3a3540",
    "#c9c1ce": "#4a4550",
    "#c9c1cf": "#4a4550",
    "#c0b7c8": "#45414b",
    "#b7a8c2": "#554c5d",
    "#a9a1ae": "#85808c",
    "#8f8895": "#77717d",
    "#746d79": "#8d8792",
    "#6f6875": "#9c97a2",
    "#655d6b": "#aaa4af",
    "#625a68": "#b5afba",
    "#5f5967": "#c6c1ca",
    "#302a35": "#f5f3f7",
}

for path in FILES:
    text = path.read_text(encoding="utf-8-sig")
    original = text

    for old, new in COLOR_REPLACEMENTS.items():
        if old == "#ffffff":
            continue
        text = text.replace(old, new)

    # Main window: stronger dark visual hierarchy.
    if path.name == "main_window.py":
        text = text.replace('"⌂",\n            "Dashboard"', '"⌂",\n            "Dashboard"')
        text = text.replace('"▣",\n            "Release Library"', '"▦",\n            "Release Library"')
        text = text.replace('"◈",\n            "Discogs Import"', '"◈",\n            "Discogs Import"')
        text = text.replace('"♫",\n            "MP3 Library"', '"♫",\n            "MP3 Library"')
        text = text.replace('"⚙",\n            "Instellingen"', '"⚙",\n            "Instellingen"')

        text = text.replace(
            'sidebar.setFixedWidth(\n            250\n        )',
            'sidebar.setFixedWidth(\n            250\n        )'
        )
        text = text.replace(
            'button.setMinimumHeight(\n            48\n        )',
            'button.setMinimumHeight(\n            58\n        )'
        )
        text = text.replace(
            'icon_label.setFixedWidth(\n            24\n        )',
            'icon_label.setFixedWidth(\n            38\n        )'
        )
        text = text.replace(
            'font-family: "Segoe UI";',
            'font-family: "Segoe UI Semibold";'
        )
        text = text.replace(
            'font-size: 18px;\n                font-weight: bold;\n            }\n\n            QPushButton#navButton[active="true"] QLabel#navIcon',
            'font-size: 28px;\n                font-weight: 700;\n                min-width: 34px;\n                min-height: 34px;\n            }\n\n            QPushButton#navButton[active="true"] QLabel#navIcon'
        )
        text = text.replace(
            'font-size: 13px;\n                font-weight: 600;\n            }\n\n            /* ==================================================\n               TOP BAR',
            'font-size: 15px;\n                font-weight: 700;\n            }\n\n            /* ==================================================\n               TOP BAR'
        )

    # Per-page dark UI should be neutral charcoal rather than near-black.
    text = text.replace("background-color: #0f0f12;", "background-color: #0b0c10;")
    text = text.replace("background-color: #0b0b0f;", "background-color: #0b0c10;")
    text = text.replace("background-color: #111116;", "background-color: #11131a;")
    text = text.replace("background-color: #121218;", "background-color: #151820;")
    text = text.replace("background-color: #141419;", "background-color: #151820;")
    text = text.replace("background-color: #16161c;", "background-color: #181b23;")

    # Keep light green / light red checklist semantics readable on dark UI.
    text = text.replace("color: #35613e;", "color: #7ee58f;")
    text = text.replace("background-color: #dff3e3;", "background-color: #193523;")
    text = text.replace("background-color: #c9e8cf;", "background-color: #244b30;")
    text = text.replace("color: #c23d82;", "color: #ff5ca8;")
    text = text.replace("color: #f2f2f5;", "color: #ffffff;")
    text = text.replace("color: #eeeeee;", "color: #ffffff;")
    text = text.replace("color: #f3effa;", "color: #ffffff;")

    if text != original:
        path.write_text(text, encoding="utf-8-sig")
        print(f"DARK UI TOEGEPAST: {path}")
    else:
        print(f"GEEN UI-WIJZIGING NODIG: {path}")

print("KID ACID DARK UI KLAAR")

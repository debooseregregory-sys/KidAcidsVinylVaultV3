from pathlib import Path
import re

FILES = [
    Path("gui/main_window.py"),
    Path("gui/release_library_page.py"),
    Path("gui/release_detail_page.py"),
]

# Background colours used by previous theme attempts. These are deliberately
# changed only when they occur in a background/background-color declaration,
# so white text remains white.
DARK_BG = {
    "#ffffff": "#121216",
    "#fff9fd": "#15151b",
    "#fff4f9": "#18131a",
    "#faf8fc": "#15151b",
    "#f8e9f1": "#18131a",
    "#f8e3ef": "#1b141b",
    "#f7f4fa": "#0b0b0f",
    "#f3edf6": "#15151b",
    "#f1eef4": "#101014",
    "#eee9f2": "#15151b",
    "#eeeaf2": "#17171d",
    "#f7e8f0": "#18131d",
    "#f6e8f1": "#18131d",
    "#e0dbe5": "#292933",
    "#d9cfdf": "#2a2730",
    "#c9c1cf": "#34303a",
    "#b7a8c2": "#403744",
    "#2b1a25": "#1b141a",
    "#1d1920": "#18151b",
    "#1b1820": "#18181e",
    "#17181d": "#17171d",
    "#17171d": "#17171d",
    "#1b1b22": "#1b1b22",
    "#18181d": "#18181d",
    "#1c1726": "#1c1821",
    "#252525": "#222228",
}


def replace_backgrounds(text: str) -> str:
    def repl(match):
        prefix = match.group(1)
        colour = match.group(2).lower()
        return f"{prefix}{DARK_BG.get(colour, colour)};"

    pattern = re.compile(
        r"(background(?:-color)?\s*:\s*)(#[0-9a-fA-F]{6})\s*;"
    )
    return pattern.sub(repl, text)


def replace_ui_font_sizes(text: str) -> str:
    # Larger, readable interface text without touching checklist semantics.
    text = text.replace('font-family: "Segoe UI";', 'font-family: "Segoe UI";')
    text = text.replace('font-size: 13px;', 'font-size: 15px;')
    text = text.replace('font-size: 12px;', 'font-size: 14px;')
    text = text.replace('font-size: 11px;', 'font-size: 13px;')
    return text


for path in FILES:
    text = path.read_text(encoding="utf-8-sig")
    original = text

    text = replace_backgrounds(text)
    text = replace_ui_font_sizes(text)

    # Final global dark surface colours where they are explicitly declared.
    text = text.replace("background-color: #0b0b0f;", "background-color: #09090c;")
    text = text.replace("background-color: #0f0f12;", "background-color: #0b0b0f;")
    text = text.replace("background-color: #0f0f14;", "background-color: #0d0d11;")
    text = text.replace("background-color: #111116;", "background-color: #101014;")

    # Sidebar: dark active state, pink only as a thin accent.
    text = text.replace(
        "background-color: #271522;",
        "background-color: #19191f;"
    )
    text = text.replace(
        "background-color: #f8e3ef;",
        "background-color: #19191f;"
    )

    # Large sidebar icon presentation.
    text = text.replace(
        'icon_label.setFixedWidth(\n            24\n        )',
        'icon_label.setFixedWidth(\n            34\n        )'
    )
    text = text.replace(
        'font-size: 18px;',
        'font-size: 28px;'
    )
    text = text.replace(
        'font-size: 13px;\n                font-weight: 600;',
        'font-size: 16px;\n                font-weight: 600;'
    )

    # Keep normal interface text white; muted labels stay light enough to read.
    text = text.replace('color: #302a35;', 'color: #f4f4f6;')
    text = text.replace('color: #2f2934;', 'color: #f4f4f6;')
    text = text.replace('color: #35303a;', 'color: #f4f4f6;')

    if text != original:
        path.write_text(text, encoding="utf-8-sig")
        print(f"ZWART THEMA TOEGEPAST: {path}")
    else:
        print(f"GEEN WIJZIGING: {path}")

print("KLAAR: volledige zwarte VinylVault interface")

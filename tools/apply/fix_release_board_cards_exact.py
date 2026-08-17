from pathlib import Path

BASE = Path(__file__).resolve().parent.parent.parent
TILE = BASE / "gui" / "release_board_tile.py"

text = TILE.read_text(encoding="utf-8-sig")

old = '''        self.data = data
        self.setObjectName("releaseBoardTile")
        self.setMinimumWidth(250)
        self.setMaximumWidth(310)
        self.setMinimumHeight(390)
'''

new = '''        self.data = data
        self.setObjectName("releaseBoardTile")

        # Fixed visual card size.  The window may show more/fewer cards,
        # but an individual release card must never stretch or shrink.
        self.setFixedSize(250, 390)
'''

if text.count(old) != 1:
    raise RuntimeError(
        f"Verwacht kaartgrootteblok 1 keer, gevonden {text.count(old)}"
    )

text = text.replace(old, new)

old_cover = '''        cover.setFixedSize(216, 216)
        cover.setAlignment(Qt.AlignmentFlag.AlignCenter)
        cover.setScaledContents(False)
'''

new_cover = '''        cover.setFixedSize(216, 216)
        cover.setAlignment(Qt.AlignmentFlag.AlignCenter)
        cover.setScaledContents(False)
        cover.setSizePolicy(
            __import__("PySide6.QtWidgets", fromlist=["QSizePolicy"]).QSizePolicy.Policy.Fixed,
            __import__("PySide6.QtWidgets", fromlist=["QSizePolicy"]).QSizePolicy.Policy.Fixed,
        )
'''

if text.count(old_cover) != 1:
    raise RuntimeError(
        f"Verwacht coverblok 1 keer, gevonden {text.count(old_cover)}"
    )

text = text.replace(old_cover, new_cover)

TILE.write_text(text, encoding="utf-8")
print("RELEASE BOARD KAARTEN ZIJN NU EXACT VAST 250x390")
print("Alleen het aantal kolommen verandert bij resize.")

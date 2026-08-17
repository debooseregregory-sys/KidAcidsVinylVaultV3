from pathlib import Path

BASE = Path(__file__).resolve().parent.parent.parent
TARGET = BASE / "gui" / "release_board_tile.py"

text = TARGET.read_text(encoding="utf-8-sig")

old = '''        self.setObjectName("releaseBoardTile")
        self.setMinimumWidth(250)
        self.setMaximumWidth(310)
        self.setMinimumHeight(390)
'''

new = '''        self.setObjectName("releaseBoardTile")
        # De kaart blijft altijd exact even groot.
        # Alleen het aantal kolommen verandert bij resize.
        self.setFixedWidth(250)
        self.setFixedHeight(390)
'''

if text.count(old) != 1:
    raise RuntimeError(
        f"Verwacht kaartgrootteblok 1 keer, gevonden {text.count(old)}"
    )

text = text.replace(old, new)
TARGET.write_text(text, encoding="utf-8")
print("RELEASE BOARD KAARTGROOTTE VASTGEZET")
print("De kaarten veranderen niet meer van formaat bij minimaliseren/maximaliseren.")

from pathlib import Path

BASE = Path(__file__).resolve().parents[2]
TARGET = BASE / "gui" / "mp3_library_page.py"

text = TARGET.read_text(encoding="utf-8-sig")

marker = '    def __init__(self, row, parent=None):\n        super().__init__(parent)\n'
replacement = '    def __init__(self, row, parent=None):\n        super().__init__(parent)\n        self.row = row\n'

if marker not in text:
    raise RuntimeError("MetadataDialog __init__ marker niet gevonden")

text = text.replace(marker, replacement, 1)
TARGET.write_text(text, encoding="utf-8-sig")
print("MetadataDialog self.row hersteld")

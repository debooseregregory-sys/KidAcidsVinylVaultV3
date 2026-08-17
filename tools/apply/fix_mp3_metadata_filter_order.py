from pathlib import Path

BASE = Path(__file__).resolve().parents[2]
TARGET = BASE / "gui" / "mp3_library_page.py"
text = TARGET.read_text(encoding="utf-8-sig")

needle = '''        self.filter = QComboBox()\n        self.filter.addItems(["Alle MP3's", "Aan vinyl gekoppeld", "Niet gekoppeld"])\n        tools.addWidget(self.filter)\n'''
insert = '''        self.filter = QComboBox()\n        self.filter.addItems(["Alle MP3's", "Aan vinyl gekoppeld", "Niet gekoppeld"])\n        tools.addWidget(self.filter)\n\n        self.metadata_filter = QComboBox()\n        self.metadata_filter.addItems(["Metadata: Alles", "Metadata: KLAAR", "Metadata: NIET GEDAAN"])\n        tools.addWidget(self.metadata_filter)\n'''
if needle not in text:
    raise RuntimeError("filter-blok niet gevonden")
if "self.metadata_filter = QComboBox()" not in text:
    text = text.replace(needle, insert, 1)

TARGET.write_text(text, encoding="utf-8-sig")
print("metadata_filter aangemaakt vóór signal-connecties")

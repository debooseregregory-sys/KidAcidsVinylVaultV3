from pathlib import Path

BASE = Path(__file__).resolve().parent.parent.parent
TARGET = BASE / "gui" / "release_showcase_page.py"

text = TARGET.read_text(encoding="utf-8-sig")

old = '''                discogs_button = QPushButton("OPEN DISCOGS")\n                discogs_button.clicked.connect(lambda url=str(release[8]): QDesktopServices.openUrl(QUrl(url)))\n                info.addWidget(discogs_button, 0, Qt.AlignmentFlag.AlignLeft)\n'''

new = '''                discogs_button = QPushButton("OPEN DISCOGS")\n                discogs_url = str(release[8])\n                discogs_button.clicked.connect(\n                    lambda _checked=False, url=discogs_url: QDesktopServices.openUrl(QUrl(url))\n                )\n                info.addWidget(discogs_button, 0, Qt.AlignmentFlag.AlignLeft)\n'''

if old not in text:
    raise RuntimeError("Discogs button-blok niet gevonden")

text = text.replace(old, new, 1)
TARGET.write_text(text, encoding="utf-8")
print("SHOWCASE DISCOGS LINK GEFIXT")
print("De clicked-bool wordt nu niet meer als QUrl gebruikt.")

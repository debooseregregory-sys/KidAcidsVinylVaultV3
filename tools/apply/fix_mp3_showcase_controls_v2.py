from pathlib import Path

FILE = Path("gui/mp3_showcase_page.py")
text = FILE.read_text(encoding="utf-8-sig")

if "self.previous = QPushButton(\"VORIGE\")" in text:
    print("Controls already present.")
    raise SystemExit(0)

needle = "        self.previous.clicked.connect(self.previous_track)\n"
if needle not in text:
    raise SystemExit("Could not find self.previous connection line.")

block = '''        controls = QHBoxLayout()\n        controls.setSpacing(10)\n\n        self.previous = QPushButton("VORIGE")\n        self.play = QPushButton("PLAY")\n        self.next = QPushButton("VOLGENDE")\n\n        self.previous.setMinimumHeight(42)\n        self.play.setMinimumHeight(42)\n        self.next.setMinimumHeight(42)\n\n        controls.addWidget(self.previous)\n        controls.addWidget(self.play, 1)\n        controls.addWidget(self.next)\n\n        cl.addLayout(controls)\n\n'''

text = text.replace(needle, block + needle, 1)

FILE.write_text(text, encoding="utf-8")
print("MP3 Showcase controls restored.")

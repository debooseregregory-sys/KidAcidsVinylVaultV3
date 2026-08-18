from pathlib import Path

TARGET = Path(__file__).resolve().parents[2] / "gui" / "mp3_showcase_page.py"
text = TARGET.read_text(encoding="utf-8-sig")

marker = '''        top.addLayout(info, 1)\n        cl.addLayout(top)\n\n        # Controls are completely outside the cover/info layout.\n'''

insert = '''        top.addLayout(info, 1)\n        cl.addLayout(top)\n\n        # Playback controls. These must be created before the signal\n        # connections at the end of build_ui().\n        controls = QHBoxLayout()\n        self.controls_layout = controls\n        controls.setSpacing(10)\n\n        self.previous = QPushButton("VORIGE")\n        self.play = QPushButton("PLAY")\n        self.next = QPushButton("VOLGENDE")\n\n        controls.addWidget(self.previous)\n        controls.addWidget(self.play, 1)\n        controls.addWidget(self.next)\n        cl.addLayout(controls)\n\n        # Controls are completely outside the cover/info layout.\n'''

if marker not in text:
    raise SystemExit("Expected controls insertion point not found.")

text = text.replace(marker, insert, 1)
TARGET.write_text(text, encoding="utf-8")
print("MP3 Showcase controls restored.")

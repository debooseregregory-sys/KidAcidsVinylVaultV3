from pathlib import Path

BASE = Path(__file__).resolve().parent.parent.parent
TARGET = BASE / "gui" / "release_showcase_page.py"

text = TARGET.read_text(encoding="utf-8-sig")

old = '''            if path:\n                play.clicked.connect(lambda p=path: self.play_mp3.emit(p))\n'''

new = '''            if path:\n                # QPushButton.clicked emits a bool; keep the MP3 path as the second/default argument.\n                play.clicked.connect(\n                    lambda checked=False, p=path: self.play_mp3.emit(p)\n                )\n'''

if old not in text:
    raise RuntimeError("Showcase PLAY-koppeling niet gevonden")

text = text.replace(old, new, 1)
TARGET.write_text(text, encoding="utf-8")

print("SHOWCASE PLAY SIGNAL GEFIXT")
print("De clicked(bool)-waarde wordt nu genegeerd en het juiste MP3-pad wordt verstuurd.")

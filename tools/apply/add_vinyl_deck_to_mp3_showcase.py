from pathlib import Path

p = Path("gui/mp3_showcase_page.py")
text = p.read_text(encoding="utf-8-sig")

if "class ShowcaseVinylDeck" not in text:
    insert_after = "\n\nclass MP3ShowcasePage(QWidget):\n"
    deck = r'''

class ShowcaseVinylDeck(QWidget):
    """Compact visual vinyl deck for MP3 Showcase.

    It is intentionally self-contained so the Showcase does not depend on
    another turntable implementation. The actual MP3 playback continues to
    use the existing VinylVault player via the play_mp3 signal.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumWidth(260)
        self.setMaximumWidth(330)
        self.current_path = ""
        self.playing = False
        self.rotation = 0

        root = QVBoxLayout(self)
        root.setContentsMargins(14, 14, 14, 14)
        root.setSpacing(10)

        title = QLabel("VINYL PLAYER")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet(
            "color:#d84b91;font-size:12px;font-weight:900;letter-spacing:2px;"
        )
        root.addWidget(title)

        self.deck = QFrame()
        self.deck.setMinimumHeight(350)
        self.deck.setStyleSheet(
            "QFrame{background:#15151c;border:1px solid #302b39;border-radius:12px;}"
        )
        deck_layout = QVBoxLayout(self.deck)
        deck_layout.setContentsMargins(18, 18, 18, 18)
        deck_layout.setSpacing(10)

        self.record = QLabel("●")
        self.record.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.record.setMinimumSize(240, 240)
        self.record.setStyleSheet(
            "QLabel{background:#09090c;color:#d84b91;border:2px solid #403544;"
            "border-radius:120px;font-size:54px;}"
        )
        deck_layout.addWidget(self.record, 1, Qt.AlignmentFlag.AlignCenter)

        self.track_label = QLabel("Geen track geselecteerd")
        self.track_label.setWordWrap(True)
        self.track_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.track_label.setStyleSheet("color:#fff;font-weight:bold;")
        deck_layout.addWidget(self.track_label)

        self.path_label = QLabel("")
        self.path_label.setWordWrap(True)
        self.path_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.path_label.setStyleSheet("color:#777783;font-size:10px;")
        deck_layout.addWidget(self.path_label)

        root.addWidget(self.deck, 1)

        self.timer = QTimer(self)
        self.timer.setInterval(80)
        self.timer.timeout.connect(self._rotate)

    def set_track(self, path, artist="", title=""):
        self.current_path = str(path or "")
        name = " - ".join(
            part.strip() for part in (artist, title) if str(part or "").strip()
        )
        self.track_label.setText(name or Path(self.current_path).stem or "Geen track")
        self.path_label.setText(self.current_path)

    def set_playing(self, playing):
        self.playing = bool(playing)
        if self.playing:
            self.timer.start()
        else:
            self.timer.stop()

    def _rotate(self):
        self.rotation = (self.rotation + 8) % 360
        # A lightweight visual cue; avoids repaint-heavy custom graphics.
        self.record.setText("●" if self.rotation % 24 else "○")
'''
    text = text.replace(insert_after, deck + insert_after, 1)

# Import insert.
needle = "from PySide6.QtWidgets import (\n"
# no extra import needed: all classes already imported in current file.

# Add deck creation before the page finishes building.
needle2 = "        root.addLayout(self.body, 1)\n"
replacement2 = '''        self.vinyl_deck = ShowcaseVinylDeck()\n        self.body.addWidget(self.vinyl_deck, 0)\n        root.addLayout(self.body, 1)\n'''
if needle2 in text and "self.vinyl_deck = ShowcaseVinylDeck()" not in text:
    text = text.replace(needle2, replacement2, 1)

# Update showcase selection so the deck displays the current track.
needle3 = "        self.load_cover(str(path), str(release_cover or \"\"))\n"
replacement3 = needle3 + "        self.vinyl_deck.set_track(str(path), artist, title)\n"
if needle3 in text and "self.vinyl_deck.set_track" not in text:
    text = text.replace(needle3, replacement3, 1)

# Keep deck playback indicator synced with play button actions.
needle4 = "                self.play_mp3.emit(path)\n"
replacement4 = "                self.vinyl_deck.set_track(path, self.artist_label.text(), self.title_label.text())\n                self.vinyl_deck.set_playing(True)\n                self.play_mp3.emit(path)\n"
if needle4 in text and "self.vinyl_deck.set_playing(True)" not in text:
    text = text.replace(needle4, replacement4, 1)

# Remove any previous broken responsive handlers added by the earlier patches.
start = text.find("    def resizeEvent(self, event):\n")
if start != -1:
    end = text.find("    def load_files(self):\n", start)
    if end != -1:
        text = text[:start] + text[end:]

p.write_text(text, encoding="utf-8-sig")
print("OK: standalone vinyl deck added to MP3 Showcase")

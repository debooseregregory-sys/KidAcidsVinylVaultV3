from pathlib import Path

p = Path('gui/mp3_showcase_page.py')
text = p.read_text(encoding='utf-8-sig')

if 'class VinylDeckPanel(QFrame):' not in text:
    marker = 'class MP3ShowcasePage(QWidget):\n'
    deck = '''class VinylDeckPanel(QFrame):\n    def __init__(self, parent=None):\n        super().__init__(parent)\n        self.setObjectName("vinylDeckPanel")\n        self.setMinimumWidth(260)\n        self.setMaximumWidth(340)\n\n        layout = QVBoxLayout(self)\n        layout.setContentsMargins(18, 18, 18, 18)\n        layout.setSpacing(10)\n\n        title = QLabel("VINYL PLAYER")\n        title.setStyleSheet("color:#d84b91;font-size:15px;font-weight:900;")\n        layout.addWidget(title)\n\n        self.record = QLabel("VINYL")\n        self.record.setMinimumSize(220, 220)\n        self.record.setMaximumSize(280, 280)\n        self.record.setAlignment(Qt.AlignmentFlag.AlignCenter)\n        self.record.setStyleSheet(\n            "QLabel{background:#111116;color:#d84b91;border:8px solid #1f1f27;"\n            "border-radius:140px;font-size:24px;font-weight:900;}"\n        )\n        layout.addWidget(self.record, 0, Qt.AlignmentFlag.AlignHCenter)\n\n        self.artist = QLabel("-\")\n        self.artist.setAlignment(Qt.AlignmentFlag.AlignCenter)\n        self.artist.setWordWrap(True)\n        self.artist.setStyleSheet("color:#aaaab3;font-size:13px;font-weight:bold;")\n        layout.addWidget(self.artist)\n\n        self.track = QLabel("Geen track geselecteerd")\n        self.track.setAlignment(Qt.AlignmentFlag.AlignCenter)\n        self.track.setWordWrap(True)\n        self.track.setStyleSheet("color:#fff;font-size:16px;font-weight:800;")\n        layout.addWidget(self.track)\n\n        self.state = QLabel("KLAAR")\n        self.state.setAlignment(Qt.AlignmentFlag.AlignCenter)\n        self.state.setStyleSheet("color:#777783;font-size:11px;font-weight:bold;")\n        layout.addWidget(self.state)\n        layout.addStretch()\n\n    def set_track(self, artist, title):\n        self.artist.setText(str(artist or "Onbekende artiest"))\n        self.track.setText(str(title or "Onbekende titel"))\n\n    def set_playing(self, playing):\n        self.state.setText("AAN HET AFSPELEN" if playing else "KLAAR")\n        self.record.setStyleSheet(\n            "QLabel{background:#1a1a20;color:#fff;border:8px solid #d84b91;"\n            "border-radius:140px;font-size:24px;font-weight:900;}"\n            if playing else\n            "QLabel{background:#111116;color:#d84b91;border:8px solid #1f1f27;"\n            "border-radius:140px;font-size:24px;font-weight:900;}"\n        )\n\n\n'''
    if marker not in text:
        raise SystemExit('Kan MP3ShowcasePage class niet vinden.')
    text = text.replace(marker, deck + marker, 1)

# Add deck after detail card is added to the actual body layout.
needle = '        self.body.addWidget(card, 1)\n'
replacement = '''        self.body.addWidget(card, 1)\n\n        self.vinyl_deck = VinylDeckPanel()\n        self.body.addWidget(self.vinyl_deck, 0)\n'''
if 'self.vinyl_deck = VinylDeckPanel()' not in text:
    if needle not in text:
        raise SystemExit('Kan detail card niet vinden.')
    text = text.replace(needle, replacement, 1)

# Update selected track in the deck.
needle_show = '        self.artist_label.setText(artist)\n        self.title_label.setText(title)\n'
replacement_show = '''        self.artist_label.setText(artist)\n        self.title_label.setText(title)\n\n        if hasattr(self, "vinyl_deck"):\n            self.vinyl_deck.set_track(artist, title)\n'''
if 'self.vinyl_deck.set_track(artist, title)' not in text:
    if needle_show not in text:
        raise SystemExit('Kan show_item metadata niet vinden.')
    text = text.replace(needle_show, replacement_show, 1)

# Set player state when play is triggered.
needle_play = '                self.play_mp3.emit(path)\n\n    def play_track_item(self, item):\n'
replacement_play = '''                if hasattr(self, "vinyl_deck"):\n                    self.vinyl_deck.set_playing(True)\n                self.play_mp3.emit(path)\n\n    def play_track_item(self, item):\n'''
if 'self.vinyl_deck.set_playing(True)' not in text:
    if needle_play not in text:
        raise SystemExit('Kan play_current niet vinden.')
    text = text.replace(needle_play, replacement_play, 1)

p.write_text(text, encoding='utf-8-sig')
print('OK: zichtbare Vinyl Player-kaart toegevoegd aan de huidige MP3 Showcase.')

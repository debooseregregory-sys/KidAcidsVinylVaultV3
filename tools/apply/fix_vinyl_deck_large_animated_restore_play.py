from pathlib import Path
import re

p = Path('gui/mp3_showcase_page.py')
text = p.read_text(encoding='utf-8-sig')

# Restore the normal play_current implementation so audio continues to use
# the existing VinylVault player signal.
text = re.sub(
    r'    def play_current\(self\):\n.*?(?=\n    def |\Z)',
    '''    def play_current(self):
        if 0 <= self.current_index < len(self.visible_items):
            path = str(self.visible_items[self.current_index][0] or "")
            if Path(path).exists():
                self.play_mp3.emit(path)
                if hasattr(self, "vinyl_deck"):
                    self.vinyl_deck.set_track(
                        str(self.visible_items[self.current_index][1] or "").strip() or "Onbekende artiest",
                        str(self.visible_items[self.current_index][2] or "").strip() or Path(path).stem,
                    )
                    self.vinyl_deck.set_playing(True)
''',
    text,
    count=1,
    flags=re.S,
)

# Make the current vinyl panel much larger if present.
text = text.replace('self.vinyl_player_panel.setMinimumWidth(260)', 'self.vinyl_player_panel.setMinimumWidth(420)')
text = text.replace('self.vinyl_player_panel.setMaximumWidth(320)', 'self.vinyl_player_panel.setMaximumWidth(520)')
text = text.replace('self.vinyl_disc.setMinimumSize(220,220)', 'self.vinyl_disc.setMinimumSize(360,360)')
text = text.replace('border-radius:110px;', 'border-radius:180px;')

# Replace simple text-only deck with an animated painter widget when available.
if 'class VinylDeckWidget' not in text:
    insert_at = text.find('class MP3ShowcasePage(QWidget):')
    widget = '''class VinylDeckWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        from PySide6.QtCore import QTimer
        from PySide6.QtGui import QPainter, QPen, QBrush, QFont
        self._QPainter = QPainter
        self._QPen = QPen
        self._QBrush = QBrush
        self._QFont = QFont
        self.angle = 0
        self.artist = "Onbekende artiest"
        self.title = "-"
        self.playing = False
        self.timer = QTimer(self)
        self.timer.setInterval(40)
        self.timer.timeout.connect(self._tick)
        self.setMinimumSize(420, 520)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

    def set_track(self, artist, title):
        self.artist = artist or "Onbekende artiest"
        self.title = title or "-"
        self.update()

    def set_playing(self, playing):
        self.playing = bool(playing)
        if self.playing:
            self.timer.start()
        else:
            self.timer.stop()
        self.update()

    def _tick(self):
        self.angle = (self.angle + 5) % 360
        self.update()

    def paintEvent(self, event):
        painter = self._QPainter(self)
        painter.setRenderHint(self._QPainter.RenderHint.Antialiasing)
        r = min(self.width() - 40, self.height() - 150)
        r = max(220, r)
        cx = self.width() // 2
        cy = 25 + r // 2

        painter.setBrush(self._QBrush(Qt.GlobalColor.black))
        painter.setPen(self._QPen(Qt.GlobalColor.darkGray, 2))
        painter.drawEllipse(cx-r//2, cy-r//2, r, r)

        painter.save()
        painter.translate(cx, cy)
        painter.rotate(self.angle)
        painter.setPen(self._QPen(Qt.GlobalColor.darkGray, 3))
        for i in range(10):
            y = -r//2 + 10 + i * max(1, r//20)
            painter.drawLine(-r//2 + 12, y, r//2 - 12, y)
        painter.restore()

        label_r = int(r * 0.34)
        painter.setBrush(self._QBrush(Qt.GlobalColor.darkMagenta))
        painter.setPen(self._QPen(Qt.GlobalColor.black, 1))
        painter.drawEllipse(cx-label_r, cy-label_r, label_r*2, label_r*2)
        painter.setBrush(self._QBrush(Qt.GlobalColor.lightGray))
        painter.drawEllipse(cx-8, cy-8, 16, 16)

        painter.setPen(self._QPen(Qt.GlobalColor.white))
        painter.setFont(self._QFont("Segoe UI", 15, self._QFont.Weight.Bold))
        painter.drawText(20, r + 55, max(0, self.width()-40), 30, Qt.AlignmentFlag.AlignCenter, self.artist)
        painter.setFont(self._QFont("Segoe UI", 18, self._QFont.Weight.Bold))
        painter.drawText(20, r + 90, max(0, self.width()-40), 36, Qt.AlignmentFlag.AlignCenter, self.title)
        painter.setFont(self._QFont("Segoe UI", 11, self._QFont.Weight.Normal))
        status = "AAN HET AFSPELEN" if self.playing else "KLAAR"
        painter.drawText(20, r + 125, max(0, self.width()-40), 24, Qt.AlignmentFlag.AlignCenter, status)


'''
    text = text[:insert_at] + widget + text[insert_at:]

# Ensure QSizePolicy import exists.
if 'QSizePolicy,' not in text:
    text = text.replace('QListWidget, QListWidgetItem, QFrame, QScrollArea,', 'QListWidget, QListWidgetItem, QFrame, QScrollArea, QSizePolicy,')

# In build_ui, replace existing simple vinyl panel creation with animated widget.
old = '''        # ============================================================
        # VINYL PLAYER PANEL
        # ============================================================
'''
if old in text:
    start = text.find(old)
    end = text.find('        body.insertWidget(', start)
    if end != -1:
        tail = text.find('\n', text.find('        )', end) + 1)
        block = '''        # ============================================================
        # VINYL PLAYER PANEL
        # ============================================================

        self.vinyl_deck = VinylDeckWidget(self)
        self.vinyl_deck.set_track("Onbekende artiest", "-")
        self.vinyl_deck.set_playing(False)
        body.addWidget(self.vinyl_deck)
'''
        text = text[:start] + block + text[tail:]

p.write_text(text, encoding='utf-8-sig')
print('OK: vinyl deck enlarged, animated, and existing PLAY signal restored.')

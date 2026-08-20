from pathlib import Path
import re

P = Path('gui/mp3_showcase_page.py')
text = P.read_text(encoding='utf-8-sig')

if 'class VinylDeckWidget(QWidget):' not in text:
    marker = 'class MP3ShowcasePage(QWidget):'
    if marker not in text:
        raise SystemExit('MP3ShowcasePage class not found')
    cls = r'''class VinylDeckWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.artist = 'KID ACID'
        self.title = 'VINYL PLAYER'
        self.playing = False
        self.angle = 0.0
        self.timer = QTimer(self)
        self.timer.setInterval(40)
        self.timer.timeout.connect(self._tick)
        self.setMinimumSize(420, 520)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setStyleSheet('background:#121219;border:1px solid #2a2532;border-radius:14px;')

    def set_track(self, artist, title):
        self.artist = str(artist or 'Onbekende artiest')
        self.title = str(title or 'Onbekende titel')
        self.update()

    def set_playing(self, playing):
        self.playing = bool(playing)
        if self.playing:
            self.timer.start()
        else:
            self.timer.stop()
        self.update()

    def _tick(self):
        self.angle = (self.angle + 5.0) % 360.0
        self.update()

    def paintEvent(self, event):
        from PySide6.QtGui import QPainter, QPen, QBrush, QFont
        from PySide6.QtCore import QPointF, QRectF

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.fillRect(self.rect(), self.palette().window())

        w = self.width()
        h = self.height()
        cx = w / 2.0
        top = 42.0
        platter = max(250.0, min(w - 48.0, h * 0.52))
        if platter < 250:
            platter = 250
        r = platter / 2.0
        cy = top + r

        painter.setPen(QPen('#d84b91', 2))
        painter.setBrush(QBrush('#0b0b0f'))
        painter.drawRoundedRect(QRectF(16, 16, w - 32, h - 32), 12, 12)

        painter.setPen(QPen('#3a3642', 2))
        painter.setBrush(QBrush('#08080b'))
        painter.drawEllipse(QPointF(cx, cy), r + 8, r + 8)

        painter.setBrush(QBrush('#050507'))
        painter.setPen(QPen('#1e1e24', 1))
        painter.drawEllipse(QPointF(cx, cy), r, r)

        # Vinyl grooves
        painter.setPen(QPen('#19191f', 1))
        for frac in (0.92, 0.84, 0.76, 0.68, 0.60, 0.52):
            rr = r * frac
            painter.drawEllipse(QPointF(cx, cy), rr, rr)

        # Rotating highlight/marker
        painter.save()
        painter.translate(cx, cy)
        painter.rotate(self.angle)
        painter.setPen(QPen('#6b203f', 3))
        painter.drawLine(QPointF(0, -r * 0.72), QPointF(0, -r * 0.94))
        painter.restore()

        # Label
        label_r = r * 0.34
        painter.setBrush(QBrush('#7b214c'))
        painter.setPen(QPen('#b44b77', 1))
        painter.drawEllipse(QPointF(cx, cy), label_r, label_r)
        painter.setBrush(QBrush('#0d0d10'))
        painter.setPen(QPen('#0d0d10', 1))
        painter.drawEllipse(QPointF(cx, cy), 7, 7)

        # Tonearm
        painter.save()
        painter.translate(cx + r * 0.78, cy - r * 0.58)
        painter.rotate(-16)
        painter.setPen(QPen('#b9bac3', 5))
        painter.drawLine(QPointF(0, 0), QPointF(-r * 0.56, r * 0.38))
        painter.setPen(QPen('#7c7d86', 3))
        painter.drawLine(QPointF(-r * 0.56, r * 0.38), QPointF(-r * 0.62, r * 0.46))
        painter.restore()

        # Text area
        font = QFont('Segoe UI', 12)
        painter.setFont(font)
        painter.setPen(QPen('#d84b91'))
        painter.drawText(QRectF(32, cy + r + 28, w - 64, 28), Qt.AlignmentFlag.AlignCenter, 'VINYL PLAYER')

        font.setBold(True)
        font.setPointSize(16)
        painter.setFont(font)
        painter.setPen(QPen('#ffffff'))
        painter.drawText(QRectF(32, cy + r + 62, w - 64, 32), Qt.AlignmentFlag.AlignCenter, self.artist)

        font.setBold(False)
        font.setPointSize(14)
        painter.setFont(font)
        painter.setPen(QPen('#c3c3cc'))
        painter.drawText(QRectF(32, cy + r + 98, w - 64, 54), Qt.AlignmentFlag.AlignCenter | Qt.TextFlag.TextWordWrap, self.title)

        font.setPointSize(11)
        painter.setFont(font)
        painter.setPen(QPen('#8e8e99'))
        status = '● AAN HET AFSPELEN' if self.playing else '○ KLAAR'
        painter.drawText(QRectF(32, h - 66, w - 64, 24), Qt.AlignmentFlag.AlignCenter, status)
        painter.end()

'''
    text = text.replace(marker, cls + '\n' + marker, 1)

# Ensure QSizePolicy import exists.
if 'QSizePolicy' not in text.split('from database.database')[0]:
    text = text.replace('QListWidget, QListWidgetItem, QFrame, QScrollArea,\n', 'QListWidget, QListWidgetItem, QFrame, QScrollArea, QSizePolicy,\n', 1)

# Add animated deck once after the current card is added to body.
if 'self.vinyl_deck = VinylDeckWidget()' not in text:
    marker = '        body.addWidget(card, 1)\n'
    insert = "        self.vinyl_deck = VinylDeckWidget()\n        body.addWidget(self.vinyl_deck, 1)\n"
    if marker not in text:
        raise SystemExit('body.addWidget(card, 1) not found')
    text = text.replace(marker, marker + insert, 1)

# Add a helper that starts the existing player and the animation.
if 'def _play_with_deck(self):' not in text:
    marker = '    def play_current(self):\n'
    method = '''    def _play_with_deck(self):\n        if 0 <= self.current_index < len(self.visible_items):\n            row = self.visible_items[self.current_index]\n            path = str(row[0] or '')\n            if Path(path).exists():\n                artist = str(row[1] or '').strip() or 'Onbekende artiest'\n                title = str(row[2] or '').strip() or Path(path).stem\n                self.vinyl_deck.set_track(artist, title)\n                self.vinyl_deck.set_playing(True)\n                self.play_mp3.emit(path)\n\n'''
    if marker not in text:
        raise SystemExit('play_current marker not found')
    text = text.replace(marker, method + marker, 1)

# Make normal play_current update deck but retain existing signal.
text = text.replace(
"    def play_current(self):\n        if 0 <= self.current_index < len(self.visible_items):\n            path = str(self.visible_items[self.current_index][0] or \"\")\n            if Path(path).exists():\n                self.play_mp3.emit(path)\n",
"    def play_current(self):\n        if 0 <= self.current_index < len(self.visible_items):\n            row = self.visible_items[self.current_index]\n            path = str(row[0] or '')\n            if Path(path).exists():\n                artist = str(row[1] or '').strip() or 'Onbekende artiest'\n                title = str(row[2] or '').strip() or Path(path).stem\n                if hasattr(self, 'vinyl_deck'):\n                    self.vinyl_deck.set_track(artist, title)\n                    self.vinyl_deck.set_playing(True)\n                self.play_mp3.emit(path)\n",
1)

# Update selection so deck follows the selected row even before play.
sel = "            self.show_item(self.visible_items[index])\n"
rep = "            self.show_item(self.visible_items[index])\n            if hasattr(self, 'vinyl_deck'):\n                row = self.visible_items[index]\n                self.vinyl_deck.set_track(row[1], row[2])\n                self.vinyl_deck.set_playing(False)\n"
text = text.replace(sel, rep, 1)

P.write_text(text, encoding='utf-8-sig')
print('OK: grote geanimeerde Vinyl Deck toegevoegd aan de huidige MP3 Showcase.')

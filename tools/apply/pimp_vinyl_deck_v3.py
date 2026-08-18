from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[2]
TARGET = ROOT / "gui" / "mp3_showcase_page.py"

new_class = r'''class VinylDeckWidget(QWidget):
    """Visual turntable for MP3 Showcase. Playback remains controlled by the page."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.artist = "KID ACID"
        self.title = "VINYL PLAYER"
        self.playing = False
        self.angle = 0.0
        self.arm_angle = -22.0
        self.setMinimumSize(620, 610)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.timer = QTimer(self)
        self.timer.setInterval(24)
        self.timer.timeout.connect(self._tick)

    def set_track(self, artist="", title=""):
        self.artist = str(artist or "Onbekende artiest")
        self.title = str(title or "Onbekende titel")
        self.update()

    def set_playing(self, playing):
        self.playing = bool(playing)
        if self.playing:
            self.timer.start()
        else:
            self.timer.stop()
        self.update()

    def _tick(self):
        self.angle = (self.angle + 2.6) % 360.0
        target = 15.0 if self.playing else -22.0
        self.arm_angle += (target - self.arm_angle) * 0.075
        self.update()

    def paintEvent(self, event):
        from math import cos, sin, radians
        from PySide6.QtGui import QPainter, QPen, QBrush, QColor, QFont, QLinearGradient
        from PySide6.QtCore import QPointF, QRectF

        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        w, h = float(self.width()), float(self.height())
        p.fillRect(self.rect(), QColor("#0b0b0f"))

        # Deck body
        body = QRectF(18, 18, w - 36, h - 36)
        grad = QLinearGradient(body.topLeft(), body.bottomRight())
        grad.setColorAt(0.0, QColor("#25242a"))
        grad.setColorAt(0.45, QColor("#15151a"))
        grad.setColorAt(1.0, QColor("#09090c"))
        p.setPen(QPen(QColor("#45414a"), 2))
        p.setBrush(QBrush(grad))
        p.drawRoundedRect(body, 20, 20)

        # Plinth / platter
        cx, cy = w * 0.43, h * 0.46
        r = min(w * 0.31, h * 0.34)
        p.setPen(QPen(QColor("#4f4c54"), 2))
        p.setBrush(QBrush(QColor("#303038")))
        p.drawEllipse(QPointF(cx, cy), r + 25, r + 25)
        p.setPen(QPen(QColor("#77737b"), 2))
        p.setBrush(QBrush(QColor("#17171c")))
        p.drawEllipse(QPointF(cx, cy), r + 13, r + 13)

        # Vinyl
        p.setPen(QPen(QColor("#29282e"), 1))
        p.setBrush(QBrush(QColor("#050507")))
        p.drawEllipse(QPointF(cx, cy), r, r)
        for f in (0.97, .94, .91, .88, .85, .82, .79, .76, .73, .70, .67, .64, .61, .58, .55):
            rr = r * f
            p.setPen(QPen(QColor(42, 41, 47, 115), 1))
            p.drawEllipse(QPointF(cx, cy), rr, rr)

        # Rotating vinyl reflections
        p.save()
        p.translate(cx, cy)
        p.rotate(self.angle)
        p.setPen(QPen(QColor(255, 255, 255, 32), 2))
        p.drawArc(QRectF(-r*.82, -r*.82, r*1.64, r*1.64), 15*16, 72*16)
        p.setPen(QPen(QColor(216, 75, 145, 70), 2))
        p.drawArc(QRectF(-r*.90, -r*.90, r*1.80, r*1.80), 190*16, 45*16)
        p.restore()

        # Label
        lr = r * .235
        p.setPen(QPen(QColor("#d8a0b8"), 2))
        p.setBrush(QBrush(QColor("#641638")))
        p.drawEllipse(QPointF(cx, cy), lr, lr)
        p.setPen(QColor("#f7e8ef"))
        p.setFont(QFont("Segoe UI", max(9, int(lr*.22)), QFont.Weight.Bold))
        p.drawText(QRectF(cx-lr, cy-lr*.16, lr*2, lr*.32), Qt.AlignmentFlag.AlignCenter, "KID ACID")
        p.setBrush(QBrush(QColor("#d8d3d8")))
        p.setPen(QPen(QColor("#77727b"), 1))
        p.drawEllipse(QPointF(cx, cy), 4, 4)

        # Tonearm pivot on the right
        pivot = QPointF(w * .82, h * .25)
        p.setPen(QPen(QColor("#111116"), 4))
        p.setBrush(QBrush(QColor("#333139")))
        p.drawEllipse(pivot, 31, 31)
        p.setPen(QPen(QColor("#77727b"), 2))
        p.drawEllipse(pivot, 20, 20)
        p.setBrush(QBrush(QColor("#b8b2ba")))
        p.drawEllipse(pivot, 6, 6)

        # S-shaped arm, calculated from pivot toward the playing/rest position
        a = radians(self.arm_angle)
        reach = r * .96
        elbow = QPointF(pivot.x() - cos(a)*reach*.48, pivot.y() + sin(a)*reach*.48)
        tip = QPointF(pivot.x() - cos(a)*reach, pivot.y() + sin(a)*reach)
        mid = QPointF((elbow.x()+tip.x())*.5, (elbow.y()+tip.y())*.5)
        bend = QPointF(mid.x()-sin(a)*18, mid.y()-cos(a)*18)

        p.setPen(QPen(QColor(0,0,0,130), 14, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        p.drawLine(pivot, elbow)
        p.drawLine(elbow, bend)
        p.drawLine(bend, tip)
        p.setPen(QPen(QColor("#bdb8c0"), 9, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        p.drawLine(pivot, elbow)
        p.drawLine(elbow, bend)
        p.drawLine(bend, tip)
        p.setPen(QPen(QColor("#eee9ee"), 3))
        p.drawLine(pivot, elbow)

        # Headshell and cartridge
        hx = tip.x() - cos(a)*24
        hy = tip.y() + sin(a)*24
        p.save()
        p.translate(hx, hy)
        p.rotate(-self.arm_angle)
        p.setPen(QPen(QColor("#28262d"), 2))
        p.setBrush(QBrush(QColor("#d4cfd4")))
        p.drawRoundedRect(QRectF(-31, -9, 38, 18), 4, 4)
        p.setBrush(QBrush(QColor("#b34d78")))
        p.drawRoundedRect(QRectF(-5, -6, 17, 12), 2, 2)
        p.setPen(QPen(QColor("#f0edf0"), 2))
        p.drawLine(QPointF(8, 0), QPointF(21, 13))
        p.setPen(QPen(QColor("#ffffff"), 1))
        p.drawLine(QPointF(21, 13), QPointF(22, 19))
        p.restore()

        # Controls / status
        status = "PLAYING" if self.playing else "READY"
        led = QColor("#72d49a") if self.playing else QColor("#625d67")
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(led))
        p.drawEllipse(QPointF(48, h-118), 6, 6)
        p.setPen(QPen(led, 1))
        p.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        p.drawText(QRectF(62, h-132, 120, 28), Qt.AlignmentFlag.AlignLeft, status)

        # Track information
        p.setPen(QColor("#d84b91"))
        p.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        p.drawText(QRectF(30, h-88, w-60, 22), Qt.AlignmentFlag.AlignCenter, self.artist)
        p.setPen(QColor("#ffffff"))
        p.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        p.drawText(QRectF(30, h-63, w-60, 30), Qt.AlignmentFlag.AlignCenter, self.title)
        p.setPen(QColor("#77727d"))
        p.setFont(QFont("Segoe UI", 9))
        p.drawText(QRectF(30, h-36, w-60, 18), Qt.AlignmentFlag.AlignCenter, "KID ACID'S VINYL VAULT")
        p.end()
'''

text = TARGET.read_text(encoding="utf-8-sig")
pattern = r"class VinylDeckWidget\(QWidget\):.*?(?=\nclass MP3ShowcasePage\(QWidget\):)"
updated, count = re.subn(pattern, new_class.rstrip(), text, count=1, flags=re.S)
if count != 1:
    raise SystemExit("VinylDeckWidget niet gevonden; bestand is NIET gewijzigd.")
TARGET.write_text(updated, encoding="utf-8-sig")
print("VinylDeckWidget vervangen.")
print("Bestand:", TARGET)
print("Backup blijft behouden.")

from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[2]
TARGET = ROOT / "gui" / "mp3_showcase_page.py"

new_class = r'''class VinylDeckWidget(QWidget):
    """Visual DJ turntable for MP3 Showcase; playback remains controlled by the page."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.artist = "KID ACID"
        self.title = "VINYL PLAYER"
        self.playing = False
        self.angle = 0.0
        self.arm_angle = -22.0
        self.pitch = 0.0
        self.setMinimumSize(680, 620)
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
        w, h = float(self.width()), float(self.height())
        p.fillRect(self.rect(), QColor("#09090c"))

        body = QRectF(16, 16, w - 32, h - 32)
        grad = QLinearGradient(body.topLeft(), body.bottomRight())
        grad.setColorAt(0.0, QColor("#2b2a2f"))
        grad.setColorAt(0.38, QColor("#19191e"))
        grad.setColorAt(1.0, QColor("#0a0a0d"))
        p.setPen(QPen(QColor("#4b4850"), 2))
        p.setBrush(QBrush(grad))
        p.drawRoundedRect(body, 18, 18)

        # platter and vinyl
        cx, cy = w * 0.40, h * 0.43
        r = min(w * 0.285, h * 0.315)
        p.setPen(QPen(QColor("#66636a"), 2))
        p.setBrush(QBrush(QColor("#38373d")))
        p.drawEllipse(QPointF(cx, cy), r + 27, r + 27)
        p.setPen(QPen(QColor("#858189"), 1))
        p.setBrush(QBrush(QColor("#1c1c21")))
        p.drawEllipse(QPointF(cx, cy), r + 16, r + 16)
        p.setPen(QPen(QColor("#242329"), 1))
        p.setBrush(QBrush(QColor("#040407")))
        p.drawEllipse(QPointF(cx, cy), r, r)

        for f in (0.985, .965, .945, .925, .905, .885, .865, .845, .825, .805,
                  .785, .765, .745, .725, .705, .685, .665, .645, .625, .605,
                  .585, .565, .545):
            rr = r * f
            p.setPen(QPen(QColor(58, 57, 63, 105), 1))
            p.drawEllipse(QPointF(cx, cy), rr, rr)

        p.save()
        p.translate(cx, cy)
        p.rotate(self.angle)
        p.setPen(QPen(QColor(255, 255, 255, 30), 2))
        p.drawArc(QRectF(-r*.86, -r*.86, r*1.72, r*1.72), 15*16, 70*16)
        p.setPen(QPen(QColor(216, 75, 145, 60), 2))
        p.drawArc(QRectF(-r*.94, -r*.94, r*1.88, r*1.88), 190*16, 42*16)
        p.restore()

        lr = r * .23
        p.setPen(QPen(QColor("#d8a0b8"), 2))
        p.setBrush(QBrush(QColor("#65183a")))
        p.drawEllipse(QPointF(cx, cy), lr, lr)
        p.setPen(QColor("#f8edf2"))
        p.setFont(QFont("Segoe UI", max(9, int(lr*.22)), QFont.Weight.Bold))
        p.drawText(QRectF(cx-lr, cy-lr*.15, lr*2, lr*.3), Qt.AlignmentFlag.AlignCenter, "KID ACID")
        p.setBrush(QBrush(QColor("#d6d2d7")))
        p.setPen(QPen(QColor("#68636b"), 1))
        p.drawEllipse(QPointF(cx, cy), 4, 4)

        # tonearm: substantial pivot, curved arm and real headshell
        pivot = QPointF(w * .79, h * .235)
        p.setPen(QPen(QColor("#09090b"), 5))
        p.setBrush(QBrush(QColor("#35333a")))
        p.drawEllipse(pivot, 34, 34)
        p.setPen(QPen(QColor("#858088"), 2))
        p.drawEllipse(pivot, 23, 23)
        p.setBrush(QBrush(QColor("#c9c4ca")))
        p.drawEllipse(pivot, 7, 7)
        p.setPen(QPen(QColor("#66616a"), 3))
        p.drawLine(QPointF(pivot.x()-16,pivot.y()+5), QPointF(pivot.x()+16,pivot.y()+5))

        a = radians(self.arm_angle)
        reach = r * .99
        elbow = QPointF(pivot.x() - cos(a)*reach*.42, pivot.y() + sin(a)*reach*.42)
        bend = QPointF(elbow.x()-sin(a)*24, elbow.y()-cos(a)*24)
        tip = QPointF(pivot.x() - cos(a)*reach, pivot.y() + sin(a)*reach)
        p.setPen(QPen(QColor(0,0,0,150), 16, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        for q1,q2 in ((pivot,elbow),(elbow,bend),(bend,tip)):
            p.drawLine(q1,q2)
        p.setPen(QPen(QColor("#c3bec5"), 10, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        for q1,q2 in ((pivot,elbow),(elbow,bend),(bend,tip)):
            p.drawLine(q1,q2)
        p.setPen(QPen(QColor("#f0edf1"), 3))
        p.drawLine(pivot, elbow)

        hx = tip.x() - cos(a)*24
        hy = tip.y() + sin(a)*24
        p.save()
        p.translate(hx, hy)
        p.rotate(-self.arm_angle)
        p.setPen(QPen(QColor("#29272d"), 2))
        p.setBrush(QBrush(QColor("#d7d2d7")))
        p.drawRoundedRect(QRectF(-32,-10,42,20),4,4)
        p.setBrush(QBrush(QColor("#a84770")))
        p.drawRoundedRect(QRectF(-4,-6,17,12),2,2)
        p.setPen(QPen(QColor("#efedef"),2))
        p.drawLine(QPointF(9,0),QPointF(22,12))
        p.setPen(QPen(QColor("#ffffff"),1))
        p.drawLine(QPointF(22,12),QPointF(23,20))
        p.restore()

        # Cue lever and arm rest
        rest = QPointF(w*.72, h*.39)
        p.setPen(QPen(QColor("#77727a"),5,Qt.PenStyle.SolidLine,Qt.PenCapStyle.RoundCap))
        p.drawLine(rest, QPointF(rest.x()+18,rest.y()-25))
        p.setPen(QPen(QColor("#b8b3ba"),3))
        p.drawLine(QPointF(rest.x()+18,rest.y()-25), QPointF(rest.x()+28,rest.y()-25))
        p.setBrush(QBrush(QColor("#343139")))
        p.drawRoundedRect(QRectF(w*.74,h*.39,12,34),4,4)

        # realistic pitch section on the far right; no text underneath it
        px = w * .90
        top, bottom = h*.43, h*.70
        p.setPen(QPen(QColor("#57535b"),2))
        p.setBrush(QBrush(QColor("#17171c")))
        p.drawRoundedRect(QRectF(px-28, top-22, 56, bottom-top+44), 10, 10)
        p.setPen(QPen(QColor("#7a757d"),3))
        p.drawLine(QPointF(px,top), QPointF(px,bottom))
        for i in range(9):
            yy = top + (bottom-top)*i/8
            p.setPen(QPen(QColor("#77727a"),2))
            p.drawLine(QPointF(px-10,yy),QPointF(px+10,yy))
        p.setPen(QPen(QColor("#d0cbd0"),2))
        knob_y = top + (bottom-top)*(.5 - self.pitch*.5)
        p.setBrush(QBrush(QColor("#c6c1c7")))
        p.drawRoundedRect(QRectF(px-10,knob_y-14,20,28),5,5)
        p.setPen(QColor("#77727c"))
        p.setFont(QFont("Segoe UI",8,QFont.Weight.Bold))
        p.drawText(QRectF(px-22,top-42,44,16),Qt.AlignmentFlag.AlignCenter,"PITCH")
        p.drawText(QRectF(px-42,top-22,18,14),Qt.AlignmentFlag.AlignRight,"+")
        p.drawText(QRectF(px-42,bottom-7,18,14),Qt.AlignmentFlag.AlignRight,"−")
        p.drawText(QRectF(px-25,bottom+12,50,15),Qt.AlignmentFlag.AlignCenter,"0")

        # physical controls
        controls_y = h*.82
        for x, label in ((w*.68,"POWER"),(w*.76,"START/STOP")):
            p.setPen(QPen(QColor("#4d4951"),2))
            p.setBrush(QBrush(QColor("#242329")))
            p.drawRoundedRect(QRectF(x-32,controls_y-18,64,36),7,7)
            p.setPen(QColor("#aaa5ac"))
            p.setFont(QFont("Segoe UI",7,QFont.Weight.Bold))
            p.drawText(QRectF(x-30,controls_y+23,60,14),Qt.AlignmentFlag.AlignCenter,label)
        p.setBrush(QBrush(QColor("#72d49a" if self.playing else "#4b4750")))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(QPointF(w*.68,controls_y),6,6)

        # speed selector
        sx, sy = w*.57, controls_y
        p.setPen(QPen(QColor("#555159"),2))
        p.setBrush(QBrush(QColor("#27262c")))
        p.drawEllipse(QPointF(sx,sy),20,20)
        p.setPen(QColor("#d8d2d8"))
        p.setFont(QFont("Segoe UI",7,QFont.Weight.Bold))
        p.drawText(QRectF(sx-30,sy+26,60,14),Qt.AlignmentFlag.AlignCenter,"33 / 45")
        p.setPen(QPen(QColor("#c8c2c8"),3))
        p.drawLine(QPointF(sx,sy),QPointF(sx+12,sy-9))

        # bottom track information, safely below controls
        p.setPen(QColor("#d84b91"))
        p.setFont(QFont("Segoe UI",11,QFont.Weight.Bold))
        p.drawText(QRectF(28,h-78,w-56,20),Qt.AlignmentFlag.AlignCenter,self.artist)
        p.setPen(QColor("#ffffff"))
        p.setFont(QFont("Segoe UI",16,QFont.Weight.Bold))
        p.drawText(QRectF(28,h-56,w-56,24),Qt.AlignmentFlag.AlignCenter,self.title)
        p.setPen(QColor("#706b73"))
        p.setFont(QFont("Segoe UI",8))
        p.drawText(QRectF(28,h-34,w-56,14),Qt.AlignmentFlag.AlignCenter,"KID ACID'S VINYL VAULT")
        p.end()
'''

text = TARGET.read_text(encoding="utf-8-sig")
pattern = r"class VinylDeckWidget\(QWidget\):.*?(?=\nclass MP3ShowcasePage\(QWidget\):)"
updated, count = re.subn(pattern, new_class.rstrip(), text, count=1, flags=re.S)
if count != 1:
    raise SystemExit("VinylDeckWidget niet gevonden; bestand is NIET gewijzigd.")
TARGET.write_text(updated, encoding="utf-8-sig")
print("VinylDeckWidget V5 vervangen.")
print("Alleen de deck-class is gewijzigd.")

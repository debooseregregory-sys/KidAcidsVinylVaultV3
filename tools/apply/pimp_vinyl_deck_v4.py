from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[2]
TARGET = ROOT / "gui" / "mp3_showcase_page.py"

new_class = r'''class VinylDeckWidget(QWidget):
    """Detailed visual DJ turntable for MP3 Showcase; playback stays external."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.artist = "KID ACID"
        self.title = "VINYL PLAYER"
        self.playing = False
        self.angle = 0.0
        self.arm_angle = -28.0
        self.setMinimumSize(650, 650)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.timer = QTimer(self)
        self.timer.setInterval(22)
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
        self.angle = (self.angle + 2.4) % 360.0
        target = 12.0 if self.playing else -28.0
        self.arm_angle += (target - self.arm_angle) * 0.055
        self.update()

    def paintEvent(self, event):
        from math import cos, sin, radians
        from PySide6.QtGui import QPainter, QPen, QBrush, QColor, QFont, QLinearGradient, QRadialGradient
        from PySide6.QtCore import QPointF, QRectF

        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = float(self.width()), float(self.height())
        p.fillRect(self.rect(), QColor("#09090c"))

        # Premium plinth with depth
        body = QRectF(14, 14, w-28, h-28)
        shadow = QRectF(20, 23, w-34, h-30)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(QColor(0,0,0,150)))
        p.drawRoundedRect(shadow, 24, 24)
        grad = QLinearGradient(body.topLeft(), body.bottomRight())
        grad.setColorAt(0, QColor("#36353a"))
        grad.setColorAt(.18, QColor("#242328"))
        grad.setColorAt(.55, QColor("#17171b"))
        grad.setColorAt(1, QColor("#0b0b0e"))
        p.setBrush(QBrush(grad)); p.setPen(QPen(QColor("#4e4b52"), 2))
        p.drawRoundedRect(body, 24, 24)
        p.setPen(QPen(QColor(255,255,255,18), 1)); p.drawRoundedRect(QRectF(24,24,w-48,h-48),20,20)

        # Deck inset / platter well
        cx, cy = w*.42, h*.43
        r = min(w*.285, h*.295)
        p.setPen(QPen(QColor("#08080a"), 3)); p.setBrush(QBrush(QColor("#111116")))
        p.drawEllipse(QPointF(cx,cy), r+30, r+30)
        p.setPen(QPen(QColor("#5d5a60"), 2)); p.setBrush(QBrush(QColor("#2b2a2f")))
        p.drawEllipse(QPointF(cx,cy), r+18, r+18)
        p.setPen(QPen(QColor("#858188"), 1)); p.drawEllipse(QPointF(cx,cy), r+12, r+12)
        p.setPen(QPen(QColor("#1b1a1f"), 2)); p.setBrush(QBrush(QColor("#0b0b0e")))
        p.drawEllipse(QPointF(cx,cy), r+5, r+5)

        # Vinyl and dense micro-grooves
        p.setPen(QPen(QColor("#17171b"), 1)); p.setBrush(QBrush(QColor("#030305")))
        p.drawEllipse(QPointF(cx,cy), r, r)
        for i in range(62):
            rr = r - 5 - i*max(1.0, r/90.0)
            if rr <= r*.28: break
            shade = 24 + (i % 4)*5
            p.setPen(QPen(QColor(shade,shade,shade+5,150), 1))
            p.drawEllipse(QPointF(cx,cy), rr, rr)

        # Rotating groove reflections
        p.save(); p.translate(cx,cy); p.rotate(self.angle)
        p.setPen(QPen(QColor(255,255,255,30), 2)); p.drawArc(QRectF(-r*.88,-r*.88,r*1.76,r*1.76),18*16,64*16)
        p.setPen(QPen(QColor(255,255,255,16), 1)); p.drawArc(QRectF(-r*.68,-r*.68,r*1.36,r*1.36),210*16,80*16)
        p.setPen(QPen(QColor(216,75,145,65), 2)); p.drawArc(QRectF(-r*.94,-r*.94,r*1.88,r*1.88),145*16,34*16)
        p.restore()

        # Label with subtle ring details
        lr = r*.235
        label = QRadialGradient(QPointF(cx-5,cy-7), lr)
        label.setColorAt(0,QColor("#9d315f")); label.setColorAt(.7,QColor("#5c1435")); label.setColorAt(1,QColor("#310d20"))
        p.setBrush(QBrush(label)); p.setPen(QPen(QColor("#d991b1"),2)); p.drawEllipse(QPointF(cx,cy),lr,lr)
        p.setPen(QPen(QColor(255,255,255,80),1)); p.drawEllipse(QPointF(cx,cy),lr*.78,lr*.78)
        p.setPen(QColor("#f5e5ec")); p.setFont(QFont("Segoe UI",max(9,int(lr*.2)),QFont.Weight.Bold))
        p.drawText(QRectF(cx-lr,cy-8,lr*2,16),Qt.AlignmentFlag.AlignCenter,"KID ACID")
        p.setPen(Qt.PenStyle.NoPen); p.setBrush(QBrush(QColor("#d7d2d8"))); p.drawEllipse(QPointF(cx,cy),4,4)

        # Arm assembly
        pivot = QPointF(w*.805,h*.255)
        p.setPen(Qt.PenStyle.NoPen); p.setBrush(QBrush(QColor(0,0,0,120))); p.drawEllipse(QPointF(pivot.x()+4,pivot.y()+6),38,38)
        p.setBrush(QBrush(QColor("#25242a"))); p.setPen(QPen(QColor("#68646b"),2)); p.drawEllipse(pivot,34,34)
        p.setBrush(QBrush(QColor("#111116"))); p.setPen(QPen(QColor("#8b878d"),2)); p.drawEllipse(pivot,23,23)
        p.setBrush(QBrush(QColor("#c9c5ca"))); p.setPen(QPen(QColor("#555158"),1)); p.drawEllipse(pivot,7,7)
        p.setBrush(QBrush(QColor("#6e6a72"))); p.drawEllipse(QPointF(pivot.x(),pivot.y()+19),3,3)

        a=radians(self.arm_angle); reach=r*.98
        elbow=QPointF(pivot.x()-cos(a)*reach*.46,pivot.y()+sin(a)*reach*.46)
        bend=QPointF((elbow.x()+pivot.x()-cos(a)*reach*.78)/2-sin(a)*16,(elbow.y()+pivot.y()+sin(a)*reach*.78)/2-cos(a)*16)
        tip=QPointF(pivot.x()-cos(a)*reach,pivot.y()+sin(a)*reach)
        pts=[pivot,elbow,bend,tip]
        # black shadow and metallic arm
        for width,col in ((16,QColor(0,0,0,150)),(11,QColor("#aaa6ad")),(7,QColor("#d7d3d8"))):
            p.setPen(QPen(col,width,Qt.PenStyle.SolidLine,Qt.PenCapStyle.RoundCap,Qt.PenJoinStyle.RoundJoin))
            for j in range(len(pts)-1): p.drawLine(pts[j],pts[j+1])
        p.setPen(QPen(QColor(255,255,255,110),2)); p.drawLine(pivot,elbow)

        # Counterweight stack behind pivot
        cw=QPointF(pivot.x()+31,pivot.y()+5)
        p.setPen(QPen(QColor("#66626a"),2)); p.setBrush(QBrush(QColor("#25242a"))); p.drawEllipse(cw,17,17)
        p.setBrush(QBrush(QColor("#403e45"))); p.drawEllipse(cw,11,11)
        p.setPen(QPen(QColor("#b7b2b9"),2)); p.drawLine(QPointF(cw.x()-7,cw.y()),QPointF(cw.x()+7,cw.y()))

        # Headshell / cartridge / stylus
        hx=tip.x()-cos(a)*25; hy=tip.y()+sin(a)*25
        p.save(); p.translate(hx,hy); p.rotate(-self.arm_angle)
        p.setPen(QPen(QColor("#17161a"),2)); p.setBrush(QBrush(QColor("#d4d0d5"))); p.drawRoundedRect(QRectF(-34,-9,42,18),4,4)
        p.setBrush(QBrush(QColor("#b94674"))); p.drawRoundedRect(QRectF(-7,-6,18,12),2,2)
        p.setPen(QPen(QColor("#4c4850"),2)); p.drawLine(QPointF(-23,-9),QPointF(-17,9))
        p.setPen(QPen(QColor("#f1edf1"),2)); p.drawLine(QPointF(8,0),QPointF(22,12)); p.setPen(QPen(QColor("#ffffff"),1)); p.drawLine(QPointF(22,12),QPointF(23,20))
        p.restore()

        # Cue lever
        lever=QPointF(w*.73,h*.65)
        p.setPen(QPen(QColor("#8b878d"),3)); p.drawLine(lever,QPointF(lever.x()+7,lever.y()-30)); p.setBrush(QBrush(QColor("#d3cfd4"))); p.drawEllipse(QPointF(lever.x()+7,lever.y()-32),4,4)

        # Pitch control and buttons
        p.setPen(QPen(QColor("#5d5960"),1)); p.setBrush(QBrush(QColor("#121217")))
        p.drawRoundedRect(QRectF(w*.69,h*.70,w*.20,92),8,8)
        p.setPen(QColor("#aaa5ad")); p.setFont(QFont("Segoe UI",8,QFont.Weight.Bold)); p.drawText(QRectF(w*.71,h*.72,w*.16,18),Qt.AlignmentFlag.AlignCenter,"PITCH")
        p.setPen(QPen(QColor("#77727a"),4)); p.drawLine(QPointF(w*.79,h*.755),QPointF(w*.79,h*.84))
        knob_y=h*(.795 if not self.playing else .77); p.setPen(QPen(QColor("#25242a"),2)); p.setBrush(QBrush(QColor("#d0ccd1"))); p.drawEllipse(QPointF(w*.79,knob_y),7,7)
        p.setPen(Qt.PenStyle.NoPen); p.setBrush(QBrush(QColor("#d84b91"))); p.drawRoundedRect(QRectF(w*.72,h*.875,46,18),4,4)
        p.setPen(QColor("#f5e8ee")); p.setFont(QFont("Segoe UI",7,QFont.Weight.Bold)); p.drawText(QRectF(w*.72,h*.875,46,18),Qt.AlignmentFlag.AlignCenter,"33")
        p.setBrush(QBrush(QColor("#35323a"))); p.drawRoundedRect(QRectF(w*.78,h*.875,46,18),4,4); p.setPen(QColor("#aaa5ad")); p.drawText(QRectF(w*.78,h*.875,46,18),Qt.AlignmentFlag.AlignCenter,"45")

        # Status and track display
        led=QColor("#71d49a") if self.playing else QColor("#625d67")
        p.setPen(Qt.PenStyle.NoPen); p.setBrush(QBrush(led)); p.drawEllipse(QPointF(48,h-74),6,6)
        p.setPen(led); p.setFont(QFont("Segoe UI",9,QFont.Weight.Bold)); p.drawText(QRectF(62,h-86,100,24),Qt.AlignmentFlag.AlignLeft,"PLAYING" if self.playing else "READY")
        p.setPen(QColor("#d84b91")); p.setFont(QFont("Segoe UI",11,QFont.Weight.Bold)); p.drawText(QRectF(175,h-88,w-210,22),Qt.AlignmentFlag.AlignRight,self.artist)
        p.setPen(QColor("#ffffff")); p.setFont(QFont("Segoe UI",16,QFont.Weight.Bold)); p.drawText(QRectF(175,h-64,w-210,28),Qt.AlignmentFlag.AlignRight,self.title)
        p.setPen(QColor("#66626a")); p.setFont(QFont("Segoe UI",8)); p.drawText(QRectF(175,h-39,w-210,16),Qt.AlignmentFlag.AlignRight,"KID ACID • VINYL VAULT")
        p.end()
'''

text = TARGET.read_text(encoding="utf-8-sig")
pattern = r"class VinylDeckWidget\(QWidget\):.*?(?=\nclass MP3ShowcasePage\(QWidget\):)"
updated, count = re.subn(pattern, new_class.rstrip(), text, count=1, flags=re.S)
if count != 1:
    raise SystemExit("VinylDeckWidget niet gevonden; bestand is NIET gewijzigd.")
TARGET.write_text(updated, encoding="utf-8-sig")
print("VinylDeckWidget V4 vervangen.")
print("Bestand:", TARGET)
print("Backup blijft behouden.")

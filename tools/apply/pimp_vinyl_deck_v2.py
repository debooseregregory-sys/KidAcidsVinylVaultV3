from pathlib import Path
PATH=Path('gui/mp3_showcase_page.py')
text=PATH.read_text(encoding='utf-8')
backup=PATH.with_name('mp3_showcase_page.py.before_vinyl_deck_v2')
backup.write_text(text,encoding='utf-8')
start=text.find('class VinylDeckWidget(QWidget):')
end=text.find('class MP3ShowcasePage(QWidget):')
if start<0 or end<0 or end<=start: raise SystemExit('VinylDeckWidget class not found')
cls=r'''class VinylDeckWidget(QWidget):
    def __init__(self,parent=None):
        super().__init__(parent)
        self.artist='KID ACID'; self.title='VINYL PLAYER'; self.playing=False; self.angle=0.0
        self.setMinimumSize(520,650)
        self.setSizePolicy(QSizePolicy.Policy.Expanding,QSizePolicy.Policy.Expanding)
        self.timer=QTimer(self); self.timer.setInterval(28); self.timer.timeout.connect(self._tick)
        self.setStyleSheet('background:#111117;border:1px solid #39313d;border-radius:18px;')
    def set_track(self,artist='',title=''):
        self.artist=str(artist or 'Onbekende artiest'); self.title=str(title or 'Onbekende titel'); self.update()
    def set_playing(self,playing):
        self.playing=bool(playing)
        if self.playing:self.timer.start()
        else:self.timer.stop()
        self.update()
    def _tick(self): self.angle=(self.angle+3.2)%360.0; self.update()
    def paintEvent(self,event):
        from math import cos,sin,radians
        from PySide6.QtGui import QPainter,QPen,QBrush,QColor,QFont
        from PySide6.QtCore import QPointF,QRectF
        p=QPainter(self); p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w=float(self.width()); h=float(self.height()); pink=QColor('#d84b91')
        p.fillRect(self.rect(),QColor('#111117'))
        p.setPen(QPen(QColor('#4a414d'),1)); p.setBrush(QBrush(QColor('#191920')))
        p.drawRoundedRect(QRectF(12,12,w-24,h-24),18,18)
        p.setPen(pink); p.setFont(QFont('Segoe UI',15,QFont.Weight.Bold))
        p.drawText(QRectF(20,24,w-40,28),Qt.AlignmentFlag.AlignCenter,"KID ACID • VINYL DECK")
        size=max(310,min(w-78,h-250)); r=size/2; cx=w/2; cy=86+r
        p.setPen(QPen(QColor('#5c5660'),2)); p.setBrush(QBrush(QColor('#29272e'))); p.drawEllipse(QPointF(cx,cy),r+18,r+18)
        p.setPen(QPen(QColor('#35323a'),2)); p.setBrush(QBrush(QColor('#0d0d11'))); p.drawEllipse(QPointF(cx,cy),r+7,r+7)
        p.setPen(QPen(QColor('#26242b'),1)); p.setBrush(QBrush(QColor('#050508'))); p.drawEllipse(QPointF(cx,cy),r,r)
        p.setBrush(QBrush(Qt.BrushStyle.NoBrush))
        for f in (.95,.90,.85,.80,.75,.70,.65,.60,.55,.50):
            rr=r*f; p.setPen(QPen(QColor('#16161c'),1)); p.drawEllipse(QPointF(cx,cy),rr,rr)
        p.save(); p.translate(cx,cy); p.rotate(self.angle)
        p.setPen(QPen(QColor(216,75,145,120),3)); p.drawArc(QRectF(-r*.82,-r*.82,r*1.64,r*1.64),20*16,75*16)
        p.setPen(QPen(QColor(255,255,255,28),2)); p.drawLine(QPointF(-r*.15,-r*.20),QPointF(r*.82,-r*.20)); p.restore()
        lr=min(68,r*.25); p.setPen(QPen(QColor('#ee9fc2'),2)); p.setBrush(QBrush(QColor('#68183f'))); p.drawEllipse(QPointF(cx,cy),lr,lr)
        p.setPen(QColor('#f7e6ee')); p.setFont(QFont('Segoe UI',max(10,int(lr/3.6)),QFont.Weight.Bold)); p.drawText(QRectF(cx-lr,cy-10,lr*2,20),Qt.AlignmentFlag.AlignCenter,'KID ACID')
        p.setPen(QPen(QColor('#c8c2ca'),1)); p.setBrush(QBrush(QColor('#d1cbd1'))); p.drawEllipse(QPointF(cx,cy),5,5)
        bx=w-78; by=120; p.setPen(QPen(QColor('#5a5360'),2)); p.setBrush(QBrush(QColor('#27242c'))); p.drawEllipse(QPointF(bx,by),24,24)
        ax=cx+r*.65 if self.playing else cx+r*.40; ay=cy-r*.06 if self.playing else cy-r*.40
        p.setPen(QPen(QColor('#b9b2bc'),8,Qt.PenStyle.SolidLine,Qt.PenCapStyle.RoundCap)); p.drawLine(QPointF(bx,by),QPointF(ax,ay))
        p.setPen(QPen(QColor('#625b65'),3)); p.drawLine(QPointF(ax,ay),QPointF(ax-22,ay+14))
        p.setPen(QPen(QColor('#111015'),1)); p.setBrush(QBrush(pink)); p.drawRoundedRect(QRectF(ax-34,ay+7,26,14),4,4)
        p.setPen(QPen(QColor('#eee'),2)); p.drawLine(QPointF(ax-22,ay+20),QPointF(ax-20,ay+32))
        sy=h-175; col=QColor('#77d999') if self.playing else QColor('#77727d')
        p.setPen(Qt.PenStyle.NoPen); p.setBrush(QBrush(col)); p.drawEllipse(QPointF(42,sy+8),6,6)
        p.setPen(col); p.setFont(QFont('Segoe UI',10,QFont.Weight.Bold)); p.drawText(QRectF(58,sy-4,160,24),Qt.AlignmentFlag.AlignLeft,'PLAYING' if self.playing else 'READY')
        for i in range(12):
            bh=7+i*2 if self.playing else 4; alpha=220 if self.playing and i<10 else 35; c=QColor(216,75,145,alpha) if i<9 else QColor(240,170,90,alpha)
            p.setPen(Qt.PenStyle.NoPen); p.setBrush(QBrush(c)); p.drawRoundedRect(QRectF(235+i*18,sy+15-bh,12,bh),3,3)
        p.setPen(pink); p.setFont(QFont('Segoe UI',13,QFont.Weight.Bold)); p.drawText(QRectF(25,h-125,w-50,24),Qt.AlignmentFlag.AlignCenter,self.artist)
        p.setPen(QColor('#fff')); p.setFont(QFont('Segoe UI',19,QFont.Weight.Bold)); p.drawText(QRectF(25,h-94,w-50,30),Qt.AlignmentFlag.AlignCenter,self.title)
        p.setPen(QColor('#78727c')); p.setFont(QFont('Segoe UI',9)); p.drawText(QRectF(25,h-55,w-50,20),Qt.AlignmentFlag.AlignCenter,"KID ACID'S VINYL VAULT")
        p.end()
'''
text=text[:start]+cls+'\n\n'+text[end:]
PATH.write_text(text,encoding='utf-8')
print('Backup:',backup)
print('VinylDeckWidget vervangen.')

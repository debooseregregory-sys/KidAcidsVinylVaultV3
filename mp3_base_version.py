from pathlib import Path
import math

from PySide6.QtCore import Qt, QTimer, Signal, QPointF, QRectF
from PySide6.QtGui import QPixmap, QPainter, QPen, QBrush, QColor, QFont, QLinearGradient, QRadialGradient
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QListWidget, QListWidgetItem, QFrame, QSizePolicy

from database.database import get_connection
from gui.player import MP3Player


class VinylDeckWidget(QWidget):
    """Visual deck. Playback is handled by the real MP3Player."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.artist = "KID ACID"
        self.title = "VINYL PLAYER"
        self.playing = False
        self.power_on = True
        self.angle = 0.0
        self.arm_progress = 0.0
        self.timer = QTimer(self)
        self.timer.setInterval(30)
        self.timer.timeout.connect(self._tick)
        self.timer.start()
        self.setMinimumHeight(500)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

    def set_track(self, artist, title):
        self.artist = str(artist or "Onbekende artiest").strip() or "Onbekende artiest"
        self.title = str(title or "-").strip() or "-"
        self.update()

    def set_playing(self, playing):
        self.playing = bool(playing) and self.power_on
        self.update()

    def set_power(self, on):
        self.power_on = bool(on)
        if not self.power_on:
            self.playing = False
        self.update()

    def _tick(self):
        if self.playing and self.power_on:
            self.angle = (self.angle + 2.8) % 360.0
        target = 1.0 if self.playing and self.power_on else 0.0
        self.arm_progress += (target - self.arm_progress) * 0.075
        if abs(target - self.arm_progress) < 0.0005:
            self.arm_progress = target
        self.update()

    def _layout(self):
        w, h = float(self.width()), float(self.height())
        r = max(145.0, min((w - 235.0) * 0.44, (h - 185.0) * 0.44, 235.0))
        cx = min(w * 0.47, w - r - 105.0)
        cy = min(h * 0.53, h - r - 105.0)
        return w, h, cx, cy, r

    def _text(self, p, rect, text, size=9, color=QColor("#8f919a"), weight=QFont.Weight.Bold, align=Qt.AlignmentFlag.AlignLeft):
        p.setPen(color)
        p.setFont(QFont("Segoe UI", size, weight))
        p.drawText(rect, align, str(text))

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setRenderHint(QPainter.RenderHint.TextAntialiasing)
        w, h, cx, cy, r = self._layout()
        p.fillRect(self.rect(), QColor("#090a0d"))
        deck = QRectF(8, 8, w - 16, h - 16)
        g = QLinearGradient(0, 8, 0, h - 8)
        g.setColorAt(0, QColor("#292b31")); g.setColorAt(.45, QColor("#191a1f")); g.setColorAt(1, QColor("#101116"))
        p.setBrush(QBrush(g)); p.setPen(QPen(QColor("#454750"), 2)); p.drawRoundedRect(deck, 18, 18)
        p.setBrush(QBrush(QColor("#17181d"))); p.setPen(QPen(QColor("#30323a"), 1)); p.drawRoundedRect(QRectF(28,28,w-56,h-56),11,11)
        self._text(p, QRectF(42,35,350,22), "KID ACID'S VINYL VAULT", 12, QColor("#d84b91"), QFont.Weight.Black)
        self._text(p, QRectF(42,57,390,17), "MP3 SHOWCASE / PROFESSIONAL DIRECT DRIVE", 8)
        pg = QRadialGradient(QPointF(cx-r*.25,cy-r*.25), r+20)
        pg.setColorAt(0,QColor("#555861")); pg.setColorAt(.62,QColor("#303239")); pg.setColorAt(1,QColor("#17181d"))
        p.setBrush(QBrush(pg)); p.setPen(QPen(QColor("#08090b"),3)); p.drawEllipse(QPointF(cx,cy),r+18,r+18)
        p.setBrush(QBrush(QColor("#22242a"))); p.setPen(QPen(QColor("#676a73"),2)); p.drawEllipse(QPointF(cx,cy),r+10,r+10)
        for i in range(60):
            a=math.radians(i*6+self.angle*.16); rr=r+5
            p.setPen(QPen(QColor("#a6a8af"),2.5 if i%5==0 else 1.4)); p.drawPoint(QPointF(cx+math.cos(a)*rr,cy+math.sin(a)*rr))
        rg=QRadialGradient(QPointF(cx-r*.35,cy-r*.35),r*1.05)
        rg.setColorAt(0,QColor("#24262b")); rg.setColorAt(.18,QColor("#0d0e11")); rg.setColorAt(.78,QColor("#030406")); rg.setColorAt(1,QColor("#111217"))
        p.setBrush(QBrush(rg)); p.setPen(QPen(QColor("#050609"),2)); p.drawEllipse(QPointF(cx,cy),r,r)
        p.save(); p.translate(cx,cy); p.rotate(self.angle); p.setBrush(Qt.BrushStyle.NoBrush)
        for f in (.985,.965,.945,.925,.905,.885,.865,.845,.825,.805,.785,.765,.745,.725,.705,.685,.665,.645,.625,.605):
            p.setPen(QPen(QColor(70,72,78,90),1)); p.drawEllipse(QPointF(0,0),r*f,r*f)
        p.setPen(QPen(QColor(225,225,230,24),3)); p.drawArc(QRectF(-r*.88,-r*.88,r*1.76,r*1.76),12*16,55*16)
        p.restore()
        label_r=min(61.0,r*.255)
        lg=QRadialGradient(QPointF(cx-label_r*.25,cy-label_r*.25),label_r)
        lg.setColorAt(0,QColor("#b94b7d")); lg.setColorAt(.72,QColor("#711b45")); lg.setColorAt(1,QColor("#45102b"))
        p.setBrush(QBrush(lg)); p.setPen(QPen(QColor("#ef9fc2"),2)); p.drawEllipse(QPointF(cx,cy),label_r,label_r)
        self._text(p,QRectF(cx-label_r,cy-11,label_r*2,18),"KID ACID",8,QColor("#f8e9f0"),QFont.Weight.Black,Qt.AlignmentFlag.AlignCenter)
        self._text(p,QRectF(cx-label_r,cy+7,label_r*2,15),"VINYL VAULT",5,QColor("#edb2ca"),QFont.Weight.Bold,Qt.AlignmentFlag.AlignCenter)
        p.setBrush(QBrush(QColor("#cfd0d5"))); p.setPen(QPen(QColor("#6e7078"),1)); p.drawEllipse(QPointF(cx,cy),5.5,5.5)
        pivot=QPointF(w-112,122); rest=QPointF(cx+r+48,cy-r*.31); play=QPointF(cx+r*.68,cy+r*.10)
        stylus=QPointF(rest.x()+(play.x()-rest.x())*self.arm_progress,rest.y()+(play.y()-rest.y())*self.arm_progress)
        dx,dy=stylus.x()-pivot.x(),stylus.y()-pivot.y(); length=max(1.0,math.hypot(dx,dy)); ux,uy=dx/length,dy/length
        perp=QPointF(-uy,ux); elbow=QPointF(pivot.x()+dx*.55+perp.x()*20,pivot.y()+dy*.55+perp.y()*20)
        path=[pivot,elbow,QPointF(stylus.x()-ux*25,stylus.y()-uy*25)]
        p.setPen(QPen(QColor("#07080a"),18,Qt.PenStyle.SolidLine,Qt.PenCapStyle.RoundCap,Qt.PenJoinStyle.RoundJoin)); p.drawPolyline(path)
        p.setPen(QPen(QColor("#9fa2aa"),12,Qt.PenStyle.SolidLine,Qt.PenCapStyle.RoundCap,Qt.PenJoinStyle.RoundJoin)); p.drawPolyline(path)
        p.setBrush(QBrush(QColor("#3a3c43"))); p.setPen(QPen(QColor("#07080a"),4)); p.drawEllipse(pivot,27,27)
        p.setBrush(QBrush(QColor("#c4c6ca"))); p.setPen(Qt.PenStyle.NoPen); p.drawEllipse(pivot,4,4)
        shell=QPointF(stylus.x()-ux*40,stylus.y()-uy*40); arm_angle=math.degrees(math.atan2(dy,dx))
        p.save(); p.translate(shell); p.rotate(arm_angle); p.setBrush(QBrush(QColor("#b9bbc1"))); p.setPen(QPen(QColor("#08090b"),3)); p.drawRoundedRect(QRectF(-27,-9,34,18),3,3); p.restore()
        p.setPen(QPen(QColor("#f1f2f4"),1.6)); p.drawLine(QPointF(stylus.x()-ux*6,stylus.y()-uy*6),QPointF(stylus.x()+ux*3,stylus.y()+uy*3))
        switch=QRectF(35,h-88,105,38); p.setBrush(QBrush(QColor("#08090b"))); p.setPen(QPen(QColor("#4a4c54"),2)); p.drawRoundedRect(switch,7,7)
        p.setBrush(QBrush(QColor("#25272d"))); p.setPen(QPen(QColor("#111216"),1)); p.drawRoundedRect(QRectF(switch.x()+3,switch.y()+3,switch.width()-6,switch.height()-6),5,5)
        half=switch.width()/2; p.setBrush(QBrush(QColor("#d84b91") if self.power_on else QColor("#3c3e46"))); p.drawRoundedRect(QRectF(switch.x()+4 if self.power_on else switch.x()+half+1,switch.y()+5,half-5,28),5,5)
        self._text(p,QRectF(switch.x(),switch.y()+7,half,22),"ON",9,QColor("#ffffff"),QFont.Weight.Black,Qt.AlignmentFlag.AlignCenter)
        self._text(p,QRectF(switch.x()+half,switch.y()+7,half,22),"OFF",9,QColor("#a7a9b0"),QFont.Weight.Black,Qt.AlignmentFlag.AlignCenter)
        strip=QRectF(155,h-92,max(260.0,w-240),58); p.setBrush(QBrush(QColor("#0c0d11"))); p.setPen(QPen(QColor("#30323a"),1)); p.drawRoundedRect(strip,7,7)
        self._text(p,QRectF(strip.x()+12,strip.y()+6,strip.width()-24,17),"33 RPM | DIRECT DRIVE | STABLE PLATTER",8)
        self._text(p,QRectF(strip.x()+12,strip.y()+27,strip.width()*.44,20),self.artist,10,QColor("#f2f2f5"),QFont.Weight.Bold)
        self._text(p,QRectF(strip.x()+strip.width()*.46,strip.y()+27,strip.width()*.51-12,20),self.title,10,QColor("#d84b91"),QFont.Weight.Black,Qt.AlignmentFlag.AlignRight)
        status=QColor("#77d999") if self.playing else QColor("#777981"); p.setBrush(QBrush(status)); p.setPen(Qt.PenStyle.NoPen); p.drawEllipse(QPointF(w-46,h-64),4,4)
        self._text(p,QRectF(w-92,h-55,45,18),"PLAY" if self.playing else "READY",7,status,QFont.Weight.Black,Qt.AlignmentFlag.AlignRight)
        p.end()

    def mousePressEvent(self,event):
        if event.button()!=Qt.MouseButton.LeftButton: return super().mousePressEvent(event)
        w,h,*_=self._layout(); switch=QRectF(35,h-88,105,38)
        if switch.contains(event.position()): self.set_power(not self.power_on); event.accept(); return
        super().mousePressEvent(event)


class MP3ShowcasePage(QWidget):
    play_mp3=Signal(str)
    def __init__(self,parent=None):
        super().__init__(parent)
        self.items=[]; self.visible_items=[]; self.current_index=-1
        self.audio_player=MP3Player(self); self.audio_player.hide()
        self.audio_player.play_started.connect(self._audio_started); self.audio_player.stopped.connect(self._audio_stopped)
        self.build_ui(); self.load_files()

    def build_ui(self):
        root=QVBoxLayout(self); root.setContentsMargins(28,22,28,22); root.setSpacing(14)
        title=QLabel("MP3 SHOWCASE"); title.setStyleSheet("font-size:26px;font-weight:900;color:#fff;"); root.addWidget(title)
        search=QHBoxLayout(); self.search=QLineEdit(); self.search.setPlaceholderText("Zoek artiest, titel, album, genre, release of bestand..."); search.addWidget(self.search,1); self.refresh=QPushButton("VERVERS"); search.addWidget(self.refresh); root.addLayout(search)
        self.status=QLabel("0 MP3's"); self.status.setStyleSheet("color:#9b9ba6;"); root.addWidget(self.status)
        body=QHBoxLayout(); body.setSpacing(20); self.list=QListWidget(); self.list.setMinimumWidth(360); self.list.currentRowChanged.connect(self.select_index); self.list.itemDoubleClicked.connect(lambda _item: self.play_current()); body.addWidget(self.list)
        card=QFrame(); card.setStyleSheet("QFrame{background:#121219;border:1px solid #2a2532;border-radius:10px;}"); cl=QVBoxLayout(card); cl.setContentsMargins(22,22,22,22); cl.setSpacing(10)
        top=QHBoxLayout(); top.setSpacing(22); self.cover=QLabel("NO COVER"); self.cover.setFixedSize(300,300); self.cover.setAlignment(Qt.AlignmentFlag.AlignCenter); self.cover.setStyleSheet("background:#0b0b0f;color:#666672;border:1px solid #302b39;border-radius:6px;"); top.addWidget(self.cover,0,Qt.AlignmentFlag.AlignTop)
        info=QVBoxLayout(); self.artist_label=QLabel("-"); self.artist_label.setStyleSheet("color:#d84b91;font-size:18px;font-weight:bold;"); self.artist_label.setWordWrap(True); info.addWidget(self.artist_label); self.title_label=QLabel("-"); self.title_label.setWordWrap(True); self.title_label.setStyleSheet("color:#fff;font-size:27px;font-weight:800;"); info.addWidget(self.title_label); self.meta_label=QLabel("-"); self.meta_label.setWordWrap(True); self.meta_label.setStyleSheet("color:#aaaab3;font-size:13px;"); info.addWidget(self.meta_label); self.release_label=QLabel("Release: -"); self.release_label.setWordWrap(True); self.release_label.setStyleSheet("color:#c5b6d4;font-size:14px;font-weight:bold;"); info.addWidget(self.release_label); self.discogs_label=QLabel("Discogs: -"); self.discogs_label.setWordWrap(True); self.discogs_label.setStyleSheet("color:#8f8798;font-size:12px;"); info.addWidget(self.discogs_label); info.addStretch(); top.addLayout(info,1); cl.addLayout(top)
        self.vinyl_deck=VinylDeckWidget(self); cl.addWidget(self.vinyl_deck,1)
        controls=QHBoxLayout(); self.previous=QPushButton("< VORIGE"); self.play=QPushButton("> PLAY"); self.next=QPushButton("VOLGENDE >"); controls.addWidget(self.previous); controls.addWidget(self.play,1); controls.addWidget(self.next); cl.addLayout(controls)
        self.track_list=QListWidget(); self.track_list.setMinimumHeight(160); self.track_list.itemDoubleClicked.connect(self.play_track_item); cl.addWidget(QLabel("TRACKS")); cl.addWidget(self.track_list,1)
        body.addWidget(card,1); root.addLayout(body,1)
        self.timer=QTimer(self); self.timer.setSingleShot(True); self.timer.setInterval(180); self.timer.timeout.connect(self.populate_list); self.search.textChanged.connect(lambda _: self.timer.start()); self.refresh.clicked.connect(self.load_files); self.previous.clicked.connect(self.previous_track); self.next.clicked.connect(self.next_track); self.play.clicked.connect(self.play_current)
        self.setStyleSheet("QWidget{background:#0b0b0f;color:#f2f2f5;} QLineEdit,QPushButton,QListWidget{background:#18181f;color:#fff;border:1px solid #30303a;border-radius:6px;padding:8px 10px;} QPushButton{font-weight:800;min-height:32px;} QPushButton:hover{border-color:#d84b91;background:#24242c;} QListWidget{background:#0f0f14;} QListWidget::item{padding:8px;border-bottom:1px solid #24242d;} QListWidget::item:selected{background:#271522;border:1px solid #5d2947;}")

    def load_files(self):
        conn=get_connection()
        try: rows=conn.execute("""SELECT m.path,m.artist,m.title,m.album,m.year,m.bpm,m.genre,COALESCE(r.artist,''),COALESCE(r.title,''),COALESCE(r.discogs,''),COALESCE(r.cover,'') FROM mp3_files m LEFT JOIN track_mp3 tm ON tm.mp3_id=m.id LEFT JOIN tracks t ON t.id=tm.track_id LEFT JOIN releases r ON r.id=t.release_id ORDER BY m.artist COLLATE NOCASE,m.title COLLATE NOCASE,m.path COLLATE NOCASE""").fetchall()
        finally: conn.close()
        unique={}
        for row in rows:
            path=str(row[0] or "")
            if path not in unique: unique[path]=tuple(row)
            elif not unique[path][9] and row[9]: unique[path]=tuple(row)
        self.items=list(unique.values()); self.populate_list()

    def populate_list(self):
        q=self.search.text().strip().casefold(); self.visible_items=[row for row in self.items if not q or q in " ".join(str(x or "") for x in row).casefold()]
        self.list.blockSignals(True); self.list.clear()
        for row in self.visible_items:
            artist=str(row[1] or "").strip(); title=str(row[2] or "").strip(); text=f"{artist} - {title}".strip(" -") or Path(str(row[0])).name; item=QListWidgetItem(text); item.setToolTip(str(row[0])); self.list.addItem(item)
        self.list.blockSignals(False); self.status.setText(f"{len(self.visible_items)} van {len(self.items)} MP3's")
        if self.visible_items: self.list.setCurrentRow(0)
        else: self.current_index=-1; self.clear_showcase()

    def select_index(self,index):
        self.current_index=index
        if 0<=index<len(self.visible_items): self.show_item(self.visible_items[index])

    def show_item(self,row):
        path,artist,title,album,year,bpm,genre,release_artist,release_title,discogs_id,release_cover=row
        artist=str(artist or "").strip() or "Onbekende artiest"; title=str(title or "").strip() or Path(str(path)).stem
        self.artist_label.setText(artist); self.title_label.setText(title); meta=[]
        if album: meta.append(f"Album: {album}")
        if year: meta.append(f"Jaar: {year}")
        if genre: meta.append(f"Genre: {genre}")
        if bpm: meta.append(f"BPM: {bpm}")
        self.meta_label.setText(" | ".join(meta) if meta else "Geen aanvullende metadata")
        self.release_label.setText(f"Release: {(str(release_artist)+' - ') if release_artist else ''}{release_title}" if release_title else "Release: geen gekoppelde release")
        self.discogs_label.setText(f"Discogs release ID: {discogs_id}" if discogs_id else "Discogs: geen releasekoppeling")
        self.vinyl_deck.set_track(artist,title); self.vinyl_deck.set_playing(False); self.load_cover(str(path),str(release_cover or "")); self.load_tracklist(str(path)); self.previous.setEnabled(self.current_index>0); self.next.setEnabled(self.current_index+1<len(self.visible_items)); self.play.setEnabled(True)

    def load_cover(self,path,release_cover):
        if release_cover and Path(release_cover).exists():
            pix=QPixmap(release_cover)
            if not pix.isNull(): self.cover.setPixmap(pix.scaled(300,300,Qt.AspectRatioMode.KeepAspectRatio,Qt.TransformationMode.SmoothTransformation)); self.cover.setText(""); return
        self.cover.clear(); self.cover.setText("NO COVER")

    def load_tracklist(self,current_path):
        self.track_list.clear()
        try:
            conn=get_connection()
            try: linked=conn.execute("SELECT t.position,t.title,t.duration,t.bpm,m.path FROM track_mp3 tm JOIN tracks t ON t.id=tm.track_id JOIN mp3_files m ON m.id=tm.mp3_id WHERE m.path=? ORDER BY t.position COLLATE NOCASE",(current_path,)).fetchall()
            finally: conn.close()
        except Exception: linked=[]
        if not linked: self.track_list.addItem("Geen gekoppelde VinylVault-track voor dit bestand"); return
        for position,title,duration,bpm,path in linked:
            text=f"{position or ''}  {title or ''}".strip(); extras=[]
            if duration: extras.append(str(duration))
            if bpm: extras.append(f"{bpm} BPM")
            if extras: text += " | " + " | ".join(extras)
            item=QListWidgetItem(text); item.setData(Qt.ItemDataRole.UserRole,str(path)); self.track_list.addItem(item)

    def _play_path(self,path):
        path=str(path or "").strip()
        if not path:
            self.status.setText("Geen MP3-pad ontvangen")
            return False
        file_path=Path(path).expanduser()
        if not file_path.exists() or not file_path.is_file():
            self.status.setText("MP3-bestand niet gevonden")
            print("MP3 SHOWCASE BESTAND NIET GEVONDEN:", path)
            return False
        path=str(file_path.resolve())

        # Use exactly the same central player object as the working MP3 Library.
        window=self.window()
        central_player=getattr(window,"mp3_player",None)
        if central_player is not None and hasattr(central_player,"play_file"):
            try:
                print("MP3 SHOWCASE -> CENTRALE PLAYER:",path)
                central_player.play_file(path)
                self.vinyl_deck.set_playing(True)
                self.status.setText(f"PLAYING: {file_path.name}")
                return True
            except Exception as exc:
                print("MP3 SHOWCASE CENTRALE PLAYER ERROR:",repr(exc))
                self.status.setText(f"Afspelen mislukt: {exc}")
                return False

        # Fallback for alternate hosts which do not expose mp3_player.
        try:
            self.audio_player.play_file(path)
            self.play_mp3.emit(path)
            self.vinyl_deck.set_playing(True)
            self.status.setText(f"PLAYING: {file_path.name}")
            return True
        except Exception as exc:
            print("MP3 SHOWCASE FALLBACK PLAYER ERROR:",repr(exc))
            self.status.setText(f"Afspelen mislukt: {exc}")
            return False

    def play_current(self):
        if 0<=self.current_index<len(self.visible_items):
            self._play_path(self.visible_items[self.current_index][0])

    def play_track_item(self,item):
        path=item.data(Qt.ItemDataRole.UserRole)
        if not self._play_path(path):
            self.play_current()

    def _audio_started(self,path):
        self.vinyl_deck.set_playing(True); self.status.setText(f"PLAYING: {Path(path).name}")

    def _audio_stopped(self):
        self.vinyl_deck.set_playing(False)

    def previous_track(self):
        if self.current_index>0: self.list.setCurrentRow(self.current_index-1); self.play_current()

    def next_track(self):
        if self.current_index+1<len(self.visible_items): self.list.setCurrentRow(self.current_index+1); self.play_current()

    def clear_showcase(self):
        self.cover.clear(); self.cover.setText("NO COVER"); self.artist_label.setText("-"); self.title_label.setText("-"); self.meta_label.setText("-"); self.release_label.setText("Release: -"); self.discogs_label.setText("Discogs: -"); self.track_list.clear(); self.previous.setEnabled(False); self.next.setEnabled(False); self.play.setEnabled(False); self.vinyl_deck.set_track("Onbekende artiest","-"); self.vinyl_deck.set_playing(False)

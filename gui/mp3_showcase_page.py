from pathlib import Path
import math

from PySide6.QtCore import Qt, QTimer, Signal, QPointF, QRectF
from PySide6.QtGui import QPixmap, QPainter, QPen, QBrush, QColor, QFont
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QListWidget, QListWidgetItem, QFrame, QSizePolicy,
)

from database.database import get_connection

try:
    from mutagen.id3 import ID3, ID3NoHeaderError
    MUTAGEN_AVAILABLE = True
except ImportError:
    MUTAGEN_AVAILABLE = False


class VinylDeckWidget(QWidget):
    """Visual turntable for the MP3 Showcase.

    This widget is deliberately self-contained: MP3 playback remains handled
    by the existing play_mp3 signal in MP3ShowcasePage.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.artist = "KID ACID"
        self.title = "VINYL PLAYER"
        self.playing = False
        self.angle = 0.0
        self.arm_angle = -38.0

        self.timer = QTimer(self)
        self.timer.setInterval(35)
        self.timer.timeout.connect(self._tick)

        self.setMinimumHeight(500)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

    def set_track(self, artist, title):
        self.artist = str(artist or "Onbekende artiest").strip() or "Onbekende artiest"
        self.title = str(title or "-").strip() or "-"
        self.update()

    def set_playing(self, playing):
        self.playing = bool(playing)
        if self.playing:
            self.timer.start()
        else:
            self.timer.stop()
        self.update()

    def _tick(self):
        self.angle = (self.angle + 4.5) % 360
        target = 18.0 if self.playing else -38.0
        self.arm_angle += (target - self.arm_angle) * 0.11
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setRenderHint(QPainter.RenderHint.TextAntialiasing)

        w = self.width()
        h = self.height()
        p.fillRect(self.rect(), QColor("#0b0b0f"))

        # Turntable body.
        deck = QRectF(10, 10, w - 20, h - 20)
        p.setBrush(QBrush(QColor("#202126")))
        p.setPen(QPen(QColor("#4a4a52"), 2))
        p.drawRoundedRect(deck, 18, 18)
        p.setBrush(QBrush(QColor("#151519")))
        p.setPen(QPen(QColor("#09090b"), 2))
        p.drawRoundedRect(QRectF(22, 22, w - 44, h - 44), 14, 14)

        # Brushed-metal inner panel.
        p.setBrush(QBrush(QColor("#19191d")))
        p.setPen(QPen(QColor("#303037"), 1))
        p.drawRoundedRect(QRectF(34, 34, w - 68, h - 68), 12, 12)

        # Platter.
        cx = w * 0.42
        cy = h * 0.42
        r = min(w * 0.31, h * 0.285)

        p.setBrush(QBrush(QColor(0, 0, 0, 150)))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(QPointF(cx + 7, cy + 9), r + 10, r + 10)
        p.setBrush(QBrush(QColor("#34343a")))
        p.setPen(QPen(QColor("#5b5b63"), 3))
        p.drawEllipse(QPointF(cx, cy), r + 6, r + 6)

        # Vinyl record.
        p.setBrush(QBrush(QColor("#050506")))
        p.setPen(QPen(QColor("#080809"), 1))
        p.drawEllipse(QPointF(cx, cy), r, r)

        p.save()
        p.translate(cx, cy)
        p.rotate(self.angle)
        p.setBrush(Qt.BrushStyle.NoBrush)
        for rr in (0.94, 0.89, 0.84, 0.79, 0.74, 0.68, 0.62, 0.56):
            p.setPen(QPen(QColor(40, 40, 44), 1))
            p.drawEllipse(QPointF(0, 0), r * rr, r * rr)
        # Moving vinyl reflection.
        p.setPen(QPen(QColor(115, 115, 122, 70), 2))
        p.drawArc(QRectF(-r * .9, -r * .9, r * 1.8, r * 1.8), 12 * 16, 48 * 16)
        p.restore()

        # Label.
        label_r = r * 0.29
        p.setBrush(QBrush(QColor("#b53e76")))
        p.setPen(QPen(QColor("#e07aa5"), 2))
        p.drawEllipse(QPointF(cx, cy), label_r, label_r)
        p.setPen(QPen(QColor("#f4bfd5"), 1))
        p.setFont(QFont("Segoe UI", max(7, int(label_r * .15)), QFont.Weight.Bold))
        p.drawText(
            QRectF(cx - label_r, cy - label_r * .32, label_r * 2, label_r * .64),
            Qt.AlignmentFlag.AlignCenter,
            "KID ACID",
        )
        p.setBrush(QBrush(QColor("#d7d7dc")))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(QPointF(cx, cy), 4.5, 4.5)

        # -------------------- REALISTIC TONEARM --------------------
        # Pivot sits to the right of the platter. The arm is drawn as a real
        # assembly: counterweight -> pivot -> arm tube -> headshell -> stylus.
        pivot = QPointF(w * 0.78, h * 0.225)
        arm_len = min(w * 0.40, h * 0.40)
        a = math.radians(self.arm_angle)
        direction = QPointF(math.cos(a), math.sin(a))
        end = QPointF(
            pivot.x() + direction.x() * arm_len,
            pivot.y() + direction.y() * arm_len,
        )

        # Counterweight behind the pivot.
        counter = QPointF(pivot.x() - 48, pivot.y() - 2)
        p.setPen(QPen(QColor("#111114"), 15, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        p.drawLine(pivot, counter)
        p.setPen(QPen(QColor("#85858d"), 10, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        p.drawLine(pivot, counter)
        p.setBrush(QBrush(QColor("#55555d")))
        p.setPen(QPen(QColor("#a0a0a7"), 2))
        p.drawEllipse(counter, 17, 17)
        p.setPen(QPen(QColor("#24242a"), 2))
        p.drawEllipse(counter, 9, 9)

        # Main arm tube with dark outline and metal highlight.
        p.setPen(QPen(QColor("#08080a"), 17, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        p.drawLine(pivot, end)
        p.setPen(QPen(QColor("#a8a8b0"), 11, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        p.drawLine(pivot, end)
        p.setPen(QPen(QColor("#dedee2"), 2, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        p.drawLine(pivot + QPointF(0, -2), end + QPointF(0, -2))

        # Headshell.
        shell = QPointF(
            end.x() + direction.x() * 20,
            end.y() + direction.y() * 20,
        )
        p.save()
        p.translate(shell)
        p.rotate(self.arm_angle)
        p.setBrush(QBrush(QColor("#25252a")))
        p.setPen(QPen(QColor("#b4b4bb"), 2))
        p.drawRoundedRect(QRectF(-5, -11, 43, 22), 4, 4)
        p.setBrush(QBrush(QColor("#111114")))
        p.setPen(QPen(QColor("#777780"), 1))
        p.drawRect(QRectF(18, -7, 18, 14))
        # Cartridge screws.
        p.setBrush(QBrush(QColor("#c0c0c4")))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(QPointF(22, -4), 1.5, 1.5)
        p.drawEllipse(QPointF(22, 4), 1.5, 1.5)
        p.restore()

        # Stylus and needle.
        stylus_top = QPointF(
            shell.x() + direction.x() * 31,
            shell.y() + direction.y() * 31,
        )
        stylus_tip = QPointF(stylus_top.x(), stylus_top.y() + 9)
        p.setPen(QPen(QColor("#d8d8dd"), 2))
        p.drawLine(stylus_top, stylus_tip)
        p.setBrush(QBrush(QColor("#f0f0f2")))
        p.drawEllipse(stylus_tip, 2.3, 2.3)

        # Pivot housing.
        p.setBrush(QBrush(QColor("#3a3a41")))
        p.setPen(QPen(QColor("#b3b3ba"), 2))
        p.drawEllipse(pivot, 20, 20)
        p.setBrush(QBrush(QColor("#111114")))
        p.setPen(QPen(QColor("#686870"), 2))
        p.drawEllipse(pivot, 8, 8)
        p.setBrush(QBrush(QColor("#c7c7cc")))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(pivot, 3, 3)

        # Small cue lever beside the arm.
        cue_x = w * 0.91
        cue_y = h * 0.31
        p.setPen(QPen(QColor("#77777f"), 4, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        p.drawLine(QPointF(cue_x, cue_y + 20), QPointF(cue_x, cue_y - 8))
        p.setBrush(QBrush(QColor("#4c4c53")))
        p.setPen(QPen(QColor("#8e8e95"), 1))
        p.drawRoundedRect(QRectF(cue_x - 7, cue_y - 13, 14, 8), 3, 3)

        # Status and track information.
        p.setPen(QPen(QColor("#d84b91")))
        p.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        p.drawText(QRectF(44, h - 132, w - 88, 20), Qt.AlignmentFlag.AlignCenter, "VINYL PLAYER")

        p.setPen(QPen(QColor("#f0f0f3")))
        p.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        p.drawText(QRectF(44, h - 110, w - 88, 22), Qt.AlignmentFlag.AlignCenter, self.artist)
        p.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        p.drawText(QRectF(38, h - 87, w - 76, 27), Qt.AlignmentFlag.AlignCenter, self.title)

        status_color = QColor("#77d999") if self.playing else QColor("#77777f")
        status = "●  PLAYING" if self.playing else "■  READY"
        p.setPen(QPen(status_color))
        p.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        p.drawText(QRectF(40, h - 58, w - 80, 18), Qt.AlignmentFlag.AlignCenter, status)

        # Strobe ticks at the front of the deck.
        for i in range(18):
            x = 48 + i * max(1, int((w - 96) / 18))
            p.setPen(QPen(QColor("#55555d"), 2))
            p.drawLine(x, h - 30, x + 7, h - 30)


class MP3ShowcasePage(QWidget):
    play_mp3 = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.items = []
        self.visible_items = []
        self.current_index = -1
        self.build_ui()
        self.load_files()

    def build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(28, 22, 28, 22)
        root.setSpacing(14)

        title = QLabel("MP3 SHOWCASE")
        title.setStyleSheet("font-size:26px;font-weight:900;color:#fff;")
        root.addWidget(title)

        search = QHBoxLayout()
        self.search = QLineEdit()
        self.search.setPlaceholderText("Zoek artiest, titel, album, genre, release of bestand...")
        search.addWidget(self.search, 1)
        self.refresh = QPushButton("VERVERS")
        search.addWidget(self.refresh)
        root.addLayout(search)

        self.status = QLabel("0 MP3's")
        self.status.setStyleSheet("color:#9b9ba6;")
        root.addWidget(self.status)

        body = QHBoxLayout()
        body.setSpacing(20)

        self.list = QListWidget()
        self.list.setMinimumWidth(360)
        self.list.currentRowChanged.connect(self.select_index)
        body.addWidget(self.list)

        card = QFrame()
        card.setStyleSheet("QFrame{background:#121219;border:1px solid #2a2532;border-radius:10px;}")
        cl = QVBoxLayout(card)
        cl.setContentsMargins(22, 22, 22, 22)
        cl.setSpacing(10)

        top = QHBoxLayout()
        top.setSpacing(22)

        self.cover = QLabel("NO COVER")
        self.cover.setFixedSize(340, 340)
        self.cover.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.cover.setStyleSheet("background:#0b0b0f;color:#666672;border:1px solid #302b39;border-radius:6px;")
        top.addWidget(self.cover, 0, Qt.AlignmentFlag.AlignTop)

        info = QVBoxLayout()
        info.setSpacing(8)
        self.artist_label = QLabel("-")
        self.artist_label.setStyleSheet("color:#d84b91;font-size:18px;font-weight:bold;")
        self.artist_label.setWordWrap(True)
        info.addWidget(self.artist_label)
        self.title_label = QLabel("-")
        self.title_label.setWordWrap(True)
        self.title_label.setStyleSheet("color:#fff;font-size:27px;font-weight:800;")
        info.addWidget(self.title_label)
        self.meta_label = QLabel("-")
        self.meta_label.setWordWrap(True)
        self.meta_label.setStyleSheet("color:#aaaab3;font-size:13px;")
        info.addWidget(self.meta_label)
        self.release_label = QLabel("Release: -")
        self.release_label.setWordWrap(True)
        self.release_label.setStyleSheet("color:#c5b6d4;font-size:14px;font-weight:bold;")
        info.addWidget(self.release_label)
        self.discogs_label = QLabel("Discogs: -")
        self.discogs_label.setWordWrap(True)
        self.discogs_label.setStyleSheet("color:#8f8798;font-size:12px;")
        info.addWidget(self.discogs_label)
        self.comment_label = QLabel("")
        self.comment_label.setWordWrap(True)
        self.comment_label.setStyleSheet("color:#777783;font-size:12px;")
        info.addWidget(self.comment_label)
        info.addStretch()
        top.addLayout(info, 1)
        cl.addLayout(top)

        # The visual deck is now part of the showcase card.
        self.vinyl_deck = VinylDeckWidget(self)
        self.vinyl_deck.set_track("Onbekende artiest", "-")
        self.vinyl_deck.set_playing(False)
        cl.addWidget(self.vinyl_deck, 1)

        controls = QHBoxLayout()
        self.previous = QPushButton("◀ VORIGE")
        self.play = QPushButton("▶ PLAY")
        self.next = QPushButton("VOLGENDE ▶")
        controls.addWidget(self.previous)
        controls.addWidget(self.play, 1)
        controls.addWidget(self.next)
        cl.addLayout(controls)

        tracks_title = QLabel("TRACKS")
        tracks_title.setStyleSheet("color:#777783;font-size:11px;font-weight:bold;letter-spacing:1.5px;")
        cl.addWidget(tracks_title)
        self.track_list = QListWidget()
        self.track_list.setMinimumHeight(190)
        self.track_list.itemDoubleClicked.connect(self.play_track_item)
        cl.addWidget(self.track_list, 1)

        body.addWidget(card, 1)
        root.addLayout(body, 1)

        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.setInterval(180)
        self.timer.timeout.connect(self.populate_list)
        self.search.textChanged.connect(lambda _: self.timer.start())
        self.refresh.clicked.connect(self.load_files)
        self.previous.clicked.connect(self.previous_track)
        self.next.clicked.connect(self.next_track)
        self.play.clicked.connect(self.play_current)

        self.setStyleSheet("""
            QWidget{background:#0b0b0f;color:#f2f2f5;}
            QLineEdit,QPushButton,QListWidget{background:#18181f;color:#fff;border:1px solid #30303a;border-radius:6px;padding:8px 10px;}
            QPushButton:hover{border-color:#d84b91;background:#24242c;}
            QListWidget{background:#0f0f14;}
            QListWidget::item{padding:8px;border-bottom:1px solid #24242d;}
            QListWidget::item:selected{background:#271522;border:1px solid #5d2947;}
        """)

    def load_files(self):
        conn = get_connection()
        try:
            rows = conn.execute("""
                SELECT m.path,m.artist,m.title,m.album,m.year,m.bpm,m.genre,
                       COALESCE(r.artist,''),COALESCE(r.title,''),COALESCE(r.discogs,''),COALESCE(r.cover,'')
                FROM mp3_files m
                LEFT JOIN track_mp3 tm ON tm.mp3_id=m.id
                LEFT JOIN tracks t ON t.id=tm.track_id
                LEFT JOIN releases r ON r.id=t.release_id
                ORDER BY m.artist COLLATE NOCASE,m.title COLLATE NOCASE,m.path COLLATE NOCASE
            """).fetchall()
        finally:
            conn.close()

        unique = {}
        for row in rows:
            path = str(row[0] or "")
            if path not in unique:
                unique[path] = tuple(row)
            elif not unique[path][9] and row[9]:
                unique[path] = tuple(row)
        self.items = list(unique.values())
        self.populate_list()

    def populate_list(self):
        q = self.search.text().strip().casefold()
        self.visible_items = [row for row in self.items if not q or q in " ".join(str(x or "") for x in row).casefold()]
        self.list.blockSignals(True)
        self.list.clear()
        for row in self.visible_items:
            name = Path(str(row[0])).name
            artist = str(row[1] or "").strip()
            title = str(row[2] or "").strip()
            text = f"{artist} — {title}".strip(" —") if artist or title else name
            item = QListWidgetItem(text)
            item.setToolTip(str(row[0]))
            self.list.addItem(item)
        self.list.blockSignals(False)
        self.status.setText(f"{len(self.visible_items)} van {len(self.items)} MP3's")
        if self.visible_items:
            self.list.setCurrentRow(0)
        else:
            self.current_index = -1
            self.clear_showcase()

    def select_index(self, index):
        self.current_index = index
        if 0 <= index < len(self.visible_items):
            self.show_item(self.visible_items[index])

    def show_item(self, row):
        path,artist,title,album,year,bpm,genre,release_artist,release_title,discogs_id,release_cover = row
        artist = str(artist or "").strip() or "Onbekende artiest"
        title = str(title or "").strip() or Path(str(path)).stem
        album = str(album or "").strip()
        self.artist_label.setText(artist)
        self.title_label.setText(title)
        meta=[]
        if album: meta.append(f"Album: {album}")
        if year: meta.append(f"Jaar: {year}")
        if genre: meta.append(f"Genre: {genre}")
        if bpm: meta.append(f"BPM: {bpm}")
        self.meta_label.setText("  •  ".join(meta) if meta else "Geen aanvullende metadata")
        if release_title:
            release_text=str(release_title)
            if release_artist: release_text=f"{release_artist} — {release_text}"
            self.release_label.setText(f"Release: {release_text}")
        else:
            self.release_label.setText("Release: geen gekoppelde release")
        self.discogs_label.setText(f"Discogs release ID: {discogs_id}" if discogs_id else "Discogs: geen releasekoppeling")
        self.vinyl_deck.set_track(artist,title)
        self.vinyl_deck.set_playing(False)
        self.load_cover(str(path),str(release_cover or ""))
        self.load_tracklist(str(path))
        self.load_comment(str(path))
        self.previous.setEnabled(self.current_index > 0)
        self.next.setEnabled(self.current_index + 1 < len(self.visible_items))
        self.play.setEnabled(True)

    def load_cover(self, path, release_cover):
        if MUTAGEN_AVAILABLE and Path(path).exists():
            try:
                tags=ID3(path)
                pictures=tags.getall("APIC")
                if pictures:
                    pixmap=QPixmap()
                    if pixmap.loadFromData(pictures[0].data):
                        self.cover.setPixmap(pixmap.scaled(340,340,Qt.AspectRatioMode.KeepAspectRatio,Qt.TransformationMode.SmoothTransformation))
                        self.cover.setText("")
                        return
            except Exception:
                pass
        if release_cover and Path(release_cover).exists():
            pixmap=QPixmap(release_cover)
            if not pixmap.isNull():
                self.cover.setPixmap(pixmap.scaled(340,340,Qt.AspectRatioMode.KeepAspectRatio,Qt.TransformationMode.SmoothTransformation))
                self.cover.setText("")
                return
        self.cover.clear(); self.cover.setText("NO COVER")

    def load_comment(self, path):
        self.comment_label.clear()
        if not MUTAGEN_AVAILABLE or not Path(path).exists(): return
        try:
            tags=ID3(path)
            values=[]
            for frame in tags.getall("COMM"):
                values.extend(str(value).strip() for value in frame.text if str(value).strip())
            if values: self.comment_label.setText("Comment: " + " • ".join(dict.fromkeys(values)))
        except Exception:
            pass

    def load_tracklist(self, current_path):
        self.track_list.clear()
        try:
            conn=get_connection()
            try:
                linked=conn.execute("""
                    SELECT t.position,t.title,t.duration,t.bpm,m.path
                    FROM track_mp3 tm JOIN tracks t ON t.id=tm.track_id JOIN mp3_files m ON m.id=tm.mp3_id
                    WHERE m.path=? ORDER BY t.position COLLATE NOCASE
                """,(current_path,)).fetchall()
            finally: conn.close()
        except Exception:
            linked=[]
        if not linked:
            item=QListWidgetItem("Geen gekoppelde VinylVault-track voor dit bestand")
            item.setForeground(Qt.GlobalColor.gray); self.track_list.addItem(item); return
        for position,title,duration,bpm,path in linked:
            text=f"{position or ''}  {title or ''}".strip()
            extras=[]
            if duration: extras.append(str(duration))
            if bpm: extras.append(f"{bpm} BPM")
            if extras: text += "  •  " + "  •  ".join(extras)
            item=QListWidgetItem(text)
            item.setData(Qt.ItemDataRole.UserRole,str(path))
            self.track_list.addItem(item)

    def play_current(self):
        if 0 <= self.current_index < len(self.visible_items):
            path=str(self.visible_items[self.current_index][0] or "")
            if Path(path).exists():
                self.vinyl_deck.set_playing(True)
                self.play_mp3.emit(path)

    def play_track_item(self, item):
        path=item.data(Qt.ItemDataRole.UserRole)
        if path and Path(str(path)).exists():
            self.vinyl_deck.set_track(self.artist_label.text(),self.title_label.text())
            self.vinyl_deck.set_playing(True)
            self.play_mp3.emit(str(path))
        else:
            self.play_current()

    def previous_track(self):
        if self.current_index > 0:
            self.list.setCurrentRow(self.current_index-1)
            self.play_current()

    def next_track(self):
        if self.current_index + 1 < len(self.visible_items):
            self.list.setCurrentRow(self.current_index+1)
            self.play_current()

    def clear_showcase(self):
        self.cover.clear(); self.cover.setText("NO COVER")
        self.artist_label.setText("-"); self.title_label.setText("-"); self.meta_label.setText("-")
        self.release_label.setText("Release: -"); self.discogs_label.setText("Discogs: -"); self.comment_label.clear()
        self.track_list.clear(); self.previous.setEnabled(False); self.next.setEnabled(False); self.play.setEnabled(False)
        self.vinyl_deck.set_track("Onbekende artiest","-"); self.vinyl_deck.set_playing(False)

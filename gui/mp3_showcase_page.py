from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QListWidget,
    QListWidgetItem,
    QFrame,
    QScrollArea,
    QSizePolicy,
)

from database.database import get_connection

try:
    from mutagen.id3 import ID3
    MUTAGEN_AVAILABLE = True
except ImportError:
    MUTAGEN_AVAILABLE = False


def ensure_mp3_discogs_columns():
    conn = get_connection()
    try:
        cols = {
            row[1]
            for row in conn.execute(
                "PRAGMA table_info(mp3_files)"
            ).fetchall()
        }
        for name, kind in (
            ("discogs_id", "TEXT"),
            ("discogs_link", "TEXT"),
            ("cover", "TEXT"),
        ):
            if name not in cols:
                conn.execute(
                    f"ALTER TABLE mp3_files ADD COLUMN {name} {kind}"
                )
        conn.commit()
    finally:
        conn.close()


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

        self.record = QLabel("VINYL")
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
        self.record.setText("VINYL" if self.rotation % 24 else "VINYL")


class VinylDeckWidget(QWidget):
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
        p.drawText(QRectF(20,24,w-40,28),Qt.AlignmentFlag.AlignCenter,"KID ACID ÔÇó VINYL DECK")
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
        p.setPen(col); p.setFont(QFont('Segoe UI',10,QFont.Weight.Bold)); p.drawText(QRectF(58,sy-4,160,24),Qt.AlignmentFlag.AlignLeft,'')
        for i in range(12):
            bh=7+i*2 if self.playing else 4; alpha=220 if self.playing and i<10 else 35; c=QColor(216,75,145,alpha) if i<9 else QColor(240,170,90,alpha)
            p.setPen(Qt.PenStyle.NoPen); p.setBrush(QBrush(c)); p.drawRoundedRect(QRectF(235+i*18,sy+15-bh,12,bh),3,3)
        p.setPen(pink); p.setFont(QFont('Segoe UI',13,QFont.Weight.Bold)); p.drawText(QRectF(25,h-125,w-50,24),Qt.AlignmentFlag.AlignCenter,self.artist)
        p.setPen(QColor('#fff')); p.setFont(QFont('Segoe UI',19,QFont.Weight.Bold)); p.drawText(QRectF(25,h-94,w-50,30),Qt.AlignmentFlag.AlignCenter,self.title)
        p.setPen(QColor('#78727c')); p.setFont(QFont('Segoe UI',9)); p.drawText(QRectF(25,h-55,w-50,20),Qt.AlignmentFlag.AlignCenter,"KID ACID'S VINYL VAULT")
        p.end()


class MP3ShowcasePage(QWidget):
    play_mp3 = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.items = []
        self.visible_items = []
        self.current_index = -1

        ensure_mp3_discogs_columns()
        self.build_ui()
        self.load_files()

    def build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(28, 22, 28, 22)
        root.setSpacing(14)

        title = QLabel("MP3 SHOWCASE")
        title.setStyleSheet(
            "font-size:26px;font-weight:900;color:#fff;"
        )
        root.addWidget(title)

        search = QHBoxLayout()
        search.setSpacing(10)

        self.search = QLineEdit()
        self.search.setPlaceholderText(
            "Zoek artiest, titel, album, genre, release of bestand..."
        )
        search.addWidget(self.search, 1)

        self.refresh = QPushButton("VERVERS")
        search.addWidget(self.refresh)
        root.addLayout(search)

        self.status = QLabel("0 MP3's")
        self.status.setStyleSheet("color:#9b9ba6;")
        root.addWidget(self.status)

        # The important part of this layout: the whole showcase content has
        # a stable working width and lives inside a scroll area. When the main
        # window is restored to a small size, Qt scrolls instead of squeezing
        # the cover, metadata and controls into each other.
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(False)
        self.scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded
        )
        self.scroll.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded
        )

        content = QWidget()
        self.content = content
        content.setMinimumWidth(1700)
        content.setMinimumHeight(760)

        body = QHBoxLayout(content)
        self.body = body
        body.setContentsMargins(0, 0, 0, 0)
        body.setSpacing(20)

        self.list = QListWidget()
        self.list.setMinimumWidth(360)
        self.list.setMaximumWidth(380)
        self.list.currentRowChanged.connect(self.select_index)
        body.addWidget(self.list)

        card = QFrame()
        self.detail_card = card
        card.setMinimumWidth(700)
        card.setStyleSheet(
            "QFrame{background:#121219;"
            "border:1px solid #2a2532;border-radius:10px;}"
        )
        cl = QVBoxLayout(card)
        cl.setContentsMargins(22, 22, 22, 22)
        cl.setSpacing(12)

        # Cover + information are always a single horizontal block.
        # Because content has a stable width, this block cannot collapse over
        # the controls when the main window becomes narrow.
        top = QHBoxLayout()
        self.top = top
        top.setSpacing(22)

        self.cover = QLabel("NO COVER")
        self.cover.setFixedSize(300, 300)
        self.cover.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.cover.setStyleSheet(
            "background:#0b0b0f;color:#666672;"
            "border:1px solid #302b39;border-radius:6px;"
        )
        top.addWidget(
            self.cover,
            0,
            Qt.AlignmentFlag.AlignTop,
        )

        info = QVBoxLayout()
        self.info_layout = info
        info.setSpacing(8)

        self.artist_label = QLabel("-")
        self.artist_label.setStyleSheet(
            "color:#d84b91;font-size:18px;font-weight:bold;"
        )
        self.artist_label.setWordWrap(True)
        info.addWidget(self.artist_label)

        self.title_label = QLabel("-")
        self.title_label.setStyleSheet(
            "color:#fff;font-size:27px;font-weight:800;"
        )
        self.title_label.setWordWrap(True)
        info.addWidget(self.title_label)

        self.meta_label = QLabel("-")
        self.meta_label.setStyleSheet(
            "color:#aaaab3;font-size:13px;"
        )
        self.meta_label.setWordWrap(True)
        info.addWidget(self.meta_label)

        self.release_label = QLabel("Release: -")
        self.release_label.setStyleSheet(
            "color:#c5b6d4;font-size:14px;font-weight:bold;"
        )
        self.release_label.setWordWrap(True)
        info.addWidget(self.release_label)

        self.metadata_status_label = QLabel(
            "Metadata: NIET GEDAAN"
        )
        self.metadata_status_label.setStyleSheet(
            "color:#aaaab3;font-size:13px;font-weight:900;"
        )
        info.addWidget(self.metadata_status_label)

        self.discogs_label = QLabel("Discogs: -")
        self.discogs_label.setStyleSheet(
            "color:#8f8798;font-size:12px;"
        )
        self.discogs_label.setWordWrap(True)
        info.addWidget(self.discogs_label)

        self.comment_label = QLabel("")
        self.comment_label.setStyleSheet(
            "color:#777783;font-size:12px;"
        )
        self.comment_label.setWordWrap(True)
        info.addWidget(self.comment_label)
        info.addStretch()

        top.addLayout(info, 1)
        cl.addLayout(top)

        # Controls are completely outside the cover/info layout.
        # They can therefore never be painted on top of the cover.
        controls = QHBoxLayout()
        self.controls_layout = controls
        controls.setSpacing(10)

        self.previous = QPushButton("VORIGE")
        self.play = QPushButton("PLAY")
        self.next = QPushButton("VOLGENDE")

        controls.addWidget(self.previous)
        controls.addWidget(self.play, 1)
        controls.addWidget(self.next)
        cl.addLayout(controls)

        tracks_title = QLabel("TRACKS")
        tracks_title.setStyleSheet(
            "color:#777783;font-size:11px;font-weight:bold;"
            "letter-spacing:1.5px;"
        )
        cl.addWidget(tracks_title)

        self.track_list = QListWidget()
        self.track_list.setMinimumHeight(190)
        self.track_list.itemDoubleClicked.connect(
            self.play_track_item
        )
        cl.addWidget(self.track_list, 1)

        body.addWidget(card, 1)
        self.vinyl_deck = VinylDeckWidget(self)
        self.vinyl_deck.set_track("Onbekende artiest", "-")
        self.vinyl_deck.set_playing(False)
        body.addWidget(self.vinyl_deck, 1)
        body.setStretch(0, 1)
        body.setStretch(1, 1)
        self.scroll.setWidget(content)
        root.addWidget(self.scroll, 1)

        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.setInterval(180)
        self.timer.timeout.connect(self.populate_list)
        self.search.textChanged.connect(
            lambda _text: self.timer.start()
        )

        self.refresh.clicked.connect(self.load_files)
        self.previous.clicked.connect(self.previous_track)
        self.next.clicked.connect(self.next_track)
        self.play.clicked.connect(self.play_current)

        self.setStyleSheet(
            """
            QWidget{background:#0b0b0f;color:#f2f2f5;}
            QLineEdit,QPushButton,QListWidget{
                background:#18181f;
                color:#fff;
                border:1px solid #30303a;
                border-radius:6px;
                padding:8px 10px;
            }
            QPushButton:hover{
                border-color:#d84b91;
                background:#24242c;
            }
            QListWidget{background:#0f0f14;}
            QListWidget::item{
                padding:8px;
                border-bottom:1px solid #24242d;
            }
            QListWidget::item:selected{
                background:#271522;
                border:1px solid #5d2947;
            }
            QScrollArea{
                background:#0b0b0f;
                border:0;
            }
            """
        )

    def load_files(self):
        conn = get_connection()
        try:
            rows = conn.execute(
                """
                SELECT
                    m.path,
                    m.artist,
                    m.title,
                    m.album,
                    m.year,
                    m.bpm,
                    m.genre,
                    COALESCE(m.metadata_checked, 0),
                    COALESCE(r.artist, ''),
                    COALESCE(r.title, ''),
                    COALESCE(m.discogs_id, r.discogs, ''),
                    COALESCE(m.cover, r.cover, ''),
                    COALESCE(m.discogs_link, ''),
                    m.duration
                FROM mp3_files m
                LEFT JOIN track_mp3 tm ON tm.mp3_id = m.id
                LEFT JOIN tracks t ON t.id = tm.track_id
                LEFT JOIN releases r ON r.id = t.release_id
                ORDER BY m.artist COLLATE NOCASE,
                         m.title COLLATE NOCASE,
                         m.path COLLATE NOCASE
                """
            ).fetchall()
        finally:
            conn.close()

        unique = {}
        for row in rows:
            path = str(row[0] or "")
            if path not in unique:
                unique[path] = tuple(row)
            else:
                current = unique[path]
                if not current[10] and row[10]:
                    unique[path] = tuple(row)

        self.items = list(unique.values())
        self.populate_list()

    def populate_list(self):
        q = self.search.text().strip().casefold()
        self.visible_items = [
            row
            for row in self.items
            if (
                not q
                or q in " ".join(
                    str(x or "") for x in row
                ).casefold()
            )
        ]

        self.list.blockSignals(True)
        self.list.clear()

        for row in self.visible_items:
            name = Path(str(row[0])).name
            artist = str(row[1] or "").strip()
            title = str(row[2] or "").strip()
            text = (
                f"{artist} - {title}".strip(" -")
                if artist or title
                else name
            )
            item = QListWidgetItem(text)
            item.setToolTip(str(row[0]))
            self.list.addItem(item)

        self.list.blockSignals(False)
        self.status.setText(
            f"{len(self.visible_items)} van "
            f"{len(self.items)} MP3's"
        )

        if self.visible_items:
            self.list.setCurrentRow(0)
        else:
            self.current_index = -1
            self.clear_showcase()

    def select_index(self, index):
        self.current_index = index
        if 0 <= index < len(self.visible_items):
            self.show_item(self.visible_items[index])
            if hasattr(self, 'vinyl_deck'):
                row = self.visible_items[index]
                self.vinyl_deck.set_track(row[1], row[2])
                self.vinyl_deck.set_playing(False)

    def show_item(self, row):
        (
            path,
            artist,
            title,
            album,
            year,
            bpm,
            genre,
            metadata_checked,
            release_artist,
            release_title,
            discogs_id,
            release_cover,
            discogs_link,
            mp3_duration,
        ) = row

        artist = str(artist or "").strip()
        title = str(title or "").strip()
        album = str(album or "").strip()

        self.artist_label.setText(
            artist or "Onbekende artiest"
        )
        self.title_label.setText(
            title or Path(str(path)).stem
        )

        meta = []
        if album:
            meta.append(f"Album: {album}")
        if year:
            meta.append(f"Jaar: {year}")
        if genre:
            meta.append(f"Genre: {genre}")
        if bpm:
            meta.append(f"BPM: {bpm}")
        if mp3_duration:
            try:
                seconds = int(round(float(mp3_duration)))
                meta.append(
                    f"Duur: {seconds // 60}:"
                    f"{seconds % 60:02d}"
                )
            except (TypeError, ValueError):
                pass

        self.meta_label.setText(
            "  -  ".join(meta)
            if meta
            else "Geen aanvullende metadata"
        )

        if release_title:
            release_text = str(release_title)
            if release_artist:
                release_text = (
                    f"{release_artist} - {release_text}"
                )
            self.release_label.setText(
                f"Release: {release_text}"
            )
        else:
            self.release_label.setText(
                "Release: geen gekoppelde release"
            )

        self.metadata_status_label.setText(
            "Metadata: KLAAR"
            if metadata_checked
            else "Metadata: NIET GEDAAN"
        )

        if discogs_id:
            text = f"Discogs release ID: {discogs_id}"
            if discogs_link:
                text += f"\n{discogs_link}"
            self.discogs_label.setText(text)
        else:
            self.discogs_label.setText(
                "Discogs: geen releasekoppeling"
            )

        self.load_cover(
            str(path),
            str(release_cover or "")
        )
        self.load_tracklist(str(path))
        self.load_comment(str(path))

        self.previous.setEnabled(
            self.current_index > 0
        )
        self.next.setEnabled(
            self.current_index + 1
            < len(self.visible_items)
        )
        self.play.setEnabled(True)

    def load_cover(self, path, release_cover):
        if MUTAGEN_AVAILABLE and Path(path).exists():
            try:
                tags = ID3(path)
                pictures = tags.getall("APIC")
                if pictures:
                    pixmap = QPixmap()
                    if pixmap.loadFromData(
                        pictures[0].data
                    ):
                        self.cover.setPixmap(
                            pixmap.scaled(
                                300,
                                300,
                                Qt.AspectRatioMode.KeepAspectRatio,
                                Qt.TransformationMode.SmoothTransformation,
                            )
                        )
                        self.cover.setText("")
                        return
            except Exception:
                pass

        if release_cover and Path(release_cover).exists():
            pixmap = QPixmap(release_cover)
            if not pixmap.isNull():
                self.cover.setPixmap(
                    pixmap.scaled(
                        300,
                        300,
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation,
                    )
                )
                self.cover.setText("")
                return

        self.cover.clear()
        self.cover.setText("NO COVER")

    def load_comment(self, path):
        self.comment_label.clear()
        if not MUTAGEN_AVAILABLE or not Path(path).exists():
            return

        try:
            tags = ID3(path)
            comments = tags.getall("COMM")
            values = []
            for frame in comments:
                values.extend(
                    str(value).strip()
                    for value in frame.text
                    if str(value).strip()
                )
            if values:
                self.comment_label.setText(
                    "Comment: "
                    + " - ".join(dict.fromkeys(values))
                )
        except Exception:
            pass

    def load_tracklist(self, current_path):
        self.track_list.clear()

        try:
            conn = get_connection()
            try:
                linked = conn.execute(
                    """
                    SELECT
                        t.position,
                        t.title,
                        t.duration,
                        t.bpm,
                        m.path
                    FROM track_mp3 tm
                    JOIN tracks t ON t.id = tm.track_id
                    JOIN mp3_files m ON m.id = tm.mp3_id
                    WHERE m.path = ?
                    ORDER BY t.position COLLATE NOCASE
                    """,
                    (current_path,),
                ).fetchall()
            finally:
                conn.close()
        except Exception:
            linked = []

        if not linked:
            item = QListWidgetItem(
                "Geen gekoppelde VinylVault-track "
                "voor dit bestand"
            )
            item.setForeground(Qt.GlobalColor.gray)
            self.track_list.addItem(item)
            return

        for position, title, duration, bpm, path in linked:
            text = (
                f"{position or ''}  {title or ''}"
            ).strip()
            extras = []
            if duration:
                extras.append(str(duration))
            if bpm:
                extras.append(f"{bpm} BPM")
            if extras:
                text += "  -  " + "  -  ".join(extras)

            item = QListWidgetItem(text)
            item.setData(
                Qt.ItemDataRole.UserRole,
                str(path),
            )
            self.track_list.addItem(item)

    def _play_with_deck(self):
        if 0 <= self.current_index < len(self.visible_items):
            row = self.visible_items[self.current_index]
            path = str(row[0] or '')
            if Path(path).exists():
                artist = str(row[1] or '').strip() or 'Onbekende artiest'
                title = str(row[2] or '').strip() or Path(path).stem
                self.vinyl_deck.set_track(artist, title)
                self.vinyl_deck.set_playing(True)
                self.play_mp3.emit(path)

    def play_current(self):
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

    def play_track_item(self, item):
        path = item.data(
            Qt.ItemDataRole.UserRole
        )
        if path and Path(str(path)).exists():
            self.play_mp3.emit(str(path))
        else:
            self.play_current()

    def previous_track(self):
        if self.current_index > 0:
            self.list.setCurrentRow(
                self.current_index - 1
            )
            self.play_current()

    def next_track(self):
        if (
            self.current_index + 1
            < len(self.visible_items)
        ):
            self.list.setCurrentRow(
                self.current_index + 1
            )
            self.play_current()

    def clear_showcase(self):
        self.cover.clear()
        self.cover.setText("NO COVER")
        self.artist_label.setText("-")
        self.title_label.setText("-")
        self.meta_label.setText("-")
        self.release_label.setText("Release: -")
        self.metadata_status_label.setText(
            "Metadata: NIET GEDAAN"
        )
        self.discogs_label.setText("Discogs: -")
        self.comment_label.clear()
        self.track_list.clear()
        self.previous.setEnabled(False)
        self.next.setEnabled(False)
        self.play.setEnabled(False)












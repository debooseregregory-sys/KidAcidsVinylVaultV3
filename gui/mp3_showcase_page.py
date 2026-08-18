from __future__ import annotations

from pathlib import Path
from math import cos, sin, radians

from PySide6.QtCore import Qt, QTimer, Signal, QPointF, QRectF
from PySide6.QtGui import QPixmap, QPainter, QPen, QBrush, QColor, QFont
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QListWidget, QListWidgetItem, QTableWidget, QTableWidgetItem,
    QHeaderView, QFrame, QScrollArea, QSizePolicy,
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
        cols = {row[1] for row in conn.execute("PRAGMA table_info(mp3_files)").fetchall()}
        for name, kind in (("discogs_id", "TEXT"), ("discogs_link", "TEXT"), ("cover", "TEXT")):
            if name not in cols:
                conn.execute(f"ALTER TABLE mp3_files ADD COLUMN {name} {kind}")
        conn.commit()
    finally:
        conn.close()


class VinylDeckWidget(QWidget):
    """Large visual turntable used by the MP3 Showcase."""

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
        self.timer.setInterval(28)
        self.timer.timeout.connect(self._tick)
        self.setStyleSheet("background:#111117;border:1px solid #39313d;border-radius:18px;")

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
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = float(self.width()), float(self.height())
        p.fillRect(self.rect(), QColor("#111117"))
        p.setPen(QPen(QColor("#4a414d"), 1))
        p.setBrush(QBrush(QColor("#191920")))
        p.drawRoundedRect(QRectF(12, 12, w - 24, h - 24), 18, 18)

        p.setPen(QColor("#d84b91")); p.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        p.drawText(QRectF(28, 26, 250, 24), Qt.AlignmentFlag.AlignLeft, "KID ACID'S VINYL VAULT")

        size = max(300, min(w - 180, h - 260))
        r = size / 2
        cx, cy = w * .43, 92 + r
        p.setPen(QPen(QColor("#5c5660"), 2)); p.setBrush(QBrush(QColor("#29272e")))
        p.drawEllipse(QPointF(cx, cy), r + 18, r + 18)
        p.setPen(QPen(QColor("#35323a"), 2)); p.setBrush(QBrush(QColor("#0d0d11")))
        p.drawEllipse(QPointF(cx, cy), r + 7, r + 7)
        p.setPen(QPen(QColor("#26242b"), 1)); p.setBrush(QBrush(QColor("#050508")))
        p.drawEllipse(QPointF(cx, cy), r, r)
        p.save(); p.translate(cx, cy); p.rotate(self.angle)
        for f in (.95,.90,.85,.80,.75,.70,.65,.60,.55,.50):
            rr = r * f; p.setPen(QPen(QColor("#16161c"), 1)); p.drawEllipse(QPointF(0,0), rr, rr)
        p.setPen(QPen(QColor(216,75,145,120), 3)); p.drawArc(QRectF(-r*.82,-r*.82,r*1.64,r*1.64),20*16,75*16)
        p.restore()
        lr = min(68, r * .25)
        p.setPen(QPen(QColor("#ee9fc2"), 2)); p.setBrush(QBrush(QColor("#68183f")))
        p.drawEllipse(QPointF(cx, cy), lr, lr)
        p.setPen(QColor("#f7e6ee")); p.setFont(QFont("Segoe UI", max(10, int(lr/3.6)), QFont.Weight.Bold))
        p.drawText(QRectF(cx-lr, cy-10, lr*2, 20), Qt.AlignmentFlag.AlignCenter, "KID ACID")
        p.setPen(QPen(QColor("#c8c2ca"), 1)); p.setBrush(QBrush(QColor("#d1cbd1")))
        p.drawEllipse(QPointF(cx, cy), 5, 5)

        # Realistic tonearm: pivot at upper right, stylus reaches the outer groove area.
        pivot = QPointF(w * .79, h * .235)
        p.setPen(QPen(QColor("#09090b"), 5)); p.setBrush(QBrush(QColor("#35333a")))
        p.drawEllipse(pivot, 24, 24)
        a = radians(self.arm_angle)
        reach = r * .90
        elbow = QPointF(pivot.x() - cos(a)*reach*.42, pivot.y() + sin(a)*reach*.42)
        bend = QPointF(elbow.x()-sin(a)*24, elbow.y()-cos(a)*24)
        head = QPointF(cx + r*.78, cy - r*.05) if self.playing else QPointF(cx + r*.72, cy - r*.40)
        p.setPen(QPen(QColor("#b9b2bc"), 8, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        p.drawLine(pivot, elbow); p.drawLine(elbow, bend); p.drawLine(bend, head)
        p.setPen(QPen(QColor("#eee"), 2)); p.drawLine(head, QPointF(head.x()-4, head.y()+22))
        p.setPen(QPen(QColor("#29272d"), 2)); p.setBrush(QBrush(QColor("#d7d2d7")))
        p.drawRoundedRect(QRectF(head.x()-28, head.y()+2, 42, 18), 4, 4)

        # Pitch control: visually separate from the platter.
        px, py = w*.82, h*.60
        p.setPen(QPen(QColor("#57515b"), 2)); p.setBrush(QBrush(QColor("#242229")))
        p.drawRoundedRect(QRectF(px-20, py-95, 40, 190), 10, 10)
        p.setPen(QColor("#aaa3ad")); p.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        p.drawText(QRectF(px-55, py-125, 110, 20), Qt.AlignmentFlag.AlignCenter, "PITCH")
        knob_y = py - 10 - self.pitch * 2
        p.setBrush(QBrush(QColor("#d84b91"))); p.setPen(QPen(QColor("#f0bfd5"), 1))
        p.drawRoundedRect(QRectF(px-13, knob_y-8, 26, 16), 4, 4)
        p.setPen(QColor("#77727c")); p.drawText(QRectF(px-55, py+105, 110, 20), Qt.AlignmentFlag.AlignCenter, f"{self.pitch:+.1f}%")

        p.setPen(QColor("#d84b91")); p.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        p.drawText(QRectF(25, h-112, w-50, 24), Qt.AlignmentFlag.AlignCenter, self.artist)
        p.setPen(QColor("#fff")); p.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        p.drawText(QRectF(25, h-82, w-50, 28), Qt.AlignmentFlag.AlignCenter, self.title)
        p.setPen(QColor("#78727c")); p.setFont(QFont("Segoe UI", 9))
        p.drawText(QRectF(25, h-50, w-50, 20), Qt.AlignmentFlag.AlignCenter, "KID ACID'S VINYL VAULT")
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
        root = QVBoxLayout(self); root.setSpacing(12)
        title = QLabel("MP3 SHOWCASE"); title.setStyleSheet("font-size:26px;font-weight:900;color:#fff;")
        root.addWidget(title)
        search = QHBoxLayout()
        self.search = QLineEdit(); self.search.setPlaceholderText("Zoek artiest, titel, album, genre, release of bestand...")
        search.addWidget(self.search); root.addLayout(search)
        self.status = QLabel("Laden..."); self.status.setStyleSheet("color:#9b9ba6;"); root.addWidget(self.status)

        body = QHBoxLayout(); body.setContentsMargins(0,0,0,0); body.setSpacing(14)

        self.list = QTableWidget(0, 2)
        self.list.setHorizontalHeaderLabels(["ARTIEST", "TRACK"])
        self.list.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.list.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.list.setAlternatingRowColors(True)
        self.list.setMinimumWidth(520)
        self.list.setMaximumWidth(620)
        header = self.list.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.list.verticalHeader().setDefaultSectionSize(34)
        self.list.itemSelectionChanged.connect(self._table_selection_changed)
        body.addWidget(self.list, 4)

        self.vinyl_deck = VinylDeckWidget(self); self.vinyl_deck.set_track("Onbekende artiest", "-")
        body.addWidget(self.vinyl_deck, 6)

        right = QFrame(); right.setMinimumWidth(320); right.setMaximumWidth(430)
        cl = QVBoxLayout(right); cl.setContentsMargins(14,14,14,14); cl.setSpacing(10)
        self.cover = QLabel(); self.cover.setAlignment(Qt.AlignmentFlag.AlignCenter); self.cover.setMinimumHeight(170); cl.addWidget(self.cover)
        self.info = QLabel("Geen track geselecteerd"); self.info.setWordWrap(True); cl.addWidget(self.info)
        tracks_title = QLabel("VINYLVAULT TRACKS"); tracks_title.setStyleSheet("font-weight:900;color:#d84b91;"); cl.addWidget(tracks_title)
        self.track_list = QListWidget(); self.track_list.setMinimumHeight(150); self.track_list.itemDoubleClicked.connect(self.play_track_item); cl.addWidget(self.track_list, 1)
        controls = QHBoxLayout()
        self.previous = QPushButton("VORIGE"); self.play = QPushButton("PLAY"); self.next = QPushButton("VOLGENDE"); self.power = QPushButton("POWER")
        controls.addWidget(self.previous); controls.addWidget(self.play,1); controls.addWidget(self.next); controls.addWidget(self.power); cl.addLayout(controls)
        body.addWidget(right, 3)
        root.addLayout(body, 1)

        self.search.textChanged.connect(self.populate_list)
        self.previous.clicked.connect(self.previous_track); self.next.clicked.connect(self.next_track); self.play.clicked.connect(self.play_current)
        self.power.clicked.connect(lambda: self.vinyl_deck.set_playing(False))

        self.setStyleSheet("""
        QWidget{background:#0b0b0f;color:#f2f2f5;}
        QLineEdit,QPushButton,QTableWidget,QListWidget{background:#18181f;color:#fff;border:1px solid #30303a;border-radius:6px;padding:7px;}
        QTableWidget{background:#0f0f14;gridline-color:#24242d;}
        QTableWidget::item{padding:7px;border-bottom:1px solid #24242d;}
        QTableWidget::item:selected{background:#271522;color:#fff;}
        QListWidget{background:#0f0f14;}
        QListWidget::item{padding:8px;border-bottom:1px solid #24242d;}
        QPushButton:hover{border-color:#d84b91;background:#24242c;}
        """)

    def load_files(self):
        conn = get_connection()
        try:
            cols = {r[1] for r in conn.execute("PRAGMA table_info(mp3_files)").fetchall()}
            optional = [c for c in ("release_id", "discogs_id", "discogs_link", "cover") if c in cols]
            select = "path, artist, title, album, genre" + (", " + ", ".join(optional) if optional else "")
            rows = conn.execute(f"SELECT {select} FROM mp3_files ORDER BY artist, title").fetchall()
            self.items = [tuple(row) for row in rows]
        finally:
            conn.close()
        self.populate_list()

    def populate_list(self):
        q = self.search.text().strip().casefold()
        self.visible_items = [row for row in self.items if not q or q in " ".join(str(x or "") for x in row).casefold()]
        self.list.blockSignals(True); self.list.setRowCount(0)
        for row in self.visible_items:
            r = self.list.rowCount(); self.list.insertRow(r)
            self.list.setItem(r,0,QTableWidgetItem(str(row[1] or "Onbekende artiest")))
            self.list.setItem(r,1,QTableWidgetItem(str(row[2] or Path(str(row[0])).stem)))
        self.list.blockSignals(False)
        self.status.setText(f"{len(self.visible_items)} van {len(self.items)} MP3's")
        if self.visible_items: self.list.selectRow(0)

    def _table_selection_changed(self):
        row = self.list.currentRow(); self.select_index(row)

    def select_index(self, index):
        self.current_index = index
        if 0 <= index < len(self.visible_items):
            row = self.visible_items[index]
            self.vinyl_deck.set_track(row[1], row[2])
            self.vinyl_deck.set_playing(False)
            self.show_item(row)

    def show_item(self, row):
        artist = str(row[1] or "Onbekende artiest"); title = str(row[2] or Path(str(row[0])).stem)
        self.info.setText(f"<b>{artist}</b><br>{title}<br><br>{Path(str(row[0])).name}")
        self.track_list.clear()
        self.previous.setEnabled(self.current_index > 0); self.next.setEnabled(self.current_index + 1 < len(self.visible_items)); self.play.setEnabled(True)

    def play_current(self):
        if 0 <= self.current_index < len(self.visible_items):
            path = str(self.visible_items[self.current_index][0] or "")
            if Path(path).exists():
                self.play_mp3.emit(path); self.vinyl_deck.set_playing(True)

    def play_track_item(self, item):
        path = item.data(Qt.ItemDataRole.UserRole)
        if path and Path(path).exists(): self.play_mp3.emit(str(path))

    def previous_track(self):
        if self.current_index > 0:
            self.list.selectRow(self.current_index - 1); self.play_current()

    def next_track(self):
        if self.current_index + 1 < len(self.visible_items):
            self.list.selectRow(self.current_index + 1); self.play_current()

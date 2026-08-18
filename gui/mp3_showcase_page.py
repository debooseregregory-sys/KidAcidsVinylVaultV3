from __future__ import annotations

from pathlib import Path
from math import cos, sin, radians

from PySide6.QtCore import Qt, QTimer, Signal, QPointF, QRectF
from PySide6.QtGui import QPixmap, QPainter, QPen, QBrush, QColor, QFont
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QListWidget, QListWidgetItem, QFrame, QScrollArea, QSizePolicy,
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
        self.power_on = True
        self.angle = 0.0
        self.arm_angle = -28.0
        self.pitch = 0.0
        self.setMinimumSize(620, 610)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.timer = QTimer(self)
        self.timer.setInterval(30)
        self.timer.timeout.connect(self._tick)

    def set_track(self, artist="", title=""):
        self.artist = str(artist or "Onbekende artiest")
        self.title = str(title or "Onbekende titel")
        self.update()

    def set_playing(self, playing):
        self.playing = bool(playing) and self.power_on
        if self.playing:
            self.timer.start()
        else:
            self.timer.stop()
        self.update()

    def set_power(self, on):
        self.power_on = bool(on)
        if not self.power_on:
            self.set_playing(False)
        self.update()

    def _tick(self):
        if self.playing:
            self.angle = (self.angle + 2.6) % 360.0
        target = 18.0 if self.playing else -28.0
        self.arm_angle += (target - self.arm_angle) * 0.08
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = float(self.width()), float(self.height())
        pink = QColor("#d84b91")
        p.fillRect(self.rect(), QColor("#0a0a0e"))
        p.setPen(QPen(QColor("#3d3943"), 1))
        p.setBrush(QBrush(QColor("#17171d")))
        p.drawRoundedRect(QRectF(10, 10, w - 20, h - 20), 20, 20)

        p.setPen(pink)
        p.setFont(QFont("Segoe UI", 13, QFont.Weight.Black))
        p.drawText(QRectF(28, 24, 300, 24), Qt.AlignmentFlag.AlignLeft, "KID ACID'S VINYL VAULT")
        p.setPen(QColor("#8d8792"))
        p.setFont(QFont("Segoe UI", 9))
        p.drawText(QRectF(28, 48, 300, 20), Qt.AlignmentFlag.AlignLeft, "MP3 SHOWCASE • VINYL DECK")

        size = max(330.0, min(w - 150.0, h - 235.0))
        r = size / 2.0
        cx, cy = w * 0.43, 80 + r
        p.setPen(QPen(QColor("#4b4650"), 2))
        p.setBrush(QBrush(QColor("#28262c")))
        p.drawEllipse(QPointF(cx, cy), r + 24, r + 24)
        p.setPen(QPen(QColor("#55505a"), 2))
        p.setBrush(QBrush(QColor("#101015")))
        p.drawEllipse(QPointF(cx, cy), r + 10, r + 10)
        p.setPen(QPen(QColor("#24232a"), 1))
        p.setBrush(QBrush(QColor("#050507")))
        p.drawEllipse(QPointF(cx, cy), r, r)

        p.setBrush(QBrush(Qt.BrushStyle.NoBrush))
        for f in (0.97, .94, .91, .88, .85, .82, .79, .76, .73, .70, .67, .64, .61, .58, .55):
            rr = r * f
            p.setPen(QPen(QColor("#17171c"), 1))
            p.drawEllipse(QPointF(cx, cy), rr, rr)

        p.save()
        p.translate(cx, cy)
        p.rotate(self.angle)
        p.setPen(QPen(QColor(216, 75, 145, 130), 3))
        p.drawArc(QRectF(-r * .86, -r * .86, r * 1.72, r * 1.72), 18 * 16, 62 * 16)
        p.setPen(QPen(QColor(255, 255, 255, 32), 2))
        p.drawLine(QPointF(-r * .12, -r * .2), QPointF(r * .83, -r * .2))
        p.restore()

        lr = min(72.0, r * .25)
        p.setPen(QPen(QColor("#ed9fc2"), 2))
        p.setBrush(QBrush(QColor("#68183f")))
        p.drawEllipse(QPointF(cx, cy), lr, lr)
        p.setPen(QColor("#f7e6ee"))
        p.setFont(QFont("Segoe UI", max(10, int(lr / 3.8)), QFont.Weight.Bold))
        p.drawText(QRectF(cx - lr, cy - 10, lr * 2, 20), Qt.AlignmentFlag.AlignCenter, "KID ACID")
        p.setPen(QPen(QColor("#bbb5bd"), 1))
        p.setBrush(QBrush(QColor("#d1cbd1")))
        p.drawEllipse(QPointF(cx, cy), 5, 5)

        pivot = QPointF(w * 0.80, 135)
        p.setPen(QPen(QColor("#08080a"), 5))
        p.setBrush(QBrush(QColor("#343139")))
        p.drawEllipse(pivot, 28, 28)
        p.setPen(QPen(QColor("#817a84"), 2))
        p.drawEllipse(pivot, 16, 16)
        a = radians(self.arm_angle)
        reach = r * 1.02
        elbow = QPointF(pivot.x() - cos(a) * reach * .43, pivot.y() + sin(a) * reach * .43)
        end = QPointF(cx + r * (.88 if self.playing else .62), cy - r * (.18 if self.playing else .54))
        bend = QPointF((elbow.x() + end.x()) / 2 - sin(a) * 22, (elbow.y() + end.y()) / 2 - cos(a) * 22)
        p.setPen(QPen(QColor("#c3bec5"), 9, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        p.drawLine(pivot, elbow)
        p.drawLine(elbow, bend)
        p.drawLine(bend, end)
        p.setPen(QPen(QColor("#69636d"), 3))
        p.drawLine(pivot, elbow)
        p.drawLine(elbow, bend)
        p.save()
        p.translate(end)
        p.rotate(-self.arm_angle)
        p.setPen(QPen(QColor("#222126"), 2))
        p.setBrush(QBrush(QColor("#d6d1d7")))
        p.drawRoundedRect(QRectF(-35, -10, 42, 20), 4, 4)
        p.setBrush(QBrush(pink))
        p.drawRoundedRect(QRectF(-24, -7, 25, 14), 3, 3)
        p.setPen(QPen(QColor("#eeeeee"), 2))
        p.drawLine(QPointF(-18, 8), QPointF(-15, 28))
        p.restore()

        pitch_x = w - 74
        top = 225
        bottom = h - 205
        p.setPen(QPen(QColor("#57515b"), 3))
        p.drawLine(QPointF(pitch_x, top), QPointF(pitch_x, bottom))
        for i in range(-8, 9):
            y = (top + bottom) / 2 - i * 15
            length = 16 if i % 4 == 0 else 9
            p.drawLine(QPointF(pitch_x - length, y), QPointF(pitch_x, y))
        knob_y = (top + bottom) / 2 - self.pitch * 15
        p.setPen(QPen(QColor("#1a181e"), 2))
        p.setBrush(QBrush(QColor("#d0cbd1")))
        p.drawRoundedRect(QRectF(pitch_x - 18, knob_y - 7, 36, 14), 4, 4)
        p.setPen(QColor("#aaa4ad"))
        p.setFont(QFont("Segoe UI", 8, QFont.Weight.Bold))
        p.drawText(QRectF(pitch_x - 28, bottom + 18, 56, 18), Qt.AlignmentFlag.AlignCenter, "PITCH")
        p.drawText(QRectF(pitch_x - 28, (top + bottom) / 2 - 9, 56, 18), Qt.AlignmentFlag.AlignCenter, "0")
        p.drawText(QRectF(pitch_x - 28, top - 22, 56, 18), Qt.AlignmentFlag.AlignCenter, "+8")
        p.drawText(QRectF(pitch_x - 28, bottom + 38, 56, 18), Qt.AlignmentFlag.AlignCenter, "-8")

        p.setPen(QColor("#77717c"))
        p.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        p.drawText(QRectF(28, h - 116, 200, 20), Qt.AlignmentFlag.AlignLeft, "33⅓ RPM   •   DIRECT DRIVE")
        p.setPen(pink if self.power_on else QColor("#55515a"))
        p.drawText(QRectF(28, h - 88, 180, 20), Qt.AlignmentFlag.AlignLeft, "● POWER ON" if self.power_on else "● POWER OFF")
        p.setPen(QColor("#ffffff"))
        p.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        p.drawText(QRectF(28, h - 60, w - 56, 24), Qt.AlignmentFlag.AlignLeft, self.artist)
        p.setFont(QFont("Segoe UI", 18, QFont.Weight.Black))
        p.drawText(QRectF(28, h - 37, w - 56, 25), Qt.AlignmentFlag.AlignLeft, self.title)
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
        root.setContentsMargins(22, 18, 22, 18)
        root.setSpacing(12)
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
        body.setContentsMargins(0, 0, 0, 0)
        body.setSpacing(18)
        self.list = QListWidget()
        self.list.setMinimumWidth(500)
        self.list.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.list.currentRowChanged.connect(self.select_index)
        body.addWidget(self.list, 5)

        right = QVBoxLayout()
        right.setSpacing(12)
        self.vinyl_deck = VinylDeckWidget(self)
        right.addWidget(self.vinyl_deck, 7)

        controls = QHBoxLayout()
        self.previous = QPushButton("VORIGE")
        self.play = QPushButton("PLAY")
        self.next = QPushButton("VOLGENDE")
        self.power = QPushButton("POWER")
        controls.addWidget(self.previous)
        controls.addWidget(self.play, 1)
        controls.addWidget(self.next)
        controls.addWidget(self.power)
        right.addLayout(controls)
        body.addLayout(right, 7)
        root.addLayout(body, 1)

        self.previous.clicked.connect(self.previous_track)
        self.next.clicked.connect(self.next_track)
        self.play.clicked.connect(self.play_current)
        self.power.clicked.connect(lambda: self.vinyl_deck.set_power(not self.vinyl_deck.power_on))
        self.search.textChanged.connect(self.populate_list)
        self.refresh.clicked.connect(self.load_files)

        self.setStyleSheet("""
            QWidget{background:#0b0b0f;color:#f2f2f5;}
            QLineEdit,QPushButton,QListWidget{background:#18181f;color:#fff;border:1px solid #30303a;border-radius:6px;padding:8px 10px;}
            QPushButton:hover{border-color:#d84b91;background:#24242c;}
            QListWidget{background:#0f0f14;}
            QListWidget::item{padding:10px;border-bottom:1px solid #24242d;}
            QListWidget::item:selected{background:#271522;border:1px solid #5d2947;}
        """)

    def populate_list(self):
        q = self.search.text().strip().casefold()
        self.visible_items = [row for row in self.items if not q or q in " ".join(str(x or "") for x in row).casefold()]
        self.list.blockSignals(True)
        self.list.clear()
        for row in self.visible_items:
            name = Path(str(row[0])).name
            artist = str(row[1] or "").strip()
            title = str(row[2] or "").strip()
            text = f"{artist}\n{title}" if artist and title else (artist or title or name)
            item = QListWidgetItem(text)
            item.setToolTip(str(row[0]))
            self.list.addItem(item)
        self.list.blockSignals(False)
        self.status.setText(f"{len(self.visible_items)} van {len(self.items)} MP3's")
        if self.visible_items:
            self.list.setCurrentRow(0)

    def select_index(self, index):
        self.current_index = index
        if 0 <= index < len(self.visible_items):
            row = self.visible_items[index]
            self.vinyl_deck.set_track(row[1], row[2])
            self.vinyl_deck.set_playing(False)
            self.show_item(row)

    def show_item(self, row):
        artist = str(row[1] or "Onbekende artiest")
        title = str(row[2] or Path(str(row[0])).stem)
        self.vinyl_deck.set_track(artist, title)
        self.previous.setEnabled(self.current_index > 0)
        self.next.setEnabled(self.current_index + 1 < len(self.visible_items))
        self.play.setEnabled(True)

    def load_files(self):
        conn = get_connection()
        try:
            # mp3_files in the current V3 database does NOT have release_id.
            # Keep this query aligned with the actual schema and only select
            # columns maintained by the MP3 subsystem.
            self.items = conn.execute(
                """
                SELECT
                    path,
                    artist,
                    title,
                    album,
                    genre,
                    discogs_id,
                    discogs_link,
                    cover
                FROM mp3_files
                ORDER BY artist COLLATE NOCASE, title COLLATE NOCASE
                """
            ).fetchall()
        finally:
            conn.close()
        self.populate_list()

    def play_current(self):
        if 0 <= self.current_index < len(self.visible_items):
            path = str(self.visible_items[self.current_index][0] or "")
            if Path(path).exists():
                self.play_mp3.emit(path)
                self.vinyl_deck.set_playing(True)

    def previous_track(self):
        if self.current_index > 0:
            self.list.setCurrentRow(self.current_index - 1)
            self.play_current()

    def next_track(self):
        if self.current_index + 1 < len(self.visible_items):
            self.list.setCurrentRow(self.current_index + 1)
            self.play_current()

    def play_track_item(self, item):
        path = item.data(Qt.ItemDataRole.UserRole)
        if path:
            self.play_mp3.emit(str(path))

    def clear_showcase(self):
        self.vinyl_deck.set_track("Onbekende artiest", "-")
        self.vinyl_deck.set_playing(False)

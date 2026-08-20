from __future__ import annotations
from pathlib import Path
from math import cos, sin, radians, hypot, atan2, degrees
from PySide6.QtCore import Qt, QTimer, Signal, QPointF, QRectF
from PySide6.QtGui import QPixmap, QPainter, QPen, QBrush, QColor, QFont
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QListWidget, QListWidgetItem, QTableWidget, QHeaderView, QFrame,
    QSizePolicy,
)
from database.database import get_connection
PINK = QColor("#d84b91")
BG = QColor("#08090c")
TEXT = QColor("#f2f2f5")
MUTED = QColor("#8e919b")
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
    """Technically detailed, realistic turntable: straight tonearm, cartridge, stylus, pitch and power."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.artist = "KID ACID"
        self.title = "VINYL PLAYER"
        self.playing = False
        self.power_on = True
        self.angle = 0.0
        self.pitch = 0.0
        self.arm_progress = 0.0
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
        self.timer.start()
        self.update()
    def set_power(self, on):
        self.power_on = bool(on)
        if not self.power_on:
            self.set_playing(False)
        self.update()
    def _tick(self):
        if self.playing:
            self.angle = (self.angle + 2.6) % 360.0
        target = 1.0 if self.playing else 0.0
        self.arm_progress += (target - self.arm_progress) * 0.08
        if not self.playing and self.arm_progress < 0.001:
            self.arm_progress = 0.0
            self.timer.stop()
        self.update()
    def _layout(self):
        w, h = float(self.width()), float(self.height())
        r = max(145.0, min((w - 250.0) * 0.46, (h - 150.0) * 0.45))
        cx = min(w * 0.46, w - r - 100)
        cy = 300 + max(0.0, h - 610.0) * 0.12
        return w, h, cx, cy, r
    def _text(self, p, rect, text, size=9, color=MUTED, weight=QFont.Weight.Bold,
              align=Qt.AlignmentFlag.AlignLeft):
        p.setPen(color)
        p.setFont(QFont("Segoe UI", size, weight))
        p.drawText(rect, align, text)
    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h, cx, cy, r = self._layout()
        # CHASSIS
        p.fillRect(self.rect(), BG)
        p.setPen(QPen(QColor("#050607"), 3))
        p.setBrush(QBrush(QColor("#111217")))
        p.drawRoundedRect(QRectF(8, 8, w - 16, h - 16), 18, 18)
        p.setPen(QPen(QColor("#3a3c45"), 1))
        p.setBrush(QBrush(QColor("#1b1c21")))
        p.drawRoundedRect(QRectF(15, 15, w - 30, h - 30), 14, 14)
        p.setPen(QPen(QColor("#090a0d"), 2))
        p.setBrush(QBrush(QColor("#121318")))
        p.drawRoundedRect(QRectF(25, 25, w - 50, h - 50), 10, 10)
        self._text(p, QRectF(34, 31, 330, 22), "KID ACID'S VINYL VAULT", 12, PINK, QFont.Weight.Black)
        self._text(p, QRectF(34, 53, 380, 18), "MP3 SHOWCASE  /  PROFESSIONAL DIRECT DRIVE", 8)
        # PLATTER
        p.setPen(QPen(QColor("#050507"), 3))
        p.setBrush(QBrush(QColor("#303139")))
        p.drawEllipse(QPointF(cx, cy), r + 20, r + 20)
        p.setPen(QPen(QColor("#4b4d55"), 2))
        p.setBrush(QBrush(QColor("#1c1d22")))
        p.drawEllipse(QPointF(cx, cy), r + 12, r + 12)
        # Strobe dots.
        for i in range(48):
            a = radians(i * 7.5 + self.angle * 0.18)
            x = cx + cos(a) * (r + 5)
            y = cy + sin(a) * (r + 5)
            p.setPen(QPen(QColor("#8d9098"), 2))
            p.drawPoint(QPointF(x, y))
        # VINYL
        p.setPen(QPen(QColor("#050506"), 2))
        p.setBrush(QBrush(QColor("#08090b")))
        p.drawEllipse(QPointF(cx, cy), r, r)
        p.setBrush(QBrush(Qt.BrushStyle.NoBrush))
        for f in (0.985, .965, .945, .925, .905, .885, .865, .845, .825,
                  .805, .785, .765, .745, .725, .705, .685, .665, .645,
                  .625, .605):
            rr = r * f
            p.setPen(QPen(QColor(42, 43, 48, 120), 1))
            p.drawEllipse(QPointF(cx, cy), rr, rr)
        p.save()
        p.translate(cx, cy)
        p.rotate(self.angle)
        p.setPen(QPen(QColor(255, 255, 255, 24), 2))
        p.drawLine(QPointF(-r * .78, -r * .23), QPointF(r * .80, -r * .23))
        p.setPen(QPen(QColor(216, 75, 145, 155), 3))
        p.drawArc(QRectF(-r * .90, -r * .90, r * 1.80, r * 1.80), 18 * 16, 52 * 16)
        p.restore()
        # LABEL + SPINDLE
        label_r = min(58.0, r * .255)
        p.setPen(QPen(QColor("#e7a0c2"), 2))
        p.setBrush(QBrush(QColor("#66193f")))
        p.drawEllipse(QPointF(cx, cy), label_r, label_r)
        p.setPen(QPen(QColor("#b23c75"), 1))
        p.drawEllipse(QPointF(cx, cy), label_r * .78, label_r * .78)
        self._text(p, QRectF(cx - label_r, cy - 9, label_r * 2, 18), "KID ACID", 8, QColor("#f7e6ee"), QFont.Weight.Black, Qt.AlignmentFlag.AlignCenter)
        self._text(p, QRectF(cx - label_r, cy + 8, label_r * 2, 14), "VINYL VAULT", 5, QColor("#e9a8c6"), QFont.Weight.Bold, Qt.AlignmentFlag.AlignCenter)
        p.setPen(QPen(QColor("#cfd0d4"), 1))
        p.setBrush(QBrush(QColor("#bfc0c5")))
        p.drawEllipse(QPointF(cx, cy), 5, 5)
        p.setBrush(QBrush(QColor("#202126")))
        p.drawEllipse(QPointF(cx, cy), 2, 2)
        # STRAIGHT TONEARM. No elbow, no kink, one physical line.
        pivot = QPointF(w - 105, 120)
        rest_stylus = QPointF(cx + r * 1.03, cy - r * .28)
        play_stylus = QPointF(cx + r * .74, cy + r * .10)
        stylus = QPointF(
            rest_stylus.x() + (play_stylus.x() - rest_stylus.x()) * self.arm_progress,
            rest_stylus.y() + (play_stylus.y() - rest_stylus.y()) * self.arm_progress,
        )
        dx = stylus.x() - pivot.x()
        dy = stylus.y() - pivot.y()
        length = max(1.0, hypot(dx, dy))
        ux, uy = dx / length, dy / length
        arm_angle = degrees(atan2(dy, dx))
        # Counterweight is collinear with the arm.
        counter = QPointF(pivot.x() - ux * 54, pivot.y() - uy * 54)
        p.setPen(QPen(QColor("#090a0d"), 4))
        p.setBrush(QBrush(QColor("#4a4c54")))
        p.drawEllipse(counter, 15, 15)
        p.setPen(QPen(QColor("#777982"), 2))
        p.drawEllipse(counter, 10, 10)
        # Pivot housing.
        p.setPen(QPen(QColor("#050507"), 4))
        p.setBrush(QBrush(QColor("#303239")))
        p.drawEllipse(pivot, 27, 27)
        p.setPen(QPen(QColor("#686b75"), 2))
        p.drawEllipse(pivot, 17, 17)
        p.setPen(QPen(QColor("#a0a2aa"), 2))
        p.drawLine(QPointF(pivot.x() - 7, pivot.y()), QPointF(pivot.x() + 7, pivot.y()))
        p.drawLine(QPointF(pivot.x(), pivot.y() - 7), QPointF(pivot.x(), pivot.y() + 7))
        # Long arm: one continuous segment from pivot to headshell.
        arm_end = QPointF(stylus.x() - ux * 25, stylus.y() - uy * 25)
        p.setPen(QPen(QColor("#07080a"), 15, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        p.drawLine(pivot, arm_end)
        p.setPen(QPen(QColor("#c2c4ca"), 9, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        p.drawLine(pivot, arm_end)
        p.setPen(QPen(QColor("#686b74"), 3, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        p.drawLine(pivot, arm_end)
        # Headshell + cartridge, aligned with the arm.
        shell = QPointF(stylus.x() - ux * 31, stylus.y() - uy * 31)
        p.save()
        p.translate(shell)
        p.rotate(arm_angle)
        p.setPen(QPen(QColor("#08090b"), 3))
        p.setBrush(QBrush(QColor("#aeb1b8")))
        p.drawRoundedRect(QRectF(-31, -8, 35, 16), 3, 3)
        p.setPen(QPen(QColor("#575a63"), 1))
        p.drawLine(QPointF(-25, -5), QPointF(-2, -5))
        p.drawLine(QPointF(-25, 5), QPointF(-2, 5))
        p.setPen(QPen(QColor("#07080a"), 2))
        p.setBrush(QBrush(QColor("#262830")))
        p.drawRoundedRect(QRectF(2, -7, 20, 14), 2, 2)
        p.setBrush(QBrush(PINK))
        p.drawRoundedRect(QRectF(15, -5, 8, 10), 2, 2)
        p.restore()
        # Stylus ends exactly at the playing surface.
        stylus_base = QPointF(stylus.x() - ux * 8, stylus.y() - uy * 8)
        p.setPen(QPen(QColor("#07080a"), 4, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        p.drawLine(stylus_base, stylus)
        p.setPen(QPen(QColor("#f3f4f5"), 1.8, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        p.drawLine(stylus_base, stylus)
        p.setPen(QPen(QColor("#ffffff"), 3))
        p.drawPoint(stylus)
        # Cue lever.
        p.setPen(QPen(QColor("#565861"), 3))
        p.drawLine(QPointF(pivot.x() + 34, pivot.y() + 18), QPointF(pivot.x() + 42, pivot.y() - 10))
        p.setPen(QPen(QColor("#a0a2a9"), 2))
        p.drawLine(QPointF(pivot.x() + 38, pivot.y() - 12), QPointF(pivot.x() + 48, pivot.y() - 12))
        # REAL PITCH FADER: recessed slot, scale, metal knob.
        pitch_x = w - 43
        top = 210
        bottom = h - 145
        center = (top + bottom) / 2
        p.setPen(QPen(QColor("#050607"), 10))
        p.drawLine(QPointF(pitch_x, top), QPointF(pitch_x, bottom))
        p.setPen(QPen(QColor("#777a83"), 3))
        p.drawLine(QPointF(pitch_x, top), QPointF(pitch_x, bottom))
        step = (bottom - top) / 16
        for i in range(-8, 9):
            y = center - i * step
            major = i in (-8, -4, 0, 4, 8)
            p.setPen(QPen(QColor("#b1b3ba") if major else QColor("#666871"), 2))
            p.drawLine(QPointF(pitch_x - (17 if major else 9), y), QPointF(pitch_x + (17 if major else 9), y))
        knob_y = center - max(-8.0, min(8.0, self.pitch)) * step
        p.setPen(QPen(QColor("#07080a"), 3))
        p.setBrush(QBrush(QColor("#c4c6cb")))
        p.drawRoundedRect(QRectF(pitch_x - 24, knob_y - 10, 48, 20), 5, 5)
        p.setPen(QPen(QColor("#70727a"), 1))
        p.drawLine(QPointF(pitch_x - 16, knob_y), QPointF(pitch_x + 16, knob_y))
        self._text(p, QRectF(pitch_x - 35, top - 32, 70, 18), "+8", 8, MUTED, QFont.Weight.Bold, Qt.AlignmentFlag.AlignCenter)
        self._text(p, QRectF(pitch_x - 35, center - 9, 70, 18), "0", 8, TEXT, QFont.Weight.Black, Qt.AlignmentFlag.AlignCenter)
        self._text(p, QRectF(pitch_x - 35, bottom + 12, 70, 18), "-8", 8, MUTED, QFont.Weight.Bold, Qt.AlignmentFlag.AlignCenter)
        self._text(p, QRectF(pitch_x - 45, bottom + 34, 90, 18), "PITCH", 8, PINK, QFont.Weight.Black, Qt.AlignmentFlag.AlignCenter)
        # PHYSICAL POWER BUTTON.
        power = QPointF(70, h - 66)
        p.setPen(QPen(QColor("#050507"), 3))
        p.setBrush(QBrush(QColor("#292b32")))
        p.drawEllipse(power, 24, 24)
        p.setPen(QPen(QColor("#555862"), 1))
        p.drawEllipse(power, 19, 19)
        p.setPen(QPen(PINK if self.power_on else QColor("#555862"), 3))
        p.drawArc(QRectF(power.x() - 11, power.y() - 11, 22, 22), 45 * 16, 270 * 16)
        p.drawLine(QPointF(power.x(), power.y() - 14), QPointF(power.x(), power.y() + 1))
        self._text(p, QRectF(power.x() - 40, power.y() + 28, 80, 18), "POWER", 7, PINK if self.power_on else MUTED, QFont.Weight.Black, Qt.AlignmentFlag.AlignCenter)
        # CLEAN TECHNICAL DISPLAY STRIP.
        strip = QRectF(120, h - 92, max(220.0, w - 300.0), 58)
        p.setPen(QPen(QColor("#2d2f36"), 1))
        p.setBrush(QBrush(QColor("#0d0e12")))
        p.drawRoundedRect(strip, 7, 7)
        self._text(p, QRectF(strip.x() + 12, strip.y() + 7, strip.width() - 24, 17), "33 RPM   |   DIRECT DRIVE   |   STABLE PLATTER", 8)
        self._text(p, QRectF(strip.x() + 12, strip.y() + 28, strip.width() * .45, 20), self.artist, 10, TEXT, QFont.Weight.Bold)
        self._text(p, QRectF(strip.x() + strip.width() * .46, strip.y() + 28, strip.width() * .52 - 12, 20), self.title, 10, PINK, QFont.Weight.Black, Qt.AlignmentFlag.AlignRight)
        p.end()
    def mousePressEvent(self, event):
        if event.button() != Qt.MouseButton.LeftButton:
            return super().mousePressEvent(event)
        w, h, *_ = self._layout()
        pos = event.position()
        power = QPointF(70, h - 66)
        if hypot(pos.x() - power.x(), pos.y() - power.y()) <= 32:
            self.set_power(not self.power_on)
            return
        pitch_x = w - 43
        top, bottom = 210, h - 145
        if abs(pos.x() - pitch_x) <= 35 and top <= pos.y() <= bottom:
            center = (top + bottom) / 2
            step = (bottom - top) / 16
            self.pitch = max(-8.0, min(8.0, (center - pos.y()) / step))
            self.update()
            return
        super().mousePressEvent(event)
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
        root.setContentsMargins(14, 12, 14, 12)
        root.setSpacing(10)
        header = QHBoxLayout()
        title = QLabel("MP3 SHOWCASE")
        title.setStyleSheet("font-size:25px;font-weight:900;color:#fff;")
        header.addWidget(title)
        header.addStretch(1)
        self.status = QLabel("Laden...")
        self.status.setStyleSheet("color:#9b9ba6;font-weight:700;")
        header.addWidget(self.status)
        root.addLayout(header)
        search = QHBoxLayout()
        self.search = QLineEdit()
        self.search.setPlaceholderText("Zoek artiest, titel, album, genre, release of bestand...")
        search.addWidget(self.search, 1)
        self.refresh = QPushButton("VERVERS")
        search.addWidget(self.refresh)
        root.addLayout(search)
        body = QHBoxLayout()
        body.setSpacing(12)
        # COLUMN 1: MP3 library.
        left = QFrame()
        left.setObjectName("column")
        ll = QVBoxLayout(left)
        ll.setContentsMargins(9, 9, 9, 9)
        lab = QLabel("MP3 LIBRARY")
        lab.setStyleSheet("font-size:12px;font-weight:900;color:#d84b91;")
        ll.addWidget(lab)
        self.list = QTableWidget(0, 2)
        self.list.setHorizontalHeaderLabels(["ARTIEST", "TRACK"])
        self.list.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.list.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.list.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.list.setMinimumWidth(290)
        self.list.verticalHeader().setDefaultSectionSize(31)
        self.list.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.list.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.list.itemSelectionChanged.connect(self._table_selection_changed)
        ll.addWidget(self.list, 1)
        body.addWidget(left, 3)
        # COLUMN 2: realistic deck.
        center = QFrame()
        center.setObjectName("column")
        cl = QVBoxLayout(center)
        cl.setContentsMargins(3, 3, 3, 3)
        self.vinyl_deck = VinylDeckWidget(self)
        cl.addWidget(self.vinyl_deck, 1)
        body.addWidget(center, 6)
        # COLUMN 3: selected track / cover / controls.
        right = QFrame()
        right.setObjectName("column")
        rl = QVBoxLayout(right)
        rl.setContentsMargins(14, 14, 14, 14)
        rl.setSpacing(10)
        now = QLabel("NOW PLAYING")
        now.setStyleSheet("font-size:12px;font-weight:900;color:#d84b91;")
        rl.addWidget(now)
        self.cover = QLabel("GEEN COVER")
        self.cover.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.cover.setMinimumHeight(170)
        self.cover.setStyleSheet("background:#0a0b0e;border:1px solid #30323a;border-radius:8px;color:#666;")
        rl.addWidget(self.cover)
        self.info = QLabel("Geen track geselecteerd")
        self.info.setWordWrap(True)
        rl.addWidget(self.info)
        tracks = QLabel("SELECTED TRACK")
        tracks.setStyleSheet("font-weight:900;color:#d84b91;")
        rl.addWidget(tracks)
        self.track_list = QListWidget()
        self.track_list.setMinimumHeight(120)
        self.track_list.itemDoubleClicked.connect(self.play_track_item)
        rl.addWidget(self.track_list, 1)
        controls = QHBoxLayout()
        self.previous = QPushButton("VORIGE")
        self.play = QPushButton("ÔûÂ PLAY")
        self.next = QPushButton("VOLGENDE")
        self.power = QPushButton("POWER")
        controls.addWidget(self.previous)
        controls.addWidget(self.play, 1)
        controls.addWidget(self.next)
        controls.addWidget(self.power)
        rl.addLayout(controls)
        body.addWidget(right, 3)
        root.addLayout(body, 1)
        self.previous.clicked.connect(self.previous_track)
        self.play.clicked.connect(self.play_current)
        self.next.clicked.connect(self.next_track)
        self.power.clicked.connect(lambda: self.vinyl_deck.set_power(not self.vinyl_deck.power_on))
        self.search.textChanged.connect(self.populate_list)
        self.refresh.clicked.connect(self.load_files)
        self.setStyleSheet("""
            QWidget{background:#0b0b0f;color:#f2f2f5;}
            QFrame#column{background:#121318;border:1px solid #292b33;border-radius:10px;}
            QLineEdit,QPushButton{background:#18181f;color:#fff;border:1px solid #30303a;border-radius:6px;padding:7px 10px;}
            QPushButton{font-weight:800;min-height:32px;}
            QPushButton:hover{border-color:#d84b91;background:#24242c;}
            QTableWidget{background:#101015;color:#f2f2f5;border:1px solid #2b2932;border-radius:7px;gridline-color:#24242d;}
            QTableWidget::item{background:#101015;color:#f2f2f5;padding:6px;border-bottom:1px solid #22222a;}
            QTableWidget::item:selected{background:#3a1d31;color:#fff;}
            QHeaderView::section{background:#18181f;color:#d84b91;border:0;padding:7px;font-weight:800;}
            QListWidget{background:#101015;color:#f2f2f5;border:1px solid #2b2932;border-radius:7px;}
            QListWidget::item{padding:7px;border-bottom:1px solid #22222a;}
            QListWidget::item:selected{background:#3a1d31;}
        """)
    def load_files(self):
        conn = get_connection()
        try:
            rows = conn.execute("""
                SELECT path, artist, title, album, genre, discogs_id, discogs_link, cover
                FROM mp3_files
                ORDER BY artist COLLATE NOCASE, title COLLATE NOCASE
            """).fetchall()
            self.items = list(rows)
        finally:
            conn.close()
        self.populate_list()
    def populate_list(self):
        q = self.search.text().strip().casefold()
        self.visible_items = [row for row in self.items if not q or q in " ".join(str(x or "") for x in row).casefold()]
        self.list.blockSignals(True)
        self.list.setRowCount(0)
        for row in self.visible_items:
            r = self.list.rowCount()
            self.list.insertRow(r)
            artist = str(row[1] or "").strip()
            title = str(row[2] or "").strip()
            self.list.setItem(r, 0, __import__("PySide6.QtWidgets", fromlist=["QTableWidgetItem"]).QTableWidgetItem(artist))
            self.list.setItem(r, 1, __import__("PySide6.QtWidgets", fromlist=["QTableWidgetItem"]).QTableWidgetItem(title or Path(str(row[0])).stem))
        self.list.blockSignals(False)
        self.status.setText(f"{len(self.visible_items)} van {len(self.items)} MP3's")
        if self.visible_items:
            self.list.selectRow(0)
        else:
            self.current_index = -1
    def _table_selection_changed(self):
        rows = self.list.selectionModel().selectedRows()
        if not rows:
            return
        self.select_index(rows[0].row())
    def select_index(self, index):
        self.current_index = index
        if 0 <= index < len(self.visible_items):
            row = self.visible_items[index]
            artist = str(row[1] or "Onbekende artiest")
            title = str(row[2] or Path(str(row[0])).stem)
            self.vinyl_deck.set_track(artist, title)
            self.vinyl_deck.set_playing(False)
            self.info.setText(f"<b>{artist}</b><br><span style='color:#d84b91;font-size:16px'>{title}</span><br><br>{row[3] or ''}<br>{row[4] or ''}")
            self.track_list.clear()
            item = QListWidgetItem(f"{artist} ÔÇö {title}")
            item.setData(Qt.ItemDataRole.UserRole, str(row[0] or ""))
            self.track_list.addItem(item)
            cover = str(row[7] or "")
            if cover and Path(cover).exists():
                pix = QPixmap(cover)
                if not pix.isNull():
                    self.cover.setPixmap(pix.scaled(self.cover.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
                    self.cover.setText("")
                else:
                    self.cover.setPixmap(QPixmap())
                    self.cover.setText("GEEN COVER")
            else:
                self.cover.setPixmap(QPixmap())
                self.cover.setText("GEEN COVER")
            self.previous.setEnabled(index > 0)
            self.next.setEnabled(index + 1 < len(self.visible_items))
            self.play.setEnabled(True)
    def play_current(self):
        if 0 <= self.current_index < len(self.visible_items):
            path = str(self.visible_items[self.current_index][0] or "")
            if Path(path).exists():
                self.play_mp3.emit(path)
                self.vinyl_deck.set_playing(True)
    def play_track_item(self, item):
        path = str(item.data(Qt.ItemDataRole.UserRole) or "")
        if path and Path(path).exists():
            self.play_mp3.emit(path)
            self.vinyl_deck.set_playing(True)
    def stop_current(self):
        self.vinyl_deck.set_playing(False)
    def previous_track(self):
        if self.current_index > 0:
            self.list.selectRow(self.current_index - 1)
            self.play_current()
    def next_track(self):
        if self.current_index + 1 < len(self.visible_items):
            self.list.selectRow(self.current_index + 1)
            self.play_current()
    def clear_showcase(self):
        self.vinyl_deck.set_track("Onbekende artiest", "-")
        self.vinyl_deck.set_playing(False)
        self.info.setText("Geen track geselecteerd")
        self.track_list.clear()
        self.cover.setPixmap(QPixmap())
        self.cover.setText("GEEN COVER")

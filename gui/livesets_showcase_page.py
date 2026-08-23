from __future__ import annotations
from gui.app_settings import paint_accent

import json
import math
from pathlib import Path

from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QPixmap, QPainter, QPen, QBrush, QFont
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
LIVESETS_FILE = DATA_DIR / "livesets.json"


class LivesetShowcaseCard(QFrame):
    open_requested = Signal(dict)

    def __init__(self, data, parent=None):
        super().__init__(parent)
        self.data = dict(data)
        self.setFixedWidth(270)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._build()

    def _build(self):
        self.setObjectName("liveCard")
        root = QVBoxLayout(self)
        root.setContentsMargins(8, 8, 8, 9)
        root.setSpacing(5)
        self.cover = QLabel("GEEN COVER")
        self.cover.setObjectName("liveCover")
        self.cover.setFixedSize(254, 143)
        self.cover.setAlignment(Qt.AlignmentFlag.AlignCenter)
        root.addWidget(self.cover)
        self._load_cover()

        artist = QLabel(str(self.data.get("artist") or "LIVESET"))
        artist.setObjectName("liveArtist")
        root.addWidget(artist)
        title = QLabel(str(self.data.get("title") or "(geen titel)"))
        title.setObjectName("liveTitle")
        title.setWordWrap(True)
        root.addWidget(title)
        meta = " • ".join(x for x in [str(self.data.get("date") or ""), str(self.data.get("location") or "")] if x)
        meta_label = QLabel(meta or "Geen datum / locatie")
        meta_label.setObjectName("liveMeta")
        meta_label.setWordWrap(True)
        root.addWidget(meta_label)

        row = QHBoxLayout()
        row.setContentsMargins(0, 1, 0, 0)
        row.addWidget(QLabel(str(self.data.get("duration") or "LIVESET")), 1)
        play = QPushButton("▶")
        play.setObjectName("cdTrackPlayButton")
        play.setFixedSize(42, 34)
        play.setCursor(Qt.CursorShape.PointingHandCursor)
        play.clicked.connect(lambda: self.open_requested.emit(self.data))
        row.addWidget(play)
        root.addLayout(row)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.open_requested.emit(self.data)
        super().mousePressEvent(event)

    def _load_cover(self):
        path = str(self.data.get("cover") or "")
        pix = QPixmap(path) if path and Path(path).exists() else QPixmap()
        if pix.isNull():
            return
        size = self.cover.size()
        scaled = pix.scaled(size, Qt.AspectRatioMode.KeepAspectRatioByExpanding, Qt.TransformationMode.SmoothTransformation)
        x = max(0, (scaled.width() - size.width()) // 2)
        y = max(0, (scaled.height() - size.height()) // 2)
        self.cover.setText("")
        self.cover.setPixmap(scaled.copy(x, y, size.width(), size.height()))


class LivesetVisualizer(QWidget):
    """Animated atmospheric footer that fills the showcase without stealing focus."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(150)
        self.setMaximumHeight(150)
        self._phase = 0.0
        self._text_offset = 0.0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._animate)
        self._timer.start(35)
        self.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent, False)

    def _animate(self):
        self._phase = (self._phase + 0.045) % (math.pi * 2)
        self._text_offset = (self._text_offset + 1.15) % 900
        self.update()

    def paintEvent(self, event):
        del event
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = self.rect().adjusted(1, 1, -1, -1)

        # Deep atmospheric background.
        painter.setBrush(QBrush(Qt.GlobalColor.black))
        painter.setPen(QPen(Qt.GlobalColor.transparent))
        painter.drawRoundedRect(rect, 14, 14)

        # Moving glow particles.
        for i in range(22):
            angle = self._phase * (0.55 + (i % 5) * 0.08) + i * 0.83
            x = rect.left() + rect.width() * (0.5 + 0.47 * math.sin(angle * 0.72 + i))
            y = rect.top() + 72 + 48 * math.sin(angle * 1.31 + i * 0.4)
            radius = 1.5 + 2.4 * (0.5 + 0.5 * math.sin(angle * 1.7))
            painter.setBrush(QBrush(Qt.GlobalColor.darkMagenta))
            painter.setPen(QPen(Qt.GlobalColor.darkMagenta))
            painter.drawEllipse(int(x - radius), int(y - radius), int(radius * 2), int(radius * 2))

        # Animated equalizer / acid pulse.
        bar_count = 56
        usable = rect.width() - 42
        step = usable / bar_count
        for i in range(bar_count):
            wave = (
                math.sin(self._phase * 2.1 + i * 0.43)
                + 0.55 * math.sin(self._phase * 3.7 - i * 0.17)
                + 0.25 * math.sin(self._phase * 1.1 + i * 0.91)
            ) / 1.8
            height = 12 + (wave + 1) * 24
            x = rect.left() + 21 + i * step
            y = rect.bottom() - 17 - height
            painter.setPen(QPen(Qt.GlobalColor.magenta, 2.2))
            painter.drawLine(int(x), int(rect.bottom() - 17), int(x), int(y))

        # Central moving pulse ring.
        cx = rect.center().x()
        cy = rect.top() + 48
        pulse = 15 + 8 * (0.5 + 0.5 * math.sin(self._phase * 2.0))
        painter.setBrush(QBrush(Qt.GlobalColor.transparent))
        painter.setPen(QPen(Qt.GlobalColor.magenta, 2.0))
        painter.drawEllipse(int(cx - pulse), int(cy - pulse), int(pulse * 2), int(pulse * 2))
        painter.setPen(QPen(Qt.GlobalColor.darkMagenta, 1.0))
        painter.drawEllipse(int(cx - pulse - 8), int(cy - pulse - 8), int((pulse + 8) * 2), int((pulse + 8) * 2))

        # Scrolling typography.
        text = "KID ACID  •  LIVE ENERGY  •  ACID HOUSE  •  TECHNO  •  DEEP GROOVES  •  LIVE ENERGY  •  "
        font = QFont("Arial", 11, QFont.Weight.Bold)
        painter.setFont(font)
        painter.setPen(QPen(Qt.GlobalColor.lightGray))
        metrics = painter.fontMetrics()
        width = metrics.horizontalAdvance(text)
        y = rect.top() + 25
        x = rect.right() - int(self._text_offset % (width + 40))
        painter.drawText(int(x), y, text)
        painter.drawText(int(x + width + 40), y, text)

        # Small label.
        small_font = QFont("Arial", 8, QFont.Weight.Bold)
        painter.setFont(small_font)
        painter.setPen(QPen(Qt.GlobalColor.gray))
        painter.drawText(rect.left() + 18, rect.top() + 48, "THE UNDERGROUND NEVER STOPS")

        painter.end()


class LivesetsShowcasePage(QWidget):
    """Standalone compact Livesets Showcase. Cards open the dedicated player/detail page."""
    open_requested = Signal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build()
        self.reload()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(28, 22, 28, 18)
        root.setSpacing(7)
        title = QLabel("LIVESETS SHOWCASE")
        title.setObjectName("showcaseTitle")
        root.addWidget(title)
        line = QFrame()
        line.setObjectName("showcaseLine")
        line.setFixedHeight(2)
        line.setMaximumWidth(150)
        root.addWidget(line)
        root.addWidget(QLabel("Compacte liveset showcase — klik een kaart om te openen."))

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        scroll.setStyleSheet(paint_accent("QScrollArea{border:0;background:transparent;}"))
        self.content = QWidget()
        self.grid = QGridLayout(self.content)
        self.grid.setContentsMargins(0, 14, 8, 10)
        self.grid.setHorizontalSpacing(14)
        self.grid.setVerticalSpacing(14)
        self.grid.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        scroll.setWidget(self.content)
        root.addWidget(scroll, 1)

        self.visualizer = LivesetVisualizer()
        root.addWidget(self.visualizer, 0)

        self.setStyleSheet(paint_accent("""
            QLabel#showcaseTitle{color:#fff;font-size:26px;font-weight:900;}
            QLabel{color:#858591;font-size:13px;}
            QFrame#showcaseLine{background:#ffcf72;border-radius:1px;}
            QFrame#liveCard{background:#121217;border:1px solid #292933;border-radius:9px;}
            QFrame#liveCard:hover{background:#17171e;border-color:#ffcf72;}
            QLabel#liveCover{background:#07070a;color:#666671;border:1px solid #2a2a33;border-radius:6px;}
            QLabel#liveArtist{color:#ffcf72;font-size:10px;font-weight:900;}
            QLabel#liveTitle{color:#fff;font-size:14px;font-weight:900;}
            QLabel#liveMeta{color:#858591;font-size:10px;}
            QPushButton#cdTrackPlayButton{background:#2a1524;color:#ff4fa3;border:1px solid #5a2a48;border-radius:10px;font-size:15px;font-weight:900;}
            QPushButton#cdTrackPlayButton:hover{background:#ff4fa3;color:#0e0e12;border-color:#ff4fa3;}
            QPushButton#cdTrackPlayButton[playing="true"]{background:#3a1a30;color:#ff6bb5;border-color:#ff4fa3;}
        """))

    def reload(self):
        while self.grid.count():
            item = self.grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        try:
            items = json.loads(LIVESETS_FILE.read_text(encoding="utf-8")) if LIVESETS_FILE.exists() else []
        except (OSError, json.JSONDecodeError):
            items = []
        for i, data in enumerate(items):
            card = LivesetShowcaseCard(data)
            card.open_requested.connect(self.open_requested.emit)
            self.grid.addWidget(card, i // 4, i % 4)

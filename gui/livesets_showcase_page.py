from __future__ import annotations

import json
from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QFrame, QGridLayout, QHBoxLayout, QLabel, QPushButton, QScrollArea, QVBoxLayout, QWidget

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
        scroll.setStyleSheet("QScrollArea{border:0;background:transparent;}")
        self.content = QWidget()
        self.grid = QGridLayout(self.content)
        # Cards start directly at the content edge instead of being centered.
        self.grid.setContentsMargins(0, 14, 8, 20)
        self.grid.setHorizontalSpacing(14)
        self.grid.setVerticalSpacing(14)
        self.grid.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        scroll.setWidget(self.content)
        root.addWidget(scroll, 1)

        self.setStyleSheet("""
            QLabel#showcaseTitle{color:#fff;font-size:26px;font-weight:900;}
            QLabel{color:#858591;font-size:13px;}
            QFrame#showcaseLine{background:#ffcf72;border-radius:1px;}
            QFrame#liveCard{background:#121217;border:1px solid #292933;border-radius:9px;}
            QFrame#liveCard:hover{background:#17171e;border-color:#ffcf72;}
            QLabel#liveCover{background:#07070a;color:#666671;border:1px solid #2a2a33;border-radius:6px;}
            QLabel#liveArtist{color:#ffcf72;font-size:10px;font-weight:900;}
            QLabel#liveTitle{color:#fff;font-size:14px;font-weight:900;}
            QLabel#liveMeta{color:#858591;font-size:10px;}
            QPushButton#cdTrackPlayButton{background:#6b1717;color:#fff;border:1px solid #8f2929;border-radius:7px;font-size:15px;font-weight:900;}
            QPushButton#cdTrackPlayButton:hover{background:#842020;border-color:#b43a3a;}
        """)

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

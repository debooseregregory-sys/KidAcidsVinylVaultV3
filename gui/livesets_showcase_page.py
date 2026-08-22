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
    play_requested = Signal(str)

    def __init__(self, data, parent=None):
        super().__init__(parent)
        self.data = data
        self._playing = False
        self._pixmap = QPixmap()
        self.setFixedWidth(322)
        self._build()

    def _build(self):
        self.setObjectName("liveCard")
        root = QVBoxLayout(self)
        root.setContentsMargins(9, 9, 9, 10)
        root.setSpacing(6)

        self.cover = QLabel("GEEN COVER")
        self.cover.setObjectName("liveCover")
        self.cover.setFixedSize(304, 171)
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

        meta = " • ".join(
            x for x in [str(self.data.get("date") or ""), str(self.data.get("location") or "")] if x
        )
        meta_label = QLabel(meta or "Geen datum / locatie")
        meta_label.setObjectName("liveMeta")
        meta_label.setWordWrap(True)
        root.addWidget(meta_label)

        row = QHBoxLayout()
        row.setContentsMargins(0, 1, 0, 0)
        detail = QLabel(str(self.data.get("duration") or "LIVESET"))
        detail.setObjectName("liveMeta")
        row.addWidget(detail, 1)

        self.play = QPushButton("▶")
        self.play.setObjectName("cdTrackPlayButton")
        self.play.setProperty("playing", False)
        self.play.setFixedSize(42, 34)
        self.play.setCursor(Qt.CursorShape.PointingHandCursor)
        self.play.clicked.connect(self._clicked)
        row.addWidget(self.play)
        root.addLayout(row)

    def _load_cover(self):
        path = str(self.data.get("cover") or "")
        if not path or not Path(path).exists():
            return
        pix = QPixmap(path)
        if pix.isNull():
            return
        scaled = pix.scaled(
            self.cover.size(),
            Qt.AspectRatioMode.KeepAspectRatioByExpanding,
            Qt.TransformationMode.SmoothTransformation,
        )
        x = max(0, (scaled.width() - self.cover.width()) // 2)
        y = max(0, (scaled.height() - self.cover.height()) // 2)
        self.cover.setText("")
        self.cover.setPixmap(scaled.copy(x, y, self.cover.width(), self.cover.height()))

    def _clicked(self):
        path = str(self.data.get("audio") or "").strip()
        if path:
            self.play_requested.emit(path)

    def set_playing(self, value):
        self._playing = bool(value)
        self.play.setProperty("playing", self._playing)
        self.play.setText("❚❚" if self._playing else "▶")
        self.play.style().unpolish(self.play)
        self.play.style().polish(self.play)
        self.play.update()


class LivesetsShowcasePage(QWidget):
    """Compact standalone Livesets showcase using the same card proportions as Vinyl."""

    play_mp3 = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.active_path = None
        self.cards = []
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

        sub = QLabel("Je livesets — eigen showcase, los van vinyl en CD")
        sub.setObjectName("showcaseSub")
        root.addWidget(sub)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop)
        scroll.setStyleSheet("QScrollArea{border:0;background:transparent;}")

        self.content = QWidget()
        self.grid = QGridLayout(self.content)
        self.grid.setContentsMargins(8, 14, 8, 20)
        self.grid.setHorizontalSpacing(16)
        self.grid.setVerticalSpacing(16)
        self.grid.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop)
        scroll.setWidget(self.content)
        root.addWidget(scroll, 1)

        self.setStyleSheet("""
            QLabel#showcaseTitle{color:#fff;font-size:26px;font-weight:900;}
            QLabel#showcaseSub{color:#858591;font-size:13px;}
            QFrame#showcaseLine{background:#ffcf72;border-radius:1px;}
            QFrame#liveCard{background:#121217;border:1px solid #292933;border-radius:9px;}
            QFrame#liveCard:hover{background:#17171e;border-color:#5b5b6b;}
            QLabel#liveCover{background:#07070a;color:#666671;border:1px solid #2a2a33;border-radius:6px;}
            QLabel#liveArtist{color:#ffcf72;font-size:12px;font-weight:800;}
            QLabel#liveTitle{color:#fff;font-size:15px;font-weight:900;}
            QLabel#liveMeta{color:#858591;font-size:11px;}
            QPushButton#cdTrackPlayButton{background:#6b1717;color:#fff;border:1px solid #8f2929;border-radius:7px;font-size:15px;font-weight:900;}
            QPushButton#cdTrackPlayButton:hover{background:#842020;border-color:#b43a3a;}
            QPushButton#cdTrackPlayButton[playing="true"]{background:#1f7a3d;border-color:#35a65b;}
            QPushButton#cdTrackPlayButton[playing="true"]:hover{background:#29934a;border-color:#4fc874;}
        """)

    def reload(self):
        while self.grid.count():
            item = self.grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self.cards = []

        try:
            items = json.loads(LIVESETS_FILE.read_text(encoding="utf-8")) if LIVESETS_FILE.exists() else []
        except (OSError, json.JSONDecodeError):
            items = []

        for i, data in enumerate(items):
            card = LivesetShowcaseCard(data)
            card.play_requested.connect(self._play)
            self.cards.append(card)
            self.grid.addWidget(card, i // 3, i % 3)

        self._sync()

    @staticmethod
    def _normal(path):
        try:
            return str(Path(str(path or "")).expanduser().resolve()).casefold()
        except OSError:
            return str(path or "").casefold()

    def _play(self, path):
        self.active_path = self._normal(path)
        self._sync()
        self.play_mp3.emit(path)

    def set_active_track(self, path):
        self.active_path = self._normal(path)
        self._sync()

    def clear_active_track(self):
        self.active_path = None
        self._sync()

    def set_playback_state(self, state):
        try:
            from PySide6.QtMultimedia import QMediaPlayer
            if state != QMediaPlayer.PlaybackState.PlayingState:
                self.clear_active_track()
        except Exception:
            self.clear_active_track()

    def _sync(self):
        for card in self.cards:
            card.set_playing(
                bool(self.active_path)
                and self._normal(card.data.get("audio")) == self.active_path
            )

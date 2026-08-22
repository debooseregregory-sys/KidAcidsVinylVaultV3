from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QEasingCurve, QPropertyAnimation, Qt, Signal
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget


class LivesetDetailPage(QWidget):
    """Dedicated Liveset playback view, visually aligned with the existing release detail pages."""

    back_requested = Signal()
    play_mp3 = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.data = {}
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(28, 24, 28, 24)
        root.setSpacing(16)

        self.back_button = QPushButton("‹  TERUG NAAR LIVESETS")
        self.back_button.setObjectName("detailBack")
        self.back_button.clicked.connect(self.back_requested.emit)
        root.addWidget(self.back_button, 0, Qt.AlignmentFlag.AlignLeft)

        panel = QFrame()
        panel.setObjectName("detailPanel")
        panel_layout = QHBoxLayout(panel)
        panel_layout.setContentsMargins(22, 22, 22, 22)
        panel_layout.setSpacing(24)

        self.cover = QLabel("GEEN COVER")
        self.cover.setObjectName("detailCover")
        self.cover.setFixedSize(440, 248)
        self.cover.setAlignment(Qt.AlignmentFlag.AlignCenter)
        panel_layout.addWidget(self.cover, 0, Qt.AlignmentFlag.AlignTop)

        info = QVBoxLayout()
        info.setSpacing(8)

        self.kicker = QLabel("LIVESET")
        self.kicker.setObjectName("detailKicker")
        info.addWidget(self.kicker)

        self.title = QLabel("(geen titel)")
        self.title.setObjectName("detailTitle")
        self.title.setWordWrap(True)
        info.addWidget(self.title)

        self.artist = QLabel("")
        self.artist.setObjectName("detailArtist")
        info.addWidget(self.artist)

        self.meta = QLabel("")
        self.meta.setObjectName("detailMeta")
        self.meta.setWordWrap(True)
        info.addWidget(self.meta)

        info.addStretch(1)

        self.play_button = QPushButton("▶  PLAY LIVESET")
        self.play_button.setObjectName("detailPlay")
        self.play_button.setFixedHeight(48)
        self.play_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.play_button.clicked.connect(self._play)
        info.addWidget(self.play_button)

        panel_layout.addLayout(info, 1)
        root.addWidget(panel)
        root.addStretch(1)

        self.setStyleSheet("""
            QFrame#detailPanel{background:#121217;border:1px solid #292933;border-radius:12px;}
            QLabel#detailCover{background:#07070a;color:#666671;border:1px solid #2a2a33;border-radius:8px;}
            QLabel#detailKicker{color:#ffcf72;font-size:11px;font-weight:900;letter-spacing:1px;}
            QLabel#detailTitle{color:#fff;font-size:30px;font-weight:900;}
            QLabel#detailArtist{color:#e7e7eb;font-size:16px;font-weight:800;}
            QLabel#detailMeta{color:#858591;font-size:13px;}
            QPushButton#detailBack{background:transparent;color:#aaaab4;border:0;padding:6px 2px;font-size:12px;font-weight:800;}
            QPushButton#detailBack:hover{color:#ffcf72;}
            QPushButton#detailPlay{background:#6b1717;color:#fff;border:1px solid #8f2929;border-radius:8px;font-size:13px;font-weight:900;}
            QPushButton#detailPlay:hover{background:#842020;border-color:#b43a3a;}
        """)

    @staticmethod
    def _crop(path: str, size):
        pix = QPixmap(path) if path and Path(path).exists() else QPixmap()
        if pix.isNull():
            return QPixmap()
        scaled = pix.scaled(size, Qt.AspectRatioMode.KeepAspectRatioByExpanding, Qt.TransformationMode.SmoothTransformation)
        x = max(0, (scaled.width() - size.width()) // 2)
        y = max(0, (scaled.height() - size.height()) // 2)
        return scaled.copy(x, y, size.width(), size.height())

    def load_liveset(self, data):
        self.data = dict(data or {})
        self.title.setText(str(self.data.get("title") or "(geen titel)"))
        self.artist.setText(str(self.data.get("artist") or "LIVESET"))
        meta = " • ".join(x for x in [str(self.data.get("date") or ""), str(self.data.get("location") or ""), str(self.data.get("duration") or "")] if x)
        self.meta.setText(meta)
        pix = self._crop(str(self.data.get("cover") or ""), self.cover.size())
        if pix.isNull():
            self.cover.setPixmap(QPixmap())
            self.cover.setText("GEEN COVER")
        else:
            self.cover.setText("")
            self.cover.setPixmap(pix)
        self.play_button.setProperty("playing", False)
        self.play_button.setText("▶  PLAY LIVESET")
        self.play_button.style().unpolish(self.play_button)
        self.play_button.style().polish(self.play_button)
        self._animate_open()

    def _animate_open(self):
        self.setWindowOpacity(0.0)
        animation = QPropertyAnimation(self, b"windowOpacity", self)
        animation.setDuration(320)
        animation.setStartValue(0.0)
        animation.setEndValue(1.0)
        animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._open_animation = animation
        animation.start()

    def _play(self):
        path = str(self.data.get("audio") or "").strip()
        if path:
            self.play_mp3.emit(path)

    def set_active_track(self, path):
        current = str(self.data.get("audio") or "").casefold()
        active = str(path or "").casefold()
        playing = bool(current and active and Path(current).name.casefold() == Path(active).name.casefold())
        self.play_button.setProperty("playing", playing)
        self.play_button.setText("❚❚  PLAYING" if playing else "▶  PLAY LIVESET")
        self.play_button.style().unpolish(self.play_button)
        self.play_button.style().polish(self.play_button)

    def clear_active_track(self):
        self.play_button.setProperty("playing", False)
        self.play_button.setText("▶  PLAY LIVESET")
        self.play_button.style().unpolish(self.play_button)
        self.play_button.style().polish(self.play_button)

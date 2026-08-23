from __future__ import annotations
from gui.app_settings import paint_accent

import math
from pathlib import Path

from PySide6.QtCore import QEasingCurve, QPropertyAnimation, Qt, Signal, QTimer
from PySide6.QtGui import QPixmap, QPainter, QPen, QBrush, QFont
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget


class LivesetPlayerVisualizer(QWidget):
    """Animated visual that lives on the actual liveset playback page."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(180)
        self.setMaximumHeight(180)
        self._phase = 0.0
        self._text_offset = 0.0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._animate)
        self._timer.start(30)

    def _animate(self):
        self._phase = (self._phase + 0.055) % (math.pi * 2)
        self._text_offset = (self._text_offset + 1.4) % 1200
        self.update()

    def paintEvent(self, event):
        del event
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = self.rect().adjusted(1, 1, -1, -1)

        painter.setBrush(QBrush(Qt.GlobalColor.black))
        painter.setPen(QPen(Qt.GlobalColor.transparent))
        painter.drawRoundedRect(rect, 14, 14)

        # Soft moving particles.
        for i in range(28):
            angle = self._phase * (0.45 + (i % 6) * 0.07) + i * 0.71
            x = rect.left() + rect.width() * (0.5 + 0.48 * math.sin(angle * 0.67 + i))
            y = rect.top() + 88 + 62 * math.sin(angle * 1.27 + i * 0.37)
            radius = 1.0 + 2.8 * (0.5 + 0.5 * math.sin(angle * 1.8))
            painter.setBrush(QBrush(Qt.GlobalColor.darkMagenta))
            painter.setPen(QPen(Qt.GlobalColor.darkMagenta))
            painter.drawEllipse(int(x - radius), int(y - radius), int(radius * 2), int(radius * 2))

        # Large central pulse.
        cx = rect.center().x()
        cy = rect.top() + 66
        pulse = 22 + 10 * (0.5 + 0.5 * math.sin(self._phase * 2.0))
        painter.setBrush(QBrush(Qt.GlobalColor.transparent))
        painter.setPen(QPen(Qt.GlobalColor.magenta, 2.2))
        painter.drawEllipse(int(cx - pulse), int(cy - pulse), int(pulse * 2), int(pulse * 2))
        painter.setPen(QPen(Qt.GlobalColor.darkMagenta, 1.2))
        painter.drawEllipse(int(cx - pulse - 11), int(cy - pulse - 11), int((pulse + 11) * 2), int((pulse + 11) * 2))
        painter.setBrush(QBrush(Qt.GlobalColor.magenta))
        painter.setPen(QPen(Qt.GlobalColor.magenta))
        painter.drawEllipse(int(cx - 5), int(cy - 5), 10, 10)

        # Wide animated waveform / equalizer.
        bar_count = 72
        usable = rect.width() - 36
        step = usable / bar_count
        for i in range(bar_count):
            wave = (
                math.sin(self._phase * 2.4 + i * 0.37)
                + 0.62 * math.sin(self._phase * 4.1 - i * 0.19)
                + 0.30 * math.sin(self._phase * 1.3 + i * 0.83)
            ) / 1.92
            height = 10 + (wave + 1.0) * 26
            x = rect.left() + 18 + i * step
            y = rect.bottom() - 15 - height
            painter.setPen(QPen(Qt.GlobalColor.magenta, 2.0))
            painter.drawLine(int(x), int(rect.bottom() - 15), int(x), int(y))

        # Moving title line.
        text = "KID ACID  •  LIVESET  •  ACID HOUSE  •  TECHNO  •  DEEP GROOVES  •  LIVE ENERGY  •  "
        font = QFont("Arial", 9, QFont.Weight.Bold)
        painter.setFont(font)
        painter.setPen(QPen(Qt.GlobalColor.lightGray))
        width = painter.fontMetrics().horizontalAdvance(text)
        x = rect.right() - int(self._text_offset % (width + 60))
        y = rect.top() + 23
        painter.drawText(int(x), y, text)
        painter.drawText(int(x + width + 60), y, text)

        painter.setFont(QFont("Arial", 8, QFont.Weight.Bold))
        painter.setPen(QPen(Qt.GlobalColor.gray))
        painter.drawText(rect.left() + 18, rect.top() + 43, "NOW PLAYING  •  THE UNDERGROUND NEVER STOPS")
        painter.end()


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

        # This is deliberately below the player/details panel: the visual reacts
        # continuously while the liveset is being listened to.
        self.visualizer = LivesetPlayerVisualizer()
        root.addWidget(self.visualizer)

        root.addStretch(1)

        self.setStyleSheet(paint_accent("""
            QFrame#detailPanel{background:#121217;border:1px solid #292933;border-radius:12px;}
            QLabel#detailCover{background:#07070a;color:#666671;border:1px solid #2a2a33;border-radius:8px;}
            QLabel#detailKicker{color:#ffcf72;font-size:11px;font-weight:900;letter-spacing:1px;}
            QLabel#detailTitle{color:#fff;font-size:30px;font-weight:900;}
            QLabel#detailArtist{color:#e7e7eb;font-size:16px;font-weight:800;}
            QLabel#detailMeta{color:#858591;font-size:13px;}
            QPushButton#detailBack{background:transparent;color:#aaaab4;border:0;padding:6px 2px;font-size:12px;font-weight:800;}
            QPushButton#detailBack:hover{color:#ffcf72;}
            QPushButton#detailPlay{background:#2a1524;color:#ff4fa3;border:1px solid #5a2a48;border-radius:10px;font-size:13px;font-weight:900;}
            QPushButton#detailPlay:hover{background:#ff4fa3;color:#0e0e12;border-color:#ff4fa3;}
            QPushButton#detailPlay[playing="true"]{background:#3a1a30;color:#ff6bb5;border-color:#ff4fa3;}
        """))

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
